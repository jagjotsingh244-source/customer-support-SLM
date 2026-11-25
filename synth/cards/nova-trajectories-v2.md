# nova-trajectories-v2

Multi-turn support conversations for NimbusCart's assistant, Nova, generated inside the real agent loop and kept only when they pass every check.

## How they were made

- A teacher model (Qwen3.5-27B, Apache-2.0) played Nova against the real tools, a seeded orders database (train-side customers only) and the real help-center search; a simulated customer with a hidden goal, limited knowledge and one of eight personas played the other side, opening from a real Bitext question.
- Every fact in a conversation comes from the database or the help center; only the behaviour comes from the teacher. The teacher read extra rules the student never sees; each step is recorded with Nova's own prompt, state block and history trimming, as served.
- Checks (synth/verify.py): tool-call schema, order facts before lookups, numbers, day counts and dates against sources, citations, returns and cancellations, hand-offs, privacy, call limit, right order, length and style, needless tool calls, a tone judge and a fact-check judge (both tested on planted faults first), and dedup.

## Contents

- 1264 conversations, 6582 training steps (one model call each: the request as the student sees it, and the teacher's message as the target).
- Columns: id, scenario, persona, customer_id, run, teacher, teacher_rules, outcome, customer_turns, messages (JSON), steps (JSON), meta (JSON).

| Scenario | Conversations |
|---|---|
| cancelled_before_ship | 133 |
| delayed | 24 |
| delivered_not_received | 87 |
| delivered_on_time | 148 |
| in_transit | 152 |
| lost | 48 |
| no_tool | 102 |
| not_yet_shipped | 49 |
| opened_electronics | 38 |
| policy_question | 111 |
| refunded | 87 |
| return_eligible | 19 |
| return_in_progress | 49 |
| return_rejected | 49 |
| ship_then_cancel_request | 37 |
| split_shipment | 102 |
| window_just_expired | 29 |

| Persona | Conversations |
|---|---|
| adversarial | 55 |
| direct | 352 |
| frustrated | 125 |
| keyword | 134 |
| polite_long | 144 |
| seed | 19 |
| two_in_one | 76 |
| typo | 189 |
| vague | 170 |

Synthetic data: every name, order and address is generated. Private; made for training a small support model, not for evaluation.
