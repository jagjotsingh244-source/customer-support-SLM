## 2026-11-23_floor-tools-v2 · floor · `Qwen/Qwen3.5-2B` · prompt v0 · tools v2 · temperature 0.2 · sampling default · scorer eval-v3

Provider `local`; served by `Qwen/Qwen3.5-2B`; commit `501012e+uncommitted changes`; database `localhost:5433`; up to 4 model calls per turn. Notes: Apple M4 (MPS), Transformers 5.23.0, fp16, in-process; same settings as the first run of this model, tools v2 (typed arguments, errors written for the model, explicit empty results, database roles)

| Category | n | tool_names | tool_args | required_calls | valid_json | facts | forbidden | escalation | all | all_required | cites | cites_source | grounded |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| order_lookup | 25 | 11/25 (44%) | 10/25 (40%) | 21/25 (84%) | 25/25 (100%) | 6/25 (24%) | 24/25 (96%) | 19/25 (76%) | 4/25 (16%) | 5/25 (20%) | 0/3 (0%) | 0/3 (0%) | 25/25 (100%) |
| returns | 15 | 5/15 (33%) | 4/15 (27%) | 10/15 (67%) | 15/15 (100%) | 4/15 (27%) | 15/15 (100%) | 10/15 (67%) | 2/15 (13%) | 3/15 (20%) | 0/2 (0%) | 0/2 (0%) | 15/15 (100%) |
| **all** | 40 | **16/40 (40%)** | **14/40 (35%)** | **31/40 (78%)** | **40/40 (100%)** | **10/40 (25%)** | **39/40 (98%)** | **29/40 (72%)** | **6/40 (15%)** | **8/40 (20%)** | **0/5 (0%)** | **0/5 (0%)** | **40/40 (100%)** |

Latency per turn (model calls + tools + database): median 16.64 s, p95 22.17 s, max 22.89 s over 41 turns.
Model calls: 137; mean prompt tokens 1351, mean completion tokens 45.
Unanswerable cases that passed escalation by offering a hand-off: 0.
Cases that errored (scored as failures): 0.
Tool-call format errors (a call left as text, or an empty reply): 0.
Grounding: 0 of 41 replies have an issue (0 per 100 replies), 0 issues.

Failed cases: ord-002, ord-003, ord-004, ord-005, ord-006, ord-007, ord-008, ord-009, ord-010, ord-011, ord-012, ord-013, ord-014, ord-017, ord-018, ord-020, ord-021, ord-022, ord-023, ord-024, ord-025, ret-001, ret-002, ret-004, ret-006, ret-007, ret-008, ret-009, ret-010, ret-011, ret-012, ret-013, ret-014, ret-015
