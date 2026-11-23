## 2026-11-22_ceiling-8calls · diagnostic · `gemini-4-hydrogen` · prompt v0 · tools v0 · temperature 0.2 · sampling default · scorer eval-v3

Provider `gemini`; served by `gemini-4-hydrogen`; commit `eea2239`; database `localhost:5433`; up to 8 model calls per turn. Notes: DIAGNOSTIC, not the ceiling: the 31 cases where the 4-call ceiling run ran out of calls, re-run with 8 calls per turn

| Category | n | tool_names | tool_args | required_calls | valid_json | facts | forbidden | escalation | all | all_required | cites | cites_source | grounded |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 8 | 0/8 (0%) | 0/8 (0%) | 8/8 (100%) | 8/8 (100%) | 5/8 (62%) | 8/8 (100%) | 7/8 (88%) | 0/8 (0%) | 5/8 (62%) | 0/8 (0%) | 0/8 (0%) | 7/8 (88%) |
| order_lookup | 10 | 0/10 (0%) | 0/10 (0%) | 9/10 (90%) | 10/10 (100%) | 9/10 (90%) | 9/10 (90%) | 10/10 (100%) | 0/10 (0%) | 7/10 (70%) | - | - | 10/10 (100%) |
| returns | 5 | 0/5 (0%) | 0/5 (0%) | 3/5 (60%) | 5/5 (100%) | 3/5 (60%) | 4/5 (80%) | 4/5 (80%) | 0/5 (0%) | 1/5 (20%) | - | - | 4/5 (80%) |
| unanswerable | 1 | 0/1 (0%) | 0/1 (0%) | 1/1 (100%) | 1/1 (100%) | 1/1 (100%) | 0/1 (0%) | 1/1 (100%) | 0/1 (0%) | 0/1 (0%) | 0/1 (0%) | 0/1 (0%) | 1/1 (100%) |
| escalation | 6 | 0/6 (0%) | 0/6 (0%) | 2/6 (33%) | 6/6 (100%) | 4/6 (67%) | 5/6 (83%) | 2/6 (33%) | 0/6 (0%) | 0/6 (0%) | - | - | 6/6 (100%) |
| adversarial | 1 | 0/1 (0%) | 0/1 (0%) | 0/1 (0%) | 1/1 (100%) | 1/1 (100%) | 1/1 (100%) | 0/1 (0%) | 0/1 (0%) | 0/1 (0%) | - | - | 1/1 (100%) |
| **all** | 31 | **0/31 (0%)** | **0/31 (0%)** | **23/31 (74%)** | **31/31 (100%)** | **23/31 (74%)** | **27/31 (87%)** | **24/31 (77%)** | **0/31 (0%)** | **13/31 (42%)** | **0/9 (0%)** | **0/9 (0%)** | **29/31 (94%)** |

Latency per turn (model calls + tools + database): median 14.37 s, p95 36.00 s, max 40.76 s over 35 turns.
Model calls: 167; mean prompt tokens 1856, mean completion tokens 260.
Unanswerable cases that passed escalation by offering a hand-off: 1: una-001
Cases that errored (scored as failures): 0.
Tool-call format errors (a call left as text, or an empty reply): 0.
Grounding: 2 of 35 replies have an issue (6 per 100 replies), 2 issues.

Failed cases: adv-010, esc-002, esc-003, esc-004, esc-005, esc-007, esc-009, ord-001, ord-002, ord-003, ord-004, ord-005, ord-009, ord-011, ord-013, ord-019, ord-021, pol-001, pol-006, pol-009, pol-014, pol-017, pol-020, pol-022, pol-025, ret-002, ret-004, ret-007, ret-010, ret-015, una-001

Grounding issues:
- pol-020: number 20 not in tool results
- ret-010: number 18 not in tool results
