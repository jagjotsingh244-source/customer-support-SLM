"""How replies are written, counted: length, placeholders, lists, digits, endings and repeated openings.

A fine-tune that learns Nova's voice should move these toward the training replies: shorter, no `{{...}}` slots,
no lists, no invented numbers, ending with one next step. A fine-tune that memorised a few phrases shows up as
many replies sharing one opening.

Measured on a fixed set of held-out prompts (held_out_prompts: 100 from the validation split, 100 from the two
intents never trained on), each with the system prompt it was built with and no tools, so every system answers
the same 200 messages. The reference column is the dataset's own replies to those prompts.

    uv run --group data python evals/style_metrics.py --reference                      # the target replies
    uv run --group data python evals/style_metrics.py --reference base.jsonl sft1.jsonl  # side by side

A replies file is JSONL with one {"id": ..., "reply": ...} per line (evals/generate_replies.py writes them).
"""

import argparse
import json
import re
from collections import Counter
from pathlib import Path

DATASET, REVISION = "123jagjot/nimbus-bitext-v1", "975c80864824005c28c22ef0411049fb81f33c8e"
SEED, PER_SPLIT = 3407, 100
WORD_LIMIT = 80  # the system prompt's "Keep replies under 80 words"

# The offer pattern is the one the rewrite checks in data_prep/prepare_bitext.py used (tests/test_style_metrics.py
# fails if they drift apart).
OFFER = re.compile(r"\b(I can|I could|I'd|I would|I'll|let me|shall I|would you like|want me to|"
                   r"happy to|glad to|a teammate|our team|the NimbusCart (website|app))\b", re.I)
LIST = re.compile(r"^\s*([-*•]|\d+[.)])\s", re.M)


def last_sentence(text):
    return re.split(r"(?<=[.?!])\s+", text.strip())[-1] if text.strip() else ""


def opening(text, n=5):
    return " ".join(re.findall(r"[a-z']+", text.lower())[:n])


def features(reply):
    last = last_sentence(reply)
    return {
        "words": len(reply.split()),
        "placeholder": "{{" in reply or "}}" in reply,
        "list": bool(LIST.search(reply)) or "**" in reply,
        "digit": bool(re.search(r"\d", reply)),
        "next_step": last.endswith("?") or bool(OFFER.search(last)),
        "over_limit": len(reply.split()) >= WORD_LIMIT,
        "exclamation": "!" in reply,
    }


def metrics(replies):
    """Summary of a list of reply strings: means and shares, plus how concentrated the openings are."""
    f = [features(r) for r in replies]
    n = len(f)
    share = lambda k: sum(x[k] for x in f) / n  # noqa: E731
    openings = Counter(opening(r) for r in replies)
    top, top_count = openings.most_common(1)[0]
    return {
        "replies": n,
        "mean words": sum(x["words"] for x in f) / n,
        "with {{": share("placeholder"),
        "with a list": share("list"),
        "with a digit": share("digit"),
        "ends with a question or offer": share("next_step"),
        f"{WORD_LIMIT}+ words": share("over_limit"),
        "with !": share("exclamation"),
        "distinct openings": len(openings) / n,
        "most common opening": f'"{top}" ({top_count / n:.0%})',
    }


def held_out_prompts():
    """The fixed 200: per split, a seeded sample of 100 rows; each keeps its system and customer messages."""
    from datasets import load_dataset

    ds = load_dataset(DATASET, revision=REVISION)
    rows = []
    for split in ("validation", "test_unseen_intents"):
        part = ds[split].shuffle(seed=SEED).select(range(PER_SPLIT))
        for r in part:
            rows.append({"id": f"{split}-{r['row_id']}", "split": split, "intent": r["intent"],
                         "messages": r["messages"][:-1], "reference": r["messages"][-1]["content"]})
    return rows


def read_replies(path):
    rows = [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]
    return {r["id"]: r["reply"] for r in rows}


def fmt(v):
    if isinstance(v, float):
        return f"{v:.1f}" if v > 1 else f"{v:.0%}"
    return str(v)


def table(columns):
    """columns: {name: metrics dict}. A markdown table with one column per system."""
    names = list(columns)
    keys = list(next(iter(columns.values())))
    lines = ["| | " + " | ".join(names) + " |", "|---|" + "---|" * len(names)]
    lines += [f"| {k} | " + " | ".join(fmt(columns[n][k]) for n in names) + " |" for k in keys]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="*", help="replies files (JSONL with id and reply)")
    ap.add_argument("--reference", action="store_true", help="add the dataset's own replies as a column")
    ap.add_argument("--split", choices=["validation", "test_unseen_intents"], help="only this half of the 200")
    a = ap.parse_args()
    prompts = held_out_prompts() if a.reference or a.split else None
    keep = {p["id"] for p in prompts if not a.split or p["split"] == a.split} if prompts else None
    cols = {}
    if a.reference:
        cols["reference"] = metrics([p["reference"] for p in prompts if p["id"] in keep])
    for f in a.files:
        replies = read_replies(f)
        cols[Path(f).stem] = metrics([v for k, v in replies.items() if keep is None or k in keep])
    if not cols:
        ap.error("give replies files, --reference, or both")
    print(table(cols))


if __name__ == "__main__":
    main()
