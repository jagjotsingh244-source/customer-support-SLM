"""Case by case, what changed between two runs of the same model: which failures went away, which appeared.

    uv run python evals/compare_cases.py evals/runs/2026-11-22_floor evals/runs/2026-11-23_floor-tools-v2
    uv run python evals/compare_cases.py BEFORE AFTER --metric all

Only the cases both runs have are compared, so a full run can be the "before" of a run over a few
categories. Both runs are re-scored first with the current scorer (no model calls).
"""

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from evals.run_eval import read_traces, report  # noqa: E402


def scores(run: Path) -> dict:
    report(run)
    return json.loads((run / "scores.json").read_text())["scores"]


def compare(before: Path, after: Path, metric: str) -> dict:
    b, a = scores(before), scores(after)
    ids = sorted(set(b) & set(a))
    cats = {t["id"]: t["category"] for t in read_traces(after)}
    out = {"cases": len(ids), "before": sum(b[i][metric] for i in ids), "after": sum(a[i][metric] for i in ids),
           "fixed": [i for i in ids if not b[i][metric] and a[i][metric]],
           "broke": [i for i in ids if b[i][metric] and not a[i][metric]],
           "by_category": {}}
    for cat in sorted({cats[i] for i in ids}):
        cs = [i for i in ids if cats[i] == cat]
        out["by_category"][cat] = (sum(b[i][metric] for i in cs), sum(a[i][metric] for i in cs), len(cs))
    out["failing_metrics_after"] = Counter(m for i in ids if not a[i][metric]
                                           for m, v in a[i].items() if v is False and m not in ("all", "all_required"))
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("before", type=Path)
    ap.add_argument("after", type=Path)
    ap.add_argument("--metric", default="all_required")
    x = ap.parse_args()
    r = compare(x.before, x.after, x.metric)
    print(f"{x.metric}: {r['before']}/{r['cases']} before, {r['after']}/{r['cases']} after")
    for cat, (b, a, n) in r["by_category"].items():
        print(f"  {cat:14s} {b}/{n} -> {a}/{n}")
    print(f"fixed ({len(r['fixed'])}): {', '.join(r['fixed']) or '-'}")
    print(f"broke ({len(r['broke'])}): {', '.join(r['broke']) or '-'}")
    print("checks failed in the cases still failing:", dict(r["failing_metrics_after"].most_common()))


if __name__ == "__main__":
    main()
