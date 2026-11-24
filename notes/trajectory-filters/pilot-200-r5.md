# Keep rate: pilot-200-r5

**114 of 200 kept (57%).** 200 of 200 were judged for tone; the others passed that check by default.

## Per check

A conversation can fail several checks. "Only" counts conversations this check alone rejected: fixing its cause would keep them.

| Check | Rejects | Only this check | What it catches |
|---|---|---|---|
| schema | 1 | 0 | Every tool call is a known tool with arguments its model accepts; no raw call markup reaches a reply. |
| tool_before_fact | 0 | 0 | Order numbers and tracking numbers in a reply come from a tool result shown before it |
| grounded_numbers | 1 | 1 | Every other number in a reply is in the tool and help-center results before it (agent/grounding.py). |
| citations | 0 | 0 | Every [kb:...] cited was returned by a help-center search earlier in the conversation. |
| end_state | 7 | 5 | Returns and cancellations end where the store's rules say: an eligible item gets a proposal, an ineligible one does not, and no reply claims a return or (where Nova cannot cancel) a cancellation is done. |
| escalation | 15 | 4 | A lost parcel is handed off; an easy scenario is not, unless the customer asked for a person; a late parcel is not offered a hand-off before the customer asks. |
| call_limit | 23 | 10 | No turn ran out of model calls and fell back to the fixed hand-off reply (no ticket, no facts). |
| privacy | 0 | 0 | No phone number, email address or another customer's order facts in a reply, and nothing of Nova's own instructions or tool names. |
| right_order | 5 | 1 | When the customer has named an item of the scenario's order (or its number), the first order lookup is that order, not another one the customer then has to correct. |
| length | 1 | 0 | No reply over 80 words or written as a list. |
| style | 3 | 2 | No closing offer of more help, no several paragraphs, no promise of emails, labels or links nobody mentioned (the same rules the generator asks the teacher to fix, synth/style.py). |
| judge_tone | 59 | 42 | The LLM judge's verdict (synth/judge.py), attached to the conversation before checking; unjudged passes here and is counted separately in the report. |
| dedup | 0 | 0 | Same scenario, same tool calls and a near-identical opening as a kept conversation |

## Per scenario

| Scenario | Kept | Total | Keep rate | Top reason |
|---|---|---|---|---|
| return_eligible | 1 | 13 | 8% | end_state 7, judge_tone 5 |
| lost | 4 | 13 | 31% | judge_tone 6, call_limit 3 |
| opened_electronics | 4 | 13 | 31% | judge_tone 5, call_limit 4 |
| window_just_expired | 6 | 13 | 46% | call_limit 4, escalation 3 |
| delayed | 6 | 13 | 46% | judge_tone 7, escalation 3 |
| split_shipment | 6 | 12 | 50% | judge_tone 6, escalation 3 |
| return_in_progress | 6 | 12 | 50% | judge_tone 5, length 1 |
| not_yet_shipped | 6 | 12 | 50% | judge_tone 5, escalation 1 |
| refunded | 8 | 12 | 67% | judge_tone 3, call_limit 1 |
| policy_question | 9 | 13 | 69% | judge_tone 3, style 1 |
| in_transit | 9 | 12 | 75% | judge_tone 3, escalation 1 |
| delivered_not_received | 9 | 12 | 75% | call_limit 2, judge_tone 1 |
| return_rejected | 9 | 12 | 75% | judge_tone 2, call_limit 1 |
| ship_then_cancel_request | 10 | 13 | 77% | judge_tone 3 |
| delivered_on_time | 10 | 12 | 83% | call_limit 1, right_order 1 |
| cancelled_before_ship | 11 | 13 | 85% | judge_tone 2 |

## Per persona

| Persona | Kept | Total | Keep rate | Top reason |
|---|---|---|---|---|
| adversarial | 2 | 10 | 20% | judge_tone 6, style 3 |
| frustrated | 8 | 30 | 27% | judge_tone 21, escalation 5 |
| two_in_one | 9 | 20 | 45% | call_limit 6, judge_tone 3 |
| typo | 17 | 30 | 57% | judge_tone 10, call_limit 5 |
| polite_long | 12 | 20 | 60% | judge_tone 7, call_limit 3 |
| vague | 21 | 30 | 70% | judge_tone 4, call_limit 4 |
| direct | 30 | 40 | 75% | judge_tone 5, call_limit 2 |
| keyword | 15 | 20 | 75% | judge_tone 3, end_state 1 |

## Worst cells (scenario x persona, at least 2 conversations)

| Scenario | Persona | Kept | Total | Reasons |
|---|---|---|---|---|
| return_eligible | direct | 0 | 3 | end_state 2, escalation 1 |
| not_yet_shipped | vague | 0 | 2 | judge_tone 1, escalation 1 |
| return_eligible | typo | 0 | 2 | call_limit 2, judge_tone 1 |
| return_eligible | frustrated | 0 | 2 | judge_tone 2, end_state 1 |
| return_in_progress | frustrated | 0 | 2 | judge_tone 2, length 1 |
| return_in_progress | typo | 0 | 2 | judge_tone 2 |
| not_yet_shipped | frustrated | 0 | 2 | judge_tone 2 |
| split_shipment | typo | 0 | 2 | judge_tone 2, escalation 1, call_limit 1 |

Cells with conversations but none kept: 42 of 122.
