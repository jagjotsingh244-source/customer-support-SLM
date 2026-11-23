## 2026-11-23_floor-policy-v0 · floor · `Qwen/Qwen3.5-2B` · prompt v0 · tools v0 · temperature 0.2 · sampling default · scorer eval-v3

Provider `local`; served by `Qwen/Qwen3.5-2B`; commit `c924ae1+uncommitted changes`; database `localhost:5433`; up to 4 model calls per turn. Notes: Apple M4 (MPS), Transformers 5.23.0, fp16, in-process; first tools and prompt, loop sends unescaped tool text

| Category | n | tool_names | tool_args | required_calls | valid_json | facts | forbidden | escalation | all | all_required | cites | cites_source | grounded |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 1/25 (4%) | 1/25 (4%) | 7/25 (28%) | 25/25 (100%) | 1/25 (4%) | 25/25 (100%) | 16/25 (64%) | 0/25 (0%) | 1/25 (4%) | 0/25 (0%) | 0/25 (0%) | 23/25 (92%) |
| old_policy | 5 | 0/5 (0%) | 0/5 (0%) | 4/5 (80%) | 5/5 (100%) | 0/5 (0%) | 5/5 (100%) | 1/5 (20%) | 0/5 (0%) | 0/5 (0%) | 0/5 (0%) | 0/5 (0%) | 5/5 (100%) |
| **all** | 30 | **1/30 (3%)** | **1/30 (3%)** | **11/30 (37%)** | **30/30 (100%)** | **1/30 (3%)** | **30/30 (100%)** | **17/30 (57%)** | **0/30 (0%)** | **1/30 (3%)** | **0/30 (0%)** | **0/30 (0%)** | **28/30 (93%)** |

Latency per turn (model calls + tools + database): median 13.08 s, p95 18.64 s, max 20.02 s over 30 turns.
Model calls: 98; mean prompt tokens 1253, mean completion tokens 38.
Unanswerable cases that passed escalation by offering a hand-off: 0.
Cases that errored (scored as failures): 0.
Tool-call format errors (a call left as text, or an empty reply): 0.
Grounding: 2 of 30 replies have an issue (7 per 100 replies), 3 issues.

Failed cases: old-001, old-002, old-003, old-004, old-005, pol-001, pol-002, pol-003, pol-004, pol-005, pol-006, pol-007, pol-008, pol-009, pol-010, pol-011, pol-012, pol-013, pol-014, pol-015, pol-016, pol-017, pol-018, pol-019, pol-020, pol-021, pol-022, pol-023, pol-024, pol-025

Grounding issues:
- pol-015: number 49 not in tool results
- pol-018: number 1 not in tool results; number 2 not in tool results
