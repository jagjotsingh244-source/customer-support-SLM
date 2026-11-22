"""One markdown table from several training runs, for training/ABLATIONS.md.

Reads each run's run_info.json, log_history.json and probes.jsonl (written by training/sft.py) and prints, per run:
the setting that varied, trainable parameters, loss at the end and at its best, held-out-intent loss, peak
memory, time, and the final reply to one probe.

    uv run python training/ablation_table.py training/runs/sft1-r8-lr2e-4-bitext_v1-1000rows \\
        training/runs/sft1-r16-lr2e-4-bitext_v1-1000rows training/runs/sft1-r64-lr2e-4-bitext_v1-1000rows
"""

import argparse
import json
from pathlib import Path

PROBE = "i want to cancel my order"


def load(run: Path) -> dict:
    info = json.loads((run / "run_info.json").read_text())
    history = json.loads((run / "log_history.json").read_text())
    probes = [json.loads(line) for line in (run / "probes.jsonl").read_text().splitlines() if line.strip()]
    return {"info": info, "history": history, "probes": probes}


def evals(history, key):
    return [(h["step"], h[key]) for h in history if key in h]


def row(run: dict, probe: str) -> dict:
    info, hist = run["info"], run["history"]
    cfg = info["config"]
    val, unseen = evals(hist, "eval_validation_loss"), evals(hist, "eval_unseen_loss")
    best_step, best_val = min(val, key=lambda p: p[1])
    last = max(run["probes"], key=lambda p: p["step"])["step"]
    reply = next(p for p in run["probes"] if p["step"] == last and p["prompt"] == probe)
    return {
        "Run": info["run_name"], "r / alpha": f"{cfg['r']} / {cfg['lora_alpha']}",
        "Trainable": f"{info['trainable_params']:,}", "Steps": info["plan"]["steps"],
        "Val loss, step 0": f"{val[0][1]:.3f}", "Val loss, end": f"{val[-1][1]:.3f}",
        "Best val (step)": f"{best_val:.3f} ({best_step})",
        "Held-out intents, end": f"{unseen[-1][1]:.3f}",
        "Peak GB": info["memory_gb"]["peak_allocated"], "Train s": info["train_seconds"],
        f"Reply to {probe!r} at step {last}": reply["reply"].replace("|", "/").replace("\n", " "),
    }


def table(rows: list[dict]) -> str:
    cols = list(rows[0])
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    lines += ["| " + " | ".join(str(r[c]) for c in cols) + " |" for r in rows]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("runs", nargs="+", type=Path)
    ap.add_argument("--probe", default=PROBE, help="the probe whose final reply goes in the table")
    a = ap.parse_args()
    print(table([row(load(r), a.probe) for r in a.runs]))


if __name__ == "__main__":
    main()
