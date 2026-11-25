"""The regression gate: PASS or BLOCK for a candidate adapter against the one Nova serves now.

    uv run python evals/gate.py \\
        --candidate 2026-11-25_golden-sft2b,2026-11-25_golden-sft2b-r2,2026-11-25_golden-sft2b-r3 \\
        --current   2026-11-25_golden-sft2a,2026-11-25_golden-sft2a-r2,2026-11-25_golden-sft2a-r3

Each side is one or more saved runs of the same case set (repeat runs are pooled: pass@1 is the mean over them).
The rules are in evals/gate.yaml. Nothing calls a model; the runs are re-scored from their traces.

- hard: absolute rules on the candidate (adversarial cases all pass, no privacy violation, no return claimed done).
- relative: no category falls more than the allowed points below the current adapter (blocking only when the 95%
  intervals do not overlap, a warning otherwise); grounding issues per 100 replies rise by at most the allowance.
- budget: p95 latency of turns with exactly one tool call. Latency depends on the GPU the runs were served on,
  so the gate prints where that was. Turns with a model call over 30 s (a cold GPU container, an API retry) are
  left out and counted (evals/metrics.py, latency_turns).

Exits 0 on PASS, 1 on BLOCK.
"""

import argparse
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from evals.metrics import LATENCY_OUTLIER_S, fmt_rate, latency_turns, quantile, rate  # noqa: E402
from evals.run_eval import RUNS, read_traces  # noqa: E402
from evals.scorecard import order_of, score_run  # noqa: E402

GATE = ROOT / "evals" / "gate.yaml"


def side(runs: list[str]) -> dict:
    """Everything the gate needs about one system, pooled over its runs."""
    sets, scored = set(), []
    for r in runs:
        case_set, ms = score_run(r)
        sets.add(case_set)
        scored.append(ms)
    if len(sets) != 1:
        raise SystemExit(f"runs mix case sets: {sorted(sets)}")
    case_set = sets.pop()
    ids = sorted({i for ms in scored for i in ms})
    # a conversation that errored (an API refusal, a crash) is left out, not counted as a failure
    per_case = {i: [ms[i]["pass"] for ms in scored if i in ms and not ms[i].get("error")] for i in ids}
    per_case = {i: v for i, v in per_case.items() if v}
    category = {i: next(ms[i]["category"] for ms in scored if i in ms) for i in ids}
    pooled = [m for ms in scored for m in ms.values() if not m.get("error")]
    one_call, dropped = latency_turns([tr for r in runs for tr in read_traces(RUNS / r) if "turns" in tr],
                                      one_tool_call=True)
    served = sorted({json.dumps(json.loads((RUNS / r / "config.json").read_text()).get("served_models"))
                     for r in runs})
    return {
        "case_set": case_set, "runs": runs, "served": served,
        "cats": {c: rate([sum(v) / len(v) for i, v in per_case.items() if category[i] == c])
                 for c in order_of(case_set) if any(category[i] == c for i in ids)},
        "adversarial": rate([p for i, v in per_case.items() if category[i] == "adversarial" for p in v]),
        "privacy": sum(m["privacy_violations"] for m in pooled),
        "claimed": sum(bool(m["return_claimed_done"]) for m in pooled),
        "issues": sum(m["replies_with_issue"] for m in pooled), "replies": sum(m["n_replies"] for m in pooled),
        "p95": quantile(one_call, 0.95) if one_call else None, "n_one_call": len(one_call), "dropped": dropped,
    }


def gate(cand: dict, cur: dict, rules: dict) -> tuple[list[str], list[str], list[str]]:
    """(blocks, warnings, passes), each a list of reasons."""
    block, warn, ok = [], [], []
    h, rel, bud = rules["hard"], rules["relative"], rules["budget"]

    adv = cand["adversarial"]
    if adv.get("n"):
        (ok if adv["mean"] >= h["adversarial_pass_rate"] else block).append(
            f"adversarial pass rate {fmt_rate(adv)} (needs {100 * h['adversarial_pass_rate']:.0f}%)")
    for key, label, limit in (("privacy", "privacy violations", h["privacy_violations"]),
                              ("claimed", "returns claimed done", h["return_claimed_done"])):
        (ok if cand[key] <= limit else block).append(f"{label}: {cand[key]} (allowed {limit})")

    drop = rel["max_category_drop_points"]
    for c, r in cand["cats"].items():
        base = cur["cats"].get(c)
        if not base or not r.get("n"):
            continue
        fall = 100 * (base["mean"] - r["mean"])
        line = f"{c}: {fmt_rate(r)} vs current {fmt_rate(base)} ({-fall:+.0f} points)"
        if fall <= drop:
            ok.append(line)
        elif r["hi"] < base["lo"]:
            block.append(line + f", more than {drop} points and the intervals do not overlap")
        else:
            warn.append(line + f", more than {drop} points, but the intervals overlap")

    p100 = lambda s: 100 * s["issues"] / s["replies"] if s["replies"] else 0.0  # noqa: E731
    line = (f"grounding issues {p100(cand):.1f} per 100 replies ({cand['issues']}/{cand['replies']}) vs current "
            f"{p100(cur):.1f} ({cur['issues']}/{cur['replies']})")
    (ok if p100(cand) <= p100(cur) + rel["max_grounding_violations_per_100"] else block).append(
        line + f"; allowed +{rel['max_grounding_violations_per_100']}")

    if cand["p95"] is None:
        warn.append("no turn with exactly one tool call: latency not measured")
    else:
        left_out = (f"; {cand['dropped']} left out with a model call over {LATENCY_OUTLIER_S:.0f} s (cold start or "
                    "retry)") if cand.get("dropped") else ""
        line = (f"p95 latency {cand['p95']:.2f} s over {cand['n_one_call']} one-tool-call turns "
                f"(budget {bud['p95_latency_s']} s; served by {', '.join(cand['served'])}{left_out})")
        (ok if cand["p95"] <= bud["p95_latency_s"] else block).append(line)
    return block, warn, ok


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--candidate", required=True, help="comma-separated run names of the new adapter")
    ap.add_argument("--current", required=True, help="comma-separated run names of the adapter Nova serves")
    ap.add_argument("--rules", type=Path, default=GATE)
    a = ap.parse_args()
    rules = yaml.safe_load(a.rules.read_text())
    cand, cur = side(a.candidate.split(",")), side(a.current.split(","))
    if cand["case_set"] != cur["case_set"]:
        raise SystemExit(f"candidate runs are {cand['case_set']}, current runs are {cur['case_set']}")
    block, warn, ok = gate(cand, cur, rules)
    print(f"{'BLOCK' if block else 'PASS'}: candidate {', '.join(cand['runs'])} against current "
          f"{', '.join(cur['runs'])} ({cand['case_set']} cases)")
    for title, xs in (("Blocks", block), ("Warnings", warn), ("Passes", ok)):
        if xs:
            print(f"\n{title}:")
            print("\n".join(f"  - {x}" for x in xs))
    sys.exit(1 if block else 0)


if __name__ == "__main__":
    main()
