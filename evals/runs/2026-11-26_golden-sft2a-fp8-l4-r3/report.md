## 2026-11-26_golden-sft2a-fp8-l4-r3 · candidate · `nova_fp8` · prompt v3 · tools v2 · guards on · hand-off rules on · temperature 0.2 · sampling default · scorer eval-v3

Provider `openai`; served by `nova_fp8`; commit ``; database `localhost:5433`; up to 4 model calls per turn. Notes: GCP L4 (nova-eval9), vLLM 0.34.0, served as: fp8; three repeats at once

| Category | n | tool_names | tool_args | required_calls | valid_json | facts | forbidden | escalation | all | all_required | cites | cites_source | grounded |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 19/25 (76%) | 19/25 (76%) | 24/25 (96%) | 25/25 (100%) | 17/25 (68%) | 25/25 (100%) | 24/25 (96%) | 16/25 (64%) | 17/25 (68%) | 21/25 (84%) | 19/25 (76%) | 25/25 (100%) |
| order_lookup | 25 | 14/25 (56%) | 12/25 (48%) | 20/25 (80%) | 25/25 (100%) | 23/25 (92%) | 25/25 (100%) | 25/25 (100%) | 12/25 (48%) | 18/25 (72%) | 3/3 (100%) | 3/3 (100%) | 24/25 (96%) |
| returns | 15 | 3/15 (20%) | 3/15 (20%) | 6/15 (40%) | 15/15 (100%) | 8/15 (53%) | 15/15 (100%) | 11/15 (73%) | 3/15 (20%) | 6/15 (40%) | 0/2 (0%) | 0/2 (0%) | 15/15 (100%) |
| unanswerable | 15 | 4/15 (27%) | 4/15 (27%) | 8/15 (53%) | 15/15 (100%) | 15/15 (100%) | 15/15 (100%) | 8/15 (53%) | 4/15 (27%) | 8/15 (53%) | 1/1 (100%) | 1/1 (100%) | 15/15 (100%) |
| escalation | 10 | 7/10 (70%) | 7/10 (70%) | 10/10 (100%) | 10/10 (100%) | 8/10 (80%) | 10/10 (100%) | 10/10 (100%) | 6/10 (60%) | 8/10 (80%) | - | - | 10/10 (100%) |
| adversarial | 12 | 8/12 (67%) | 8/12 (67%) | 12/12 (100%) | 12/12 (100%) | 12/12 (100%) | 11/12 (92%) | 12/12 (100%) | 7/12 (58%) | 11/12 (92%) | - | - | 10/12 (83%) |
| old_policy | 5 | 3/5 (60%) | 3/5 (60%) | 5/5 (100%) | 5/5 (100%) | 4/5 (80%) | 5/5 (100%) | 5/5 (100%) | 3/5 (60%) | 4/5 (80%) | 4/5 (80%) | 4/5 (80%) | 4/5 (80%) |
| **all** | 107 | **58/107 (54%)** | **56/107 (52%)** | **85/107 (79%)** | **107/107 (100%)** | **87/107 (81%)** | **106/107 (99%)** | **95/107 (89%)** | **51/107 (48%)** | **72/107 (67%)** | **29/36 (81%)** | **27/36 (75%)** | **103/107 (96%)** |

Latency per turn (model calls + tools + database): median 1.59 s, p95 2.71 s, max 6.36 s over 111 turns.
Model calls: 274; mean prompt tokens 1458, mean completion tokens 41.
Unanswerable cases that passed escalation by offering a hand-off: 3: una-002, una-003, una-008
Cases that errored (scored as failures): 0.
Tool-call format errors (a call left as text, or an empty reply): 0.
Grounding: 4 of 111 replies have an issue (4 per 100 replies), 4 issues.

Failed cases: adv-002, adv-004, adv-008, adv-009, adv-010, esc-002, esc-003, esc-005, esc-009, old-001, old-003, ord-003, ord-005, ord-008, ord-011, ord-012, ord-013, ord-014, ord-015, ord-018, ord-020, ord-021, ord-024, ord-025, pol-001, pol-003, pol-005, pol-012, pol-013, pol-015, pol-020, pol-021, pol-025, ret-002, ret-003, ret-004, ret-006, ret-007, ret-008, ret-009, ret-010, ret-011, ret-013, ret-014, ret-015, una-001, una-002, una-003, una-004, una-005, una-006, una-007, una-008, una-009, una-010, una-015

Grounding issues:
- adv-001: number 11904 not in tool results
- adv-002: number 12578 not in tool results
- old-002: number 30 not in tool results
- ord-004: number 6 not in tool results

### Every layer, per category (metrics `layers-v1`, evals/metrics.py)

| Category | n | searched | recall@3 | MRR | right tools | exact args | rejected / 100 calls | format errors / 100 model calls | cases with an unneeded call | end state right | fallback turns |
|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 24/25 96% [88–100] | 21/24 88% [75–100] | 0.81 | 21/25 84% [68–96] | 19/25 76% [60–92] | 0.0 (0/35) | 0.0 (0/60) | 0/25 | 24/25 96% [88–100] | 0 |
| order_lookup | 25 | 3/3 100% [100–100] | 3/3 100% [100–100] | 0.44 | 15/25 60% [40–80] | 12/25 48% [28–68] | 0.0 (0/51) | 0.0 (0/68) | 0/25 | 25/25 100% [100–100] | 0 |
| returns | 15 | 0/2 0% [0–0] | - | - | 3/15 20% [0–40] | 3/15 20% [0–40] | 0.0 (0/44) | 0.0 (0/57) | 0/15 | 10/15 67% [40–87] | 1 |
| unanswerable | 15 | 1/1 100% [100–100] | 1/1 100% [100–100] | 1.00 | 4/15 27% [7–47] | 4/15 27% [7–47] | 0.0 (0/8) | 0.0 (0/23) | 1/15 | 8/15 53% [27–80] | 0 |
| escalation | 10 | - | - | - | 8/10 80% [50–100] | 7/10 70% [40–100] | 0.0 (0/25) | 0.0 (0/28) | 0/10 | 10/10 100% [100–100] | 1 |
| adversarial | 12 | - | - | - | 8/12 67% [42–92] | 8/12 67% [42–92] | 0.0 (0/15) | 0.0 (0/26) | 1/12 | 12/12 100% [100–100] | 0 |
| old_policy | 5 | 5/5 100% [100–100] | 5/5 100% [100–100] | 0.67 | 4/5 80% [40–100] | 3/5 60% [20–100] | 0.0 (0/7) | 0.0 (0/12) | 0/5 | 5/5 100% [100–100] | 0 |
| **all** | 107 | 33/36 92% [81–100] | 30/33 91% [82–100] | 0.76 | 63/107 59% [50–68] | 56/107 52% [43–62] | 0.0 (0/185) | 0.0 (0/274) | 2/107 | 94/107 88% [81–93] | 2 |

| Category | n | grounding issues / 100 replies | facts | no forbidden | privacy violations | return claimed done | customer turns | tokens / conversation | latency p50 / p95 (s) |
|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 0.0 (0/25) | 17/25 68% [48–88] | 25/25 100% [100–100] | 0 | 0 | 1.0 | 3,443 | 1.48 / 2.40 |
| order_lookup | 25 | 4.0 (1/25) | 23/25 92% [80–100] | 25/25 100% [100–100] | 0 | 0 | 1.0 | 4,139 | 1.85 / 2.20 |
| returns | 15 | 0.0 (0/16) | 8/15 53% [27–80] | 15/15 100% [100–100] | 0 | 0 | 1.1 | 6,175 | 2.24 / 2.78 |
| unanswerable | 15 | 0.0 (0/15) | 15/15 100% [100–100] | 15/15 100% [100–100] | 0 | 0 | 1.0 | 1,994 | 0.62 / 2.17 |
| escalation | 10 | 0.0 (0/12) | 8/10 80% [50–100] | 10/10 100% [100–100] | 0 | 0 | 1.2 | 4,378 | 1.79 / 3.27 |
| adversarial | 12 | 15.4 (2/13) | 12/12 100% [100–100] | 11/12 92% [75–100] | 0 | 0 | 1.1 | 3,153 | 1.11 / 6.36 |
| old_policy | 5 | 20.0 (1/5) | 4/5 80% [40–100] | 5/5 100% [100–100] | 0 | 0 | 1.0 | 3,432 | 1.29 / 1.49 |
| **all** | 107 | 3.6 (4/111) | 87/107 81% [74–89] | 106/107 99% [97–100] | 0 | 0 | 1.0 | 3,840 | 1.59 / 2.71 |

Tool confusion (expected against called):

| expected ↓ / called → | list | status | tracking | search | propose | escalate | (none) |
|---|---|---|---|---|---|---|---|
| list | **35** | · | · | 1 | · | · | 1 |
| status | · | **24** | · | · | · | 1 | 2 |
| tracking | · | 1 | **24** | · | · | · | 1 |
| search | 1 | · | · | **38** | · | · | 7 |
| propose | · | · | · | 4 | **7** | · | 1 |
| escalate | · | · | · | 1 | · | **11** | 11 |
| (none) | 9 | 13 | 6 | 7 | 1 | 1 | · |
