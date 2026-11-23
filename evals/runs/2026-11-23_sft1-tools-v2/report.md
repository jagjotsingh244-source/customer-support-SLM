## 2026-11-23_sft1-tools-v2 · candidate · `Qwen/Qwen3.5-2B` · prompt v0 · tools v2 · temperature 0.2 · sampling default · scorer eval-v3

Provider `local`; served by `Qwen/Qwen3.5-2B`; commit `501012e+uncommitted changes`; database `localhost:5433`; up to 4 model calls per turn. Notes: Apple M4 (MPS), Transformers 5.23.0, fp16, in-process; same settings as the first run of this model, tools v2 (typed arguments, errors written for the model, explicit empty results, database roles); adapter merged. Ran with the first wording of the empty results (see 2026-11-23_floor-tools-v2-first-wording); it made no tool calls, so no tool result reached it

| Category | n | tool_names | tool_args | required_calls | valid_json | facts | forbidden | escalation | all | all_required | cites | cites_source | grounded |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| order_lookup | 25 | 0/25 (0%) | 0/25 (0%) | 0/25 (0%) | 25/25 (100%) | 0/25 (0%) | 25/25 (100%) | 25/25 (100%) | 0/25 (0%) | 0/25 (0%) | 0/3 (0%) | 0/3 (0%) | 25/25 (100%) |
| returns | 15 | 0/15 (0%) | 0/15 (0%) | 0/15 (0%) | 15/15 (100%) | 1/15 (7%) | 15/15 (100%) | 13/15 (87%) | 0/15 (0%) | 0/15 (0%) | 0/2 (0%) | 0/2 (0%) | 14/15 (93%) |
| **all** | 40 | **0/40 (0%)** | **0/40 (0%)** | **0/40 (0%)** | **40/40 (100%)** | **1/40 (2%)** | **40/40 (100%)** | **38/40 (95%)** | **0/40 (0%)** | **0/40 (0%)** | **0/5 (0%)** | **0/5 (0%)** | **39/40 (98%)** |

Latency per turn (model calls + tools + database): median 3.05 s, p95 3.30 s, max 3.51 s over 41 turns.
Model calls: 41; mean prompt tokens 969, mean completion tokens 40.
Unanswerable cases that passed escalation by offering a hand-off: 0.
Cases that errored (scored as failures): 0.
Tool-call format errors (a call left as text, or an empty reply): 0.
Grounding: 1 of 41 replies have an issue (2 per 100 replies), 1 issues.

Failed cases: ord-001, ord-002, ord-003, ord-004, ord-005, ord-006, ord-007, ord-008, ord-009, ord-010, ord-011, ord-012, ord-013, ord-014, ord-015, ord-016, ord-017, ord-018, ord-019, ord-020, ord-021, ord-022, ord-023, ord-024, ord-025, ret-001, ret-002, ret-003, ret-004, ret-005, ret-006, ret-007, ret-008, ret-009, ret-010, ret-011, ret-012, ret-013, ret-014, ret-015

Grounding issues:
- ret-010: number 3 not in tool results
