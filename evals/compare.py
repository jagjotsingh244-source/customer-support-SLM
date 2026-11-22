"""Put eval runs side by side, per category, on the same frozen scorer.

    uv run python evals/compare.py evals/runs/2026-11-22_floor evals/runs/2026-11-22_ceiling
    uv run python evals/compare.py RUN_A RUN_B --metric all --metric facts

Every run is re-scored first (no model calls), so all columns use the current SCORER_VERSION.
Cells show counts and percentages ("19/25 (76%)"): with 25 cases a category, one case is 4 points.
When a floor and a ceiling are given, the last column is the gap the ceiling leaves above the floor.
"""

import argparse
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from evals.run_eval import QUOTAS, SCORER_VERSION, read_traces, report  # noqa: E402

DEFAULT_METRICS = ["all_required", "all", "required_calls", "facts", "forbidden", "escalation"]


def load_run(path: Path) -> dict:
    report(path)                                   # re-score with the current scorer
    scores = json.loads((path / "scores.json").read_text())["scores"]
    config = json.loads((path / "config.json").read_text())
    traces = [t for t in read_traces(path) if "error" not in t]
    turn_s = sorted(tr["turn_s"] for t in traces for tr in t["turns"])
    return {"name": path.name, "config": config, "scores": scores, "traces": traces, "turn_s": turn_s}


def cell(ids, scores, metric) -> str:
    k = sum(scores[i][metric] for i in ids)
    return f"{k}/{len(ids)} ({100 * k / len(ids):.0f}%)" if ids else "-"


def table(runs: list[dict], metric: str) -> str:
    cats = {}
    for r in runs:
        for i in r["scores"]:
            cats.setdefault(i.split("-")[0], set()).add(i)
    prefix = {"pol": "policy", "ord": "order_lookup", "ret": "returns", "una": "unanswerable",
              "esc": "escalation", "adv": "adversarial"}
    header = "| Category | " + " | ".join(f"{r['name']} (`{r['config']['model']}`)" for r in runs) + " |"
    lines = [f"**{metric}**", "", header, "|---|" + "---|" * len(runs)]
    order = [p for p, c in prefix.items() if c in QUOTAS]
    for p in order + ["all"]:
        row = []
        for r in runs:
            ids = sorted(i for i in r["scores"] if p == "all" or i.startswith(p + "-"))
            row.append(cell(ids, r["scores"], metric))
        name = "**all**" if p == "all" else prefix[p]
        lines.append(f"| {name} | " + " | ".join(row) + " |")
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("runs", nargs="+", type=Path)
    ap.add_argument("--metric", action="append", help=f"default: {', '.join(DEFAULT_METRICS)}")
    a = ap.parse_args()
    runs = [load_run(p) for p in a.runs]
    print(f"Scorer {SCORER_VERSION}; runs: " + "; ".join(
        f"{r['name']} = {r['config']['system']}, `{r['config']['model']}` via {r['config']['provider']}"
        for r in runs) + "\n")
    for m in a.metric or DEFAULT_METRICS:
        print(table(runs, m) + "\n")
    print("| Run | Turns | Median turn | p95 turn | Model calls |\n|---|---|---|---|---|")
    for r in runs:
        t = r["turn_s"]
        calls = sum(len(tr["model_calls"]) for x in r["traces"] for tr in x["turns"])
        p95 = t[min(len(t) - 1, int(0.95 * len(t)))] if t else 0
        print(f"| {r['name']} | {len(t)} | {statistics.median(t):.2f} s | {p95:.2f} s | {calls} |" if t else
              f"| {r['name']} | 0 | - | - | 0 |")


if __name__ == "__main__":
    main()
