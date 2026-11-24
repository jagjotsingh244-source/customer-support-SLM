# Keep rate: pilot-200

**89 of 192 kept (46%).** 192 of 192 were judged for tone; the others passed that check by default.

## Per check

A conversation can fail several checks. "Only" counts conversations this check alone rejected: fixing its cause would keep them.

| Check | Rejects | Only this check | What it catches |
|---|---|---|---|
| schema | 1 | 0 | Every tool call is a known tool with arguments its model accepts; no raw call markup reaches a reply. |
| tool_before_fact | 0 | 0 | Order numbers and tracking numbers in a reply come from a tool result shown before it |
| grounded_numbers | 17 | 4 | Every other number in a reply is in the tool and help-center results before it (agent/grounding.py). |
| citations | 15 | 7 | Every [kb:...] cited was returned by a help-center search earlier in the conversation. |
| end_state | 9 | 5 | Returns and cancellations end where the store's rules say: an eligible item gets a proposal, an ineligible one does not, and no reply claims a return or (where Nova cannot cancel) a cancellation is done. |
| escalation | 30 | 6 | A lost parcel is handed off; an easy scenario is not, unless the customer asked for a person; a late parcel is not offered a hand-off before the customer asks. |
| call_limit | 22 | 2 | No turn ran out of model calls and fell back to the fixed hand-off reply (no ticket, no facts). |
| privacy | 1 | 1 | No phone number, email address or another customer's order facts in a reply, and nothing of Nova's own instructions or tool names. |
| right_order | 5 | 0 | When the customer has named an item of the scenario's order (or its number), the first order lookup is that order, not another one the customer then has to correct. |
| length | 1 | 0 | No reply over 80 words or written as a list. |
| style | 1 | 0 | No closing offer of more help, no several paragraphs, no promise of emails, labels or links nobody mentioned (the same rules the generator asks the teacher to fix, synth/style.py). |
| judge_tone | 69 | 27 | The LLM judge's verdict (synth/judge.py), attached to the conversation before checking; unjudged passes here and is counted separately in the report. |
| dedup | 0 | 0 | Same scenario, same tool calls and a near-identical opening as a kept conversation |

## Per scenario

| Scenario | Kept | Total | Keep rate | Top reason |
|---|---|---|---|---|
| return_eligible | 1 | 13 | 8% | judge_tone 10, call_limit 5 |
| delayed | 1 | 12 | 8% | escalation 11, grounded_numbers 7 |
| not_yet_shipped | 2 | 12 | 17% | end_state 5, judge_tone 5 |
| opened_electronics | 3 | 13 | 23% | judge_tone 8, citations 4 |
| split_shipment | 3 | 11 | 27% | escalation 6, grounded_numbers 4 |
| window_just_expired | 4 | 12 | 33% | judge_tone 6, citations 2 |
| return_rejected | 4 | 11 | 36% | judge_tone 4, citations 2 |
| refunded | 6 | 12 | 50% | judge_tone 5, escalation 1 |
| policy_question | 7 | 12 | 58% | judge_tone 4, citations 1 |
| return_in_progress | 7 | 12 | 58% | judge_tone 5, call_limit 2 |
| lost | 7 | 12 | 58% | judge_tone 4, call_limit 3 |
| delivered_not_received | 7 | 12 | 58% | judge_tone 4, call_limit 3 |
| in_transit | 8 | 12 | 67% | escalation 3, judge_tone 2 |
| ship_then_cancel_request | 9 | 12 | 75% | judge_tone 2, citations 1 |
| cancelled_before_ship | 10 | 12 | 83% | citations 2 |
| delivered_on_time | 10 | 12 | 83% | escalation 1, right_order 1 |

## Per persona

| Persona | Kept | Total | Keep rate | Top reason |
|---|---|---|---|---|
| two_in_one | 5 | 19 | 26% | call_limit 9, judge_tone 9 |
| adversarial | 3 | 10 | 30% | judge_tone 7, call_limit 3 |
| frustrated | 9 | 28 | 32% | judge_tone 16, escalation 6 |
| keyword | 7 | 16 | 44% | judge_tone 5, citations 3 |
| typo | 15 | 30 | 50% | judge_tone 13, escalation 6 |
| vague | 15 | 30 | 50% | judge_tone 6, end_state 4 |
| polite_long | 11 | 19 | 58% | judge_tone 4, escalation 4 |
| direct | 24 | 40 | 60% | judge_tone 9, escalation 6 |

## Worst cells (scenario x persona, at least 2 conversations)

| Scenario | Persona | Kept | Total | Reasons |
|---|---|---|---|---|
| delayed | direct | 0 | 3 | grounded_numbers 3, escalation 3, judge_tone 1 |
| opened_electronics | typo | 0 | 2 | judge_tone 2, call_limit 1, citations 1 |
| not_yet_shipped | vague | 0 | 2 | end_state 2 |
| return_in_progress | frustrated | 0 | 2 | judge_tone 2, call_limit 1 |
| policy_question | direct | 0 | 2 | judge_tone 1, citations 1 |
| return_eligible | frustrated | 0 | 2 | call_limit 2, judge_tone 2 |
| return_eligible | typo | 0 | 2 | judge_tone 2, end_state 1 |
| lost | typo | 0 | 2 | judge_tone 2, grounded_numbers 1 |

Cells with conversations but none kept: 56 of 120.
