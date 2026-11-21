# NimbusCart help center

The pages in this folder are the only source of policy facts Nova may state.
Retrieval indexes every `*.md` file here except this README and files starting
with `_`.

- `_archive/` holds old policy versions. Never indexed; kept to test that Nova
  cites the current rule.
- `_customer_words.md` lists how customers phrase things. Never indexed; used to
  test retrieval.

## Writing rules

1. One topic per page, one rule per `##` section. Retrieval returns sections.
2. Every number as digits with its unit: "7 days", never "seven days" or "a week".
3. The exception sits next to the rule it changes, in the same section.
4. One term per idea (table below). Never a synonym.
5. Reference tone: short, factual, no marketing.
6. Under 600 words per page, with front matter: `id`, `title`,
   `policy_version`, `effective_date`, `tags`.
7. Every number must agree with `db/seed.py`. `scripts/check_kb.py` checks the
   rules above and lists every number across all pages.

## Terms

| Use | Never |
|---|---|
| return window | return period, return timeframe |
| refund | money back, reimbursement |
| business days (Monday to Friday) | working days |
| shipping charge | delivery fee, shipping fee |
| shipment (one box with its own tracking number) | parcel, package, box |
| tracking number | AWB, consignment number |
| carrier (the company: BlueLine, SwiftShip) | courier company, logistics partner |
| courier (the person at your door) | delivery boy, rider |
| estimated delivery date | ETA, expected date |
| pickup (a return collected from you) | collection, reverse pickup |
| inspection | quality check |
| support team | agent, executive |
| ticket | complaint, case |
