# nova-rejects-v1

The conversations the checks rejected, each with every reason it failed.

## How they were made

- A teacher model (Qwen3.5-27B, Apache-2.0) played Nova against the real tools, a seeded orders database (train-side customers only) and the real help-center search; a simulated customer with a hidden goal, limited knowledge and one of eight personas played the other side, opening from a real Bitext question.
- Every fact in a conversation comes from the database or the help center; only the behaviour comes from the teacher. The teacher read extra rules the student never sees; each step is recorded with Nova's own prompt, state block and history trimming, as served.
- Checks (synth/verify.py): tool-call schema, order facts before lookups, numbers, day counts and dates against sources, citations, returns and cancellations, hand-offs, privacy, call limit, right order, length and style, needless tool calls, a tone judge and a fact-check judge (both tested on planted faults first), and dedup.

## Contents

- 2264 conversations, 16083 training steps (one model call each: the request as the student sees it, and the teacher's message as the target).
- Columns: id, scenario, persona, customer_id, run, teacher, teacher_rules, outcome, customer_turns, messages (JSON), steps (JSON), meta (JSON), reasons (JSON), first_reason.

| Scenario | Conversations |
|---|---|
| cancelled_before_ship | 66 |
| delayed | 178 |
| delivered_not_received | 140 |
| delivered_on_time | 46 |
| in_transit | 40 |
| lost | 179 |
| no_tool | 118 |
| not_yet_shipped | 155 |
| opened_electronics | 184 |
| policy_question | 89 |
| refunded | 123 |
| return_eligible | 180 |
| return_in_progress | 150 |
| return_rejected | 168 |
| ship_then_cancel_request | 167 |
| split_shipment | 103 |
| window_just_expired | 178 |

| Persona | Conversations |
|---|---|
| adversarial | 130 |
| direct | 366 |
| frustrated | 405 |
| keyword | 214 |
| polite_long | 207 |
| seed | 41 |
| two_in_one | 240 |
| typo | 324 |
| vague | 337 |

| First reason | Conversations |
|---|---|
| judge_facts | 1042 |
| escalation | 344 |
| judge_tone | 340 |
| grounded_numbers | 176 |
| end_state | 97 |
| style | 78 |
| schema | 52 |
| right_order | 41 |
| needless_tool | 36 |
| dedup | 30 |
| call_limit | 20 |
| citations | 5 |
| length | 2 |
| privacy | 1 |

Synthetic data: every name, order and address is generated. Private; made for training a small support model, not for evaluation.
