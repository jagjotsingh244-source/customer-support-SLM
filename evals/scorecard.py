"""Score systems layer by layer and category by category, over repeated runs, with 95% intervals.

    # each system: its golden runs and its simulated runs (same settings, repeated)
    uv run python evals/scorecard.py --out evals/reports/04a_layers_tables.md \\
        --golden base=2026-11-25_golden-base,2026-11-25_golden-base-r2,2026-11-25_golden-base-r3 ... \\
        --simulated base=2026-11-25_sim-base-r1,2026-11-25_sim-base-r2,2026-11-25_sim-base-r3 ...

    # every saved golden run, one row each, with the layer metrics (no model is called)
    uv run python evals/scorecard.py --rescore-all --out evals/reports/04a_rescored_runs.md

A case passes a golden run when the scorer's all_required holds (evals/run_eval.py, eval-v3: every required
call, the facts, nothing forbidden, the right hand-off). A simulated case passes when the end state is right
(a proposal and a ticket exactly when expected), Nova looked at the evidence the answer needs (the customer's
order, or the help-center section), the facts it needs were given, nothing forbidden or private was said, and
no return was claimed done. The evidence check was added after the first full runs (evals/build_simulated.py).

pass@1 is the mean pass rate over the runs; pass^k the share of cases that pass in all k runs (evals/metrics.py).
Intervals resample cases (2,000 bootstrap draws), so they show how much a category could move with other cases
of the same kind, not run-to-run noise; pass^k is where run-to-run noise shows.
"""

import argparse
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from evals.build_simulated import load_cases as load_sim  # noqa: E402
from evals.metrics import (HAD_RETURN, METRICS_VERSION, PRIVACY_CASES, confusion, confusion_rows,  # noqa: E402
                           fmt_rate, layer_metrics, pass_hat_k, quantile, rate)
from evals.run_eval import RUNS, SCORER_VERSION, read_traces, score  # noqa: E402
from evals.validate import QUOTAS, load, normalize  # noqa: E402

SIM_ORDER = ["order_lookup", "returns", "escalation", "policy", "unanswerable", "adversarial"]


# Scoring one trace --------------------------------------------------------------------------------------------

def golden_case_metrics(case, trace: dict) -> dict:
    s = score(case, trace)
    e = case.expect
    m = layer_metrics(trace, category=case.category, expected_tools=[t.name for t in e.tool_calls],
                      sources=e.sources, expect_proposal=e.confirm_card, expect_ticket=e.should_escalate,
                      ticket_offer_ok=case.category == "unanswerable",
                      private_terms=e.must_not_include if case.id in PRIVACY_CASES else [],
                      had_return=case.scenario in HAD_RETURN)
    return {**m, "pass": s["all_required"], "strict": s["all"], "exact_args": s["tool_args"], "facts": s["facts"],
            "forbidden_ok": s["forbidden"], "escalation_ok": s["escalation"],
            "expected_tools": [t.name for t in e.tool_calls], "called_tools": [c["name"] for c in trace.get("tool_calls", [])]}


def sim_case_metrics(case, trace: dict) -> dict:
    e = case.expect
    if "error" in trace:
        return {"error": True, "pass": False, "category": case.category}
    m = layer_metrics(trace, category=case.category, expected_tools=None, sources=e["sources"],
                      expect_proposal=e["proposal"], expect_ticket=e["ticket"], ticket_offer_ok=e["ticket_offer_ok"],
                      private_terms=case.private, had_return=case.had_return, person_ask_ok=True)
    text = normalize(" ".join(r or "" for r in trace["replies"]))
    facts = all(normalize(f) in text for f in e["must_include"])
    forbidden_ok = not any(normalize(f) in text for f in e["must_not_include"])
    db = trace.get("db", {})
    db_agrees = (bool(db.get("returns")) == m["proposal"]) and (bool(db.get("tickets")) == m["ticket"]) if db else None
    ok_v1 = m["end_state_ok"] and facts and forbidden_ok and not m["privacy_violations"] and not m["return_claimed_done"]
    evidence = all(has_evidence(trace, ev) for ev in e.get("evidence", []))
    return {**m, "pass": ok_v1 and evidence, "pass_v1": ok_v1, "evidence": evidence, "facts": facts,
            "forbidden_ok": forbidden_ok, "db_agrees": db_agrees, "gave_up": trace["sim"]["outcome"] == "gave_up",
            "sim_outcome": trace["sim"]["outcome"], "sim_tokens": trace["sim"]["usage"]}


ORDER_LOOKUPS = {"get_order_status", "get_tracking", "propose_return"}


def has_evidence(trace: dict, ev: dict) -> bool:
    """Nova looked at what the answer needs: the customer's order (a lookup of that order that returned it) or
    the help-center section (returned by one of its searches)."""
    for c in trace.get("tool_calls", []):
        result = c.get("result") if isinstance(c.get("result"), dict) else {}
        if "order" in ev and c["name"] in ORDER_LOOKUPS and (c.get("args") or {}).get("order_id") == ev["order"] \
                and "error" not in result:
            return True
        if "section" in ev and c["name"] == "search_help_center" and \
                ev["section"] in [x.get("id") for x in result.get("results", []) if isinstance(x, dict)]:
            return True
    return False


def run_layers(cases: dict, traces: list[dict]) -> list[str]:
    """The layer section of one golden (or probe) run's own report.md (evals/run_eval.py)."""
    ms = {t["id"]: golden_case_metrics(cases[t["id"]], t) for t in traces if t["id"] in cases}
    pairs = [(m["expected_tools"], m["called_tools"]) for m in ms.values() if not m.get("error")]
    detail = privacy_details([ms], "this run")
    return [f"### Every layer, per category (metrics `{METRICS_VERSION}`, evals/metrics.py)", "",
            *layer_tables([ms], "golden"), "", "Tool confusion (expected against called):", "",
            *confusion_rows(confusion(pairs)), *(["", "Privacy violations:", *detail] if detail else [])]


def score_run(run: str) -> tuple[str, dict[str, dict]]:
    """(case set, {case id: metrics}) for one run folder."""
    out = RUNS / run
    config = json.loads((out / "config.json").read_text())
    case_set = config.get("case_set", "golden")
    traces = read_traces(out)
    if case_set == "simulated":
        cases = {c.id: c for c in load_sim()}
        return case_set, {t["id"]: sim_case_metrics(cases[t["id"]], t) for t in traces if t["id"] in cases}
    cases = {c.id: c for _, c in load()[0]}
    return case_set, {t["id"]: golden_case_metrics(cases[t["id"]], t) for t in traces if t["id"] in cases}


# Tables -------------------------------------------------------------------------------------------------------

def order_of(case_set: str) -> list[str]:
    return SIM_ORDER if case_set == "simulated" else list(QUOTAS)


def reliability_table(systems: dict[str, list[dict[str, dict]]], case_set: str) -> list[str]:
    """Per category and system: pass@1 (mean over runs) and pass^k (every run), both with intervals."""
    names = list(systems)
    k = min(len(r) for r in systems.values())
    rows = ["| Category | n | " + " | ".join(f"{s} pass@1 | {s} pass^{k}" for s in names) + " |",
            "|---|---|" + "---|---|" * len(names)]
    def cells(runs, cat):
        ids = sorted({i for r in runs for i, m in r.items() if cat is None or m["category"] == cat})
        res = {i: [r[i]["pass"] if i in r else False for r in runs[:k]] for i in ids}
        p1 = rate([sum(v) / len(v) for v in res.values()])
        pk = rate([pass_hat_k(v, k) for v in res.values()])
        return len(ids), f"{fmt_rate(p1)} | {fmt_rate(pk)}"
    for cat in order_of(case_set) + [None]:
        n, parts = 0, []
        for s in names:
            n, c = cells(systems[s], cat)
            parts.append(c)
        if n:
            label = "**all**" if cat is None else cat
            rows.append(f"| {label} | {n} | " + " | ".join(parts) + " |")
    return rows


def pass_curve(systems: dict[str, list[dict[str, dict]]]) -> list[str]:
    k = min(len(r) for r in systems.values())
    rows = ["| System | " + " | ".join(f"pass^{j}" for j in range(1, k + 1)) + " |", "|---|" + "---|" * k]
    for s, runs in systems.items():
        ids = sorted({i for r in runs for i in r})
        res = [[r[i]["pass"] if i in r else False for r in runs[:k]] for i in ids]
        rows.append(f"| {s} | " + " | ".join(f"{100 * statistics.mean(pass_hat_k(v, j) for v in res):.0f}%"
                                             for j in range(1, k + 1)) + " |")
    return rows


def _pool(runs: list[dict[str, dict]], cat) -> list[dict]:
    return [m for r in runs for m in r.values() if not m.get("error") and (cat is None or m["category"] == cat)]


def _per_case(runs, cat, key) -> list[float]:
    """Per-case mean of a yes/no metric over the runs (None where it does not apply)."""
    by = defaultdict(list)
    for r in runs:
        for i, m in r.items():
            if not m.get("error") and (cat is None or m["category"] == cat) and m.get(key) is not None:
                by[i].append(float(m[key]))
    return [sum(v) / len(v) for v in by.values()]


def per100(num: int, den: int) -> str:
    return f"{100 * num / den:.1f} ({num}/{den})" if den else "-"


def layer_tables(runs: list[dict[str, dict]], case_set: str) -> list[str]:
    """Every metric of the catalogue, per category, pooled over the runs."""
    golden = case_set != "simulated"
    head1 = ["searched", "recall@3", "MRR", "right tools"] + (["exact args"] if golden else []) + \
            ["rejected / 100 calls", "format errors / 100 model calls", "cases with an unneeded call",
             "end state right", "fallback turns"]
    head2 = ["grounding issues / 100 replies", "facts", "no forbidden", "privacy violations",
             "return claimed done", "customer turns", "tokens / conversation", "latency p50 / p95 (s)"]
    t1 = ["| Category | n | " + " | ".join(head1) + " |", "|---|---|" + "---|" * len(head1)]
    t2 = ["| Category | n | " + " | ".join(head2) + " |", "|---|---|" + "---|" * len(head2)]
    for cat in order_of(case_set) + [None]:
        ms = _pool(runs, cat)
        if not ms:
            continue
        n = len({i for r in runs for i, m in r.items() if cat is None or m["category"] == cat})
        label = "**all**" if cat is None else cat
        rrs = _per_case(runs, cat, "rr")
        c1 = [fmt_rate(rate(_per_case(runs, cat, "searched"))), fmt_rate(rate(_per_case(runs, cat, "recall3"))),
              f"{statistics.mean(rrs):.2f}" if rrs else "-",
              fmt_rate(rate(_per_case(runs, cat, "right_tools"))) if golden else "-"]
        if golden:
            c1.append(fmt_rate(rate(_per_case(runs, cat, "exact_args"))))
        unneeded = [any(m["unneeded_calls"] for r in runs for j, m in r.items() if j == i and not m.get("error"))
                    for i in {i for r in runs for i, m in r.items() if cat is None or m["category"] == cat}]
        c1 += [per100(sum(m["rejected_calls"] for m in ms), sum(m["n_calls"] for m in ms)),
               per100(sum(m["format_errors"] for m in ms), sum(m["n_model_calls"] for m in ms)),
               f"{sum(unneeded)}/{len(unneeded)}",
               fmt_rate(rate(_per_case(runs, cat, "end_state_ok"))),
               str(sum(m["fallback_turns"] for m in ms))]
        turn_s = [s for m in ms for s in m["turn_s"]]
        c2 = [per100(sum(m["replies_with_issue"] for m in ms), sum(m["n_replies"] for m in ms)),
              fmt_rate(rate(_per_case(runs, cat, "facts"))), fmt_rate(rate(_per_case(runs, cat, "forbidden_ok"))),
              str(sum(m["privacy_violations"] for m in ms)), str(sum(m["return_claimed_done"] for m in ms)),
              f"{statistics.mean(m['customer_turns'] for m in ms):.1f}",
              f"{statistics.mean(m['tokens'] for m in ms):,.0f}",
              f"{quantile(turn_s, 0.5):.2f} / {quantile(turn_s, 0.95):.2f}" if turn_s else "-"]
        t1.append(f"| {label} | {n} | " + " | ".join(c1) + " |")
        t2.append(f"| {label} | {n} | " + " | ".join(c2) + " |")
    return t1 + [""] + t2


def sim_extras(runs: list[dict[str, dict]]) -> list[str]:
    """Simulated runs only: the evidence rule, the customer's own verdict, and the database cross-check."""
    rows = ["| Category | n | looked at the evidence | customer gave up | pass, first rule (no evidence check) | pass |",
            "|---|---|---|---|---|---|"]
    for cat in SIM_ORDER + [None]:
        n = len({i for r in runs for i, m in r.items() if cat is None or m["category"] == cat})
        if n:
            rows.append(f"| {'**all**' if cat is None else cat} | {n} | "
                        + " | ".join(fmt_rate(rate(_per_case(runs, cat, k)))
                                     for k in ("evidence", "gave_up", "pass_v1", "pass")) + " |")
    ms = _pool(runs, None)
    outcomes = defaultdict(int)
    for m in ms:
        outcomes[m["sim_outcome"]] += 1
    agree = [m["db_agrees"] for m in ms if m.get("db_agrees") is not None]
    errors = sum(1 for r in runs for m in r.values() if m.get("error"))
    return rows + ["", f"Customer endings: " + ", ".join(f"{k} {v}" for k, v in sorted(outcomes.items())) +
            f". Database end state agrees with the tool results in {sum(agree)}/{len(agree)} conversations."
            + (f" Errored conversations (scored as failures): {errors}." if errors else "")]


def privacy_details(runs, name) -> list[str]:
    out = []
    for n, r in enumerate(runs, 1):
        for i, m in sorted(r.items()):
            for d in m.get("privacy_detail", []):
                out.append(f"- {name + ' run ' + str(n) + ', ' if len(runs) > 1 else ''}{i}: {d}")
    return out


def systems_report(golden: dict[str, list[str]], simulated: dict[str, list[str]]) -> str:
    lines = [f"Scorer `{SCORER_VERSION}` (pass), metrics `{METRICS_VERSION}`. Runs per system: "
             + "; ".join(f"{s}: {', '.join(f'`{x}`' for x in rs)}" for s, rs in {**golden}.items()) + ".", ""]
    for title, spec in (("Golden set (scripted)", golden), ("Simulated customers", simulated)):
        if not spec:
            continue
        systems = {s: [score_run(r)[1] for r in rs] for s, rs in spec.items()}
        case_set = "simulated" if spec is simulated else "golden"
        lines += [f"## {title}", "", "### Reliability: pass@1 and pass^k per category", "",
                  *reliability_table(systems, case_set), "", "pass^k for k = 1 to "
                  f"{min(len(r) for r in systems.values())}, all cases:", "", *pass_curve(systems), ""]
        for s, runs in systems.items():
            lines += [f"### {s}: every layer, per category ({len(runs)} runs pooled)", "", *layer_tables(runs, case_set), ""]
            if case_set == "simulated":
                lines += sim_extras(runs) + [""]
            if case_set == "golden":
                pairs = [(m["expected_tools"], m["called_tools"]) for r in runs for m in r.values() if not m.get("error")]
                lines += [f"Tool confusion, {s} (expected against called, {len(runs)} runs):", "",
                          *confusion_rows(confusion(pairs)), ""]
            if det := privacy_details(runs, s):
                lines += ["Privacy violations:", *det, ""]
    return "\n".join(lines) + "\n"


def rescore_all() -> str:
    """Every saved golden run, scored with the layer metrics: one row each."""
    head = ["Run", "system", "model", "n", "pass (all_required)", "recall@3", "right tools", "rejected / 100 calls",
            "format err / 100", "unneeded", "end state", "grounding / 100", "privacy", "return done", "tokens / conv",
            "p95 turn s"]
    rows = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    for out in sorted(p for p in RUNS.iterdir() if (p / "config.json").exists()):
        config = json.loads((out / "config.json").read_text())
        if config.get("case_set", "golden") != "golden":
            continue
        _, r = score_run(out.name)
        ms = [m for m in r.values() if not m.get("error")]
        if not ms:
            continue
        turn_s = [s for m in ms for s in m["turn_s"]]
        rows.append("| " + " | ".join([
            f"`{out.name}`", str(config.get("system")), f"`{config.get('model')}`", str(len(r)),
            fmt_rate(rate([m["pass"] for m in r.values()])),
            fmt_rate(rate([m["recall3"] for m in ms]), counts=True),
            fmt_rate(rate([m["right_tools"] for m in ms])),
            per100(sum(m["rejected_calls"] for m in ms), sum(m["n_calls"] for m in ms)),
            per100(sum(m["format_errors"] for m in ms), sum(m["n_model_calls"] for m in ms)),
            str(sum(bool(m["unneeded_calls"]) for m in ms)),
            fmt_rate(rate([m["end_state_ok"] for m in ms])),
            per100(sum(m["replies_with_issue"] for m in ms), sum(m["n_replies"] for m in ms)),
            str(sum(m["privacy_violations"] for m in ms)), str(sum(m["return_claimed_done"] for m in ms)),
            f"{statistics.mean(m['tokens'] for m in ms):,.0f}",
            f"{quantile(turn_s, 0.95):.2f}" if turn_s else "-"]) + " |")
    return "\n".join(rows) + "\n"


def parse_spec(items: list[str]) -> dict[str, list[str]]:
    out = {}
    for item in items or []:
        name, _, runs = item.partition("=")
        out[name] = [r for r in runs.split(",") if r]
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--golden", nargs="*", help="system=run1,run2,run3")
    ap.add_argument("--simulated", nargs="*", help="system=run1,run2,run3")
    ap.add_argument("--rescore-all", action="store_true")
    ap.add_argument("--out", type=Path)
    a = ap.parse_args()
    text = rescore_all() if a.rescore_all else systems_report(parse_spec(a.golden), parse_spec(a.simulated))
    if a.out:
        a.out.write_text(text)
    print(text)


if __name__ == "__main__":
    main()
