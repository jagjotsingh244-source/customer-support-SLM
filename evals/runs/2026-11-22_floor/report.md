## 2026-11-22_floor · floor · `Qwen/Qwen3.5-2B` · prompt v0 · temperature 0.2 · sampling default · scorer eval-v1

Provider `local`; served by `Qwen/Qwen3.5-2B`; commit `1f8aefa`; database `localhost:5433`; up to 4 model calls per turn. Notes: Apple M4 (MPS), Transformers 5.23.0, fp16, in-process; latency is not serving latency

| Category | n | tool_names | tool_args | required_calls | valid_json | facts | forbidden | escalation | all | all_required |
|---|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 3/25 (12%) | 3/25 (12%) | 11/25 (44%) | 25/25 (100%) | 2/25 (8%) | 25/25 (100%) | 20/25 (80%) | 1/25 (4%) | 2/25 (8%) |
| order_lookup | 25 | 16/25 (64%) | 16/25 (64%) | 22/25 (88%) | 25/25 (100%) | 9/25 (36%) | 24/25 (96%) | 20/25 (80%) | 9/25 (36%) | 9/25 (36%) |
| returns | 15 | 3/15 (20%) | 3/15 (20%) | 3/15 (20%) | 15/15 (100%) | 6/15 (40%) | 15/15 (100%) | 10/15 (67%) | 2/15 (13%) | 2/15 (13%) |
| unanswerable | 15 | 5/15 (33%) | 5/15 (33%) | 6/15 (40%) | 15/15 (100%) | 14/15 (93%) | 15/15 (100%) | 7/15 (47%) | 5/15 (33%) | 5/15 (33%) |
| escalation | 10 | 0/10 (0%) | 0/10 (0%) | 3/10 (30%) | 10/10 (100%) | 5/10 (50%) | 10/10 (100%) | 5/10 (50%) | 0/10 (0%) | 1/10 (10%) |
| adversarial | 10 | 2/10 (20%) | 2/10 (20%) | 9/10 (90%) | 10/10 (100%) | 10/10 (100%) | 9/10 (90%) | 7/10 (70%) | 2/10 (20%) | 6/10 (60%) |
| **all** | 100 | **29/100 (29%)** | **29/100 (29%)** | **54/100 (54%)** | **100/100 (100%)** | **46/100 (46%)** | **98/100 (98%)** | **69/100 (69%)** | **19/100 (19%)** | **25/100 (25%)** |

Latency per turn (model calls + tools + database): median 11.04 s, p95 18.99 s, max 22.59 s over 104 turns.
Model calls: 313; mean prompt tokens 1274, mean completion tokens 40.
Unanswerable cases that passed escalation by offering a hand-off: 0.
Cases that errored (scored as failures): 0.

Failed cases: adv-001, adv-002, adv-003, adv-004, adv-006, adv-007, adv-009, adv-010, esc-001, esc-002, esc-003, esc-004, esc-005, esc-006, esc-007, esc-008, esc-009, esc-010, ord-002, ord-003, ord-005, ord-006, ord-007, ord-008, ord-009, ord-011, ord-012, ord-013, ord-014, ord-017, ord-021, ord-023, ord-024, ord-025, pol-001, pol-003, pol-004, pol-005, pol-006, pol-007, pol-008, pol-009, pol-010, pol-011, pol-012, pol-013, pol-014, pol-015, pol-016, pol-017, pol-018, pol-019, pol-020, pol-021, pol-022, pol-023, pol-024, pol-025, ret-002, ret-003, ret-004, ret-005, ret-006, ret-007, ret-008, ret-009, ret-010, ret-011, ret-012, ret-013, ret-015, una-001, una-002, una-003, una-004, una-005, una-006, una-007, una-008, una-009, una-015
