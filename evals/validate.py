"""Check the golden eval cases against the case format and the seeded store.

    uv run python evals/validate.py             # every category must be at its quota
    uv run python evals/validate.py --partial   # while writing: skip the quota check
    uv run python evals/validate.py --probes    # the phrasing probes in evals/probes/
    uv run python evals/validate.py --fresh     # the 50 fresh cases in evals/fresh/

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

Phrasing probes (evals/probes/*.jsonl) are rewordings of golden cases: offensive, typo-heavy, polite or
keyword-only versions of a clean message. Each names the golden case it rephrases and must keep that case's
customer, scenario, category and expectations exactly, so a score difference between the two comes from the
phrasing alone. They are checked like golden cases, kept out of the 100-case golden set, and reported apart.

Fresh cases (evals/fresh/*.jsonl) are 50 more cases in the golden set's proportions, written from the store and
the help center alone after every tuning decision was made, and scored once per system. They are checked like
golden cases, against their own quotas, and their ids must not repeat a golden id.

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
PROBES = ROOT / "evals" / "probes"
FRESH = ROOT / "evals" / "fresh"
DB_URL = os.environ.get("DB_URL", "postgresql://nimbus:nimbus@localhost:5433/nimbus")

# old_policy: the customer quotes a rule from kb/_archive/; Nova must give and cite the current one.
QUOTAS = {"policy": 25, "order_lookup": 25, "returns": 15,
          "unanswerable": 15, "escalation": 10, "adversarial": 12, "old_policy": 5}
FRESH_QUOTAS = {"policy": 12, "order_lookup": 12, "returns": 7,
                "unanswerable": 7, "escalation": 5, "adversarial": 5, "old_policy": 2}
PREFIX = {"policy": "pol", "order_lookup": "ord", "returns": "ret",
          "unanswerable": "una", "escalation": "esc", "adversarial": "adv", "old_policy": "old"}
ORDER_TOOLS = {"get_order_status", "get_tracking", "propose_return"}
PHRASING_QUOTAS = {"offensive": 3, "typos": 3, "polite": 3, "keyword": 3}


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
    category: Literal["policy", "order_lookup", "returns", "unanswerable", "escalation", "adversarial",
                      "old_policy"]
    scenario: str | None              # seed scenario of the order the case is about; None if no order
    customer_id: int
    turns: list[str] = Field(min_length=1)
    expect: Expect
    notes: str = Field(min_length=10)


class ProbeCase(Case):
    phrasing: Literal["offensive", "typos", "polite", "keyword"]
    rephrases: str                    # id of the golden case this one rewords


def load(directory: Path = GOLDEN, model: type[Case] = Case) -> tuple[list[tuple[str, Case]], list[str]]:
    cases, errors = [], []
    for path in sorted(directory.glob("*.jsonl")):
        for n, line in enumerate(path.read_text().splitlines(), 1):
            if not line.strip():
                continue
            where = f"{path.name}:{n}"
            try:
                cases.append((where, model.model_validate_json(line)))
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


def load_probes() -> tuple[list[tuple[str, Case]], list[str]]:
    return load(PROBES, ProbeCase)


def check_probes(probes, golden) -> list[str]:
    """Each probe rewords a golden case and keeps everything else about it."""
    errors, by_id = [], {c.id: c for _, c in golden}
    for where, p in probes:
        g = by_id.get(p.rephrases)
        if g is None:
            errors.append(f"{where} {p.id}: rephrases '{p.rephrases}', which is not a golden case")
            continue
        for field in ("category", "scenario", "customer_id", "expect"):
            if getattr(p, field) != getattr(g, field):
                errors.append(f"{where} {p.id}: {field} differs from {g.id}")
        if p.turns == g.turns:
            errors.append(f"{where} {p.id}: same message as {g.id}; a probe must reword it")
        if p.id in by_id:
            errors.append(f"{where} {p.id}: id is also a golden case id")
    counts = Counter(p.phrasing for _, p in probes)
    print(f"{'phrasing':<14}{'cases':>6}{'quota':>7}")
    for phr, quota in PHRASING_QUOTAS.items():
        print(f"{phr:<14}{counts[phr]:>6}{quota:>7}")
        if counts[phr] != quota:
            errors.append(f"{phr}: {counts[phr]} probes, quota is {quota}")
    return errors


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--partial", action="store_true", help="skip the per-category quota check")
    ap.add_argument("--probes", action="store_true", help="check the phrasing probes instead of the golden set")
    ap.add_argument("--fresh", action="store_true", help="check the fresh cases instead of the golden set")
    a = ap.parse_args()

    if a.probes:
        golden, errors = load()
        probes, errors_p = load_probes()
        errors = errors + errors_p + check_probes(probes, golden)
        conn = connect(DB_URL)
        for where, case in probes:
            errors += [f"{where} {case.id}: {msg}" for msg in check(case, conn)]
        if errors:
            print(f"\n{len(errors)} problem(s):")
            for err in errors:
                print(" -", err)
            sys.exit(1)
        print(f"\n{len(probes)} phrasing probes valid")
        return

    cases, errors = load(FRESH if a.fresh else GOLDEN)
    ids = Counter(c.id for _, c in cases)
    errors += [f"id '{i}' is used {n} times" for i, n in ids.items() if n > 1]
    if a.fresh:
        golden_ids = {c.id for _, c in load()[0]}
        errors += [f"{c.id}: also a golden id" for _, c in cases if c.id in golden_ids]
    quotas = FRESH_QUOTAS if a.fresh else QUOTAS

    conn = connect(DB_URL)
    for where, case in cases:
        errors += [f"{where} {case.id}: {msg}" for msg in check(case, conn)]

    counts = Counter(c.category for _, c in cases)
    print(f"{'category':<14}{'cases':>6}{'quota':>7}")
    for cat, quota in quotas.items():
        print(f"{cat:<14}{counts[cat]:>6}{quota:>7}")
        if counts[cat] > quota or (not a.partial and counts[cat] != quota):
            errors.append(f"{cat}: {counts[cat]} cases, quota is {quota}")
    compound = sum(1 for _, c in cases if "compound" in c.notes.lower())
    print(f"{'total':<14}{len(cases):>6}{sum(quotas.values()):>7}   compound: {compound}")

    if errors:
        print(f"\n{len(errors)} problem(s):")
        for err in errors:
            print(" -", err)
        sys.exit(1)
    print("\nfresh set valid" if a.fresh else "\ngolden set valid")


if __name__ == "__main__":
    main()
