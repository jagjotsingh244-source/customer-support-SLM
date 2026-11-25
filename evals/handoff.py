"""Hand-off decisions in both directions, from saved traces: what the model did, and what the code rules in
agent/escalation.py would have added.

    uv run python evals/handoff.py <run> [<run> ...]            # one section per run, then one per system
    uv run python evals/handoff.py <run> ... --tickets          # also every ticket: the model's summary and
                                                                # the one ticket_summary() builds from the state

Missing a needed hand-off is the expensive error (a customer with a lost parcel or a payment dispute left with a
bot); handing off too often defeats the point of Nova. So both directions are counted:

    recall      needed hand-offs that happened / needed hand-offs
    precision   needed hand-offs that happened / hand-offs that happened

What "needed" means, per case set:
    golden, fresh   expect.should_escalate (evals/validate.py load(), load(FRESH))
    simulated       expect.ticket (evals/simulated/cases.jsonl); ticket_offer_ok cases accept an offer too

What "happened" means is the scorer's own definition, so these numbers agree with the reports:
    golden, fresh   trace["escalated"]: a successful escalate_to_human call, or the loop's fallback reply
                    ("Let me connect you with a teammate."), which sets the same flag (evals/run_eval.py score())
    simulated       a ticket opened: a successful escalate_to_human call (evals/metrics.py end_state()); the
                    fallback reply alone opens no ticket
The other kind is shown next to it (fallback-only hand-offs), never merged silently.

The offer: in an unanswerable case (golden, fresh) or a ticket_offer_ok case (simulated), an explicit offer to
hand off ("Would you like me to connect you with our support team?") stands in for the call in the scorer
(run_eval.offered_handoff, metrics.HANDOFF_OFFER). It is reported as a separate recall, "with offers".

The replay ("model + code rules"): each conversation is walked turn by turn. Per turn, the customer's message
and that turn's tool results (as saved) go to escalation.must_escalate(), with the count of turns without
progress *before* this turn (the loop checks it when the customer's message arrives; the lost-parcel rule after
a tracking result); then escalation.Progress.end_turn() updates the count with this turn. The replayed outcome
is: the model handed off, or a rule fired on some turn. This is an estimate: after a forced hand-off the rest
of the conversation would have gone differently, and turns the model never reached are not replayed.

Intervals are 95% bootstrap intervals (evals/metrics.py rate()), resampling hand-offs (precision) or needed
cases (recall). Pooled over repeated runs they resample case-runs, not cases, so they are a little narrow.
"""

import argparse
import json
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from agent import escalation  # noqa: E402
from agent.state import State, parse_args  # noqa: E402
from config import now  # noqa: E402
from evals.metrics import _result, fmt_rate, rate  # noqa: E402
from evals.run_eval import RUNS, offered_handoff, read_traces  # noqa: E402

FALLBACK_REPLY = "Let me connect you with a teammate."   # agent/loop.py FALLBACK_REPLY
SIMULATED = ROOT / "evals" / "simulated" / "cases.jsonl"


# Ground truth ---------------------------------------------------------------------------------------------

@dataclass
class Truth:
    needed: bool
    offer_ok: bool           # an explicit offer stands in for the hand-off
    category: str


def truths(case_set: str) -> dict[str, Truth]:
    if case_set == "simulated":
        out = {}
        for line in SIMULATED.read_text().splitlines():
            if line.strip():
                c = json.loads(line)
                out[c["id"]] = Truth(c["expect"]["ticket"], c["expect"]["ticket_offer_ok"], c["category"])
        return out
    from evals.validate import FRESH, load
    cases, _ = load(FRESH) if case_set == "fresh" else load()
    return {c.id: Truth(c.expect.should_escalate, c.category == "unanswerable", c.category) for _, c in cases}


# Reading one trace -----------------------------------------------------------------------------------------

def customer_messages(trace: dict) -> list[str]:
    return [m.get("content") or "" for m in trace.get("messages", []) if m.get("role") == "user"]


def turn_calls(turn: dict) -> list[dict]:
    """A turn's tool calls as Progress.end_turn() reads them: name, parsed result, ok, parsed arguments."""
    out = []
    for c in turn.get("tool_calls", []):
        r = _result(c) if not isinstance(c.get("result"), list) else c["result"]
        ok = c.get("ok", not (isinstance(r, dict) and "error" in r))
        out.append({"name": c["name"], "result": r, "ok": bool(ok), "args": parse_args(c.get("args"))})
    return out


def tickets(trace: dict) -> list[tuple[int, dict]]:
    """(turn index, call) for every successful escalate_to_human call."""
    return [(i, c) for i, t in enumerate(trace.get("turns", [])) for c in turn_calls(t)
            if c["name"] == "escalate_to_human" and c["ok"]]


def fallback_turns(trace: dict) -> list[int]:
    return [i for i, t in enumerate(trace.get("turns", [])) if t.get("reply") == FALLBACK_REPLY]


@dataclass
class Fired:
    turn: int                 # 0-based customer turn
    rule: escalation.Escalation
    counter_before: int


def replay(trace: dict, when=None) -> list[Fired]:
    """Every turn on which a rule would have fired. The counter passed for turn i is the one left by turns
    before i; this turn's calls update it only afterwards."""
    when = when or now()
    progress = escalation.Progress()
    fired = []
    for i, (msg, turn) in enumerate(zip(customer_messages(trace), trace.get("turns", []))):
        calls = turn_calls(turn)
        before = progress.turns_without_progress
        results = [c["result"] for c in calls if isinstance(c["result"], dict)]
        if hit := escalation.must_escalate(msg, before, results, when):
            fired.append(Fired(i, hit, before))
            break                                   # the loop hands off once; nothing fires after a ticket
        if any(c["name"] == "escalate_to_human" and c.get("ok") for c in calls):
            break                                   # the model's own ticket: the rules stay quiet from here
        progress.end_turn(msg, calls, turn.get("reply"))
    return fired


# One case -------------------------------------------------------------------------------------------------

@dataclass
class CaseResult:
    id: str
    category: str
    needed: bool
    model: bool                  # handed off, the scorer's definition for this case set
    ticket: bool                 # a successful escalate_to_human call
    fallback: bool               # the loop's fallback reply on some turn
    offered: bool                # an offer where one is accepted, and no hand-off
    fired: list[Fired] = field(default_factory=list)
    model_turn: int | None = None   # first turn with a hand-off (the scorer's definition)
    ticket_turn: int | None = None  # first turn with a ticket opened
    last_msg: str = ""
    person_ask: bool = False     # simulated: the scorer accepts an unexpected ticket after a person ask

    @property
    def first_rule(self) -> Fired | None:
        return self.fired[0] if self.fired else None

    @property
    def replayed(self) -> bool:
        return self.model or bool(self.fired)


def judge_case(trace: dict, truth: Truth, case_set: str, when=None) -> CaseResult:
    msgs = customer_messages(trace)
    ts = tickets(trace)
    fb = fallback_turns(trace)
    ticket = bool(ts)
    model = ticket if case_set == "simulated" else bool(trace.get("escalated"))
    if case_set == "simulated":
        offered = truth.offer_ok and not ticket and any(offered_handoff(r) for r in trace.get("replies", []))
    else:
        offered = truth.needed and truth.offer_ok and not model and offered_handoff(trace.get("final_reply"))
    turns = [i for i, _ in ts] + ([] if case_set == "simulated" else fb)
    person = False
    if case_set == "simulated":
        from synth.verify import PERSON_ASK
        upto = msgs[: (ts[0][0] + 1)] if ts else msgs
        person = bool(PERSON_ASK.search(" ".join(upto)))
    return CaseResult(trace["id"], truth.category, truth.needed, model, ticket, bool(fb), offered,
                      replay(trace, when), min(turns) if turns else None, ts[0][0] if ts else None,
                      (msgs[-1] if msgs else ""), person)


# Arithmetic -----------------------------------------------------------------------------------------------

def precision_recall(rows: list[CaseResult], replayed: bool = False) -> dict:
    """Counts and rates. `replayed` uses the model + rules outcome."""
    did = [(r.replayed if replayed else r.model) for r in rows]
    tp = sum(d and r.needed for d, r in zip(did, rows))
    handoffs = sum(did)
    needed = sum(r.needed for r in rows)
    offers = sum(r.offered and r.needed and not d for d, r in zip(did, rows))
    return {
        "cases": len(rows), "needed": needed, "handoffs": handoffs, "tp": tp,
        "missed": needed - tp, "unneeded": handoffs - tp,
        "precision": rate([r.needed for d, r in zip(did, rows) if d]),
        "recall": rate([d for d, r in zip(did, rows) if r.needed]),
        "recall_offer": rate([d or r.offered for d, r in zip(did, rows) if r.needed]),
        "offers": offers,
    }


# Output ---------------------------------------------------------------------------------------------------

def short(text: str, n: int = 90) -> str:
    text = " ".join((text or "").split()).replace("|", "/")
    return text if len(text) <= n else text[: n - 1] + "…"


def rule_text(f: Fired | None) -> str:
    return f"{f.rule.reason} (turn {f.turn + 1})" if f else "none"


def table(named: list[tuple[str, list[CaseResult]]], case_set: str) -> list[str]:
    out = ["| | cases | needed | hand-offs | fallback-only | recall | recall with offers | precision | missed | unneeded |",
           "|---|---|---|---|---|---|---|---|---|---|"]
    for name, rows in named:
        for label, rp in (("model only", False), ("model + code rules", True)):
            m = precision_recall(rows, rp)
            fb_only = "-" if rp else str(sum(r.fallback and not r.ticket for r in rows))
            out.append(f"| {name}, {label} | {m['cases']} | {m['needed']} | {m['handoffs']} | {fb_only} | "
                       f"{fmt_rate(m['recall'])} | {fmt_rate(m['recall_offer'])} | {fmt_rate(m['precision'])} | "
                       f"{m['missed']} | {m['unneeded']} |")
    if case_set == "simulated":
        out.append("")
        out.append("Simulated runs count a ticket as the hand-off (as the scorecard does); fallback-only is the "
                   "number of conversations with a fallback reply and no ticket, counted as no hand-off.")
    return out


def miss_lines(rows: list[CaseResult], case_set: str) -> list[str]:
    out = []
    missed = [r for r in rows if r.needed and not r.model]
    unneeded = [r for r in rows if r.model and not r.needed]
    added = [r for r in rows if not r.model and r.fired and not r.needed]
    for title, group, what in (("Missed hand-offs (needed, the model did not)", missed, "missed"),
                               ("Unneeded hand-offs (the model handed off, not needed)", unneeded, "unneeded"),
                               ("Unneeded hand-offs the rules would add", added, "added")):
        out += ["", f"**{title}: {len(group)}**", ""]
        if not group:
            continue
        out += ["| case | category | rule | after the rules | how | last customer message |", "|---|---|---|---|---|---|"]
        for r in group:
            if what == "missed":
                after = "caught" if r.fired else "still missed"
                how = "offered" if r.offered else ""
            elif what == "unneeded":
                after = "unchanged"
                how = "fallback reply" if not r.ticket else ("ticket; customer asked for a person" if r.person_ask
                                                            else "ticket")
            else:
                after = "added"
                how = "customer asked for a person" if r.person_ask else ""
            out.append(f"| {r.id} | {r.category} | {rule_text(r.first_rule)} | {after} | {how} | {short(r.last_msg)} |")
    return out


def load_run(run: str, when=None) -> tuple[dict, list[CaseResult]]:
    out = RUNS / run
    config = json.loads((out / "config.json").read_text())
    case_set = config.get("case_set", "golden")
    truth = truths(case_set)
    rows = [judge_case(t, truth[t["id"]], case_set, when) for t in read_traces(out)
            if "error" not in t and t["id"] in truth]
    return config, rows


def system_name(config: dict) -> str:
    return f"{config.get('model')} ({config.get('case_set', 'golden')})"


def ticket_lines(run: str, rows_by_id: dict[str, CaseResult], when=None) -> list[str]:
    """Every successful escalate_to_human call in a run: the model's summary, and ticket_summary() rebuilt
    from the state the loop would have had at that point."""
    out = []
    for trace in read_traces(RUNS / run):
        if "error" in trace or trace["id"] not in rows_by_id:
            continue
        msgs = customer_messages(trace)
        state, tools_called = State(), []
        fired = {f.turn: f for f in rows_by_id[trace["id"]].fired}
        for i, turn in enumerate(trace.get("turns", [])):
            for c in turn_calls(turn):
                if c["name"] == "escalate_to_human" and c["ok"]:
                    args = c["args"] or {}
                    rule = next((fired[j].rule for j in sorted(fired) if j <= i), None)
                    reason = rule or escalation.Escalation(f"model: {args.get('reason', '?')}", args.get("reason", "other"))
                    rebuilt = escalation.ticket_summary(state, reason, msgs[: i + 1], tools_called)
                    out += [f"- **{run} / {trace['id']}**, turn {i + 1}, reason `{args.get('reason')}`, "
                            f"rule: {rule.reason if rule else 'none'}",
                            f"  - model: {args.get('summary')!r}",
                            f"  - rebuilt: {rebuilt!r}",
                            f"  - customer said: {' / '.join(short(m, 120) for m in msgs[: i + 1])}"]
                if isinstance(c["result"], dict):
                    state.update(c["name"], c["args"], c["result"])
                tools_called.append(c["name"])
    return out


def report(runs: list[str], show_tickets: bool = False) -> str:
    lines = ["# Hand-off decisions: model only, and model + code rules (replayed)", "",
             "The replay is an estimate: after a forced hand-off the conversation would have gone differently, "
             "so a rule's effect on later turns is not shown.", ""]
    systems: dict[str, list[CaseResult]] = defaultdict(list)
    sets = {}
    for run in runs:
        config, rows = load_run(run)
        name = system_name(config)
        systems[name] += rows
        sets[name] = config.get("case_set", "golden")
        lines += [f"## {run}", "", f"model `{config.get('model')}`, cases `{config.get('case_set')}`, "
                  f"{len(rows)} traces scored", ""]
        lines += table([(run, rows)], sets[name])
        lines += miss_lines(rows, sets[name])
        if show_tickets:
            lines += ["", "Tickets:", ""] + ticket_lines(run, {r.id: r for r in rows})
        lines.append("")
    if len(runs) > 1:
        lines += ["## Pooled per system", ""]
        for cs in dict.fromkeys(sets.values()):
            lines += table([(n, rs) for n, rs in systems.items() if sets[n] == cs], cs) + [""]
        lines += ["## Rules that fired (first per conversation), pooled", "",
                  "Where the first rule fired against when the model handed off: *model later* means the rule was "
                  "first (it would have moved the hand-off earlier); *same turn or earlier*, that the model had "
                  "already handed off. *Again after a ticket* counts every turn, first or not, on which a rule "
                  "fired once a ticket was already open: without a check for an open ticket, each would be a "
                  "second ticket.", "",
                  "| system | rule | needed | not needed | model never handed off | model later | model same turn or earlier | "
                  "again after a ticket (turns) |", "|---|---|---|---|---|---|---|---|"]
        for name, rows in systems.items():
            by = defaultdict(lambda: [0] * 6)
            for r in rows:
                if f := r.first_rule:
                    b = by[f.rule.reason]
                    b[0 if r.needed else 1] += 1
                    b[2 if r.model_turn is None else 3 if r.model_turn > f.turn else 4] += 1
                for f in r.fired:
                    if r.ticket_turn is not None and f.turn > r.ticket_turn:
                        by[f.rule.reason][5] += 1
            for k, v in sorted(by.items()):
                lines.append(f"| {name} | {k} | " + " | ".join(map(str, v)) + " |")
    return "\n".join(lines) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("runs", nargs="+", help="run folders under evals/runs/")
    ap.add_argument("--tickets", action="store_true", help="list every ticket with the rebuilt summary")
    a = ap.parse_args()
    print(report(a.runs, a.tickets))


if __name__ == "__main__":
    main()
