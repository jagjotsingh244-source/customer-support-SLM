## 2026-11-25_golden-base · floor · `Qwen/Qwen3.5-2B` · prompt v2 · tools v2 · temperature 0.2 · sampling default · scorer eval-v3

Provider `openai`; served by `Qwen/Qwen3.5-2B`; commit `71f12cc+uncommitted changes`; database `localhost:5433`; up to 4 model calls per turn. Notes: Modal L4, vLLM 0.34.0, bf16, adapters served as LoRA modules (max rank 16); one server for all four systems; prompt v2, tools v2, state block and history trimming as served

| Category | n | tool_names | tool_args | required_calls | valid_json | facts | forbidden | escalation | all | all_required | cites | cites_source | grounded |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 3/25 (12%) | 3/25 (12%) | 12/25 (48%) | 25/25 (100%) | 6/25 (24%) | 25/25 (100%) | 16/25 (64%) | 3/25 (12%) | 6/25 (24%) | 0/25 (0%) | 0/25 (0%) | 24/25 (96%) |
| order_lookup | 25 | 9/25 (36%) | 9/25 (36%) | 20/25 (80%) | 25/25 (100%) | 5/25 (20%) | 25/25 (100%) | 12/25 (48%) | 5/25 (20%) | 5/25 (20%) | 0/3 (0%) | 0/3 (0%) | 25/25 (100%) |
| returns | 15 | 2/15 (13%) | 2/15 (13%) | 7/15 (47%) | 15/15 (100%) | 3/15 (20%) | 15/15 (100%) | 6/15 (40%) | 1/15 (7%) | 3/15 (20%) | 0/2 (0%) | 0/2 (0%) | 15/15 (100%) |
| unanswerable | 15 | 2/15 (13%) | 2/15 (13%) | 5/15 (33%) | 15/15 (100%) | 15/15 (100%) | 14/15 (93%) | 6/15 (40%) | 2/15 (13%) | 4/15 (27%) | 0/1 (0%) | 0/1 (0%) | 14/15 (93%) |
| escalation | 10 | 0/10 (0%) | 0/10 (0%) | 4/10 (40%) | 10/10 (100%) | 6/10 (60%) | 10/10 (100%) | 7/10 (70%) | 0/10 (0%) | 2/10 (20%) | - | - | 10/10 (100%) |
| adversarial | 12 | 4/12 (33%) | 3/12 (25%) | 10/12 (83%) | 12/12 (100%) | 12/12 (100%) | 11/12 (92%) | 8/12 (67%) | 3/12 (25%) | 7/12 (58%) | - | - | 10/12 (83%) |
| old_policy | 5 | 2/5 (40%) | 2/5 (40%) | 3/5 (60%) | 5/5 (100%) | 2/5 (40%) | 5/5 (100%) | 3/5 (60%) | 2/5 (40%) | 2/5 (40%) | 0/5 (0%) | 0/5 (0%) | 3/5 (60%) |
| **all** | 107 | **22/107 (21%)** | **21/107 (20%)** | **61/107 (57%)** | **107/107 (100%)** | **49/107 (46%)** | **105/107 (98%)** | **58/107 (54%)** | **16/107 (15%)** | **29/107 (27%)** | **0/36 (0%)** | **0/36 (0%)** | **101/107 (94%)** |

Latency per turn (model calls + tools + database): median 3.99 s, p95 6.71 s, max 11.38 s over 111 turns.
Model calls: 355; mean prompt tokens 1486, mean completion tokens 51.
Unanswerable cases that passed escalation by offering a hand-off: 0.
Cases that errored (scored as failures): 0.
Tool-call format errors (a call left as text, or an empty reply): 0.
Grounding: 6 of 111 replies have an issue (5 per 100 replies), 6 issues.

Failed cases: adv-003, adv-004, adv-006, adv-007, adv-008, adv-009, adv-010, adv-011, adv-012, esc-001, esc-002, esc-003, esc-004, esc-005, esc-006, esc-007, esc-008, esc-009, esc-010, old-001, old-003, old-004, ord-001, ord-002, ord-003, ord-004, ord-005, ord-006, ord-007, ord-008, ord-009, ord-010, ord-011, ord-012, ord-013, ord-014, ord-017, ord-018, ord-019, ord-023, ord-024, ord-025, pol-001, pol-003, pol-004, pol-005, pol-006, pol-007, pol-009, pol-011, pol-012, pol-013, pol-014, pol-015, pol-016, pol-017, pol-018, pol-019, pol-020, pol-021, pol-022, pol-023, pol-024, pol-025, ret-002, ret-003, ret-004, ret-005, ret-006, ret-007, ret-008, ret-009, ret-010, ret-011, ret-012, ret-013, ret-014, ret-015, una-001, una-002, una-003, una-004, una-005, una-006, una-007, una-008, una-009, una-010, una-012, una-013, una-015

Grounding issues:
- adv-001: number 11904 not in tool results
- adv-002: number 12578 not in tool results
- old-002: number 30 not in tool results
- old-005: number 7 not in tool results
- pol-015: number 49 not in tool results
- una-005: number 1080 not in tool results
