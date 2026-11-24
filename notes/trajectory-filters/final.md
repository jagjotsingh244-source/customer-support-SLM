# Keep rate: all runs

**1006 of 3270 kept (31%).** 3050 of 3270 were judged for tone and 3270 for facts; unjudged ones passed those checks by default.

## Per check

A conversation can fail several checks. "Only" counts conversations this check alone rejected: fixing its cause would keep them.

| Check | Rejects | Only this check | What it catches |
|---|---|---|---|
| schema | 52 | 1 | Every tool call is a known tool with arguments its model accepts; no raw call markup reaches a reply. |
| tool_before_fact | 0 | 0 | Order numbers and tracking numbers in a reply come from a tool result shown before it |
| grounded_numbers | 180 | 7 | Every other number in a reply is in the tool and help-center results before it (agent/grounding.py). |
| citations | 5 | 0 | Every [kb:...] cited was returned by a help-center search earlier in the conversation. |
| end_state | 111 | 4 | Returns and cancellations end where the store's rules say: an eligible item gets a proposal, an ineligible one does not, and no reply claims a return or (where Nova cannot cancel) a cancellation is done. |
| escalation | 397 | 27 | A lost parcel is handed off; an easy scenario is not, unless the customer asked for a person; a late parcel is not offered a hand-off before the customer asks. |
| call_limit | 86 | 3 | No turn ran out of model calls and fell back to the fixed hand-off reply (no ticket, no facts). |
| privacy | 1 | 1 | No phone number, email address or another customer's order facts in a reply, and nothing of Nova's own instructions or tool names. |
| right_order | 79 | 6 | When the customer has named an item of the scenario's order (or its number), the first order lookup is that order, not another one the customer then has to correct. |
| needless_tool | 41 | 18 | No tool call where none is needed: in a chat built for that (greetings, "are you a bot?", out of scope), or in answer to a customer's plain thanks or goodbye. |
| length | 6 | 0 | No reply over 80 words or written as a list. |
| style | 111 | 61 | No closing offer of more help, no several paragraphs, no promise of emails, labels or links nobody mentioned (the same rules the generator asks the teacher to fix, synth/style.py). |
| judge_tone | 617 | 53 | The LLM judge's verdict (synth/judge.py), attached to the conversation before checking; unjudged passes here and is counted separately in the report. |
| judge_facts | 1995 | 1042 | The fact-check judge's verdict (synth/judge.py --rubric facts): every reply read against the lookup results it was given |
| dedup | 30 | 30 | Same scenario, same tool calls and a near-identical opening as a kept conversation |

## Per scenario

| Scenario | Kept | Total | Keep rate | Top reason |
|---|---|---|---|---|
| opened_electronics | 8 | 192 | 4% | judge_facts 181, judge_tone 41 |
| delayed | 8 | 186 | 4% | judge_facts 172, judge_tone 87 |
| return_eligible | 9 | 189 | 5% | judge_facts 170, judge_tone 75 |
| window_just_expired | 12 | 190 | 6% | judge_facts 173, grounded_numbers 44 |
| lost | 13 | 192 | 7% | judge_facts 173, grounded_numbers 40 |
| return_rejected | 21 | 189 | 11% | judge_facts 161, judge_tone 35 |
| ship_then_cancel_request | 25 | 192 | 13% | judge_facts 160, judge_tone 23 |
| not_yet_shipped | 32 | 187 | 17% | judge_facts 151, judge_tone 44 |
| return_in_progress | 41 | 191 | 21% | judge_facts 145, judge_tone 39 |
| delivered_not_received | 52 | 192 | 27% | judge_facts 108, escalation 69 |
| refunded | 66 | 189 | 35% | judge_facts 112, judge_tone 31 |
| split_shipment | 89 | 192 | 46% | judge_facts 91, judge_tone 51 |
| no_tool | 102 | 220 | 46% | style 67, needless_tool 41 |
| policy_question | 102 | 191 | 53% | judge_facts 76, escalation 20 |
| cancelled_before_ship | 127 | 193 | 66% | judge_facts 56, judge_tone 19 |
| delivered_on_time | 147 | 193 | 76% | judge_facts 32, judge_tone 13 |
| in_transit | 152 | 192 | 79% | judge_facts 28, judge_tone 23 |

## Per persona

| Persona | Kept | Total | Keep rate | Top reason |
|---|---|---|---|---|
| adversarial | 20 | 150 | 13% | judge_facts 115, judge_tone 39 |
| frustrated | 72 | 477 | 15% | judge_facts 363, judge_tone 204 |
| two_in_one | 61 | 301 | 20% | judge_facts 231, escalation 66 |
| vague | 151 | 488 | 31% | judge_facts 300, judge_tone 66 |
| seed | 19 | 60 | 32% | style 24, dedup 17 |
| typo | 162 | 486 | 33% | judge_facts 286, judge_tone 74 |
| keyword | 116 | 330 | 35% | judge_facts 188, judge_tone 57 |
| polite_long | 124 | 331 | 37% | judge_facts 188, judge_tone 48 |
| direct | 281 | 647 | 43% | judge_facts 324, judge_tone 71 |

## Worst cells (scenario x persona, at least 2 conversations)

| Scenario | Persona | Kept | Total | Reasons |
|---|---|---|---|---|
| opened_electronics | frustrated | 0 | 30 | judge_facts 29, judge_tone 15, escalation 7 |
| delayed | frustrated | 0 | 30 | judge_facts 29, judge_tone 24, escalation 21 |
| lost | typo | 0 | 29 | judge_facts 28, grounded_numbers 5, escalation 5 |
| lost | frustrated | 0 | 29 | judge_facts 27, judge_tone 8, right_order 4 |
| window_just_expired | frustrated | 0 | 29 | judge_facts 27, judge_tone 15, end_state 7 |
| return_eligible | frustrated | 0 | 28 | judge_facts 27, judge_tone 17, end_state 9 |
| window_just_expired | vague | 0 | 28 | judge_facts 27, grounded_numbers 8, escalation 4 |
| return_eligible | typo | 0 | 28 | judge_facts 25, judge_tone 11, end_state 7 |

Cells with conversations but none kept: 28 of 135.
