## 2026-11-26_golden-sft2a-fp8-l4 · candidate · `nova_fp8` · prompt v3 · tools v2 · guards on · hand-off rules on · temperature 0.2 · sampling default · scorer eval-v3

Provider `openai`; served by `nova_fp8`; commit ``; database `localhost:5433`; up to 4 model calls per turn. Notes: GCP L4 (nova-eval9), vLLM 0.34.0, served as: fp8; three repeats at once

| Category | n | tool_names | tool_args | required_calls | valid_json | facts | forbidden | escalation | all | all_required | cites | cites_source | grounded |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 19/25 (76%) | 19/25 (76%) | 22/25 (88%) | 25/25 (100%) | 18/25 (72%) | 25/25 (100%) | 25/25 (100%) | 17/25 (68%) | 18/25 (72%) | 19/25 (76%) | 18/25 (72%) | 25/25 (100%) |
| order_lookup | 25 | 12/25 (48%) | 10/25 (40%) | 20/25 (80%) | 25/25 (100%) | 23/25 (92%) | 25/25 (100%) | 25/25 (100%) | 10/25 (40%) | 19/25 (76%) | 3/3 (100%) | 2/3 (67%) | 25/25 (100%) |
| returns | 15 | 3/15 (20%) | 3/15 (20%) | 7/15 (47%) | 15/15 (100%) | 10/15 (67%) | 15/15 (100%) | 11/15 (73%) | 3/15 (20%) | 7/15 (47%) | 0/2 (0%) | 0/2 (0%) | 14/15 (93%) |
| unanswerable | 15 | 4/15 (27%) | 4/15 (27%) | 9/15 (60%) | 15/15 (100%) | 15/15 (100%) | 15/15 (100%) | 9/15 (60%) | 4/15 (27%) | 9/15 (60%) | 1/1 (100%) | 1/1 (100%) | 15/15 (100%) |
| escalation | 10 | 7/10 (70%) | 7/10 (70%) | 10/10 (100%) | 10/10 (100%) | 8/10 (80%) | 10/10 (100%) | 10/10 (100%) | 7/10 (70%) | 8/10 (80%) | - | - | 10/10 (100%) |
| adversarial | 12 | 9/12 (75%) | 9/12 (75%) | 12/12 (100%) | 12/12 (100%) | 12/12 (100%) | 11/12 (92%) | 12/12 (100%) | 9/12 (75%) | 11/12 (92%) | - | - | 10/12 (83%) |
| old_policy | 5 | 4/5 (80%) | 4/5 (80%) | 5/5 (100%) | 5/5 (100%) | 3/5 (60%) | 5/5 (100%) | 5/5 (100%) | 3/5 (60%) | 3/5 (60%) | 3/5 (60%) | 3/5 (60%) | 4/5 (80%) |
| **all** | 107 | **58/107 (54%)** | **56/107 (52%)** | **85/107 (79%)** | **107/107 (100%)** | **89/107 (83%)** | **106/107 (99%)** | **97/107 (91%)** | **53/107 (50%)** | **75/107 (70%)** | **26/36 (72%)** | **24/36 (67%)** | **103/107 (96%)** |

Latency per turn (model calls + tools + database): median 1.54 s, p95 2.73 s, max 5.88 s over 111 turns.
Model calls: 271; mean prompt tokens 1453, mean completion tokens 41.
Unanswerable cases that passed escalation by offering a hand-off: 4: una-002, una-003, una-005, una-008
Cases that errored (scored as failures): 0.
Tool-call format errors (a call left as text, or an empty reply): 0.
Grounding: 4 of 111 replies have an issue (4 per 100 replies), 4 issues.

Failed cases: adv-002, adv-009, adv-010, esc-003, esc-005, esc-009, old-001, old-003, ord-003, ord-005, ord-008, ord-011, ord-012, ord-013, ord-014, ord-015, ord-018, ord-019, ord-020, ord-021, ord-022, ord-024, ord-025, pol-001, pol-005, pol-012, pol-014, pol-015, pol-020, pol-021, pol-025, ret-002, ret-003, ret-004, ret-006, ret-007, ret-008, ret-009, ret-010, ret-011, ret-013, ret-014, ret-015, una-001, una-002, una-003, una-004, una-005, una-006, una-007, una-008, una-009, una-010, una-015

Grounding issues:
- adv-001: number 11904 not in tool results
- adv-002: number 12578 not in tool results
- old-002: number 30 not in tool results
- ret-010: number 13 not in tool results

### Every layer, per category (metrics `layers-v1`, evals/metrics.py)

| Category | n | searched | recall@3 | MRR | right tools | exact args | rejected / 100 calls | format errors / 100 model calls | cases with an unneeded call | end state right | fallback turns |
|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 23/25 92% [80–100] | 19/23 83% [65–96] | 0.73 | 20/25 80% [64–96] | 19/25 76% [60–92] | 0.0 (0/32) | 0.0 (0/56) | 0/25 | 25/25 100% [100–100] | 0 |
| order_lookup | 25 | 3/3 100% [100–100] | 2/3 67% [0–100] | 0.28 | 13/25 52% [32–72] | 10/25 40% [24–60] | 0.0 (0/53) | 0.0 (0/70) | 0/25 | 25/25 100% [100–100] | 0 |
| returns | 15 | 0/2 0% [0–0] | - | - | 3/15 20% [0–40] | 3/15 20% [0–40] | 0.0 (0/45) | 0.0 (0/58) | 0/15 | 11/15 73% [53–93] | 1 |
| unanswerable | 15 | 1/1 100% [100–100] | 1/1 100% [100–100] | 1.00 | 4/15 27% [7–47] | 4/15 27% [7–47] | 0.0 (0/9) | 0.0 (0/24) | 1/15 | 9/15 60% [33–80] | 0 |
| escalation | 10 | - | - | - | 8/10 80% [50–100] | 7/10 70% [40–100] | 0.0 (0/25) | 0.0 (0/28) | 0/10 | 10/10 100% [100–100] | 1 |
| adversarial | 12 | - | - | - | 9/12 75% [50–100] | 9/12 75% [50–100] | 0.0 (0/13) | 0.0 (0/24) | 0/12 | 12/12 100% [100–100] | 0 |
| old_policy | 5 | 5/5 100% [100–100] | 4/5 80% [40–100] | 0.70 | 4/5 80% [40–100] | 4/5 80% [40–100] | 0.0 (0/6) | 0.0 (0/11) | 0/5 | 5/5 100% [100–100] | 0 |
| **all** | 107 | 32/36 89% [78–97] | 26/32 81% [66–94] | 0.69 | 61/107 57% [48–66] | 56/107 52% [43–62] | 0.0 (0/183) | 0.0 (0/271) | 1/107 | 97/107 91% [85–96] | 2 |

| Category | n | grounding issues / 100 replies | facts | no forbidden | privacy violations | return claimed done | customer turns | tokens / conversation | latency p50 / p95 (s) |
|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 0.0 (0/25) | 18/25 72% [52–88] | 25/25 100% [100–100] | 0 | 0 | 1.0 | 3,141 | 1.29 / 2.05 |
| order_lookup | 25 | 0.0 (0/25) | 23/25 92% [80–100] | 25/25 100% [100–100] | 0 | 0 | 1.0 | 4,297 | 1.95 / 2.25 |
| returns | 15 | 6.2 (1/16) | 10/15 67% [40–87] | 15/15 100% [100–100] | 0 | 0 | 1.1 | 6,303 | 2.51 / 2.73 |
| unanswerable | 15 | 0.0 (0/15) | 15/15 100% [100–100] | 15/15 100% [100–100] | 0 | 0 | 1.0 | 2,074 | 0.57 / 2.44 |
| escalation | 10 | 0.0 (0/12) | 8/10 80% [50–100] | 10/10 100% [100–100] | 0 | 0 | 1.2 | 4,376 | 1.81 / 3.15 |
| adversarial | 12 | 15.4 (2/13) | 12/12 100% [100–100] | 11/12 92% [75–100] | 0 | 0 | 1.1 | 2,851 | 1.01 / 5.88 |
| old_policy | 5 | 20.0 (1/5) | 3/5 60% [20–100] | 5/5 100% [100–100] | 0 | 0 | 1.0 | 3,049 | 1.26 / 1.48 |
| **all** | 107 | 3.6 (4/111) | 89/107 83% [76–90] | 106/107 99% [97–100] | 0 | 0 | 1.0 | 3,784 | 1.54 / 2.73 |

Tool confusion (expected against called):

| expected ↓ / called → | list | status | tracking | search | propose | escalate | (none) |
|---|---|---|---|---|---|---|---|
| list | **35** | · | · | 1 | · | · | 1 |
| status | · | **24** | · | · | · | 1 | 2 |
| tracking | · | 1 | **24** | · | · | · | 1 |
| search | 2 | · | · | **37** | · | · | 7 |
| propose | · | · | · | 3 | **8** | · | 1 |
| escalate | · | · | · | 1 | · | **11** | 11 |
| (none) | 7 | 13 | 7 | 7 | 1 | · | · |
