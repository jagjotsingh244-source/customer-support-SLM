# Keep rate: full-a

**322 of 500 kept (64%).** 500 of 500 were judged for tone; the others passed that check by default.

## Per check

A conversation can fail several checks. "Only" counts conversations this check alone rejected: fixing its cause would keep them.

| Check | Rejects | Only this check | What it catches |
|---|---|---|---|
| schema | 38 | 1 | Every tool call is a known tool with arguments its model accepts; no raw call markup reaches a reply. |
| tool_before_fact | 0 | 0 | Order numbers and tracking numbers in a reply come from a tool result shown before it |
| grounded_numbers | 3 | 2 | Every other number in a reply is in the tool and help-center results before it (agent/grounding.py). |
| citations | 1 | 0 | Every [kb:...] cited was returned by a help-center search earlier in the conversation. |
| end_state | 8 | 4 | Returns and cancellations end where the store's rules say: an eligible item gets a proposal, an ineligible one does not, and no reply claims a return or (where Nova cannot cancel) a cancellation is done. |
| escalation | 23 | 3 | A lost parcel is handed off; an easy scenario is not, unless the customer asked for a person; a late parcel is not offered a hand-off before the customer asks. |
| call_limit | 36 | 0 | No turn ran out of model calls and fell back to the fixed hand-off reply (no ticket, no facts). |
| privacy | 0 | 0 | No phone number, email address or another customer's order facts in a reply, and nothing of Nova's own instructions or tool names. |
| right_order | 15 | 6 | When the customer has named an item of the scenario's order (or its number), the first order lookup is that order, not another one the customer then has to correct. |
| length | 0 | 0 | No reply over 80 words or written as a list. |
| style | 2 | 1 | No closing offer of more help, no several paragraphs, no promise of emails, labels or links nobody mentioned (the same rules the generator asks the teacher to fix, synth/style.py). |
| judge_tone | 151 | 107 | The LLM judge's verdict (synth/judge.py), attached to the conversation before checking; unjudged passes here and is counted separately in the report. |
| dedup | 0 | 0 | Same scenario, same tool calls and a near-identical opening as a kept conversation |

## Per scenario

| Scenario | Kept | Total | Keep rate | Top reason |
|---|---|---|---|---|
| delayed | 12 | 32 | 38% | judge_tone 19, escalation 6 |
| return_eligible | 13 | 31 | 42% | judge_tone 14, end_state 6 |
| split_shipment | 17 | 31 | 55% | judge_tone 13, escalation 8 |
| policy_question | 18 | 31 | 58% | judge_tone 12, escalation 2 |
| return_in_progress | 18 | 31 | 58% | judge_tone 11, schema 3 |
| not_yet_shipped | 18 | 31 | 58% | judge_tone 11, end_state 1 |
| lost | 19 | 31 | 61% | judge_tone 10, escalation 4 |
| opened_electronics | 20 | 32 | 62% | judge_tone 11, schema 5 |
| refunded | 20 | 31 | 65% | judge_tone 10, schema 2 |
| delivered_not_received | 21 | 31 | 68% | judge_tone 7, schema 5 |
| window_just_expired | 23 | 32 | 72% | judge_tone 6, schema 3 |
| delivered_on_time | 23 | 31 | 74% | judge_tone 7, schema 2 |
| return_rejected | 23 | 31 | 74% | judge_tone 5, schema 3 |
| cancelled_before_ship | 24 | 31 | 77% | judge_tone 7, schema 1 |
| ship_then_cancel_request | 25 | 31 | 81% | judge_tone 4, end_state 1 |
| in_transit | 28 | 32 | 88% | judge_tone 4, escalation 2 |

## Per persona

| Persona | Kept | Total | Keep rate | Top reason |
|---|---|---|---|---|
| adversarial | 7 | 25 | 28% | judge_tone 15, escalation 2 |
| frustrated | 25 | 75 | 33% | judge_tone 48, escalation 8 |
| vague | 43 | 75 | 57% | judge_tone 27, schema 10 |
| two_in_one | 30 | 50 | 60% | judge_tone 14, schema 12 |
| polite_long | 37 | 50 | 74% | judge_tone 11, right_order 2 |
| keyword | 37 | 50 | 74% | judge_tone 9, schema 2 |
| typo | 60 | 75 | 80% | judge_tone 13, schema 6 |
| direct | 83 | 100 | 83% | judge_tone 14, schema 3 |

## Worst cells (scenario x persona, at least 2 conversations)

| Scenario | Persona | Kept | Total | Reasons |
|---|---|---|---|---|
| delayed | frustrated | 0 | 5 | judge_tone 5, escalation 3 |
| split_shipment | frustrated | 0 | 5 | judge_tone 5, escalation 2 |
| return_eligible | frustrated | 0 | 4 | judge_tone 3, schema 2, call_limit 2 |
| refunded | frustrated | 0 | 4 | judge_tone 4 |
| return_in_progress | two_in_one | 0 | 3 | judge_tone 2, schema 1, call_limit 1 |
| return_eligible | two_in_one | 0 | 3 | end_state 3, schema 2, call_limit 2 |
| split_shipment | two_in_one | 0 | 3 | schema 3, escalation 3, call_limit 3 |
| in_transit | adversarial | 0 | 2 | judge_tone 2 |

Cells with conversations but none kept: 16 of 128.
