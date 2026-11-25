"""Hand labels for the judge: 50 replies, each marked PASS or FAIL for grounded and for resolved.

    uv run python evals/judge_labels.py sheet     # labels.jsonl -> label_sheet.md, to read and correct
    uv run python evals/judge_labels.py read      # label_sheet.md -> labels.jsonl (the reviewed verdicts)
    uv run python evals/judge_labels.py stats
    uv run python evals/judge_labels.py sheet --fresh   # the 25 fresh test replies: label_sheet_fresh.md

The labels come before the judge. Verdicts were drafted with one sentence of reasoning, then reviewed by hand
in the sheet, and the reviewed verdict is the label. The 50 are split once, at random within each combination of
verdicts (seed 3407): the judge prompt is tuned on the 25 "tune" replies only, and agreement is reported on the
25 "test" replies, which are never used for tuning.

A second test set, "fresh" (25 more replies from the repeat runs, on cases the first 50 do not use), was added
after the judge missed the bar on "test": the prompt changed after that measurement (date facts worked out by
code), so "test" could no longer show how the changed judge does on unseen replies. The fresh replies were
labelled before the judge saw them, applying the criteria below as they stood then, including two rules made
explicit while tuning: "cannot answer" needs a search that found nothing, and a parcel with no tracking scan for
about a week may be lost.

The criteria, as the labels apply them:

GROUNDED  every factual claim in the reply about this customer's orders, the store's policies, dates, amounts,
          statuses, or actions taken (a ticket opened, a return created) is directly supported by the evidence:
          the tool results Nova had, today's date and the customer's name. What Nova says about its own
          abilities, greetings, apologies and questions are not claims. Repeating what the customer said as if it
          had been checked, or working out a date from inputs that are not in the evidence, is not supported.
RESOLVED  the reply deals with what the customer asked in this message: it answers it correctly from the
          evidence, or, when the evidence cannot answer it, says so and offers or makes a hand-off. A hand-off is
          made when the customer asks for a person, a parcel may be lost (long past its estimate with no
          movement) or a delivered parcel never arrived. Asking permission to look something up instead of
          looking, leaving part of the question unanswered, ignoring what the customer said, or answering wrongly
          fails.
"""

import argparse
import json
import random
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from evals.judge_units import evidence_text, get_unit, history_text  # noqa: E402

DIR = ROOT / "evals" / "judge"
LABELS = DIR / "labels.jsonl"
SHEET = DIR / "label_sheet.md"
FRESH_SHEET = DIR / "label_sheet_fresh.md"
LINE = re.compile(r"^\*\*(Grounded|Resolved):\*\*\s*(PASS|FAIL)\b\s*[—-]?\s*(.*)$", re.I)


def load() -> list[dict]:
    return [json.loads(x) for x in LABELS.read_text().splitlines() if x.strip()]


def save(rows: list[dict]) -> None:
    LABELS.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))


def split(rows: list[dict], seed: int = 3407) -> None:
    """Half of each verdict combination to tune, half to test (odd groups alternate which side gets the extra)."""
    rng = random.Random(seed)
    groups = defaultdict(list)
    for r in rows:
        groups[(r["grounded"], r["resolved"])].append(r)
    extra_to_tune = True
    for key in sorted(groups):
        g = groups[key]
        rng.shuffle(g)
        half = len(g) // 2 + (len(g) % 2 if extra_to_tune else 0)
        if len(g) % 2:
            extra_to_tune = not extra_to_tune
        for i, r in enumerate(g):
            r["split"] = "tune" if i < half else "test"


def sheet(rows: list[dict]) -> str:
    out = [f"# Label sheet: {len(rows)} replies, grounded and resolved", "",
           "For each reply, read the customer's message and the evidence (what Nova's tools returned), then check "
           "the two verdicts. **Change PASS to FAIL or back wherever you disagree**, and edit the reason if you "
           "like. Keep the format `**Grounded:** PASS — reason`. Your edits are the labels the judge is measured "
           "against.", "",
           "**Grounded:** every claim about the customer's orders, store policies, dates, amounts, statuses or "
           "actions taken is supported by the evidence. Nova's words about itself, greetings and questions are "
           "not claims. Repeating the customer's words as if checked, or working out a date from inputs not in "
           "the evidence, is unsupported.", "",
           "**Resolved:** the reply deals with what the customer asked: answers it correctly from the evidence, or "
           "says it cannot and offers or makes a hand-off. Hand-offs are needed when the customer asks for a "
           "person, a parcel may be lost, or a delivered parcel never arrived. Asking permission instead of "
           "looking, leaving part of the question out, ignoring the customer, or a wrong answer fails.", ""]
    for n, r in enumerate(rows, 1):
        u = get_unit(r["id"])
        out += [f"## {n}. `{r['id']}`", ""]
        if u.history:
            out += ["Earlier in the chat:", "", "```", history_text(u, 4), "```", ""]
        out += [f"**Customer:** {u.customer}", "", "<details><summary>Evidence</summary>", "", "```",
                evidence_text(u), "```", "", "</details>", "", f"**Nova:** {u.reply}", "",
                f"**Grounded:** {r['grounded']} — {r['grounded_why']}", "",
                f"**Resolved:** {r['resolved']} — {r['resolved_why']}", ""]
    return "\n".join(out) + "\n"


def read_sheet(rows: list[dict], path: Path = SHEET) -> list[str]:
    """Copy the verdicts in the sheet back into the labels; returns the changes made."""
    by_id = {r["id"]: r for r in rows}
    current, changes = None, []
    for line in path.read_text().splitlines():
        if m := re.match(r"^## \d+\. `(.+)`", line):
            current = by_id[m.group(1)]
        elif current and (m := LINE.match(line.strip())):
            key = m.group(1).lower()
            verdict, why = m.group(2).upper(), m.group(3).strip()
            if verdict != current[key]:
                changes.append(f"{current['id']}: {key} {current[key]} -> {verdict}")
                current[f"{key}_draft"] = current.get(f"{key}_draft", current[key])
            current[key], current[f"{key}_why"] = verdict, why or current[f"{key}_why"]
    return changes


def stats(rows: list[dict]) -> str:
    c = Counter((r["split"], r["grounded"], r["resolved"]) for r in rows)
    lines = []
    for s in ("tune", "test", "fresh"):
        rs = [r for r in rows if r["split"] == s]
        lines.append(f"{s}: {len(rs)} replies; grounded FAIL {sum(r['grounded'] == 'FAIL' for r in rs)}, "
                     f"resolved FAIL {sum(r['resolved'] == 'FAIL' for r in rs)}")
    return "\n".join(lines) + "\n" + str(dict(c))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("action", choices=["sheet", "read", "stats"])
    ap.add_argument("--fresh", action="store_true", help="the fresh test set and its own sheet")
    a = ap.parse_args()
    rows = load()
    path = FRESH_SHEET if a.fresh else SHEET
    mine = [r for r in rows if (r["split"] == "fresh") == a.fresh]
    if a.action == "sheet":
        path.write_text(sheet(mine))
        print(f"wrote {path.relative_to(ROOT)}")
    elif a.action == "read":
        changes = read_sheet(mine, path)
        for r in mine:
            r["reviewed"] = True
        save(rows)
        print(f"{len(changes)} verdicts changed in review" + ("".join(f"\n  {c}" for c in changes)))
    print(stats(rows))


if __name__ == "__main__":
    main()
