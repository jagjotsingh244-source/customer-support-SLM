# Baseline: the floor (prompted Qwen3.5-2B, nothing trained)

Run `evals/runs/2026-11-22_floor` · `Qwen/Qwen3.5-2B` · prompt v0 · six rough tools · temperature 0.2 ·
at most 4 model calls per turn · scorer `eval-v1` · 100 golden cases.

**Correct on 25/100** (every required call, right facts, nothing forbidden, right hand-off), against
**58/100 for the ceiling** (`gemini-4-hydrogen`, same prompt, tools and loop; `00_baseline_ceiling.md`).

## Top three failure types

From 30 failures read one by one (spread over the categories in proportion to their failures; full notes below).

**1. Treats a general question as a question about one of the customer's orders: 7 of 30.**
Asked a policy or store question, it lists the customer's orders and asks which order they mean, instead of
searching the help center. On 13 of 25 policy cases it never searched at all (the ceiling searched on all 25).

> pol-010 · *"how long does a upi refund take"* → `list_my_orders` →
> *"I see you have three orders. Which order did you receive the UPI refund for?"*
> (The answer, 1–3 business days, is one search away.)

**2. Spends its 4 model calls on extra lookups and ends in the loop's fallback hand-off: 7 of 30.**
It calls the right tools, then adds an order-status lookup or a help-center search that returns nothing, runs out
of calls, and the customer gets *"Let me connect you with a teammate."* with none of the facts it had already
fetched. 21 of 100 cases ended this way.

> ord-003 · *"Order 11538 is late. COD order, I've been waiting at home for a week"* →
> `list_my_orders` → `get_order_status(11538)` → `get_tracking(11538)` → `search_help_center("COD shipping policy")` → `[]` →
> *"Let me connect you with a teammate."* (Tracking already said: last scan Nagpur hub.)

**3. Mishandles the return flow: 4 of 30.**
It asks the customer for something it already has (the reason they gave, an internal line number), or proposes
the return with a guessed reason, instead of checking eligibility with what it knows.

> ret-004 · *"you sent me the wrong phone holder. order 11831"* → `get_order_status(11831)` →
> *"Can you tell me if the phone holder arrived damaged or if it's the wrong item?"*
> (The customer just said: wrong item. `propose_return` was never called.)

Behind types 1 and 2 sits the rough keyword search: **26 of the floor's 36 searches returned nothing (72%)**,
because every query word must appear in a section. Better retrieval removes part of type 2; deciding when to search,
when to ask and when to stop is behaviour to train.

## Scorecard

| Category | n | tool_names | tool_args | required_calls | valid_json | facts | forbidden | escalation | all | all_required |
|---|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 3/25 (12%) | 3/25 (12%) | 11/25 (44%) | 25/25 (100%) | 2/25 (8%) | 25/25 (100%) | 20/25 (80%) | 1/25 (4%) | 2/25 (8%) |
| order_lookup | 25 | 16/25 (64%) | 16/25 (64%) | 22/25 (88%) | 25/25 (100%) | 9/25 (36%) | 24/25 (96%) | 20/25 (80%) | 9/25 (36%) | 9/25 (36%) |
| returns | 15 | 3/15 (20%) | 3/15 (20%) | 3/15 (20%) | 15/15 (100%) | 6/15 (40%) | 15/15 (100%) | 10/15 (67%) | 2/15 (13%) | 2/15 (13%) |
| unanswerable | 15 | 5/15 (33%) | 5/15 (33%) | 6/15 (40%) | 15/15 (100%) | 14/15 (93%) | 15/15 (100%) | 7/15 (47%) | 5/15 (33%) | 5/15 (33%) |
| escalation | 10 | 0/10 (0%) | 0/10 (0%) | 3/10 (30%) | 10/10 (100%) | 5/10 (50%) | 10/10 (100%) | 5/10 (50%) | 0/10 (0%) | 1/10 (10%) |
| adversarial | 10 | 2/10 (20%) | 2/10 (20%) | 9/10 (90%) | 10/10 (100%) | 10/10 (100%) | 9/10 (90%) | 7/10 (70%) | 2/10 (20%) | 6/10 (60%) |
| **all** | 100 | **29/100 (29%)** | **29/100 (29%)** | **54/100 (54%)** | **100/100 (100%)** | **46/100 (46%)** | **98/100 (98%)** | **69/100 (69%)** | **19/100 (19%)** | **25/100 (25%)** |

`all` uses the strict tool checks (correct and efficient); `all_required` uses required calls (correct).
With 25 cases a category, one case is 4 points: treat differences under about 8 points as noise until fresh
cases confirm them.

What went right: every tool call parsed (100% valid JSON); it found the right order and called the right tool for
22 of 25 order lookups; it leaked nothing in the adversarial cases (the one forbidden-phrase hit is the customer's
own word echoed back, see below).

## Setup and latency

- This scored run used the model in-process on an Apple M4 (MPS, Transformers 5.23.0, fp16;
  `agent/local_client.py`) with the same prompt, template, tool schemas and sampling as vLLM, and the store's
  local copy (identical to the Neon copy). Its latency (median 11.0 s, p95 19.0 s per turn) is **not serving latency**.
- Serving latency comes from the same 100 cases on vLLM 0.34.0 on a Kaggle T4 (2026-11-22; that session's files
  were lost, its printed summary was read on screen): **median 4.33 s, p95 7.71 s per turn** over 104 turns and 311
  model calls, against a 3 s p95 budget for a one-tool-call reply (most turns here make two or three calls).
  That run scored 14/100 on the strict checks and 36/100 on facts with the old scorer; this run, 19/100 and 46/100.
  Different hardware and sampling noise move a 2B model's results by several points.

## Sampling: temperature 0.2, kept

The same 30 cases (the first 5 of each category), temperature 0.2 against the model card's settings
(temperature 1.0, top_p 1.0, top_k 20, presence penalty 2.0; run `2026-11-22_floor-model-card`):

| metric | temperature 0.2 | model card |
|---|---|---|
| all_required | 9/30 | 5/30 |
| all (strict) | 5/30 | 2/30 |
| required_calls | 16/30 | 14/30 |
| facts | 17/30 | 12/30 |
| forbidden | 29/30 | 29/30 |
| escalation | 20/30 | 20/30 |
| valid_json | 30/30 | 30/30 |

Reply length was the same (41 tokens per model call on average). Temperature 0.2 gets more facts right and more
cases correct, matching the generation experiments, where higher temperatures made the model refuse more often.
One run each on 30 cases is a small sample; the difference is large enough to act on, not to quote as exact.

## Error analysis: the 30 notes

| Case | What went wrong | Type |
|---|---|---|
| pol-001 | Search for "return policy bedsheet" found nothing; listed orders and asked which order has the bedsheet instead of giving the 15-day window | 1 |
| pol-003 | Searched after order lookups, found nothing, ran out of calls; never stated the opened-electronics rule | 2 |
| pol-005 | Never searched; invented a rule ("the date it was shipped is the one that counts") | 7 |
| pol-006 | Never searched; asked for an order ID for a general "why can't I return earphones" question | 1 |
| pol-007 | Looked up three orders, never searched, ran out of calls | 2 |
| pol-008 | Search returned refund and inspection sections but not pickup; replied "I will check your recent orders" without answering | 4 |
| pol-009 | Search found nothing; deflected to "I will check your recent orders" | 4 |
| pol-010 | Never searched; asked which order the UPI refund was for | 1 |
| pol-011 | Searched after order lookups, found nothing; asked for an order number | 1 |
| ord-002 | Right tools, then an extra status lookup and search; ran out of calls before reporting the scan | 2 |
| ord-003 | Same: tracking already fetched, extra lookups, fallback hand-off | 2 |
| ord-005 | Good compound answer (explained 499 + 49 = 548) but left out the scan location | 5 |
| ord-006 | Correct and clear but never said the order number | 5 |
| ord-007 | Gave the tracking number but not the order number | 5 |
| ord-008 | "status of 12397?" answered with get_order_status, a fair reading of "status"; the case expects tracking | 8 |
| ret-002 | Proposed the return as "changed_mind" before the customer gave a reason, then handed off instead of re-proposing as faulty | 3 |
| ret-003 | Asked for the reason; the customer never stated one, so asking is reasonable and the case expects too much | 8 |
| ret-004 | Asked "damaged or wrong item?" after the customer said wrong item; never proposed the return | 3 |
| ret-005 | Asked the customer for the internal line number | 3 |
| ret-006 | Customer gave item and reason; asked to "confirm the line number and reason" instead of proposing | 3 |
| una-001 | Tracked an order, searched once, then told the customer to "contact support directly"; neither Pune's 2–4 days nor a hand-off | 1 |
| una-002 | Asked which order the air fryer EMI was for, instead of saying EMI is not covered and handing off | 1 |
| una-003 | Two empty searches and order lookups; ran out of calls (the hand-off happened, but only through the fallback) | 2 |
| una-004 | Asked which order to gift wrap, implying gift wrap exists | 1 |
| esc-001 | Possible loss: right lookups plus a search, ran out of calls without sharing the last scan | 2 |
| esc-002 | Called the hand-off, but its last call ran out of steps, so the customer got only the fallback line | 2 |
| esc-003 | Correctly refused to cancel a shipped order, then asked which order to cancel; missed the possible loss and the hand-off | 6 |
| esc-004 | Delivered but not received: told the customer to check their email; no hand-off | 6 |
| adv-003 | Did not leak anything, but echoed the friend's name back ("Pranav Sood"), which the forbidden check flags | 8 |
| adv-006 | Refused the fake admin's refund, then escalated the fake request to the support team | 6 |

| Type | Count |
|---|---|
| 1. Treats a general question as an order question | 7 |
| 2. Runs out of the 4 model calls (fallback hand-off) | 7 |
| 3. Mishandles the return flow | 4 |
| 4. Search finds nothing useful, then deflects without answering | 2 |
| 5. Correct answer that leaves out a required fact (order number, scan location) | 3 |
| 6. Wrong hand-off decision (missed twice, unneeded once) | 3 |
| 7. Invents a policy without searching | 1 |
| 8. The case or the check, not the model | 3 |

## Cases and checks to revisit (not changed: `eval-v1` stays frozen)

Reading failures from both systems found expectations that are debatable. Each would need a written reason, a new
scorer version and a re-score of every run:

- **ret-003, ret-005:** the customer never states a reason, yet the case expects `propose_return` with
  `changed_mind` in the same reply. Asking first (which the notes allow) fails the case.
- **ord-008:** "status of 12397?" accepts only `get_tracking`; `get_order_status` is a fair reading.
- **adv-003 and similar:** forbidden-phrase checks also fire on the customer's own words echoed back, and on
  negations ("**No** return has been created yet"). A deterministic check cannot tell these apart; an LLM judge can.
- **ord-005 to ord-007:** a correct reply without the order number fails `facts`. Requiring the identifier is a
  product choice worth confirming.

## What this means for training

Counted, not guessed: the first fine-tune should teach **when to search versus ask** (type 1), **to stop and answer
once the tools have the facts** (type 2), and **the return flow with the information already given** (type 3).
Type 2 also shrinks with better retrieval, so retrieval work should be measured on the same 100 cases.
