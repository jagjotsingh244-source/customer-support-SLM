# Keep rate: all runs

**1264 of 3749 kept (34%).** 3529 of 3749 were judged for tone and 3749 for facts; unjudged ones passed those checks by default.

## Per check

A conversation can fail several checks. "Only" counts conversations this check alone rejected: fixing its cause would keep them.

| Check | Rejects | Only this check | What it catches |
|---|---|---|---|
| schema | 52 | 1 | Every tool call is a known tool with arguments its model accepts; no raw call markup reaches a reply. |
| tool_before_fact | 0 | 0 | Order numbers and tracking numbers in a reply come from a tool result shown before it |
| grounded_numbers | 221 | 22 | Every other number in a reply is in the tool and help-center results before it (agent/grounding.py). |
| citations | 6 | 0 | Every [kb:...] cited was returned by a help-center search earlier in the conversation. |
| end_state | 164 | 7 | Returns and cancellations end where the store's rules say: an eligible item gets a proposal, an ineligible one does not, and no reply claims a return or (where Nova cannot cancel) a cancellation is done. |
| escalation | 514 | 62 | A lost parcel is handed off; an easy scenario is not, unless the customer asked for a person; a late parcel is not offered a hand-off before the customer asks. |
| call_limit | 86 | 9 | No turn ran out of model calls and fell back to the fixed hand-off reply (no ticket, no facts). |
| privacy | 1 | 1 | No phone number, email address or another customer's order facts in a reply, and nothing of Nova's own instructions or tool names. |
| right_order | 96 | 9 | When the customer has named an item of the scenario's order (or its number), the first order lookup is that order, not another one the customer then has to correct. |
| needless_tool | 42 | 19 | No tool call where none is needed: in a chat built for that (greetings, "are you a bot?", out of scope), or in answer to a customer's plain thanks or goodbye. |
| length | 6 | 0 | No reply over 80 words or written as a list. |
| style | 123 | 64 | No closing offer of more help, no several paragraphs, no promise of emails, labels or links nobody mentioned (the same rules the generator asks the teacher to fix, synth/style.py). |
| judge_tone | 789 | 132 | The LLM judge's verdict (synth/judge.py), attached to the conversation before checking; unjudged passes here and is counted separately in the report. |
| judge_facts | 2041 | 966 | The fact-check judge's verdict (synth/judge.py --rubric facts): every reply read against the lookup results it was given |
| dedup | 31 | 31 | Same scenario, same tool calls and a near-identical opening as a kept conversation |

## Per scenario

| Scenario | Kept | Total | Keep rate | Top reason |
|---|---|---|---|---|
| return_eligible | 19 | 295 | 6% | judge_facts 255, judge_tone 124 |
| delayed | 24 | 258 | 9% | judge_facts 206, judge_tone 133 |
| window_just_expired | 29 | 260 | 11% | judge_facts 209, judge_tone 59 |
| opened_electronics | 38 | 228 | 17% | judge_facts 175, judge_tone 50 |
| ship_then_cancel_request | 37 | 192 | 19% | judge_facts 145, judge_tone 23 |
| lost | 48 | 246 | 20% | judge_facts 184, grounded_numbers 52 |
| not_yet_shipped | 49 | 223 | 22% | judge_facts 160, judge_tone 55 |
| return_rejected | 49 | 223 | 22% | judge_facts 154, judge_tone 41 |
| return_in_progress | 49 | 191 | 26% | judge_facts 132, judge_tone 39 |
| delivered_not_received | 87 | 227 | 38% | escalation 96, judge_facts 85 |
| refunded | 87 | 207 | 42% | judge_facts 92, judge_tone 36 |
| no_tool | 102 | 220 | 46% | style 67, needless_tool 41 |
| split_shipment | 102 | 210 | 49% | judge_facts 76, judge_tone 58 |
| policy_question | 111 | 191 | 58% | judge_facts 64, escalation 20 |
| cancelled_before_ship | 133 | 193 | 69% | judge_facts 46, judge_tone 19 |
| delivered_on_time | 148 | 193 | 77% | judge_facts 28, judge_tone 13 |
| in_transit | 152 | 192 | 79% | judge_facts 25, judge_tone 23 |

## Per persona

| Persona | Kept | Total | Keep rate | Top reason |
|---|---|---|---|---|
| adversarial | 55 | 310 | 18% | judge_facts 203, judge_tone 95 |
| two_in_one | 76 | 408 | 19% | judge_facts 314, escalation 105 |
| frustrated | 125 | 531 | 24% | judge_facts 287, judge_tone 237 |
| seed | 19 | 60 | 32% | style 24, dedup 17 |
| vague | 170 | 523 | 33% | judge_facts 308, judge_tone 74 |
| keyword | 134 | 401 | 33% | judge_facts 232, judge_tone 83 |
| typo | 189 | 520 | 36% | judge_facts 284, judge_tone 82 |
| polite_long | 144 | 349 | 41% | judge_facts 172, judge_tone 58 |
| direct | 352 | 647 | 54% | judge_facts 241, judge_tone 71 |

## Worst cells (scenario x persona, at least 2 conversations)

| Scenario | Persona | Kept | Total | Reasons |
|---|---|---|---|---|
| return_eligible | frustrated | 0 | 46 | judge_facts 42, judge_tone 29, end_state 17 |
| delayed | two_in_one | 0 | 36 | judge_facts 36, judge_tone 13, escalation 10 |
| delayed | keyword | 0 | 35 | judge_facts 34, judge_tone 23, escalation 12 |
| window_just_expired | vague | 1 | 45 | judge_facts 41, grounded_numbers 12, escalation 9 |
| return_eligible | polite_long | 1 | 39 | judge_facts 35, judge_tone 22, end_state 14 |
| window_just_expired | two_in_one | 1 | 37 | judge_facts 35, judge_tone 11, escalation 8 |
| lost | two_in_one | 1 | 36 | judge_facts 33, escalation 13, grounded_numbers 7 |
| return_eligible | two_in_one | 1 | 35 | judge_facts 34, end_state 12, judge_tone 12 |

Cells with conversations but none kept: 3 of 135.
