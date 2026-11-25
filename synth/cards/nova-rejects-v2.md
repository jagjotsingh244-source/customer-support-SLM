# nova-rejects-v2

The conversations the checks rejected, each with every reason it failed.

## How they were made

- A teacher model (Qwen3.5-27B, Apache-2.0) played Nova against the real tools, a seeded orders database (train-side customers only) and the real help-center search; a simulated customer with a hidden goal, limited knowledge and one of eight personas played the other side, opening from a real Bitext question.
- Every fact in a conversation comes from the database or the help center; only the behaviour comes from the teacher. The teacher read extra rules the student never sees; each step is recorded with Nova's own prompt, state block and history trimming, as served.
- Checks (synth/verify.py): tool-call schema, order facts before lookups, numbers, day counts and dates against sources, citations, returns and cancellations, hand-offs, privacy, call limit, right order, length and style, needless tool calls, a tone judge and a fact-check judge (both tested on planted faults first), and dedup.

## Contents

- 2485 conversations, 18218 training steps (one model call each: the request as the student sees it, and the teacher's message as the target).
- Columns: id, scenario, persona, customer_id, run, teacher, teacher_rules, outcome, customer_turns, messages (JSON), steps (JSON), meta (JSON), reasons (JSON), first_reason.

| Scenario | Conversations |
|---|---|
| cancelled_before_ship | 60 |
| delayed | 234 |
| delivered_not_received | 140 |
| delivered_on_time | 45 |
| in_transit | 40 |
| lost | 198 |
| no_tool | 118 |
| not_yet_shipped | 174 |
| opened_electronics | 190 |
| policy_question | 80 |
| refunded | 120 |
| return_eligible | 276 |
| return_in_progress | 142 |
| return_rejected | 174 |
| ship_then_cancel_request | 155 |
| split_shipment | 108 |
| window_just_expired | 231 |

| Persona | Conversations |
|---|---|
| adversarial | 255 |
| direct | 295 |
| frustrated | 406 |
| keyword | 267 |
| polite_long | 205 |
| seed | 41 |
| two_in_one | 332 |
| typo | 331 |
| vague | 353 |

| First reason | Conversations |
|---|---|
| judge_facts | 966 |
| escalation | 439 |
| judge_tone | 436 |
| grounded_numbers | 217 |
| end_state | 145 |
| style | 86 |
| schema | 52 |
| right_order | 48 |
| needless_tool | 36 |
| dedup | 31 |
| call_limit | 20 |
| citations | 6 |
| length | 2 |
| privacy | 1 |

Synthetic data: every name, order and address is generated. Private; made for training a small support model, not for evaluation.
