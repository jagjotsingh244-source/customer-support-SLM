# Privacy

What Nova, NimbusCart's support assistant, can see, what it can say, and what is kept. The store's data is
synthetic, but it is handled as if it were real. Each claim below names the file that implements it; gaps are
listed at the end. The field-by-field review is in `evals/reports/05c_privacy_audit.md`.

## What Nova can see

Only the signed-in customer's own data, through six tools (`agent/tools_v2.py`, SQL in `agent/tools_v0.py`):

| Tool | Returns |
|---|---|
| `list_my_orders` | order number, date placed, status, total, item names |
| `get_order_status` | order number, status, placed / cancelled time, payment method (upi, card, wallet or cod: never a number), total, shipping fee, delivery **city**; per item: line number, name, category, quantity, price, opened; returns (id, status, reason, dates, rejection reason, lines); refunds (id, amount, method, status, dates) |
| `get_tracking` | per box: carrier, tracking number, status, ETA, delivery time, items, last scan time, place and event |
| `search_help_center` | up to 3 help-center sections (public policy text) |
| `propose_return` | whether one item can be returned, the refund estimate, a proposal id for the Confirm button |
| `escalate_to_human` | a ticket number |

No tool selects a street address, pincode, phone number, email, card number or bank detail
(`tests/test_guardrails.py` checks the SQL). With the guards on, results are trimmed further before the model
reads them (`agent/privacy.py` `minimise`): internal ids (`return_id`, `refund_id`, `shipment_id`) and when bank
details were added are dropped, and order, return and refund timestamps are cut to the date. Delivery and scan
times keep the time of day: a "never got it" dispute and the lost-parcel rule need them. The customer is never a tool argument: it comes from the session,
and every query runs in a transaction that sets `app.customer_id`, so Postgres row-level security returns only
that customer's rows (`db/roles.sql`). Another customer's order looks exactly like an order that does not exist.
The tools connect as `nova_reader` and `nova_writer`, which own no table and cannot update or delete anything.

The system prompt carries today's date and the customer's full name (`agent/prompts.py`).

## What Nova can say

Every reply passes through checks in code before the customer sees it, when the guards are on
(`agent/guardrails.py`, `agent/privacy.py`):

- **Personal data**: a phone number (any common Indian layout), a card-like number (13 to 19 digits that pass
  the Luhn check), an email address, a UPI ID, or an Aadhaar, PAN or IFSC number replaces the whole reply with a
  safe one. No tool returns any of these, so one in a reply was copied from the conversation or made up.
- **Asking for secrets**: a reply that asks for an OTP, CVV, UPI PIN, password, card number or bank details is
  replaced (a warning such as "never share your OTP" passes). With the checks off, a planted carrier name once
  made the model ask for a card number and CVV (`evals/reports/05a_attacks.md`).
- **Links**: every URL, markdown image, HTML tag with a `src`/`href`, `//host` and bare `host/path` link is
  removed.
- **Prompt echo**: a reply that repeats 8 words in a row from the system prompt's rules is replaced.
- **Unbacked action claims**: "your refund has been approved", "I've cancelled it", "the pickup is booked" are
  replaced unless a tool result in the conversation shows it. Nova cannot refund, cancel or confirm anything.
- **Tool names** ("I can call list_my_orders") are reworded into plain words.

Text from outside the support team (product names, carrier events, help-center pages) has sentences that read
like instructions cut out before the model sees it, and each result is labelled with its source.

## What is logged, and for how long

- **Tool-call log lines** (`nova.tools` logger, `agent/loop.py`): trace id, turn, tool, arguments passed through
  `redact()`, success, latency, result size. Guard hits are logged by name, without the text.
- **Traces**: every message, tool call, result and timing. Eval runs write them to
  `evals/runs/<run>/traces.jsonl`, raw. Production traces are to be written one file per day to
  `logs/traces/raw/`, with a copy in `logs/traces/redacted/` where every string has gone through
  `redact_obj()`: phone numbers masked to the last four digits, card numbers and email addresses replaced.
- **Retention** (`scripts/prune_traces.py`): a raw file older than 30 days is deleted, but only after its redacted
  copy exists with every line; redacted copies are deleted after 365 days. Dry run by default; `--apply` acts.
  It refuses any directory not named `traces`, and never follows a link out of it.
- **Tickets**: the hand-off summary a teammate reads, stored redacted whoever wrote it (`agent/tools_v2.py`
  `escalate_to_human`). With the hand-off rules on it is built in code from the conversation state, not by the
  model (`agent/escalation.py`).
- `logs/` is in `.gitignore`: traces never go to Git.

## The lethal trifecta

An assistant is exposed when it has all three of: access to private data, exposure to text an attacker can
write, and a way to send data out. Nova has the first two: it reads the customer's orders, and it reads help-center
text, carrier scan events and product names that other people write. So it must never get the third. No tool sends
email, posts a message, calls a webhook or fetches a URL; `tests/test_guardrails.py` checks that the tool code
imports no network library and that no tool schema mentions email, URLs or webhooks. The link guard closes the
last route, a reply that carries data in a link the customer's browser would load.

## Not done yet

- **Production traces are not written yet.** The retention script is ready for the layout above; the serving API
  that will write it comes next. The eval runs' `traces.jsonl` files are kept raw (synthetic data), including the
  original of any reply a guard replaced, for debugging.
- **The checks run where they are switched on**: `--guards` and `--handoff-rules` in `evals/run_eval.py`. The
  serving path must construct `Guard` and `HandoffRules` for every conversation; `agent/chat.py`, the early
  developer console on the first tools, passes neither.
- **Redaction is pattern-only.** A redacted trace still holds the customer's full name, order numbers, delivery
  city and item names, so it is still personal data for the year it is kept. The audit recommends only the first
  name in the prompt; that changes the model's input, so it waits for the next prompt version.
- **Bank account numbers** (9 to 18 digits, no checksum) are not caught: a pattern that broad would catch order
  references and UPI transaction ids. The help center tells customers never to share bank details in chat.
- The help center's privacy page does not state a retention period.
