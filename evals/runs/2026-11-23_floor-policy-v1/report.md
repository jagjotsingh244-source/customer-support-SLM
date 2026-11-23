## 2026-11-23_floor-policy-v1 · floor · `Qwen/Qwen3.5-2B` · prompt v1 · tools v1 · temperature 0.2 · sampling default · scorer eval-v3

Provider `local`; served by `Qwen/Qwen3.5-2B`; commit `c924ae1+uncommitted changes`; database `localhost:5433`; up to 4 model calls per turn. Notes: Apple M4 (MPS), Transformers 5.23.0, fp16, in-process; help-center retrieval tools and citation prompt

| Category | n | tool_names | tool_args | required_calls | valid_json | facts | forbidden | escalation | all | all_required | cites | cites_source | grounded |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 0/25 (0%) | 0/25 (0%) | 6/25 (24%) | 25/25 (100%) | 4/25 (16%) | 25/25 (100%) | 18/25 (72%) | 0/25 (0%) | 4/25 (16%) | 0/25 (0%) | 0/25 (0%) | 23/25 (92%) |
| old_policy | 5 | 0/5 (0%) | 0/5 (0%) | 4/5 (80%) | 5/5 (100%) | 3/5 (60%) | 5/5 (100%) | 3/5 (60%) | 0/5 (0%) | 3/5 (60%) | 0/5 (0%) | 0/5 (0%) | 5/5 (100%) |
| **all** | 30 | **0/30 (0%)** | **0/30 (0%)** | **10/30 (33%)** | **30/30 (100%)** | **7/30 (23%)** | **30/30 (100%)** | **21/30 (70%)** | **0/30 (0%)** | **7/30 (23%)** | **0/30 (0%)** | **0/30 (0%)** | **28/30 (93%)** |

Latency per turn (model calls + tools + database): median 11.49 s, p95 23.77 s, max 24.83 s over 30 turns.
Model calls: 91; mean prompt tokens 1347, mean completion tokens 36.
Unanswerable cases that passed escalation by offering a hand-off: 0.
Cases that errored (scored as failures): 0.
Tool-call format errors (a call left as text, or an empty reply): 0.
Grounding: 2 of 30 replies have an issue (7 per 100 replies), 3 issues.

Failed cases: old-001, old-002, old-003, old-004, old-005, pol-001, pol-002, pol-003, pol-004, pol-005, pol-006, pol-007, pol-008, pol-009, pol-010, pol-011, pol-012, pol-013, pol-014, pol-015, pol-016, pol-017, pol-018, pol-019, pol-020, pol-021, pol-022, pol-023, pol-024, pol-025

Grounding issues:
- pol-010: number 10 not in tool results; number 7 not in tool results
- pol-018: number 3 not in tool results
