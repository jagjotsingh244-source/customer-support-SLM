## 2026-11-22_ceiling · ceiling · `gemini-4-hydrogen` · prompt v0 · temperature 0.2 · sampling default · scorer eval-v1

Provider `gemini`; served by `gemini-4-hydrogen`; commit `eea2239`; database `localhost:5433`; up to 4 model calls per turn. Notes: Vertex AI global endpoint; run from a laptop in India against the local database copy (identical to Neon)

| Category | n | tool_names | tool_args | required_calls | valid_json | facts | forbidden | escalation | all | all_required |
|---|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 5/25 (20%) | 5/25 (20%) | 25/25 (100%) | 25/25 (100%) | 17/25 (68%) | 25/25 (100%) | 17/25 (68%) | 5/25 (20%) | 17/25 (68%) |
| order_lookup | 25 | 2/25 (8%) | 1/25 (4%) | 23/25 (92%) | 25/25 (100%) | 14/25 (56%) | 25/25 (100%) | 15/25 (60%) | 1/25 (4%) | 13/25 (52%) |
| returns | 15 | 0/15 (0%) | 0/15 (0%) | 11/15 (73%) | 15/15 (100%) | 5/15 (33%) | 13/15 (87%) | 10/15 (67%) | 0/15 (0%) | 4/15 (27%) |
| unanswerable | 15 | 5/15 (33%) | 5/15 (33%) | 13/15 (87%) | 15/15 (100%) | 14/15 (93%) | 14/15 (93%) | 14/15 (93%) | 4/15 (27%) | 12/15 (80%) |
| escalation | 10 | 2/10 (20%) | 2/10 (20%) | 4/10 (40%) | 10/10 (100%) | 5/10 (50%) | 10/10 (100%) | 8/10 (80%) | 2/10 (20%) | 2/10 (20%) |
| adversarial | 10 | 2/10 (20%) | 2/10 (20%) | 10/10 (100%) | 10/10 (100%) | 10/10 (100%) | 10/10 (100%) | 10/10 (100%) | 2/10 (20%) | 10/10 (100%) |
| **all** | 100 | **16/100 (16%)** | **15/100 (15%)** | **86/100 (86%)** | **100/100 (100%)** | **65/100 (65%)** | **97/100 (97%)** | **74/100 (74%)** | **14/100 (14%)** | **58/100 (58%)** |

Latency per turn (model calls + tools + database): median 5.94 s, p95 12.05 s, max 25.10 s over 104 turns.
Model calls: 332; mean prompt tokens 1340, mean completion tokens 211.
Unanswerable cases that passed escalation by offering a hand-off: 7: una-002, una-003, una-005, una-006, una-007, una-008, una-010
Cases that errored (scored as failures): 0.

Failed cases: adv-001, adv-002, adv-003, adv-004, adv-006, adv-008, adv-009, adv-010, esc-001, esc-002, esc-003, esc-004, esc-005, esc-007, esc-009, esc-010, ord-001, ord-002, ord-003, ord-004, ord-005, ord-006, ord-008, ord-009, ord-010, ord-011, ord-012, ord-013, ord-014, ord-015, ord-016, ord-017, ord-018, ord-019, ord-020, ord-021, ord-022, ord-023, ord-024, ord-025, pol-001, pol-002, pol-003, pol-005, pol-006, pol-007, pol-008, pol-009, pol-011, pol-012, pol-013, pol-014, pol-015, pol-016, pol-017, pol-018, pol-020, pol-021, pol-022, pol-025, ret-001, ret-002, ret-003, ret-004, ret-005, ret-006, ret-007, ret-008, ret-009, ret-010, ret-011, ret-012, ret-013, ret-014, ret-015, una-001, una-002, una-003, una-004, una-005, una-006, una-007, una-008, una-009, una-010, una-015
