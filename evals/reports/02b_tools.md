# Hardened tools: what they fixed without training, and what is left

The typed tool layer (`agent/tools_v2.py`) changes how tools answer the model, not what the model knows:

- **Validation before anything runs.** One strict Pydantic model per tool. `"#10482"`, `10482.0` and an added
  `customer_id` are refused, never quietly coerced.
- **Errors written for the model.** One shape everywhere, `{"error", "detail"}`, where the detail is one sentence:
  what was wrong, what right looks like, what to do next ("Order numbers are 5 digits, like 10482, with no # or
  spaces. If unsure, call list_my_orders."). After a second failure on the same tool in one turn, the detail steers
  the model to ask the customer or hand off. No stack trace ever reaches the model.
- **No blanks.** No tool returns `[]`, `null` or a raw exception. An empty result is stated as a fact ("Not shipped
  yet, so there is no tracking number.").
- **Database roles and a confirm step for returns** (see `DESIGN.md`, "Who can touch which rows").

**In one line:** on the 40 order and return cases, the hardened tools fixed 3 baseline failures and broke 6, so the
floor model went from **11/40 to 8/40** (required-calls view). The reason is in the baseline's own traces: the floor
model made **no argument errors in 101 tool calls**, and its only empty results were 11 keyword searches that the
retrieval work had already fixed. There was almost nothing here for error handling to fix. What moved the scores was
the *wording* of the tools, which a 2B model takes very literally. SFT-1 still makes no tool calls, so nothing
changed for it (0/40 both times).

## Setup

Same model, same settings, same machine as each model's first golden run; only the tools differ.

| | Before | After |
|---|---|---|
| Floor (Qwen3.5-2B, prompted) | `2026-11-22_floor` | `2026-11-23_floor-tools-v2` |
| SFT-1 (`123jagjot/sft1-r16-lr2e-4-bitext_v1`) | `2026-11-23_sft1-mac` | `2026-11-23_sft1-tools-v2` |
| Tools | v0 (untyped, raw errors, `[]` for nothing found, keyword search) | v2 |
| Shared | Apple M4 (MPS), Transformers, fp16; prompt v0; temperature 0.2; 4 model calls per turn; scorer `eval-v3` | |

Cases: the 25 `order_lookup` and 15 `returns` golden cases, the categories where the tools do most of the work.
Comparison per case: `uv run python evals/compare_cases.py BEFORE AFTER --metric all_required`.

One diagnostic run sits in between: `2026-11-23_floor-tools-v2-first-wording`, the first version of the empty
results, explained below.

## Results

| Floor, 40 cases | Before (v0) | v2, first wording | v2 |
|---|---|---|---|
| all_required (every needed call, right args, facts, nothing forbidden, right escalation) | **11** | 7 | **8** |
| all (strict: exactly the expected calls) | 11 | 6 | 6 |
| facts | 15 | 10 | 10 |
| escalation correct | 30 | 22 | 29 |
| order_lookup, all_required | 9/25 | 6/25 | 5/25 |
| returns, all_required | 2/15 | 1/15 | 3/15 |
| tool calls / `propose_return` / `escalate_to_human` | 101 / 4 / 2 | 115 / 4 / 14 | 106 / 15 / 4 |
| tool errors returned to the model | 0 | 1 | 0 |
| turns ending in the hand-off fallback (ran out of calls) | 8 | 18 | 10 |

Fixed by v2: `ret-003`, `ret-005`, `ret-008` (the model now proposes the return instead of stopping). Broken by v2:
`ord-004`, `ord-010`, `ord-018`, `ord-022`, `ret-001`, `ret-014`.

SFT-1: 0/40 before and after, 0 tool calls in either run. It answers every order question from nothing, the
failure found when it was trained (`evals/reports/02_sft_bitext.md`). Better tools cannot help a model that never
calls them.

## Why the scores moved

**1. A sentence the model misread.** The first version of `get_order_status` said `"returns": "No return on this
order."` when nothing had been started. The 2B model read it as "this order cannot be returned": in 6 cases it then
searched the policy and escalated, with summaries like *"Customer wants to return a frying pan but order has no
return policy"*. Hand-offs went from 2 to 14. The text now says what has not happened, not what is not allowed: `"No
return has been started for this order."`. With that one change, hand-offs fell back to 4 and `propose_return` calls
rose from 4 to 15.

**2. The hand-off reason list invites hand-offs.** `escalate_to_human` now takes a `reason` from the ticket reasons
(`not_received`, `lost_parcel`, `damaged`, ...). To find what broke the order cases, the 5 that changed were re-run
twice, each time undoing one change. Returning `list_my_orders` as a bare list instead of `{"orders": [...]}` fixed
none of them. Putting back the old summary-only hand-off schema stopped `ord-004` (a parcel with no scan for days)
from being escalated as `lost_parcel`, though its reply then left out the order number, and `ord-022` passed. The reason list stays, because a teammate needs it to
route the ticket. When to hand off is behaviour, and it is trained next.

**3. Some of it is luck.** In the same experiment, `ord-020`'s very first tool call came out differently with an
identical prompt (`limit` 5 instead of 10). Two identical floor runs agreed on all 12 cases they shared
(`evals/reports/01_phrasing_probes_baseline.md`), so the noise is small, but with 40 cases a few flips each way
are expected.

## What hardening is for, then

Not for lifting this model's score. It is for what the model must never get away with, and for what training will
copy:

- **Fault injection** (`tests/test_tool_errors.py`, in CI): 15 malformed calls, from `"#10482"` and `10482.0` to an
  unknown tool, a smuggled `customer_id` and a reason outside the list. Each gets a one-sentence error, none reaches
  the database, and none returns a stack trace.
- **No blanks, checked on real data:** every order of every eval customer through every order tool and two return
  reasons per item (over 1,000 calls): no empty list and no null anywhere in a result.
- **A bug the sweep found:** 63 orders cancelled after packing keep a voided shipping label. The old `get_tracking`
  handed its tracking number to the model as if the parcel had shipped. Voided labels are no longer shipments.
- **Training data:** the next fine-tune learns from conversations that call these tools. One error shape and stated
  empty results mean the model learns one way to recover, not six.

## What is left: the targets for the next fine-tune

The 32 floor cases still failing on v2, each counted once by its first cause:

| Failure | Cases | Example |
|---|---|---|
| Keeps calling after it has the answer, runs out of calls, hands off | 10 | `ret-006`: order, item and eligibility all found, then a policy search, then the fallback |
| Right calls, but the reply leaves out a fact it was given (the order number, the amount) | 8 | `ord-006`: "Your power bank is on its way..." with no order number |
| Wrong tool, or stops before the call that answers | 7 | `ord-014`: a tracking question answered with `propose_return`; `ord-010`: lists orders, then asks which one |
| Wrong box in a split shipment | 3 | `ord-011`: reports the delivered box when the customer asked about the missing one |
| Reads the tool's note to the customer | 3 | `ret-004`: *"The customer has a Confirm button on their card. Please ask the customer to press Confirm"* |
| Hands off without being asked | 1 | `ord-004`: an overdue parcel escalated as `lost_parcel` |

Two findings for later work:

- **The model chooses the return reason.** In `ret-009` the customer says an opened speaker "sounds meh" (a change
  of mind, so not returnable once opened) and the model calls `propose_return` with `reason: "faulty"`, which passes.
  The Confirm click is the safeguard only if the card shows the reason being claimed. **The chat UI's Confirm card
  must show the reason**, so the customer confirms "faulty", not just "return". Pickup inspection catches false
  "faulty" claims later (`failed_inspection`), but that costs a pickup.
- **A scorer gap:** `ret-002`'s reply says "₹2,799" and the check looks for "2799". Number formats in replies are a
  check problem, not a model problem; they belong with the evaluation harness work.

## Files

- `agent/tools_v2.py`: `call_tool` (validation, errors, the retry rule), explicit empty results, voided labels.
- `agent/loop.py`: calls tools through the dispatcher; one log line per call (`trace_id`, `turn`, `tool`, `args`,
  `ok`, `latency_ms`, `result_bytes`), also kept in each trace's `tool_calls`.
- `tests/test_tool_errors.py`: fault injection, the retry rule, no stack traces, the no-blanks sweep.
- `evals/compare_cases.py`: per-case before/after for two runs.
