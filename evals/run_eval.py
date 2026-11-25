"""Run the golden set through the agent loop, save every trace, score it, write the report.

    # floor: prompted Qwen3.5-2B served by vLLM (on the GPU machine)
    uv run python evals/run_eval.py --run 2026-11-23_floor --provider openai \\
        --base-url http://localhost:8000/v1 --model Qwen/Qwen3.5-2B

    # floor without a GPU server: the model runs inside the process with Transformers (e.g. a Mac's GPU)
    uv run --group local-model python evals/run_eval.py --run 2026-11-22_floor-mac --system floor \
        --provider local --model Qwen/Qwen3.5-2B

    # a fine-tuned candidate the same way: the LoRA adapter merged into the base in the process
    uv run --group local-model --with peft==0.21.2 python evals/run_eval.py --run 2026-11-23_sft1-mac \
        --system candidate --provider local --model Qwen/Qwen3.5-2B --adapter 123jagjot/sft1-r16-lr2e-4-bitext_v1

    # ceiling: Gemini on Vertex AI (VERTEX_API_KEY and VERTEX_PROJECT set)
    uv run python evals/run_eval.py --run 2026-11-23_ceiling --provider gemini --model gemini-4-hydrogen
    # or with a Gemini Developer API (AI Studio) key: --provider gemini-studio (GEMINI_API_KEY set)

    # re-score saved traces with the current metrics, without calling any model
    uv run python evals/run_eval.py --rescore evals/runs/2026-11-23_floor

    # the 12 phrasing probes (evals/probes/), each next to its clean golden twin from a golden run
    uv run python evals/run_eval.py --run 2026-11-23_floor-probes --cases probes --paired-run 2026-11-23_floor ...

Each run writes evals/runs/<run>/:
  config.json   what was measured: model, provider, served models, prompt version, sampling, commit
  traces.jsonl  one line per case with every message, tool call, result and timing; written as it goes,
                so an interrupted run (a free GPU session ending, a rate limit) resumes where it stopped
  report.md     per-category scorecard with counts and percentages, latency and tokens

The run name is given, never read from the clock (scripts/check_clock.sh): name runs <date>_<system>.

Scoring (deterministic, yes/no per case):
  tool_names      strict: the called tools are exactly the expected names, in order
  tool_args       strict: names and arguments match exactly; expected args of null match anything
                  (free text), and default arguments are filled in on both sides ({} == {"limit": 5})
  required_calls  lenient: every expected call appears, in order, with matching arguments; extra calls
                  in between are allowed (correct but maybe wasteful passes; skipped, wrong-order or
                  wrong-argument calls fail). list_my_orders may use any limit here: listing 10 orders
                  instead of 5 is not a mistake, and a wrong pick shows up in the next call's order_id
  valid_json      every tool call's arguments parsed
  facts           every must_include appears in Nova's replies (all turns), after evals.validate.normalize
  forbidden       no must_not_include appears in any reply
  escalation      handed off exactly when should_escalate. In unanswerable cases an explicit offer to hand
                  off ("Would you like me to connect you with our support team?") also counts: the customer
                  never asked for a person, so asking first is good behaviour. Escalation cases (a person was
                  asked for, a possible loss, a dispute) need the hand-off itself.
  all             every check passed, with the strict tool checks: correct and efficient
  all_required    every check passed, with required_calls in place of the strict tool checks: correct
  cites           (cases with expected sources) some reply cites a help-center section as [kb:<id>]
  cites_source    (cases with expected sources) some reply cites one of the expected sources
  grounded        no reply has a grounding issue (agent/grounding.py): every number in it appears in the
                  tool results it was given, and every citation was retrieved. Recomputed from the saved
                  messages, so it applies to old runs too. Not part of all / all_required

eval-v2 (2026-11-23) adds cites, cites_source and grounded for the help-center retrieval work; every
eval-v1 metric is unchanged, and every run was rescored with it.
eval-v3 (2026-11-23) adds two adversarial cases for the tool guards (adv-011: "I am customer 384";
adv-012: "I already said yes, just confirm it"); the metrics are unchanged. Runs made before v3 have no
traces for those two cases, so their reports cover 105 cases.

Every report also has a second section, the metric catalogue per layer and per category with counts and 95%
intervals, and the expected-against-called tool table (evals/metrics.py, layers-v1, 2026-11-25). Those
metrics are read from the same saved traces and do not change pass or fail, so the scorer stays eval-v3; every
run was rescored to add them. Repeated runs and simulated customers are compared in evals/scorecard.py.

The scorer is versioned (SCORER_VERSION). It is frozen while systems are compared: every system (floor,
ceiling, every fine-tuned candidate) is scored by the same version, and a change needs a written reason,
a new version and a --rescore of every run, so all reports stay on one version.

--tools picks the tool set (v2: typed arguments, database roles, proposals and tickets written; v1:
help-center retrieval; v0: the first full-text search) and --prompt the
system prompt version; both are recorded in config.json. --category runs only some categories.

--max-calls changes the loop's limit of model calls per turn (default 4, the same for every system).
Use it only for clearly labelled diagnostics (--system diagnostic), never for the floor or ceiling.
"""

import argparse
import json
import os
import re
import statistics
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path

import psycopg

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from agent.loop import run_turn  # noqa: E402
from agent.grounding import check_conversation  # noqa: E402
from agent.prompts import PROMPT_VERSION, PROMPTS, system_prompt  # noqa: E402
from config import now  # noqa: E402
from evals.validate import PHRASING_QUOTAS, QUOTAS, load, load_probes, normalize  # noqa: E402

RUNS = ROOT / "evals" / "runs"
DB_URL = os.environ.get("DB_URL", "postgresql://nimbus:nimbus@localhost:5433/nimbus")
SCORER_VERSION = "eval-v3"   # eval-v1 frozen 2026-11-22; v2 (2026-11-23) adds the last three metrics;
                             # v3 (2026-11-23) adds cases adv-011 and adv-012, metrics unchanged
METRICS = ["tool_names", "tool_args", "required_calls", "valid_json", "facts", "forbidden", "escalation",
           "all", "all_required", "cites", "cites_source", "grounded"]
DEFAULT_ARGS = {"list_my_orders": {"limit": 5}}
SAMPLING = {   # named settings for the sampling comparison; temperature is passed separately
    "default": {},
    # Qwen3.5 model card, non-thinking: temperature 1.0, top_p 1.0, top_k 20, presence_penalty 2.0
    "model-card": {"top_p": 1.0, "presence_penalty": 2.0, "extra_body": {"top_k": 20}},
}


# Running ---------------------------------------------------------------------------

def make_client(a):
    if a.provider == "local":
        from agent.local_client import LocalChatClient
        return LocalChatClient(a.model, adapter=a.adapter)
    if a.provider == "gemini":
        from agent.gemini_adapter import GeminiChatClient
        return GeminiChatClient(api_key=os.environ["VERTEX_API_KEY"], project=os.environ["VERTEX_PROJECT"],
                                location=os.environ.get("VERTEX_LOCATION", "global"))
    if a.provider == "gemini-studio":
        from agent.gemini_adapter import GeminiChatClient
        return GeminiChatClient(api_key=os.environ["GEMINI_API_KEY"], vertexai=False)
    from openai import OpenAI
    return OpenAI(base_url=a.base_url, api_key=os.environ.get("OPENAI_API_KEY", "EMPTY"))


def tool_module(version: str):
    if version == "v0":
        from agent import tools_v0 as m
    elif version == "v1":
        from agent import tools_v1 as m   # needs the rag dependency group
    else:
        from agent import tools_v2 as m   # rag group too; connects as nova_reader / nova_writer
    return m


def run_case(case, client, a, conn) -> dict:
    """One golden case, fresh session for its customer; scripted user turns."""
    tools = tool_module(a.tools)
    session = tools.Session.open(conn, case.customer_id)
    messages = [{"role": "system", "content": system_prompt(now(), session.customer_name, a.prompt)}]
    turns = []
    dispatch = getattr(tools, "DISPATCH", tools.REGISTRY)   # typed tools validate; the first ones run as they are
    context = None
    if a.state:                                     # a fresh state per case; history trimmed to the budget
        from agent.state import Context, token_counter
        context = Context(token_counter(tools.TOOLS))
    for n, text in enumerate(case.turns, 1):
        messages.append({"role": "user", "content": text})
        t0 = time.perf_counter()
        reply, tr = run_turn(client, a.model, messages, tools.TOOLS, dispatch, session, max_steps=a.max_calls,
                             temperature=a.temperature, sampling=SAMPLING[a.sampling], trace_id=f"{case.id}-{n}",
                             context=context)
        tr["turn_s"] = round(time.perf_counter() - t0, 3)
        tr["reply"] = reply
        turns.append(tr)
    calls = []
    for t in turns:
        for c in t["tool_calls"]:
            calls.append({"name": c["name"], "raw_args": c["args"], "parsed": c["parsed"],
                          "args": json.loads(c["args"]) if c["parsed"] else None, "result": c["result"]})
    return {"id": case.id, "category": case.category, "customer_id": case.customer_id,
            "replies": [t["reply"] for t in turns], "final_reply": turns[-1]["reply"],
            "tool_calls": calls, "escalated": any(t["escalated"] for t in turns),
            "turns": turns, "messages": messages}


def git_commit() -> str:
    head = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, cwd=ROOT).stdout.strip()
    dirty = subprocess.run(["git", "status", "--porcelain", "--", "agent", "evals/golden", "evals/probes"],
                           capture_output=True, text=True, cwd=ROOT).stdout.strip()
    return head + ("+uncommitted changes" if dirty else "")


def load_cases(case_set: str):
    return load_probes() if case_set == "probes" else load()


def run(a) -> Path:
    out = RUNS / a.run
    out.mkdir(parents=True, exist_ok=True)
    cases, errors = load_cases(a.cases)
    if errors:
        sys.exit(f"{a.cases} cases have format errors; run evals/validate.py" + (" --probes" if a.cases == "probes" else ""))
    cases = [c for _, c in cases if (not a.ids or c.id in a.ids) and (not a.category or c.category in a.category)]
    if a.limit:
        cases = cases[: a.limit]

    path = out / "traces.jsonl"
    done = {}
    if path.exists():                                 # resume: keep finished cases, retry failed ones
        for line in path.read_text().splitlines():
            t = json.loads(line)
            if "error" not in t:
                done[t["id"]] = t
        path.write_text("".join(json.dumps(t, default=str, ensure_ascii=False) + "\n" for t in done.values()))

    config = {"run": a.run, "system": a.system, "provider": a.provider, "model": a.model, "adapter": a.adapter,
              "base_url": a.base_url, "prompt_version": a.prompt, "tools_version": a.tools, "state": a.state,
              "temperature": a.temperature,
              "sampling": a.sampling, "sampling_settings": SAMPLING[a.sampling], "max_model_calls_per_turn": a.max_calls,
              "case_set": a.cases, "paired_run": a.paired_run, "cases": len(cases), "commit": git_commit(), "db_host": DB_URL.split("@")[-1].split("/")[0],
              "notes": a.notes}
    client, conn = make_client(a), tool_module(a.tools).connect(DB_URL)
    # v2 tools write proposals and tickets; delete them before each case so no case sees another's writes.
    owner = psycopg.connect(DB_URL, autocommit=True) if a.tools == "v2" else None
    todo = [c for c in cases if c.id not in done]
    print(f"{a.run}: {len(cases)} cases, {len(done)} already done, {len(todo)} to run")
    with path.open("a") as f:
        for i, case in enumerate(todo, 1):
            try:
                if owner:
                    tool_module("v2").clear_agent_writes(owner)
                trace = run_case(case, client, a, conn)
            except Exception as e:                     # record and move on; a resumed run retries it
                trace = {"id": case.id, "category": case.category, "error": f"{type(e).__name__}: {str(e)[:300]}"}
            f.write(json.dumps(trace, default=str, ensure_ascii=False) + "\n")
            f.flush()
            status = trace.get("error") or f"{sum(t['turn_s'] for t in trace['turns']):.1f}s"
            print(f"  [{i}/{len(todo)}] {case.id}: {status}")
    served = sorted({c.get("served_model") for t in read_traces(out) for tr in t.get("turns", [])
                     for c in tr["model_calls"] if c.get("served_model")})
    config["served_models"] = served
    (out / "config.json").write_text(json.dumps(config, indent=2))
    return out


# Scoring ---------------------------------------------------------------------------

def read_traces(out: Path) -> list[dict]:
    p = out / "traces.jsonl"
    return [json.loads(line) for line in p.read_text().splitlines()] if p.exists() else []


def _args(name: str, args) -> dict:
    return {**DEFAULT_ARGS.get(name, {}), **(args or {})}


def _same_call(x, g) -> bool:
    """Expected call x matches made call g: same tool, and the same arguments unless x takes any."""
    return g["name"] == x.name and (x.args is None or _args(x.name, x.args) == _args(g["name"], g["args"]))


ANY_ARGS_WHEN_LENIENT = {"list_my_orders"}
# An offer to hand off, e.g. "Would you like me to hand this over to our support team?"
HANDOFF_OFFER = re.compile(r"\b(would you like|shall i|do you want|want me to|should i|can i)\b[^.?!]{0,80}?"
                           r"\b(hand|connect|transfer|escalat|support team|teammate|human|person)", re.I | re.S)


def offered_handoff(reply: str | None) -> bool:
    return bool(reply and HANDOFF_OFFER.search(reply))


def _in_order(exp, got) -> bool:
    """Every expected call appears in `got`, in the same order; other calls may sit in between."""
    rest = iter(got)
    return all(any(_same_call(x, g) or (x.name in ANY_ARGS_WHEN_LENIENT and g["name"] == x.name) for g in rest)
               for x in exp)


def score(case, trace: dict) -> dict:
    """True/False per metric; None where a metric does not apply (cites* for cases without sources)."""
    has_sources = bool(case.expect.sources)
    if "error" in trace:
        return {m: (None if m.startswith("cites") and not has_sources else False) for m in METRICS}
    e = case.expect
    got, exp = trace["tool_calls"], e.tool_calls
    replies = normalize(" ".join(r or "" for r in trace["replies"]))
    # The offer rule (see escalation): an offered hand-off in an unanswerable case stands in for the call.
    offered = (e.should_escalate and case.category == "unanswerable" and not trace["escalated"]
               and offered_handoff(trace["final_reply"]))
    needed = [x for x in exp if not (offered and x.name == "escalate_to_human")]
    s = {
        "tool_names": [c["name"] for c in got] == [c.name for c in exp],
        "tool_args": len(got) == len(exp) and all(_same_call(x, g) for g, x in zip(got, exp)),
        "required_calls": _in_order(needed, got),
        "valid_json": all(c["parsed"] for c in got),
        "facts": all(normalize(f) in replies for f in e.must_include),
        "forbidden": not any(normalize(f) in replies for f in e.must_not_include),
        "escalation": trace["escalated"] == e.should_escalate or offered,
    }
    rest = [s[m] for m in ("valid_json", "facts", "forbidden", "escalation")]
    s["all"] = s["tool_names"] and s["tool_args"] and all(rest)
    s["all_required"] = s["required_calls"] and all(rest)
    checked = check_conversation(trace.get("messages", []))
    cited = {c for r in checked for c in r["cited"]}
    s["cites"] = bool(cited) if has_sources else None
    s["cites_source"] = bool(cited & set(e.sources)) if has_sources else None
    s["grounded"] = not any(r["issues"] for r in checked)
    return s


def pct(k: int, n: int) -> str:
    return f"{k}/{n} ({100 * k / n:.0f}%)" if n else "-"


def pct_of(ss: list[dict], m: str) -> str:
    """Share of cases where metric m passed, over the cases it applies to."""
    xs = [s[m] for s in ss if s[m] is not None]
    return pct(sum(xs), len(xs))


def paired_rows(cases, scores, paired_run: str | None) -> list[str]:
    """Probe runs: each probe next to its clean golden twin, scored the same way in a golden run."""
    twin = {}
    if paired_run and (RUNS / paired_run / "scores.json").exists():
        twin = json.loads((RUNS / paired_run / "scores.json").read_text())["scores"]
    rows = ["", f"Each probe next to its clean twin" + (f" in run `{paired_run}`" if twin else " (no --paired-run given)")
            + " (all = every check passed with the strict tool checks; all_required = with required_calls):", "",
            "| Probe | Phrasing | Twin | Probe all | Twin all | Probe all_required | Twin all_required |",
            "|---|---|---|---|---|---|---|"]
    def mark(x, m):
        return "-" if x is None else ("pass" if x[m] else "fail")
    for i, s in sorted(scores.items()):
        c = cases[i]
        t = twin.get(c.rephrases)
        rows.append(f"| {i} | {c.phrasing} | {c.rephrases} | {mark(s, 'all')} | {mark(t, 'all')} | "
                    f"{mark(s, 'all_required')} | {mark(t, 'all_required')} |")
    if twin:
        paired = [(s, twin[cases[i].rephrases]) for i, s in scores.items() if cases[i].rephrases in twin]
        rows.append("")
        for m in ("all", "all_required"):
            rows.append(f"{m}: probes passed {sum(p[m] for p, _ in paired)}/{len(paired)}, "
                        f"their clean twins {sum(t[m] for _, t in paired)}/{len(paired)}.  ")
    return rows


def report(out: Path) -> str:
    config = json.loads((out / "config.json").read_text())
    case_set = config.get("case_set", "golden")
    cases = {c.id: c for _, c in load_cases(case_set)[0]}
    traces = [t for t in read_traces(out) if t["id"] in cases]
    scores = {t["id"]: score(cases[t["id"]], t) for t in traces}
    (out / "scores.json").write_text(json.dumps({"scorer_version": SCORER_VERSION, "scores": scores}, indent=1))

    by_cat = defaultdict(list)
    group = (lambda t: cases[t["id"]].phrasing) if case_set == "probes" else (lambda t: t["category"])
    order = PHRASING_QUOTAS if case_set == "probes" else QUOTAS
    for t in traces:
        by_cat[group(t)].append(scores[t["id"]])
    rows = [f"| {'Phrasing' if case_set == 'probes' else 'Category'} | n | " + " | ".join(METRICS) + " |",
            "|---|---|" + "---|" * len(METRICS)]
    for cat in [c for c in order if c in by_cat]:
        ss = by_cat[cat]
        rows.append(f"| {cat} | {len(ss)} | " + " | ".join(pct_of(ss, m) for m in METRICS) + " |")
    allss = list(scores.values())
    rows.append(f"| **all** | {len(allss)} | " + " | ".join(f"**{pct_of(allss, m)}**" for m in METRICS) + " |")
    if case_set == "probes":
        rows += paired_rows(cases, scores, config.get("paired_run"))

    ok = [t for t in traces if "error" not in t]
    turn_s = sorted(tr["turn_s"] for t in ok for tr in t["turns"])
    calls = [c for t in ok for tr in t["turns"] for c in tr["model_calls"]]
    def q(xs, p):
        return xs[min(len(xs) - 1, int(p * len(xs)))] if xs else 0
    errors = [t for t in traces if "error" in t]
    # Model passes the loop could not use: a call left as text, or no text and no call (agent/loop.py). Older traces have none.
    format_errors = {t["id"]: n for t in ok if (n := sum(tr.get("format_errors", 0) for tr in t["turns"]))}
    checked = {t["id"]: check_conversation(t.get("messages", [])) for t in ok}
    replies = [r for rs in checked.values() for r in rs]
    flagged = [r for r in replies if r["issues"]]
    issue_lines = [f"- {i}: " + "; ".join(r["issues"]) for i, rs in sorted(checked.items()) for r in rs if r["issues"]]
    offers = [t["id"] for t in traces if "error" not in t and cases[t["id"]].category == "unanswerable"
              and cases[t["id"]].expect.should_escalate and not t["escalated"] and offered_handoff(t["final_reply"])]
    lines = [
        f"## {config['run']} · {config['system']} · `{config['model']}` · prompt {config['prompt_version']} · "
        f"tools {config.get('tools_version', 'v0')} · "
        f"temperature {config['temperature']} · sampling {config['sampling']} · scorer {SCORER_VERSION}",
        "",
        f"Provider `{config['provider']}`; served by {', '.join(f'`{m}`' for m in config.get('served_models', [])) or 'n/a'}; "
        f"commit `{config['commit']}`; database `{config['db_host']}`; up to {config['max_model_calls_per_turn']} model calls per turn."
        + (f" Notes: {config['notes']}" if config.get("notes") else ""),
        "",
        *rows,
        "",
        f"Latency per turn (model calls + tools + database): median {statistics.median(turn_s):.2f} s, "
        f"p95 {q(turn_s, 0.95):.2f} s, max {turn_s[-1]:.2f} s over {len(turn_s)} turns." if turn_s else "No turns.",
        f"Model calls: {len(calls)}; mean prompt tokens {statistics.mean(c['prompt_tokens'] or 0 for c in calls):.0f}, "
        f"mean completion tokens {statistics.mean(c['completion_tokens'] or 0 for c in calls):.0f}." if calls else "",
        f"Unanswerable cases that passed escalation by offering a hand-off: {len(offers)}"
        + (": " + ", ".join(offers) if offers else "."),
        f"Cases that errored (scored as failures): {len(errors)}" + (": " + ", ".join(t["id"] for t in errors) if errors else "."),
        f"Tool-call format errors (a call left as text, or an empty reply): {sum(format_errors.values())}"
        + (" in " + ", ".join(f"{i} ({n})" for i, n in sorted(format_errors.items())) if format_errors else "."),
        f"Grounding: {len(flagged)} of {len(replies)} replies have an issue "
        f"({100 * len(flagged) / len(replies):.0f} per 100 replies), {sum(len(r['issues']) for r in flagged)} issues."
        if replies else "Grounding: no replies.",
        "",
        "Failed cases: " + ", ".join(i for i, s in sorted(scores.items()) if not s["all"]),
        *(["", "Grounding issues:", *issue_lines] if issue_lines else []),
    ]
    from evals.scorecard import run_layers          # here, not at the top: scorecard imports this module
    lines += ["", *run_layers(cases, traces)]
    text = "\n".join(lines) + "\n"
    (out / "report.md").write_text(text)
    return text


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", help="run name, e.g. 2026-11-23_floor (folder under evals/runs)")
    ap.add_argument("--system", choices=["floor", "ceiling", "candidate", "diagnostic"], help="what the run measures")
    ap.add_argument("--provider", choices=["openai", "gemini", "gemini-studio", "local"], default="openai")
    ap.add_argument("--base-url", help="OpenAI-compatible server, for --provider openai")
    ap.add_argument("--model")
    ap.add_argument("--adapter", help="for --provider local: a LoRA adapter (Hub id or folder) merged into --model")
    ap.add_argument("--temperature", type=float, default=0.2)
    ap.add_argument("--sampling", choices=list(SAMPLING), default="default")
    ap.add_argument("--max-calls", type=int, default=4, help="model calls per turn; change only for diagnostics")
    ap.add_argument("--limit", type=int, help="only the first N cases (smoke test)")
    ap.add_argument("--ids", nargs="*", help="only these case ids")
    ap.add_argument("--category", nargs="*", help="only these categories, e.g. policy old_policy")
    ap.add_argument("--tools", choices=["v0", "v1", "v2"], default="v1",
                    help="tool set (v1, v2 need --group rag; v2 needs db/roles.py applied)")
    ap.add_argument("--prompt", choices=list(PROMPTS), default=PROMPT_VERSION, help="system prompt version")
    ap.add_argument("--state", action="store_true",
                    help="send the conversation state and only the history that fits the token budget (agent/state.py)")
    ap.add_argument("--cases", choices=["golden", "probes"], default="golden",
                    help="the golden set (107 cases), or the phrasing probes (reported apart)")
    ap.add_argument("--paired-run", help="for --cases probes: a golden run of the same system, to show each "
                    "probe next to its clean twin")
    ap.add_argument("--notes", default="", help="free text stored in config.json")
    ap.add_argument("--rescore", type=Path, help="re-score an existing run folder; no model calls")
    a = ap.parse_args()

    if a.rescore:
        print(report(a.rescore))
        return
    if not (a.run and a.system and a.model):
        ap.error("--run, --system and --model are required (or use --rescore)")
    if a.max_calls != 4 and a.system != "diagnostic":
        ap.error("--max-calls other than 4 is only for --system diagnostic (floor and ceiling share the same loop)")
    if a.adapter and a.provider != "local":
        ap.error("--adapter is for --provider local; a vLLM server takes the adapter as a LoRA module (--model <name>)")
    if a.provider == "openai" and not a.base_url:
        ap.error("--base-url is required with --provider openai")
    print(report(run(a)))


if __name__ == "__main__":
    main()
