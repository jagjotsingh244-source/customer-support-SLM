## 2026-11-23_floor-tools-v2-first-wording · diagnostic · `Qwen/Qwen3.5-2B` · prompt v0 · tools v2 · temperature 0.2 · sampling default · scorer eval-v3

Provider `local`; served by `Qwen/Qwen3.5-2B`; commit `501012e+uncommitted changes`; database `localhost:5433`; up to 4 model calls per turn. Notes: Apple M4 (MPS), Transformers 5.23.0, fp16, in-process; same settings as the first run of this model, tools v2 (typed arguments, errors written for the model, explicit empty results, database roles). First wording of the empty results: get_order_status said "No return on this order.", which the model read as "cannot be returned"; replaced by "No return has been started for this order."

| Category | n | tool_names | tool_args | required_calls | valid_json | facts | forbidden | escalation | all | all_required | cites | cites_source | grounded |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| order_lookup | 25 | 9/25 (36%) | 9/25 (36%) | 19/25 (76%) | 25/25 (100%) | 7/25 (28%) | 25/25 (100%) | 17/25 (68%) | 5/25 (20%) | 6/25 (24%) | 0/3 (0%) | 0/3 (0%) | 25/25 (100%) |
| returns | 15 | 2/15 (13%) | 2/15 (13%) | 2/15 (13%) | 15/15 (100%) | 3/15 (20%) | 15/15 (100%) | 5/15 (33%) | 1/15 (7%) | 1/15 (7%) | 0/2 (0%) | 0/2 (0%) | 15/15 (100%) |
| **all** | 40 | **11/40 (28%)** | **11/40 (28%)** | **21/40 (52%)** | **40/40 (100%)** | **10/40 (25%)** | **40/40 (100%)** | **22/40 (55%)** | **6/40 (15%)** | **7/40 (18%)** | **0/5 (0%)** | **0/5 (0%)** | **40/40 (100%)** |

Latency per turn (model calls + tools + database): median 15.87 s, p95 19.93 s, max 20.75 s over 41 turns.
Model calls: 137; mean prompt tokens 1358, mean completion tokens 48.
Unanswerable cases that passed escalation by offering a hand-off: 0.
Cases that errored (scored as failures): 0.
Tool-call format errors (a call left as text, or an empty reply): 0.
Grounding: 0 of 41 replies have an issue (0 per 100 replies), 0 issues.

Failed cases: ord-001, ord-002, ord-003, ord-004, ord-005, ord-006, ord-007, ord-008, ord-009, ord-010, ord-011, ord-012, ord-013, ord-014, ord-017, ord-018, ord-021, ord-023, ord-024, ord-025, ret-001, ret-002, ret-003, ret-004, ret-005, ret-006, ret-007, ret-008, ret-009, ret-010, ret-011, ret-012, ret-013, ret-015
