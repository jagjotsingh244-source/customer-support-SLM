"""Check the help center against its writing rules and against the seed data.

    uv run python scripts/check_kb.py            # run every check
    uv run python scripts/check_kb.py --numbers  # also list every number on every page

Writing rules (kb/README.md): front matter, under 600 words, `##` sections,
digits instead of spelled-out or vague timings, one term per idea.
Seed agreement: the numbers the pages promise must be the numbers db/seed.py
uses, so a policy cannot drift away from the data it describes.
Exits non-zero if any check fails.
"""

import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from db import seed  # noqa: E402  (constants only; does not touch the database)

KB = ROOT / "kb"
FIELDS = {"id", "title", "policy_version", "effective_date", "tags"}
MAX_WORDS = 600

VAGUE = r"\b(quickly|soon|shortly|promptly|as soon as possible|a few|a couple of|some time|a week|in no time)\b"
SPELLED = (r"\b(one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|fifteen|twenty|thirty)"
           r"[ -](business )?(day|week|month|hour|year)s?\b")
SYNONYMS = {  # never -> use instead (kb/README.md)
    r"return (period|timeframe)": "return window", r"money back|reimburse\w*": "refund",
    r"working days?": "business days", r"delivery fee|shipping fee": "shipping charge",
    r"parcels?|packages?|\bbox(es)?\b": "shipment", r"\bAWB\b|consignment": "tracking number",
    r"\bETA\b|expected date": "estimated delivery date", r"reverse pickup|collection": "pickup",
    r"quality check": "inspection", r"\bagents?\b|\bexecutives?\b": "support team",
    r"\bcomplaints?\b": "ticket",
}


def rng_text(lo_hi):
    return f"{lo_hi[0]}–{lo_hi[1]}"


def money(x):
    return f"₹{int(x)}"


# What each page must say, built from the seed's own constants.
SEED_FACTS = {
    "returns-general": [f"within {seed.WINDOW_DAYS['home']} days of delivery",
                        f"{seed.WINDOW_DAYS['electronics']}-day return window",
                        f"{rng_text(seed.PICKUP_DAYS)} days after you confirm",
                        "within 2 days of pickup"],
    "returns-electronics": [f"within {seed.WINDOW_DAYS['electronics']} days of delivery"],
    "refunds-timing": [f"UPI: {rng_text(seed.REFUND_DAYS['upi'])} business days",
                       f"Wallet: {rng_text(seed.REFUND_DAYS['wallet'])} business days",
                       f"Card: {rng_text(seed.REFUND_DAYS['card'])} business days",
                       f"{rng_text(seed.REFUND_DAYS['bank_transfer'])} business days by bank transfer",
                       "within\n2 days of pickup"],
    "refunds-payment-methods": [f"{rng_text(seed.REFUND_DAYS['upi'])} business days",
                                f"{rng_text(seed.REFUND_DAYS['card'])} business days"],
    "refunds-partial": [f"The {money(seed.SHIPPING_FEE)} shipping charge is not refunded"],
    "payment-failures": [f"within {rng_text(seed.REVERSAL_DAYS)} business\ndays"],
    "shipping-charges": [f"more than {money(seed.FREE_SHIPPING_ABOVE)}",
                         f"{money(seed.SHIPPING_FEE)} shipping charge",
                         f"is {money(seed.FREE_SHIPPING_ABOVE + seed.SHIPPING_FEE)}"],
    "shipping-times": [f"takes {rng_text(seed.TRANSIT_DAYS['metro'])} days",
                       f"takes {rng_text(seed.TRANSIT_DAYS['other'])} days", *seed.METRO],
    "warranty": [f"from 0 to {max(p.warranty_months for p in seed.PRODUCTS)} months"],
}


def pages():
    for path in sorted(KB.glob("*.md")):
        if path.name == "README.md" or path.name.startswith("_"):
            continue
        text = path.read_text()
        m = re.match(r"---\n(.*?)\n---\n(.*)", text, re.S)
        meta = yaml.safe_load(m.group(1)) if m else {}
        yield path, meta, (m.group(2) if m else text)


def check_page(path, meta, body):
    errors = []
    if missing := FIELDS - set(meta):
        errors.append(f"front matter missing {sorted(missing)}")
    if meta.get("id") != path.stem:
        errors.append(f"id {meta.get('id')!r} does not match the file name")
    if (words := len(body.split())) > MAX_WORDS:
        errors.append(f"{words} words (max {MAX_WORDS})")
    if body.count("\n## ") < 2:
        errors.append("needs at least 2 '##' sections")
    flat = " ".join(body.split())
    for pattern, what in [(VAGUE, "vague timing"), (SPELLED, "number in words")]:
        for hit in re.finditer(pattern, flat, re.I):
            errors.append(f"{what}: {hit.group(0)!r}")
    for pattern, use in SYNONYMS.items():
        for hit in re.finditer(pattern, flat, re.I if pattern.islower() else 0):
            errors.append(f"term {hit.group(0)!r}: use {use!r}")
    for fact in SEED_FACTS.get(path.stem, []):
        if " ".join(fact.split()) not in flat:
            errors.append(f"does not say {fact!r}, which db/seed.py uses")
    return errors


def check_non_returnable(all_text):
    """Every product the seed marks not returnable must be covered by the page."""
    page = all_text["returns-non-returnable"].lower()
    stems = ["earbud", "earphone", "trimmer", "pillow", "screen protector"]
    errors = []
    for p in seed.PRODUCTS:
        if not p.returnable and not any(s in p.name.lower() and s in page for s in stems):
            errors.append(f"returns-non-returnable: product {p.name!r} is not returnable in the seed but not listed")
    return errors


def numbers_table(all_text):
    unit = r"(?:business days|days|day|months|hours|digits|IST)"
    pat = re.compile(rf"(₹\d+(?:,\d{{3}})*|\d+(?:[–:.]\d+)?(?:-day|-month)?(?:\s+{unit})?)")
    rows = []
    for page, body in all_text.items():
        section = ""
        for line in body.splitlines():
            if line.startswith("## "):
                section = line[3:]
            for hit in pat.finditer(line):
                rows.append((hit.group(1), page, section))
    rows.sort(key=lambda r: (re.sub(r"\D.*", "", r[0].lstrip("₹")).zfill(6), r[0], r[1]))
    print("\n| Number | Page | Section |\n|---|---|---|")
    for r in rows:
        print(f"| {r[0]} | {r[1]} | {r[2]} |")


def main():
    all_text, failures = {}, []
    for path, meta, body in pages():
        all_text[path.stem] = body
        failures += [f"{path.stem}: {e}" for e in check_page(path, meta, body)]
    failures += check_non_returnable(all_text)
    print(f"{len(all_text)} pages checked")
    for f in failures:
        print("FAIL", f)
    if "--numbers" in sys.argv:
        numbers_table(all_text)
    if not failures:
        print("help center passed: writing rules hold and every number matches db/seed.py")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
