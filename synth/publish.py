"""Filter every generation run and build the two datasets: nova-trajectories (kept) and nova-rejects.

All runs are filtered together (synth/verify.py), with the tone and fact-check verdicts attached, so dedup works
across runs. Each row is one conversation: its messages as recorded, its training steps (the request the student
would see and the teacher's message as target), and its metadata. Rejects keep their reasons: a rejected
conversation plus a corrected version of its bad turn is the pair preference tuning needs later.

    uv run --group data python -m synth.publish            # build locally, write the cards and the keep-rate report
    uv run --group data python -m synth.publish --push     # and push both datasets to the Hub (private)
"""

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from synth.verify import filter_run, report  # noqa: E402

RAW = ROOT / "data" / "synthetic" / "raw"
OUT = ROOT / "data" / "synthetic"
CARDS = ROOT / "synth" / "cards"
REPORT = ROOT / "notes" / "trajectory-filters" / "final.md"
HUB_USER = "123jagjot"
# v2: hand-off time promises removed in code (synth/repair.py) and the fill-r6 run added.
VERSION = "v2"
# Generation runs that go into the datasets. The first pilot used older teacher rules and an older judge; the
# test runs before it had no personas. Later pilots passed the same checks as the full run and are kept.
# fill-r6: conversations for the scenario x persona cells filtering had left empty (teacher rules r6).
# fill-r7: every cell brought to at least five kept, then well-keeping scenarios topped up (Vertex AI teacher).
RUNS = ["pilot-200-r4", "pilot-200-r5", "full-a", "full-b1", "full-b2", "full-b3", "full-b4", "full-b5", "no-tool",
        "fill-r6", "fill-r7"]
TONE = {"pilot-200-r4": "judge3", "pilot-200-r5": "judge3", "full-a": "judge3"}   # newest tone verdicts per run


def load(run: str) -> list[dict]:
    path = RAW / f"{run}.jsonl"
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()] if path.exists() else []


def verdicts(run: str, kind: str) -> dict:
    path = RAW / f"{run}.{kind}.jsonl"
    return {j["id"]: j for j in map(json.loads, path.read_text().splitlines())} if path.exists() else {}


def collect() -> list[dict]:
    """Every conversation of every run, repaired (synth/repair.py), with its verdicts. A repaired conversation
    whose fact verdict failed for a time promise takes its verdict from the judging after the repair; without one
    it keeps the old verdict and stays rejected. Removing the time words cannot change a tone verdict."""
    from synth.repair import failed_for_time, repair
    convs = []
    for run in RUNS:
        tone = verdicts(run, TONE.get(run, "judge3")) or verdicts(run, "judge")
        facts = verdicts(run, "facts")
        facts_after = verdicts(run, "facts-repaired")
        for c in load(run):
            c["meta"].setdefault("run", f"{run}.jsonl")
            repaired = repair(c)
            if c["id"] in tone:
                c["judge"] = tone[c["id"]]
            if c["id"] in facts:
                c["fact_judge"] = facts[c["id"]]
                if repaired and failed_for_time(facts[c["id"]]) and c["id"] in facts_after:
                    c["fact_judge"] = facts_after[c["id"]]
            convs.append(c)
    return convs


def row(c: dict, reasons: list[str] | None = None) -> dict:
    """One dataset row; nested structures as JSON strings, so every row has the same columns."""
    m = c["meta"]
    out = {"id": c["id"], "scenario": m["scenario"], "persona": m["persona"], "customer_id": m["customer_id"],
           "run": m["run"], "teacher": m.get("teacher", ""), "teacher_rules": m.get("teacher_rules", ""),
           "outcome": m["outcome"], "customer_turns": m["customer_turns"],
           "messages": json.dumps(c["messages"], ensure_ascii=False),
           "steps": json.dumps([{"messages": s["messages"], "target": s["target"]} for s in c["steps"] if s["ok"]],
                               ensure_ascii=False),
           "meta": json.dumps(m, ensure_ascii=False, default=str),
           # the first Nova reply (1-based) the fact-check judge found a slip in; 0 if none or not judged
           "fact_reply": int((c.get("fact_judge") or {}).get("reply") or 0) if not (c.get("fact_judge") or {}).get("pass", True) else 0}
    if reasons is not None:
        out["reasons"] = json.dumps(reasons, ensure_ascii=False)
        out["first_reason"] = reasons[0].split(":")[0]
    return out


def card(kept: list[dict], rejected: list[dict], kind: str) -> str:
    convs = kept if kind == "kept" else rejected
    steps = sum(sum(1 for s in c["steps"] if s["ok"]) for c in convs)
    name = f"nova-trajectories-{VERSION}" if kind == "kept" else f"nova-rejects-{VERSION}"
    lines = [f"# {name}", "",
             ("Multi-turn support conversations for NimbusCart's assistant, Nova, generated inside the real agent "
              "loop and kept only when they pass every check." if kind == "kept" else
              "The conversations the checks rejected, each with every reason it failed."), "",
             "## How they were made", "",
             "- A teacher model (Qwen3.5-27B, Apache-2.0) played Nova against the real tools, a seeded orders "
             "database (train-side customers only) and the real help-center search; a simulated customer with a "
             "hidden goal, limited knowledge and one of eight personas played the other side, opening from a real "
             "Bitext question.",
             "- Every fact in a conversation comes from the database or the help center; only the behaviour comes "
             "from the teacher. The teacher read extra rules the student never sees; each step is recorded with "
             "Nova's own prompt, state block and history trimming, as served.",
             "- Checks (synth/verify.py): tool-call schema, order facts before lookups, numbers, day counts and "
             "dates against sources, citations, returns and cancellations, hand-offs, privacy, call limit, right "
             "order, length and style, needless tool calls, a tone judge and a fact-check judge (both tested on "
             "planted faults first), and dedup.", "",
             "## Contents", "",
             f"- {len(convs)} conversations, {steps} training steps (one model call each: the request as the "
             "student sees it, and the teacher's message as the target).",
             "- Columns: id, scenario, persona, customer_id, run, teacher, teacher_rules, outcome, customer_turns, "
             "messages (JSON), steps (JSON), meta (JSON)" + (", reasons (JSON), first_reason." if kind != "kept"
                                                               else "."), "",
             "| Scenario | Conversations |", "|---|---|"]
    lines += [f"| {s} | {n} |" for s, n in sorted(Counter(c["meta"]["scenario"] for c in convs).items())]
    lines += ["", "| Persona | Conversations |", "|---|---|"]
    lines += [f"| {p} | {n} |" for p, n in sorted(Counter(c["meta"]["persona"] for c in convs).items())]
    if kind != "kept":
        lines += ["", "| First reason | Conversations |", "|---|---|"]
        lines += [f"| {r} | {n} |" for r, n in
                  Counter(c["rejected"][0].split(":")[0] for c in rejected).most_common()]
    lines += ["", "Synthetic data: every name, order and address is generated. Private; made for training a small "
              "support model, not for evaluation."]
    return "\n".join(lines) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--push", action="store_true", help="push both datasets and their cards to the Hub (private)")
    a = ap.parse_args()
    from datasets import Dataset                          # the data group
    convs = collect()
    kept, rejected = filter_run(convs)
    print(f"{len(kept)} kept, {len(rejected)} rejected of {len(convs)}")
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(report("all runs", kept, rejected))
    CARDS.mkdir(parents=True, exist_ok=True)
    sets = {f"nova-trajectories-{VERSION}": (Dataset.from_list([row(c) for c in kept]), card(kept, rejected, "kept")),
            f"nova-rejects-{VERSION}": (Dataset.from_list([row(c, c["rejected"]) for c in rejected]),
                                card(kept, rejected, "rejected"))}
    for name, (ds, text) in sets.items():
        ds.save_to_disk(OUT / name)
        (CARDS / f"{name}.md").write_text(text)
        print(f"  {name}: {len(ds)} rows -> {OUT / name}, card synth/cards/{name}.md")
    if a.push:
        from huggingface_hub import DatasetCard
        for name, (ds, text) in sets.items():
            repo = f"{HUB_USER}/{name}"
            ds.push_to_hub(repo, private=True)
            DatasetCard(text).push_to_hub(repo, repo_type="dataset")
            print(f"  pushed {repo} (private)")


if __name__ == "__main__":
    main()
