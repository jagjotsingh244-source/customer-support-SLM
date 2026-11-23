"""Blind side-by-side: read two systems' replies to the same prompts without knowing which is which.

`make` picks prompts both files answered (half from each split), shuffles which reply is shown first for each
prompt, and writes a sheet to fill in plus a key that maps it back. Do not open key.json until you have chosen.
`score` reads your choices and unblinds them. "=" means both replies are equally good; "x" means neither is
acceptable to send, which matters when both models answer without tools and neither can give the facts.

    uv run python evals/blind_compare.py make evals/style/base.jsonl evals/style/sft1.jsonl --out evals/blind/sft1-vs-base
    # fill in every "Choice" line in evals/blind/sft1-vs-base/sheet.md with 1, 2, = (equally good) or x (neither
    # is acceptable)
    uv run python evals/blind_compare.py score evals/blind/sft1-vs-base
"""

import argparse
import json
import random
import re
from collections import Counter
from pathlib import Path

CHOICE = "Choice (1, 2 or =):"


def read(path):
    return {r["id"]: r for r in (json.loads(x) for x in Path(path).read_text().splitlines() if x.strip())}


def make(a):
    x, y = read(a.a), read(a.b)
    names = [Path(a.a).stem, Path(a.b).stem]
    rng = random.Random(a.seed)
    common = sorted(k for k in x if k in y)
    by_split = {}
    for k in common:
        by_split.setdefault(x[k]["split"], []).append(k)
    picked = []
    for ids in by_split.values():
        picked += rng.sample(ids, min(len(ids), a.n // len(by_split)))
    rng.shuffle(picked)
    key, lines = [], [f"# Blind side-by-side ({len(picked)} prompts)", "",
                      "For each prompt, which reply would you rather a NimbusCart customer got? Judge as the "
                      "customer: helpful, honest, short, a sensible next step. Write 1, 2 or = (equally good) "
                      "after each "
                      f'"{CHOICE}", or x if neither is acceptable to send. Do not open key.json until every '
                      "line is filled in.", ""]
    for i, k in enumerate(picked, 1):
        first = rng.randrange(2)
        shown = [(x, y)[first], (x, y)[1 - first]]
        key.append({"n": i, "id": k, "split": x[k]["split"], "reply_1": names[first], "reply_2": names[1 - first]})
        lines += [f"## {i}. {x[k]['intent']}", "", f"**Customer:** {x[k]['prompt']}", "",
                  f"**Reply 1:** {shown[0][k]['reply']}", "", f"**Reply 2:** {shown[1][k]['reply']}", "",
                  f"{CHOICE} ", ""]
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "sheet.md").write_text("\n".join(lines))
    (out / "key.json").write_text(json.dumps({"systems": names, "seed": a.seed, "pairs": key}, indent=1))
    print(f"wrote {out}/sheet.md ({len(picked)} prompts); the key is in {out}/key.json")


def score(a):
    out = Path(a.dir)
    choices = [m.group(1).strip().lower() for m in re.finditer(rf"^{re.escape(CHOICE)}(.*)$", (out / "sheet.md").read_text(), re.M)]
    key = json.loads((out / "key.json").read_text())
    valid = {"1", "2", "=", "x"}
    if len(choices) != len(key["pairs"]) or any(c not in valid for c in choices):
        missing = [i + 1 for i, c in enumerate(choices) if c not in valid]
        raise SystemExit(f"fill in every choice with 1, 2, = or x first (missing or unreadable: {missing})")
    total, by_split = Counter(), {}
    for pair, c in zip(key["pairs"], choices):
        winner = {"=": "equally good", "x": "neither acceptable"}.get(c) or pair[f"reply_{c}"]
        total[winner] += 1
        by_split.setdefault(pair["split"], Counter())[winner] += 1
    cols = key["systems"] + ["equally good", "neither acceptable"]
    print("| | " + " | ".join(cols) + " |\n|---|" + "---|" * len(cols))
    for name, counts in [("all", total)] + sorted(by_split.items()):
        n = sum(counts.values())
        print(f"| {name} ({n}) | " + " | ".join(f"{counts[c]} ({counts[c] / n:.0%})" for c in cols) + " |")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("make")
    m.add_argument("a")
    m.add_argument("b")
    m.add_argument("--out", required=True)
    m.add_argument("--n", type=int, default=30)
    m.add_argument("--seed", type=int, default=3407)
    s = sub.add_parser("score")
    s.add_argument("dir")
    a = ap.parse_args()
    make(a) if a.cmd == "make" else score(a)


if __name__ == "__main__":
    main()
