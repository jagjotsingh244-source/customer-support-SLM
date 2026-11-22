"""Read eval cases one at a time: what the case expected next to what the model did.

    uv run python evals/show_case.py evals/runs/2026-11-22_floor ord-001 ret-005
    uv run python evals/show_case.py evals/runs/2026-11-22_floor --failed --category returns
    uv run python evals/show_case.py evals/runs/2026-11-22_floor --failed --limit 30 > failures.txt

For error analysis: read each failure, write one sentence on what went wrong, then group the
sentences into a few failure types and count them. Scores come from the run's scores.json, so
run `evals/run_eval.py --rescore <run>` first if the scorer changed.
"""

import argparse
import json
import sys
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from evals.run_eval import METRICS, read_traces  # noqa: E402
from evals.validate import load, normalize  # noqa: E402

WIDTH = 100


def wrap(text: str, indent: str = "    ") -> str:
    return "\n".join(textwrap.fill(line, WIDTH, initial_indent=indent, subsequent_indent=indent)
                     for line in (text or "").splitlines() or [""])


def fmt_args(args) -> str:
    return "any" if args is None else json.dumps(args, ensure_ascii=False)


def show(case, trace: dict, scores: dict) -> str:
    e = case.expect
    out = [f"{'=' * WIDTH}", f"{case.id}  [{case.category}]  customer {case.customer_id}"
           + (f"  scenario {case.scenario}" if case.scenario else "")]
    failed = [m for m in METRICS if not scores.get(m, False)]
    out.append("FAILED: " + (", ".join(failed) if failed else "nothing (passes every check)"))
    out.append("NOTES (why the case exists):")
    out.append(wrap(case.notes))

    if "error" in trace:
        out.append(f"RUN ERROR: {trace['error']}")
        return "\n".join(out)

    out.append("EXPECTED TOOL CALLS:  " + (" -> ".join(f"{x.name}({fmt_args(x.args)})" for x in e.tool_calls) or "none"))
    out.append("ACTUAL TOOL CALLS:    " + (" -> ".join(f"{c['name']}({c['raw_args']})" for c in trace["tool_calls"]) or "none"))
    for c in trace["tool_calls"]:
        res = json.dumps(c["result"], default=str, ensure_ascii=False)
        out.append(f"    {c['name']} -> {res[:220]}{'...' if len(res) > 220 else ''}")

    replies = normalize(" ".join(r or "" for r in trace["replies"]))
    missing = [f for f in e.must_include if normalize(f) not in replies]
    present = [f for f in e.must_not_include if normalize(f) in replies]
    out.append(f"MUST INCLUDE: {e.must_include or '-'}" + (f"   MISSING: {missing}" if missing else ""))
    out.append(f"MUST NOT INCLUDE: {e.must_not_include or '-'}" + (f"   FOUND: {present}" if present else ""))
    out.append(f"SHOULD HAND OFF: {e.should_escalate}   HANDED OFF: {trace['escalated']}")

    for i, (turn, tr) in enumerate(zip(case.turns, trace["turns"]), 1):
        calls = tr["model_calls"]
        out.append(f"TURN {i}  ({tr['turn_s']:.1f}s, {len(calls)} model calls)")
        out.append(wrap("CUSTOMER: " + turn))
        out.append(wrap("NOVA:     " + (tr["reply"] or "(no text)")))
    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run", type=Path, help="run folder, e.g. evals/runs/2026-11-22_floor")
    ap.add_argument("ids", nargs="*", help="case ids to show (default: all, or all failures with --failed)")
    ap.add_argument("--failed", action="store_true", help="only cases that fail all_required (a real mistake)")
    ap.add_argument("--category")
    ap.add_argument("--limit", type=int)
    a = ap.parse_args()

    cases = {c.id: c for _, c in load()[0]}
    traces = {t["id"]: t for t in read_traces(a.run)}
    scores = json.loads((a.run / "scores.json").read_text())["scores"]
    ids = a.ids or sorted(traces)
    if a.failed:
        ids = [i for i in ids if not scores[i]["all_required"]]
    if a.category:
        ids = [i for i in ids if cases[i].category == a.category]
    if a.limit:
        ids = ids[: a.limit]
    for i in ids:
        print(show(cases[i], traces[i], scores[i]))
    print(f"\n{len(ids)} case(s) shown")


if __name__ == "__main__":
    main()
