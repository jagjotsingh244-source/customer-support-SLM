"""Check the golden eval cases against the case format and the seeded store.

    uv run python evals/validate.py             # every category must be at its quota
    uv run python evals/validate.py --partial   # while writing: skip the quota check

A golden case states what is true, so every expectation must be traceable to the
database or the help center. For each case in evals/golden/*.jsonl this checks:

1. The format (a Pydantic model; unknown fields are errors) and unique ids.
2. The customer is in the eval partition (never one the training data can use).
3. Every order_id in an expected tool call belongs to that customer, except in
   adversarial cases, where a foreign order must come back as "not_found".
4. The case's scenario is the seed scenario of the order it is about.
5. Every expected tool call returns real data when called directly as that
   customer (no error, nothing empty), and list_my_orders, when expected
   before another order tool, actually lists that order.
6. Every expected `sources` section exists in kb_sections.
7. Every must_include fact appears in what the expected tools return or in the
   expected sources, so no fact comes from memory.

Exits non-zero on any failure.
"""

import argparse
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from agent.tools_v0 import REGISTRY, Session, connect  # noqa: E402

GOLDEN = ROOT / "evals" / "golden"
DB_URL = os.environ.get("DB_URL", "postgresql://nimbus:nimbus@localhost:5433/nimbus")

QUOTAS = {"policy": 25, "order_lookup": 25, "returns": 15,
          "unanswerable": 15, "escalation": 10, "adversarial": 10}
PREFIX = {"policy": "pol", "order_lookup": "ord", "returns": "ret",
          "unanswerable": "una", "escalation": "esc", "adversarial": "adv"}
ORDER_TOOLS = {"get_order_status", "get_tracking", "propose_return"}


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ToolCall(Strict):
    name: Literal["list_my_orders", "get_order_status", "get_tracking",
                  "search_help_center", "propose_return", "escalate_to_human"]
    # Exact arguments the model must pass. None means "any arguments" (free text
    # such as a search query or a hand-off summary, which cannot be matched exactly).
    args: dict[str, Any] | None


class Expect(Strict):
    tool_calls: list[ToolCall]
    must_include: list[str]
    must_not_include: list[str]
    should_escalate: bool
    confirm_card: bool
    sources: list[str] = Field(default_factory=list)   # help-center section_ids the answer rests on


class Case(Strict):
    id: str
    category: Literal["policy", "order_lookup", "returns", "unanswerable", "escalation", "adversarial"]
    scenario: str | None              # seed scenario of the order the case is about; None if no order
    customer_id: int
    turns: list[str] = Field(min_length=1)
    expect: Expect
    notes: str = Field(min_length=10)


def load() -> tuple[list[tuple[str, Case]], list[str]]:
    cases, errors = [], []
    for path in sorted(GOLDEN.glob("*.jsonl")):
        for n, line in enumerate(path.read_text().splitlines(), 1):
            if not line.strip():
                continue
            where = f"{path.name}:{n}"
            try:
                cases.append((where, Case.model_validate_json(line)))
            except ValidationError as e:
                errors.append(f"{where}: bad format: {e.errors()[0]['loc']} {e.errors()[0]['msg']}")
    return cases, errors


CONTRACTIONS = {"can't": "cannot", "can not": "cannot", "won't": "will not", "isn't": "is not",
                "don't": "do not", "doesn't": "does not", "aren't": "are not",
                "hasn't": "has not", "haven't": "have not", "wasn't": "was not"}


def normalize(text: str) -> str:
    """Text as the checks compare it. The scorer must use this same function.

    Lowercase; '_' read as ' ' (bank_transfer); every dash and "x to y" between
    numbers becomes "x-y" ("5–7", "5 - 7", "5 to 7"); "7-day" becomes "7 day";
    common contractions spelled out; whitespace collapsed. So a fact written
    "5-7" matches "5–7 business days" and "5 to 7 days", and "7 day" matches
    "7 days" and "7-day window".
    """
    t = text.lower().replace("_", " ").replace("’", "'")
    t = re.sub(r"[–—]", "-", t)
    t = re.sub(r"(\d)\s*(?:-|to)\s*(\d)", r"\1-\2", t)
    t = re.sub(r"(\d)-(day|days|month|months|hour|hours|business)\b", r"\1 \2", t)
    for short, full in CONTRACTIONS.items():
        t = t.replace(short, full)
    return re.sub(r"\s+", " ", t)


def flat(x: Any) -> str:
    """Everything a tool returned, as one normalized string."""
    return normalize(x if isinstance(x, str) else json.dumps(x, default=str, ensure_ascii=False))


def check(case: Case, conn) -> list[str]:
    errs = []
    e = case.expect
    if not case.id.startswith(PREFIX[case.category] + "-"):
        errs.append(f"id should start with '{PREFIX[case.category]}-'")

    row = conn.execute("SELECT partition FROM customers WHERE customer_id = %s", (case.customer_id,)).fetchone()
    if row is None:
        return [f"customer {case.customer_id} does not exist"]
    if row["partition"] != "eval":
        errs.append(f"customer {case.customer_id} is in '{row['partition']}', not eval")

    session = Session.open(conn, case.customer_id)
    evidence = []                                    # what the facts must be found in
    listed = None
    for call in e.tool_calls:
        if call.args is None:
            if call.name in ORDER_TOOLS:
                errs.append(f"{call.name}: order tools need exact args")
            continue
        oid = call.args.get("order_id")
        if oid is not None:
            owner = conn.execute("SELECT customer_id FROM orders WHERE order_id = %s", (oid,)).fetchone()
            if owner is None:
                errs.append(f"order {oid} does not exist")
                continue
            foreign = owner["customer_id"] != case.customer_id
            if foreign and case.category != "adversarial":
                errs.append(f"order {oid} belongs to customer {owner['customer_id']}, not {case.customer_id}")
            if not foreign and case.scenario is not None and call.name in ORDER_TOOLS:
                scen = conn.execute("SELECT scenario FROM scenarios WHERE order_id = %s", (oid,)).fetchone()
                if scen and scen["scenario"] != case.scenario:
                    errs.append(f"order {oid} is scenario '{scen['scenario']}', case says '{case.scenario}'")
            if listed is not None and oid not in listed:
                errs.append(f"list_my_orders is expected first, but it does not list order {oid}")
        try:
            result = REGISTRY[call.name](session=session, **call.args)
        except Exception as ex:
            errs.append(f"{call.name}({call.args}) raised {type(ex).__name__}: {ex}")
            continue
        if isinstance(result, dict) and result.get("error") == "not_found" and case.category == "adversarial":
            continue                                 # the expected answer to a foreign order
        if not result or (isinstance(result, dict) and "error" in result):
            errs.append(f"{call.name}({call.args}) returned no real data: {result}")
            continue
        if call.name == "list_my_orders":
            listed = {o["order_id"] for o in result}
        evidence.append(flat(result))

    for sid in e.sources:
        sec = conn.execute("SELECT body FROM kb_sections WHERE section_id = %s", (sid,)).fetchone()
        if sec is None:
            errs.append(f"source '{sid}' is not a help-center section")
        else:
            evidence.append(flat(sec["body"]))

    joined = " ".join(evidence)
    for fact in e.must_include:
        if normalize(fact) not in joined:
            errs.append(f"must_include '{fact}' is not in any expected tool result or source")
    for fact in e.must_not_include:
        if normalize(fact) in (normalize(f) for f in e.must_include):
            errs.append(f"'{fact}' is in both must_include and must_not_include")
    if e.should_escalate and not any(c.name == "escalate_to_human" for c in e.tool_calls):
        errs.append("should_escalate is true but escalate_to_human is not an expected call")
    return errs


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--partial", action="store_true", help="skip the per-category quota check")
    a = ap.parse_args()

    cases, errors = load()
    ids = Counter(c.id for _, c in cases)
    errors += [f"id '{i}' is used {n} times" for i, n in ids.items() if n > 1]

    conn = connect(DB_URL)
    for where, case in cases:
        errors += [f"{where} {case.id}: {msg}" for msg in check(case, conn)]

    counts = Counter(c.category for _, c in cases)
    print(f"{'category':<14}{'cases':>6}{'quota':>7}")
    for cat, quota in QUOTAS.items():
        print(f"{cat:<14}{counts[cat]:>6}{quota:>7}")
        if counts[cat] > quota or (not a.partial and counts[cat] != quota):
            errors.append(f"{cat}: {counts[cat]} cases, quota is {quota}")
    compound = sum(1 for _, c in cases if "compound" in c.notes.lower())
    print(f"{'total':<14}{len(cases):>6}{sum(QUOTAS.values()):>7}   compound: {compound}")

    if errors:
        print(f"\n{len(errors)} problem(s):")
        for err in errors:
            print(" -", err)
        sys.exit(1)
    print("\ngolden set valid")


if __name__ == "__main__":
    main()
