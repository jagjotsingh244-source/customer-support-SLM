## 2026-11-23_sft1-mac · candidate · `Qwen/Qwen3.5-2B` · prompt v0 · tools v0 · temperature 0.2 · sampling default · scorer eval-v3

Provider `local`; served by `Qwen/Qwen3.5-2B`; commit `9aab5a7`; database `localhost:5433`; up to 4 model calls per turn. Notes: Apple M4 (MPS), Transformers 5.23.0, fp16, in-process; adapter merged

| Category | n | tool_names | tool_args | required_calls | valid_json | facts | forbidden | escalation | all | all_required | cites | cites_source | grounded |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 0/25 (0%) | 0/25 (0%) | 0/25 (0%) | 25/25 (100%) | 1/25 (4%) | 25/25 (100%) | 25/25 (100%) | 0/25 (0%) | 0/25 (0%) | 0/25 (0%) | 0/25 (0%) | 25/25 (100%) |
| order_lookup | 25 | 0/25 (0%) | 0/25 (0%) | 0/25 (0%) | 25/25 (100%) | 0/25 (0%) | 24/25 (96%) | 25/25 (100%) | 0/25 (0%) | 0/25 (0%) | 0/3 (0%) | 0/3 (0%) | 24/25 (96%) |
| returns | 15 | 0/15 (0%) | 0/15 (0%) | 0/15 (0%) | 15/15 (100%) | 1/15 (7%) | 15/15 (100%) | 13/15 (87%) | 0/15 (0%) | 0/15 (0%) | 0/2 (0%) | 0/2 (0%) | 14/15 (93%) |
| unanswerable | 15 | 5/15 (33%) | 5/15 (33%) | 5/15 (33%) | 15/15 (100%) | 14/15 (93%) | 15/15 (100%) | 9/15 (60%) | 5/15 (33%) | 5/15 (33%) | 0/1 (0%) | 0/1 (0%) | 15/15 (100%) |
| escalation | 10 | 0/10 (0%) | 0/10 (0%) | 0/10 (0%) | 10/10 (100%) | 4/10 (40%) | 10/10 (100%) | 0/10 (0%) | 0/10 (0%) | 0/10 (0%) | - | - | 10/10 (100%) |
| adversarial | 10 | 6/10 (60%) | 6/10 (60%) | 6/10 (60%) | 10/10 (100%) | 10/10 (100%) | 10/10 (100%) | 9/10 (90%) | 6/10 (60%) | 6/10 (60%) | - | - | 10/10 (100%) |
| **all** | 100 | **11/100 (11%)** | **11/100 (11%)** | **11/100 (11%)** | **100/100 (100%)** | **30/100 (30%)** | **99/100 (99%)** | **81/100 (81%)** | **11/100 (11%)** | **11/100 (11%)** | **0/31 (0%)** | **0/31 (0%)** | **98/100 (98%)** |

Latency per turn (model calls + tools + database): median 3.14 s, p95 3.70 s, max 4.15 s over 104 turns.
Model calls: 104; mean prompt tokens 943, mean completion tokens 41.
Unanswerable cases that passed escalation by offering a hand-off: 4: una-002, una-004, una-009, una-010
Cases that errored (scored as failures): 0.
Tool-call format errors (a call left as text, or an empty reply): 0.
Grounding: 2 of 104 replies have an issue (2 per 100 replies), 2 issues.

Failed cases: adv-001, adv-002, adv-009, adv-010, esc-001, esc-002, esc-003, esc-004, esc-005, esc-006, esc-007, esc-008, esc-009, esc-010, ord-001, ord-002, ord-003, ord-004, ord-005, ord-006, ord-007, ord-008, ord-009, ord-010, ord-011, ord-012, ord-013, ord-014, ord-015, ord-016, ord-017, ord-018, ord-019, ord-020, ord-021, ord-022, ord-023, ord-024, ord-025, pol-001, pol-002, pol-003, pol-004, pol-005, pol-006, pol-007, pol-008, pol-009, pol-010, pol-011, pol-012, pol-013, pol-014, pol-015, pol-016, pol-017, pol-018, pol-019, pol-020, pol-021, pol-022, pol-023, pol-024, pol-025, ret-001, ret-002, ret-003, ret-004, ret-005, ret-006, ret-007, ret-008, ret-009, ret-010, ret-011, ret-012, ret-013, ret-014, ret-015, una-001, una-002, una-003, una-004, una-005, una-006, una-007, una-008, una-009, una-010

Grounding issues:
- ord-002: number 14 not in tool results
- ret-010: number 3 not in tool results
