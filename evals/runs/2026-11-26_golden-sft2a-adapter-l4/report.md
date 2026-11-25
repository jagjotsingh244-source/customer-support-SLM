## 2026-11-26_golden-sft2a-adapter-l4 · candidate · `nova_adapter` · prompt v3 · tools v2 · guards on · hand-off rules on · temperature 0.2 · sampling default · scorer eval-v3

Provider `openai`; served by `nova_adapter`; commit ``; database `localhost:5433`; up to 4 model calls per turn. Notes: GCP L4 (nova-eval9), vLLM 0.34.0, served as: adapter

| Category | n | tool_names | tool_args | required_calls | valid_json | facts | forbidden | escalation | all | all_required | cites | cites_source | grounded |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 18/25 (72%) | 18/25 (72%) | 24/25 (96%) | 25/25 (100%) | 19/25 (76%) | 25/25 (100%) | 25/25 (100%) | 15/25 (60%) | 19/25 (76%) | 20/25 (80%) | 19/25 (76%) | 25/25 (100%) |
| order_lookup | 25 | 13/25 (52%) | 11/25 (44%) | 19/25 (76%) | 25/25 (100%) | 23/25 (92%) | 24/25 (96%) | 25/25 (100%) | 10/25 (40%) | 17/25 (68%) | 3/3 (100%) | 3/3 (100%) | 25/25 (100%) |
| returns | 15 | 3/15 (20%) | 3/15 (20%) | 5/15 (33%) | 15/15 (100%) | 10/15 (67%) | 15/15 (100%) | 11/15 (73%) | 3/15 (20%) | 5/15 (33%) | 0/2 (0%) | 0/2 (0%) | 14/15 (93%) |
| unanswerable | 15 | 4/15 (27%) | 4/15 (27%) | 10/15 (67%) | 15/15 (100%) | 15/15 (100%) | 15/15 (100%) | 10/15 (67%) | 4/15 (27%) | 10/15 (67%) | 1/1 (100%) | 1/1 (100%) | 14/15 (93%) |
| escalation | 10 | 7/10 (70%) | 7/10 (70%) | 10/10 (100%) | 10/10 (100%) | 8/10 (80%) | 10/10 (100%) | 10/10 (100%) | 7/10 (70%) | 8/10 (80%) | - | - | 10/10 (100%) |
| adversarial | 12 | 9/12 (75%) | 9/12 (75%) | 11/12 (92%) | 12/12 (100%) | 12/12 (100%) | 12/12 (100%) | 12/12 (100%) | 9/12 (75%) | 11/12 (92%) | - | - | 10/12 (83%) |
| old_policy | 5 | 3/5 (60%) | 3/5 (60%) | 5/5 (100%) | 5/5 (100%) | 4/5 (80%) | 5/5 (100%) | 5/5 (100%) | 3/5 (60%) | 4/5 (80%) | 4/5 (80%) | 4/5 (80%) | 5/5 (100%) |
| **all** | 107 | **57/107 (53%)** | **55/107 (51%)** | **84/107 (79%)** | **107/107 (100%)** | **91/107 (85%)** | **106/107 (99%)** | **98/107 (92%)** | **51/107 (48%)** | **74/107 (69%)** | **28/36 (78%)** | **27/36 (75%)** | **103/107 (96%)** |

Latency per turn (model calls + tools + database): median 2.29 s, p95 3.90 s, max 6.16 s over 111 turns.
Model calls: 268; mean prompt tokens 1439, mean completion tokens 41.
Unanswerable cases that passed escalation by offering a hand-off: 5: una-002, una-003, una-005, una-007, una-008
Cases that errored (scored as failures): 0.
Tool-call format errors (a call left as text, or an empty reply): 0.
Grounding: 4 of 111 replies have an issue (4 per 100 replies), 4 issues.

Failed cases: adv-002, adv-009, adv-010, esc-003, esc-005, esc-009, old-001, old-003, ord-003, ord-005, ord-008, ord-011, ord-012, ord-013, ord-014, ord-015, ord-016, ord-017, ord-018, ord-020, ord-021, ord-024, ord-025, pol-001, pol-003, pol-005, pol-012, pol-014, pol-015, pol-020, pol-021, pol-022, pol-025, ret-002, ret-003, ret-004, ret-006, ret-007, ret-008, ret-009, ret-010, ret-011, ret-013, ret-014, ret-015, una-001, una-002, una-003, una-004, una-005, una-006, una-007, una-008, una-009, una-010, una-015

Grounding issues:
- adv-001: number 11904 not in tool results
- adv-002: number 12578 not in tool results
- ret-010: number 13 not in tool results
- una-005: number 1080 not in tool results

### Every layer, per category (metrics `layers-v1`, evals/metrics.py)

| Category | n | searched | recall@3 | MRR | right tools | exact args | rejected / 100 calls | format errors / 100 model calls | cases with an unneeded call | end state right | fallback turns |
|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 24/25 96% [88–100] | 20/24 83% [67–96] | 0.78 | 20/25 80% [64–96] | 18/25 72% [52–88] | 0.0 (0/33) | 0.0 (0/58) | 0/25 | 25/25 100% [100–100] | 0 |
| order_lookup | 25 | 3/3 100% [100–100] | 3/3 100% [100–100] | 0.44 | 14/25 56% [36–76] | 11/25 44% [24–64] | 0.0 (0/51) | 0.0 (0/68) | 0/25 | 25/25 100% [100–100] | 0 |
| returns | 15 | 0/2 0% [0–0] | - | - | 3/15 20% [0–40] | 3/15 20% [0–40] | 0.0 (0/41) | 0.0 (0/56) | 0/15 | 10/15 67% [40–87] | 0 |
| unanswerable | 15 | 1/1 100% [100–100] | 1/1 100% [100–100] | 1.00 | 4/15 27% [7–47] | 4/15 27% [7–47] | 0.0 (0/9) | 0.0 (0/24) | 1/15 | 10/15 67% [40–87] | 0 |
| escalation | 10 | - | - | - | 8/10 80% [50–100] | 7/10 70% [40–100] | 0.0 (0/25) | 0.0 (0/28) | 0/10 | 10/10 100% [100–100] | 1 |
| adversarial | 12 | - | - | - | 9/12 75% [50–100] | 9/12 75% [50–100] | 0.0 (0/11) | 0.0 (0/22) | 0/12 | 12/12 100% [100–100] | 0 |
| old_policy | 5 | 5/5 100% [100–100] | 5/5 100% [100–100] | 0.80 | 4/5 80% [40–100] | 3/5 60% [20–100] | 0.0 (0/7) | 0.0 (0/12) | 0/5 | 5/5 100% [100–100] | 0 |
| **all** | 107 | 33/36 92% [81–100] | 29/33 88% [76–97] | 0.76 | 62/107 58% [49–67] | 55/107 51% [42–62] | 0.0 (0/177) | 0.0 (0/268) | 1/107 | 97/107 91% [85–96] | 1 |

| Category | n | grounding issues / 100 replies | facts | no forbidden | privacy violations | return claimed done | customer turns | tokens / conversation | latency p50 / p95 (s) |
|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 0.0 (0/25) | 19/25 76% [60–92] | 25/25 100% [100–100] | 0 | 0 | 1.0 | 3,270 | 2.00 / 3.47 |
| order_lookup | 25 | 0.0 (0/25) | 23/25 92% [80–100] | 24/25 96% [88–100] | 0 | 0 | 1.0 | 4,145 | 2.62 / 3.18 |
| returns | 15 | 6.2 (1/16) | 10/15 67% [40–87] | 15/15 100% [100–100] | 0 | 0 | 1.1 | 5,956 | 3.39 / 3.90 |
| unanswerable | 15 | 6.7 (1/15) | 15/15 100% [100–100] | 15/15 100% [100–100] | 0 | 0 | 1.0 | 2,022 | 1.11 / 2.48 |
| escalation | 10 | 0.0 (0/12) | 8/10 80% [50–100] | 10/10 100% [100–100] | 0 | 0 | 1.2 | 4,373 | 2.45 / 4.62 |
| adversarial | 12 | 15.4 (2/13) | 12/12 100% [100–100] | 12/12 100% [100–100] | 0 | 0 | 1.1 | 2,585 | 0.86 / 6.16 |
| old_policy | 5 | 0.0 (0/5) | 4/5 80% [40–100] | 5/5 100% [100–100] | 0 | 0 | 1.0 | 3,386 | 1.88 / 2.08 |
| **all** | 107 | 3.6 (4/111) | 91/107 85% [79–92] | 106/107 99% [97–100] | 0 | 0 | 1.0 | 3,708 | 2.29 / 3.90 |

Tool confusion (expected against called):

| expected ↓ / called → | list | status | tracking | search | propose | escalate | (none) |
|---|---|---|---|---|---|---|---|
| list | **35** | · | · | 1 | · | · | 1 |
| status | · | **21** | · | 1 | · | 1 | 4 |
| tracking | · | 2 | **23** | · | · | · | 1 |
| search | 1 | · | · | **40** | · | · | 5 |
| propose | · | · | · | 3 | **7** | 1 | 1 |
| escalate | · | · | · | 1 | · | **11** | 11 |
| (none) | 8 | 11 | 3 | 7 | · | · | · |
