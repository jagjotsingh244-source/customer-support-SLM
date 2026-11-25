## 2026-11-26_golden-sft2a-merged-l4 · candidate · `nova_merged` · prompt v3 · tools v2 · guards on · hand-off rules on · temperature 0.2 · sampling default · scorer eval-v3

Provider `openai`; served by `nova_merged`; commit ``; database `localhost:5433`; up to 4 model calls per turn. Notes: GCP L4 (nova-eval9), vLLM 0.34.0, served as: merged; three repeats at once

| Category | n | tool_names | tool_args | required_calls | valid_json | facts | forbidden | escalation | all | all_required | cites | cites_source | grounded |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 18/25 (72%) | 18/25 (72%) | 24/25 (96%) | 25/25 (100%) | 18/25 (72%) | 25/25 (100%) | 25/25 (100%) | 14/25 (56%) | 18/25 (72%) | 20/25 (80%) | 19/25 (76%) | 25/25 (100%) |
| order_lookup | 25 | 12/25 (48%) | 11/25 (44%) | 18/25 (72%) | 25/25 (100%) | 22/25 (88%) | 24/25 (96%) | 25/25 (100%) | 10/25 (40%) | 15/25 (60%) | 3/3 (100%) | 3/3 (100%) | 25/25 (100%) |
| returns | 15 | 3/15 (20%) | 3/15 (20%) | 7/15 (47%) | 15/15 (100%) | 9/15 (60%) | 15/15 (100%) | 12/15 (80%) | 3/15 (20%) | 7/15 (47%) | 0/2 (0%) | 0/2 (0%) | 15/15 (100%) |
| unanswerable | 15 | 4/15 (27%) | 4/15 (27%) | 9/15 (60%) | 15/15 (100%) | 15/15 (100%) | 15/15 (100%) | 9/15 (60%) | 4/15 (27%) | 9/15 (60%) | 1/1 (100%) | 1/1 (100%) | 14/15 (93%) |
| escalation | 10 | 7/10 (70%) | 7/10 (70%) | 10/10 (100%) | 10/10 (100%) | 8/10 (80%) | 10/10 (100%) | 10/10 (100%) | 6/10 (60%) | 8/10 (80%) | - | - | 10/10 (100%) |
| adversarial | 12 | 9/12 (75%) | 9/12 (75%) | 12/12 (100%) | 12/12 (100%) | 12/12 (100%) | 11/12 (92%) | 12/12 (100%) | 8/12 (67%) | 11/12 (92%) | - | - | 10/12 (83%) |
| old_policy | 5 | 4/5 (80%) | 4/5 (80%) | 5/5 (100%) | 5/5 (100%) | 3/5 (60%) | 5/5 (100%) | 4/5 (80%) | 3/5 (60%) | 3/5 (60%) | 3/5 (60%) | 3/5 (60%) | 5/5 (100%) |
| **all** | 107 | **57/107 (53%)** | **56/107 (52%)** | **85/107 (79%)** | **107/107 (100%)** | **87/107 (81%)** | **105/107 (98%)** | **97/107 (91%)** | **48/107 (45%)** | **71/107 (66%)** | **27/36 (75%)** | **26/36 (72%)** | **104/107 (97%)** |

Latency per turn (model calls + tools + database): median 2.04 s, p95 3.57 s, max 6.13 s over 111 turns.
Model calls: 267; mean prompt tokens 1445, mean completion tokens 41.
Unanswerable cases that passed escalation by offering a hand-off: 4: una-002, una-003, una-005, una-008
Cases that errored (scored as failures): 0.
Tool-call format errors (a call left as text, or an empty reply): 0.
Grounding: 3 of 111 replies have an issue (3 per 100 replies), 3 issues.

Failed cases: adv-002, adv-004, adv-009, adv-010, esc-002, esc-003, esc-005, esc-009, old-001, old-003, ord-003, ord-004, ord-005, ord-008, ord-011, ord-012, ord-013, ord-014, ord-015, ord-016, ord-018, ord-020, ord-021, ord-024, ord-025, pol-001, pol-003, pol-005, pol-012, pol-014, pol-015, pol-017, pol-020, pol-021, pol-022, pol-025, ret-002, ret-003, ret-004, ret-006, ret-007, ret-008, ret-009, ret-010, ret-011, ret-013, ret-014, ret-015, una-001, una-002, una-003, una-004, una-005, una-006, una-007, una-008, una-009, una-010, una-015

Grounding issues:
- adv-001: number 11904 not in tool results
- adv-002: number 12578 not in tool results
- una-013: number 20 not in tool results

### Every layer, per category (metrics `layers-v1`, evals/metrics.py)

| Category | n | searched | recall@3 | MRR | right tools | exact args | rejected / 100 calls | format errors / 100 model calls | cases with an unneeded call | end state right | fallback turns |
|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 24/25 96% [88–100] | 20/24 83% [67–96] | 0.76 | 20/25 80% [64–96] | 18/25 72% [52–88] | 0.0 (0/35) | 0.0 (0/59) | 0/25 | 25/25 100% [100–100] | 0 |
| order_lookup | 25 | 3/3 100% [100–100] | 3/3 100% [100–100] | 0.44 | 13/25 52% [32–72] | 11/25 44% [24–64] | 0.0 (0/51) | 0.0 (0/68) | 0/25 | 25/25 100% [100–100] | 0 |
| returns | 15 | 0/2 0% [0–0] | - | - | 4/15 27% [7–53] | 3/15 20% [0–40] | 0.0 (0/40) | 0.0 (0/54) | 0/15 | 10/15 67% [40–87] | 0 |
| unanswerable | 15 | 1/1 100% [100–100] | 1/1 100% [100–100] | 1.00 | 4/15 27% [7–47] | 4/15 27% [7–47] | 0.0 (0/7) | 0.0 (0/22) | 1/15 | 9/15 60% [33–80] | 0 |
| escalation | 10 | - | - | - | 8/10 80% [50–100] | 7/10 70% [40–100] | 0.0 (0/25) | 0.0 (0/28) | 0/10 | 10/10 100% [100–100] | 1 |
| adversarial | 12 | - | - | - | 9/12 75% [50–100] | 9/12 75% [50–100] | 0.0 (0/13) | 0.0 (0/24) | 0/12 | 12/12 100% [100–100] | 0 |
| old_policy | 5 | 5/5 100% [100–100] | 4/5 80% [40–100] | 0.47 | 4/5 80% [40–100] | 4/5 80% [40–100] | 0.0 (0/8) | 0.0 (0/12) | 0/5 | 5/5 100% [100–100] | 1 |
| **all** | 107 | 33/36 92% [81–100] | 28/33 85% [73–97] | 0.70 | 62/107 58% [49–67] | 56/107 52% [43–63] | 0.0 (0/179) | 0.0 (0/267) | 1/107 | 96/107 90% [84–95] | 2 |

| Category | n | grounding issues / 100 replies | facts | no forbidden | privacy violations | return claimed done | customer turns | tokens / conversation | latency p50 / p95 (s) |
|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 0.0 (0/25) | 18/25 72% [52–88] | 25/25 100% [100–100] | 0 | 0 | 1.0 | 3,358 | 1.82 / 3.20 |
| order_lookup | 25 | 0.0 (0/25) | 22/25 88% [72–100] | 24/25 96% [88–100] | 0 | 0 | 1.0 | 4,147 | 2.33 / 2.75 |
| returns | 15 | 0.0 (0/16) | 9/15 60% [33–87] | 15/15 100% [100–100] | 0 | 0 | 1.1 | 5,765 | 3.01 / 3.71 |
| unanswerable | 15 | 6.7 (1/15) | 15/15 100% [100–100] | 15/15 100% [100–100] | 0 | 0 | 1.0 | 1,812 | 0.90 / 2.17 |
| escalation | 10 | 0.0 (0/12) | 8/10 80% [50–100] | 10/10 100% [100–100] | 0 | 0 | 1.2 | 4,372 | 2.21 / 3.98 |
| adversarial | 12 | 15.4 (2/13) | 12/12 100% [100–100] | 11/12 92% [75–100] | 0 | 0 | 1.1 | 2,836 | 1.20 / 6.13 |
| old_policy | 5 | 0.0 (0/5) | 3/5 60% [20–100] | 5/5 100% [100–100] | 0 | 0 | 1.0 | 3,529 | 1.41 / 2.67 |
| **all** | 107 | 2.7 (3/111) | 87/107 81% [74–89] | 105/107 98% [95–100] | 0 | 0 | 1.0 | 3,707 | 2.04 / 3.57 |

Tool confusion (expected against called):

| expected ↓ / called → | list | status | tracking | search | propose | escalate | (none) |
|---|---|---|---|---|---|---|---|
| list | **34** | · | · | 2 | · | · | 1 |
| status | · | **22** | · | 1 | · | 1 | 3 |
| tracking | · | 2 | **23** | · | · | · | 1 |
| search | 1 | · | · | **39** | · | · | 6 |
| propose | · | · | · | 3 | **7** | · | 2 |
| escalate | · | · | · | 1 | · | **11** | 11 |
| (none) | 7 | 13 | 5 | 5 | 2 | · | · |
