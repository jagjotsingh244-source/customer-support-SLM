"""One table across the systems: quality per category, grounding, latency and cost, from saved runs only.

    uv run python evals/compare_systems.py --out evals/reports/04_comparison_tables.md \\
        --golden base=2026-11-25_golden-base,2026-11-25_golden-base-r2,2026-11-25_golden-base-r3 ... \\
        --fresh base=2026-11-25_fresh-base ... gemini=2026-11-25_fresh-gemini

Quality is pass@1 per category (the scorer's all_required, eval-v3), averaged over a system's repeat runs, with
95% bootstrap intervals over cases. Grounding is the code check (agent/grounding.py): replies with a number,
date or order fact that is not in the tool results, per 100 replies. Latency is per customer turn, as measured
by the eval runner (model calls, tools and the database); turns with a model call over 30 s (a cold GPU container
or an API retry) are left out and counted. Conversations that errored (an API refusal) are left out of the pass
rates, and the cells they affect are marked †.

Cost per 1,000 conversations is worked out two ways, as the method asks:
- API model: the measured tokens per conversation (thinking counted as output) times the list price.
- The 2B: GPU price per hour divided by conversations per hour. Conversations per hour is measured on runs that
  shared one GPU at the same time (--gpu-runs: the four fresh runs, one conversation at a time each, so four at
  once): their conversations divided by the longest run's time. vLLM can serve more at once, so this is an upper
  bound on the cost, and an estimate until throughput is measured on the serving GPU. Without --gpu-runs, one
  conversation at a time is assumed.
"""

import argparse
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from evals.metrics import LATENCY_OUTLIER_S, fmt_rate, latency_turns, quantile, rate  # noqa: E402
from evals.run_eval import RUNS, read_traces  # noqa: E402
from evals.scorecard import parse_spec, score_run  # noqa: E402

# Prices, looked up 2026-11-25. Gemini: Vertex AI global endpoint, per 1M tokens. GPU: Modal, per second.
PRICE_PER_M = {"gemini-4-hydrogen": (1.50, 7.50), "gemini-4-neon": (3.00, 15.00)}
GPU_PER_HOUR = {"L4": 0.000222 * 3600}
INR_PER_USD = 88.6
THROUGHPUT = {}   # conversations per hour on the GPU, set by --gpu-runs
COLUMNS = [("order_lookup", "Order tasks"), ("policy", "Policy"), ("old_policy", "Old policy"),
           ("returns", "Returns"), ("escalation", "Escalation"), ("unanswerable", "Unanswerable"),
           ("adversarial", "Adversarial")]
NAMES = {"base": "Prompted 2B (floor)", "sft1": "SFT-1", "sft2a": "SFT-2a", "sft2b": "SFT-2b",
         "gemini": "Gemini 4 Hydrogen (ceiling)"}


def system(runs: list[str]) -> dict:
    scored = [score_run(r)[1] for r in runs]
    traces = [t for r in runs for t in read_traces(RUNS / r) if "error" not in t]
    configs = [json.loads((RUNS / r / "config.json").read_text()) for r in runs]
    ids = sorted({i for ms in scored for i in ms})
    cat = {i: next(ms[i]["category"] for ms in scored if i in ms) for i in ids}
    # errored conversations (an API refusal, a crash) are left out of the pass rates, not counted as failures
    done = {i: [ms[i]["pass"] for ms in scored if i in ms and not ms[i].get("error")] for i in ids}
    per_case = {i: sum(v) / len(v) for i, v in done.items() if v}
    pooled = [m for ms in scored for m in ms.values() if not m.get("error")]
    turns = [t for tr in traces for t in tr["turns"] if "turn_s" in t]
    lat, dropped = latency_turns(traces)
    lat_one, _ = latency_turns(traces, one_tool_call=True)
    conv_s = [sum(t["turn_s"] for t in tr["turns"] if not slow(t)) for tr in traces]
    calls = [m for t in turns for m in t["model_calls"]]
    return {
        "runs": runs, "n_runs": len(runs), "model": configs[0]["model"], "provider": configs[0]["provider"],
        "cats": {c: rate([v for i, v in per_case.items() if cat[i] == c]) for c, _ in COLUMNS},
        "cat_total": {c: sum(1 for i in ids if cat[i] == c) for c, _ in COLUMNS},
        "all": rate(list(per_case.values())), "n_cases": len(per_case), "n_total": len(ids),
        "errors": sum(1 for r in runs for t in read_traces(RUNS / r) if "error" in t),
        "issues": sum(m["replies_with_issue"] for m in pooled), "replies": sum(m["n_replies"] for m in pooled),
        "privacy": sum(m["privacy_violations"] for m in pooled),
        "claimed": sum(bool(m["return_claimed_done"]) for m in pooled),
        "p50": quantile(lat, 0.5), "p95": quantile(lat, 0.95), "p95_one": quantile(lat_one, 0.95) if lat_one else None,
        "lat_dropped": dropped, "n_turns": len(turns),
        "conv_s": statistics.mean(conv_s) if conv_s else 0.0,
        "prompt_per_conv": sum(m.get("prompt_tokens") or 0 for m in calls) / len(traces),
        "compl_per_conv": sum(m.get("completion_tokens") or 0 for m in calls) / len(traces),
    }


def slow(turn: dict) -> bool:
    """A turn with a cold-start or retry model call, left out of timings (evals/metrics.py, latency_turns)."""
    return any((m.get("latency_s") or 0) > LATENCY_OUTLIER_S for m in turn.get("model_calls", []))


def cost_per_1000(s: dict) -> tuple[float, str]:
    """(USD per 1,000 conversations, how it was worked out)."""
    if s["model"] in PRICE_PER_M:
        pin, pout = PRICE_PER_M[s["model"]]
        usd = 1000 * (s["prompt_per_conv"] * pin + s["compl_per_conv"] * pout) / 1e6
        return usd, (f"measured: {s['prompt_per_conv']:,.0f} input + {s['compl_per_conv']:,.0f} output tokens per "
                     f"conversation at ${pin}/${pout} per 1M")
    if THROUGHPUT:
        per_hour, how = THROUGHPUT["per_hour"], THROUGHPUT["how"]
    else:
        per_hour = 3600 / s["conv_s"] if s["conv_s"] else 0
        how = f"one at a time ({s['conv_s']:.1f} s each)"
    usd = 1000 * GPU_PER_HOUR["L4"] / per_hour if per_hour else float("nan")
    return usd, f"estimate: L4 at ${GPU_PER_HOUR['L4']:.2f}/h, {per_hour:,.0f} conversations/h, {how}"


def gpu_throughput(runs: list[str]) -> dict:
    """Conversations per hour when these runs shared one GPU at the same time."""
    walls, n = [], 0
    for r in runs:
        ts = [t for t in read_traces(RUNS / r) if "error" not in t]
        walls.append(sum(t["turn_s"] for tr in ts for t in tr["turns"] if not slow(t)))
        n += len(ts)
    return {"per_hour": 3600 * n / max(walls),
            "how": f"measured with {len(runs)} runs sharing the GPU ({n} conversations in {max(walls) / 60:.1f} min)"}


def pct(r: dict, total: int | None = None) -> str:
    """A pass rate in %; marked † when some of the category's conversations errored and are left out."""
    if not r.get("n"):
        return "-"
    return f"{100 * r['mean']:.0f}" + (f"† ({r['n']}/{total})" if total and r["n"] < total else "")


def main_table(systems: dict[str, dict], title: str) -> list[str]:
    head = [c for _, c in COLUMNS] + ["All", "Grounding issues / 100 replies", "p95 latency (s)",
                                      "Cost / 1,000 conversations"]
    rows = [f"### {title}", "", "| System | " + " | ".join(head) + " |", "|---|" + "---|" * len(head)]
    for key, s in systems.items():
        usd, _ = cost_per_1000(s)
        est = "" if s["model"] in PRICE_PER_M else " (est.)"
        cells = [pct(s["cats"][c], s["cat_total"][c]) for c, _ in COLUMNS] + [
            f"**{pct(s['all'], s['n_total'])}**", f"{100 * s['issues'] / s['replies']:.1f}" if s["replies"] else "-",
            f"{s['p95']:.1f}", f"${usd:.2f} (₹{usd * INR_PER_USD:,.0f}){est}"]
        runs = f" ×{s['n_runs']}" if s["n_runs"] > 1 else ""
        rows.append(f"| {NAMES.get(key, key)}{runs} | " + " | ".join(cells) + " |")
    return rows


def appendix(systems: dict[str, dict], title: str) -> list[str]:
    rows = [f"### {title}", "", "| Category | " + " | ".join(NAMES.get(k, k) for k in systems) + " |",
            "|---|" + "---|" * len(systems)]
    for c, label in COLUMNS + [(None, "**all**")]:
        cells = [fmt_rate(s["all"] if c is None else s["cats"][c]) for s in systems.values()]
        rows.append(f"| {label} | " + " | ".join(cells) + " |")
    extra = [("Runs", lambda s: str(s["n_runs"])), ("Cases", lambda s: str(s["n_cases"])),
             ("Errored conversations", lambda s: str(s["errors"])),
             ("Grounding issues", lambda s: f"{s['issues']}/{s['replies']} replies"),
             ("Privacy violations", lambda s: str(s["privacy"])),
             ("Returns claimed done", lambda s: str(s["claimed"])),
             ("Latency p50 / p95 per turn (s)", lambda s: f"{s['p50']:.2f} / {s['p95']:.2f}"),
             (f"Turns left out of latency (a model call over {LATENCY_OUTLIER_S:.0f} s)",
              lambda s: f"{s['lat_dropped']} of {s['n_turns']}"),
             ("p95, turns with one tool call (s)", lambda s: f"{s['p95_one']:.2f}" if s["p95_one"] is not None else "-"),
             ("Mean conversation (s)", lambda s: f"{s['conv_s']:.1f}"),
             ("Tokens per conversation (in / out)", lambda s: f"{s['prompt_per_conv']:,.0f} / {s['compl_per_conv']:,.0f}"),
             ("Cost per 1,000 conversations", lambda s: cost_per_1000(s)[1])]
    rows += [f"| {label} | " + " | ".join(f(s) for s in systems.values()) + " |" for label, f in extra]
    return rows


def gap_table(golden: dict[str, dict], fresh: dict[str, dict]) -> list[str]:
    rows = ["### Golden against fresh", "",
            "| System | Golden pass@1 | Fresh pass@1 | Gap (points) |", "|---|---|---|---|"]
    for k in fresh:
        if k in golden:
            g, f = golden[k]["all"], fresh[k]["all"]
            rows.append(f"| {NAMES.get(k, k)} | {fmt_rate(g, counts=False)} | {fmt_rate(f, counts=False)} | "
                        f"{100 * (f['mean'] - g['mean']):+.0f} |")
    return rows


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--golden", nargs="+", required=True, help="system=run1,run2,...")
    ap.add_argument("--fresh", nargs="+", default=[])
    ap.add_argument("--gpu-runs", help="comma-separated runs that shared one GPU at once, for the 2B's throughput")
    ap.add_argument("--out", type=Path)
    a = ap.parse_args()
    if a.gpu_runs:
        THROUGHPUT.update(gpu_throughput(a.gpu_runs.split(",")))
    golden = {k: system(v) for k, v in parse_spec(a.golden).items()}
    fresh = {k: system(v) for k, v in parse_spec(a.fresh).items()}
    lines = ["# Comparison tables (generated by evals/compare_systems.py)", "",
             *main_table(golden, "Golden set (107 cases), pass@1 % per category"), ""]
    if fresh:
        lines += [*main_table(fresh, "Fresh set (50 cases, each system once), pass@1 % per category"), "",
                  *gap_table(golden, fresh), ""]
    lines += ["## Appendix: counts and 95% intervals", "", *appendix(golden, "Golden set"), ""]
    if fresh:
        lines += [*appendix(fresh, "Fresh set"), ""]
    text = "\n".join(lines) + "\n"
    if a.out:
        a.out.write_text(text)
    print(text)


if __name__ == "__main__":
    main()
