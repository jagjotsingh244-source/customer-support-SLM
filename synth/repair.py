"""Remove "a teammate will reply shortly" from recorded conversations, and pick out the ones to judge again.

The hand-off tool's result tells Nova to say a teammate will pick the problem up "without promising a time", yet
the teacher ended most hand-offs with "they will reply to you shortly". The fact-check judge failed 454
conversations for that alone. Removing the time words (synth/style.py, drop_time_promises) changes nothing else in
a reply, so it is done in code, on every Nova message: the recorded conversation, and each training step's history
and target. A conversation whose fact verdict failed for a time promise is judged again after the repair, because
the judge names only the first slip it finds and a later one may still be there.

    uv run --group data python -m synth.repair            # write <run>.repaired-pending.jsonl per run
    # then, on the teacher's server:
    uv run ... python -m synth.judge data/synthetic/raw/<run>.repaired-pending.jsonl --rubric facts \
        --out data/synthetic/raw/<run>.facts-repaired.jsonl
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from synth.style import drop_time_promises, time_promise  # noqa: E402

RAW = ROOT / "data" / "synthetic" / "raw"
NOTE = "time promise removed after a hand-off"
# How the fact-check judge words a failure for promising a time.
TIME_VERDICT = re.compile(r"shortly|soon|timeframe|specific time|promis\w* a (reply|time)|promise of contact", re.I)


def _fix(msg: dict) -> bool:
    if msg.get("role") != "assistant" or not msg.get("content") or not time_promise(msg["content"]):
        return False
    msg["content"] = drop_time_promises(msg["content"])
    return True


def repair(conv: dict) -> bool:
    """Drop time promises from every Nova message in place; True if anything changed."""
    changed = False
    for m in conv["messages"]:
        changed |= _fix(m)
    for s in conv.get("steps", []):
        for m in s["messages"]:
            changed |= _fix(m)
        changed |= _fix(s["target"])
    if changed:
        conv["meta"]["repaired"] = NOTE
    return changed


def failed_for_time(verdict: dict | None) -> bool:
    return bool(verdict) and not verdict.get("pass", True) and bool(TIME_VERDICT.search(verdict.get("why", "")))


def main() -> None:
    from synth.publish import RUNS, load, verdicts
    total = 0
    for run in RUNS:
        facts = verdicts(run, "facts")
        pending = []
        for c in load(run):
            if repair(c) and failed_for_time(facts.get(c["id"])):
                pending.append(c)
        path = RAW / f"{run}.repaired-pending.jsonl"
        path.write_text("".join(json.dumps(c, ensure_ascii=False) + "\n" for c in pending))
        total += len(pending)
        print(f"{run}: {len(pending)} to judge again -> {path.name}")
    print(f"{total} in all")


if __name__ == "__main__":
    main()
