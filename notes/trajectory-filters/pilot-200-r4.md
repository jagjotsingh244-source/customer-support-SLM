# Keep rate: pilot-200-r4

**107 of 200 kept (54%).** 200 of 200 were judged for tone; the others passed that check by default.

## Per check

A conversation can fail several checks. "Only" counts conversations this check alone rejected: fixing its cause would keep them.

| Check | Rejects | Only this check | What it catches |
|---|---|---|---|
| schema | 2 | 0 | Every tool call is a known tool with arguments its model accepts; no raw call markup reaches a reply. |
| tool_before_fact | 0 | 0 | Order numbers and tracking numbers in a reply come from a tool result shown before it |
| grounded_numbers | 0 | 0 | Every other number in a reply is in the tool and help-center results before it (agent/grounding.py). |
| citations | 0 | 0 | Every [kb:...] cited was returned by a help-center search earlier in the conversation. |
| end_state | 5 | 3 | Returns and cancellations end where the store's rules say: an eligible item gets a proposal, an ineligible one does not, and no reply claims a return or (where Nova cannot cancel) a cancellation is done. |
| escalation | 37 | 16 | A lost parcel is handed off; an easy scenario is not, unless the customer asked for a person; a late parcel is not offered a hand-off before the customer asks. |
| call_limit | 27 | 2 | No turn ran out of model calls and fell back to the fixed hand-off reply (no ticket, no facts). |
| privacy | 0 | 0 | No phone number, email address or another customer's order facts in a reply, and nothing of Nova's own instructions or tool names. |
| right_order | 9 | 2 | When the customer has named an item of the scenario's order (or its number), the first order lookup is that order, not another one the customer then has to correct. |
| length | 0 | 0 | No reply over 80 words or written as a list. |
| style | 1 | 1 | No closing offer of more help, no several paragraphs, no promise of emails, labels or links nobody mentioned (the same rules the generator asks the teacher to fix, synth/style.py). |
| judge_tone | 64 | 32 | The LLM judge's verdict (synth/judge.py), attached to the conversation before checking; unjudged passes here and is counted separately in the report. |
| dedup | 0 | 0 | Same scenario, same tool calls and a near-identical opening as a kept conversation |

## Per scenario

| Scenario | Kept | Total | Keep rate | Top reason |
|---|---|---|---|---|
| delayed | 0 | 13 | 0% | escalation 12, judge_tone 4 |
| return_eligible | 3 | 13 | 23% | judge_tone 6, call_limit 5 |
| not_yet_shipped | 3 | 12 | 25% | judge_tone 8, escalation 1 |
| split_shipment | 3 | 12 | 25% | escalation 8, call_limit 3 |
| delivered_not_received | 6 | 12 | 50% | call_limit 5, judge_tone 5 |
| window_just_expired | 7 | 13 | 54% | judge_tone 6, call_limit 2 |
| lost | 7 | 13 | 54% | judge_tone 4, call_limit 2 |
| opened_electronics | 7 | 13 | 54% | judge_tone 6, call_limit 3 |
| in_transit | 8 | 12 | 67% | escalation 3, judge_tone 2 |
| delivered_on_time | 8 | 12 | 67% | judge_tone 4, right_order 1 |
| return_rejected | 8 | 12 | 67% | judge_tone 3, call_limit 2 |
| policy_question | 9 | 13 | 69% | judge_tone 3, escalation 2 |
| ship_then_cancel_request | 9 | 13 | 69% | judge_tone 3, end_state 1 |
| refunded | 9 | 12 | 75% | judge_tone 3, escalation 2 |
| return_in_progress | 9 | 12 | 75% | judge_tone 3, call_limit 1 |
| cancelled_before_ship | 11 | 13 | 85% | escalation 1, judge_tone 1 |

## Per persona

| Persona | Kept | Total | Keep rate | Top reason |
|---|---|---|---|---|
| frustrated | 6 | 30 | 20% | judge_tone 18, escalation 8 |
| two_in_one | 6 | 20 | 30% | call_limit 8, judge_tone 8 |
| adversarial | 4 | 10 | 40% | judge_tone 5, escalation 2 |
| typo | 15 | 30 | 50% | judge_tone 11, escalation 8 |
| polite_long | 11 | 20 | 55% | escalation 6, judge_tone 5 |
| keyword | 14 | 20 | 70% | judge_tone 4, escalation 2 |
| direct | 29 | 40 | 72% | judge_tone 6, escalation 5 |
| vague | 22 | 30 | 73% | judge_tone 7, escalation 2 |

## Worst cells (scenario x persona, at least 2 conversations)

| Scenario | Persona | Kept | Total | Reasons |
|---|---|---|---|---|
| delayed | direct | 0 | 3 | escalation 3 |
| opened_electronics | typo | 0 | 2 | judge_tone 2, escalation 1, call_limit 1 |
| return_eligible | frustrated | 0 | 2 | call_limit 2, judge_tone 1 |
| return_eligible | typo | 0 | 2 | end_state 1, judge_tone 1 |
| split_shipment | frustrated | 0 | 2 | escalation 2, right_order 1, judge_tone 1 |
| delayed | vague | 0 | 2 | judge_tone 2, escalation 1 |
| not_yet_shipped | frustrated | 0 | 2 | judge_tone 2 |
| split_shipment | typo | 0 | 2 | escalation 2, call_limit 1, judge_tone 1 |

Cells with conversations but none kept: 47 of 122.
