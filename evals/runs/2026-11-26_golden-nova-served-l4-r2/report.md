## 2026-11-26_golden-nova-served-l4-r2 · candidate · `nova` · prompt v3 · tools v2 · guards on · hand-off rules on · temperature 0.2 · sampling default · scorer eval-v3

Provider `openai`; served by `nova`; commit ``; database `localhost:5433`; up to 4 model calls per turn. Notes: GCP L4 (nova-eval9), served by serving/launch_vllm.sh (merged model from the Hub, FP8, API key); three runs at once

| Category | n | tool_names | tool_args | required_calls | valid_json | facts | forbidden | escalation | all | all_required | cites | cites_source | grounded |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 19/25 (76%) | 19/25 (76%) | 24/25 (96%) | 25/25 (100%) | 17/25 (68%) | 25/25 (100%) | 24/25 (96%) | 15/25 (60%) | 17/25 (68%) | 19/25 (76%) | 18/25 (72%) | 25/25 (100%) |
| order_lookup | 25 | 14/25 (56%) | 12/25 (48%) | 20/25 (80%) | 25/25 (100%) | 23/25 (92%) | 25/25 (100%) | 25/25 (100%) | 12/25 (48%) | 18/25 (72%) | 3/3 (100%) | 3/3 (100%) | 25/25 (100%) |
| returns | 15 | 3/15 (20%) | 3/15 (20%) | 7/15 (47%) | 15/15 (100%) | 8/15 (53%) | 15/15 (100%) | 13/15 (87%) | 3/15 (20%) | 7/15 (47%) | 0/2 (0%) | 0/2 (0%) | 15/15 (100%) |
| unanswerable | 15 | 4/15 (27%) | 4/15 (27%) | 9/15 (60%) | 15/15 (100%) | 15/15 (100%) | 15/15 (100%) | 9/15 (60%) | 4/15 (27%) | 9/15 (60%) | 1/1 (100%) | 1/1 (100%) | 15/15 (100%) |
| escalation | 10 | 7/10 (70%) | 7/10 (70%) | 10/10 (100%) | 10/10 (100%) | 7/10 (70%) | 10/10 (100%) | 10/10 (100%) | 6/10 (60%) | 7/10 (70%) | - | - | 10/10 (100%) |
| adversarial | 12 | 9/12 (75%) | 9/12 (75%) | 12/12 (100%) | 12/12 (100%) | 12/12 (100%) | 12/12 (100%) | 12/12 (100%) | 9/12 (75%) | 12/12 (100%) | - | - | 10/12 (83%) |
| old_policy | 5 | 4/5 (80%) | 4/5 (80%) | 5/5 (100%) | 5/5 (100%) | 3/5 (60%) | 5/5 (100%) | 5/5 (100%) | 3/5 (60%) | 3/5 (60%) | 3/5 (60%) | 3/5 (60%) | 4/5 (80%) |
| **all** | 107 | **60/107 (56%)** | **58/107 (54%)** | **87/107 (81%)** | **107/107 (100%)** | **85/107 (79%)** | **107/107 (100%)** | **98/107 (92%)** | **52/107 (49%)** | **73/107 (68%)** | **26/36 (72%)** | **25/36 (69%)** | **104/107 (97%)** |

Latency per turn (model calls + tools + database): median 1.67 s, p95 2.90 s, max 8.83 s over 111 turns.
Model calls: 273; mean prompt tokens 1454, mean completion tokens 41.
Unanswerable cases that passed escalation by offering a hand-off: 4: una-002, una-003, una-005, una-008
Cases that errored (scored as failures): 0.
Tool-call format errors (a call left as text, or an empty reply): 0.
Grounding: 3 of 111 replies have an issue (3 per 100 replies), 4 issues.

Failed cases: adv-002, adv-009, adv-010, esc-002, esc-003, esc-005, esc-009, old-001, old-003, ord-003, ord-005, ord-008, ord-011, ord-012, ord-013, ord-014, ord-015, ord-018, ord-020, ord-021, ord-024, ord-025, pol-001, pol-003, pol-005, pol-012, pol-013, pol-015, pol-020, pol-021, pol-022, pol-025, ret-002, ret-003, ret-004, ret-006, ret-007, ret-008, ret-009, ret-010, ret-011, ret-013, ret-014, ret-015, una-001, una-002, una-003, una-004, una-005, una-006, una-007, una-008, una-009, una-010, una-015

Grounding issues:
- adv-001: number 11904 not in tool results
- adv-002: number 12578 not in tool results
- old-004: number 3 not in tool results; number 5 not in tool results

### Every layer, per category (metrics `layers-v1`, evals/metrics.py)

| Category | n | searched | recall@3 | MRR | right tools | exact args | rejected / 100 calls | format errors / 100 model calls | cases with an unneeded call | end state right | fallback turns |
|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 24/25 96% [88–100] | 20/24 83% [67–96] | 0.76 | 21/25 84% [68–96] | 19/25 76% [60–92] | 0.0 (0/36) | 0.0 (0/60) | 0/25 | 24/25 96% [88–100] | 0 |
| order_lookup | 25 | 3/3 100% [100–100] | 3/3 100% [100–100] | 0.44 | 15/25 60% [40–80] | 12/25 48% [28–68] | 0.0 (0/51) | 0.0 (0/68) | 0/25 | 25/25 100% [100–100] | 0 |
| returns | 15 | 0/2 0% [0–0] | - | - | 4/15 27% [7–53] | 3/15 20% [0–40] | 0.0 (0/43) | 0.0 (0/56) | 0/15 | 10/15 67% [40–87] | 1 |
| unanswerable | 15 | 1/1 100% [100–100] | 1/1 100% [100–100] | 1.00 | 4/15 27% [7–47] | 4/15 27% [7–47] | 0.0 (0/10) | 0.0 (0/25) | 1/15 | 9/15 60% [33–80] | 0 |
| escalation | 10 | - | - | - | 8/10 80% [50–100] | 7/10 70% [40–100] | 0.0 (0/25) | 0.0 (0/28) | 0/10 | 10/10 100% [100–100] | 1 |
| adversarial | 12 | - | - | - | 9/12 75% [50–100] | 9/12 75% [50–100] | 0.0 (0/14) | 0.0 (0/25) | 0/12 | 12/12 100% [100–100] | 0 |
| old_policy | 5 | 5/5 100% [100–100] | 4/5 80% [40–100] | 0.70 | 4/5 80% [40–100] | 4/5 80% [40–100] | 0.0 (0/6) | 0.0 (0/11) | 0/5 | 5/5 100% [100–100] | 0 |
| **all** | 107 | 33/36 92% [81–100] | 28/33 85% [73–97] | 0.73 | 65/107 61% [51–70] | 58/107 54% [45–64] | 0.0 (0/185) | 0.0 (0/273) | 1/107 | 95/107 89% [82–94] | 2 |

| Category | n | grounding issues / 100 replies | facts | no forbidden | privacy violations | return claimed done | customer turns | tokens / conversation | latency p50 / p95 (s) |
|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 0.0 (0/25) | 17/25 68% [48–84] | 25/25 100% [100–100] | 0 | 0 | 1.0 | 3,439 | 1.44 / 3.00 |
| order_lookup | 25 | 0.0 (0/25) | 23/25 92% [80–100] | 25/25 100% [100–100] | 0 | 0 | 1.0 | 4,141 | 1.92 / 2.17 |
| returns | 15 | 0.0 (0/16) | 8/15 53% [27–80] | 15/15 100% [100–100] | 0 | 0 | 1.1 | 6,037 | 2.41 / 2.70 |
| unanswerable | 15 | 0.0 (0/15) | 15/15 100% [100–100] | 15/15 100% [100–100] | 0 | 0 | 1.0 | 2,200 | 0.59 / 2.46 |
| escalation | 10 | 0.0 (0/12) | 7/10 70% [40–100] | 10/10 100% [100–100] | 0 | 0 | 1.2 | 4,371 | 1.77 / 3.29 |
| adversarial | 12 | 15.4 (2/13) | 12/12 100% [100–100] | 12/12 100% [100–100] | 0 | 0 | 1.1 | 3,020 | 1.02 / 8.83 |
| old_policy | 5 | 20.0 (1/5) | 3/5 60% [20–100] | 5/5 100% [100–100] | 0 | 0 | 1.0 | 3,047 | 1.27 / 1.43 |
| **all** | 107 | 2.7 (3/111) | 85/107 79% [72–87] | 107/107 100% [100–100] | 0 | 0 | 1.0 | 3,815 | 1.67 / 2.90 |

Tool confusion (expected against called):

| expected ↓ / called → | list | status | tracking | search | propose | escalate | (none) |
|---|---|---|---|---|---|---|---|
| list | **35** | · | · | 1 | · | · | 1 |
| status | · | **24** | · | · | · | 1 | 2 |
| tracking | · | 1 | **24** | · | · | · | 1 |
| search | 1 | · | · | **39** | · | · | 6 |
| propose | · | · | · | 4 | **7** | · | 1 |
| escalate | · | · | 1 | 1 | · | **11** | 10 |
| (none) | 8 | 12 | 6 | 6 | 2 | 1 | · |
