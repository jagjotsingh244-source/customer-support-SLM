"""Pick the 30-case smoke eval: golden cases that tell systems apart and give the same result every run.

    uv run python evals/smoke.py --runs <every saved golden run of the systems to compare> --out evals/smoke.json
    uv run python evals/run_eval.py --run <name> --ids $(uv run python evals/smoke.py --ids) ...

A case that every system always passes, or always fails, says nothing when it runs in CI; one that flips from run
to run of the same system raises false alarms. So each golden case is ranked by how far apart the systems' pass
rates are (the spread: 1.0 when one system passes every run and another fails every run) minus how much each
system flips on it (the mean, over systems, of the binary entropy of its pass rate across its runs). Ties go to
the case the adapters pass more often. The 30 are taken per category in the golden set's proportions, so the
smoke set still covers every layer. In the adversarial quota, the cases about another customer's data come first,
because a single privacy failure blocks a release (evals/gate.yaml).

Only golden cases are used. The fresh cases stay unseen.
"""

import argparse
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from evals.metrics import PRIVACY_CASES  # noqa: E402
from evals.run_eval import RUNS  # noqa: E402
from evals.scorecard import score_run  # noqa: E402

OUT = ROOT / "evals" / "smoke.json"
QUOTAS = {"policy": 7, "order_lookup": 7, "returns": 4, "unanswerable": 4, "escalation": 3, "adversarial": 4,
          "old_policy": 1}


def entropy(p: float) -> float:
    return 0.0 if p in (0.0, 1.0) else -(p * math.log2(p) + (1 - p) * math.log2(1 - p))


def pick(runs: list[str]) -> list[dict]:
    results, systems, category = defaultdict(list), defaultdict(lambda: defaultdict(list)), {}
    for r in runs:
        case_set, ms = score_run(r)
        if case_set != "golden":
            raise SystemExit(f"{r} is a {case_set} run; the smoke set comes from golden runs only")
        model = json.loads((RUNS / r / "config.json").read_text())["model"]
        for i, m in ms.items():
            ok = bool(m.get("pass"))
            results[i].append(ok)
            systems[i][model].append(ok)
            category[i] = m["category"]
    scored = []
    for i, xs in results.items():
        p = sum(xs) / len(xs)
        rates = [sum(v) / len(v) for v in systems[i].values()]
        spread = max(rates) - min(rates)
        flips = sum(entropy(r) for r in rates) / len(rates)
        scored.append({"id": i, "category": category[i], "pass_rate": round(p, 2), "spread": round(spread, 2),
                       "flips": round(flips, 2), "score": round(spread - flips, 3), "privacy": i in PRIVACY_CASES})
    out = []
    for cat, n in QUOTAS.items():
        pool = [s for s in scored if s["category"] == cat]
        key = (lambda s: (not s["privacy"], -s["score"], -s["pass_rate"], s["id"])) if cat == "adversarial" else \
              (lambda s: (-s["score"], -s["pass_rate"], s["id"]))
        out += sorted(pool, key=key)[:n]
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--runs", nargs="+", help="golden runs to rank the cases by; without it, read --out")
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--ids", action="store_true", help="print the chosen ids, space-separated")
    a = ap.parse_args()
    if a.runs:
        chosen = pick(a.runs)
        a.out.write_text(json.dumps({"runs": a.runs, "cases": chosen}, indent=1) + "\n")
    chosen = json.loads(a.out.read_text())["cases"]
    if a.ids:
        print(" ".join(c["id"] for c in chosen))
        return
    for c in chosen:
        print(f"{c['id']:<9} {c['category']:<13} pass {c['pass_rate']:.2f}  spread {c['spread']:.2f}  "
              f"flips {c.get('flips', 0):.2f}  score {c['score']:.2f}" + ("  privacy" if c["privacy"] else ""))
    print(f"{len(chosen)} cases")


if __name__ == "__main__":
    main()
