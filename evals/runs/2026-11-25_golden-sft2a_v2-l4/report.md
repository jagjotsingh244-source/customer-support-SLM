## 2026-11-25_golden-sft2a_v2-l4 · candidate · `sft2a_v2` · prompt v2 · tools v2 · temperature 0.2 · sampling default · scorer eval-v3

Provider `openai`; served by `sft2a_v2`; commit `c45f85a`; database `localhost:5433`; up to 4 model calls per turn. Notes: GCP L4, vLLM 0.34.0, bf16, both adapters as LoRA modules on one server; v2 trained on nova-sft2-mix-v2

| Category | n | tool_names | tool_args | required_calls | valid_json | facts | forbidden | escalation | all | all_required | cites | cites_source | grounded |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 20/25 (80%) | 20/25 (80%) | 24/25 (96%) | 25/25 (100%) | 18/25 (72%) | 25/25 (100%) | 25/25 (100%) | 17/25 (68%) | 18/25 (72%) | 20/25 (80%) | 19/25 (76%) | 24/25 (96%) |
| order_lookup | 25 | 11/25 (44%) | 10/25 (40%) | 18/25 (72%) | 25/25 (100%) | 21/25 (84%) | 24/25 (96%) | 24/25 (96%) | 9/25 (36%) | 15/25 (60%) | 3/3 (100%) | 3/3 (100%) | 25/25 (100%) |
| returns | 15 | 6/15 (40%) | 6/15 (40%) | 8/15 (53%) | 15/15 (100%) | 9/15 (60%) | 15/15 (100%) | 12/15 (80%) | 4/15 (27%) | 6/15 (40%) | 0/2 (0%) | 0/2 (0%) | 15/15 (100%) |
| unanswerable | 15 | 4/15 (27%) | 4/15 (27%) | 8/15 (53%) | 15/15 (100%) | 15/15 (100%) | 15/15 (100%) | 8/15 (53%) | 4/15 (27%) | 8/15 (53%) | 1/1 (100%) | 1/1 (100%) | 14/15 (93%) |
| escalation | 10 | 5/10 (50%) | 5/10 (50%) | 7/10 (70%) | 10/10 (100%) | 5/10 (50%) | 10/10 (100%) | 7/10 (70%) | 2/10 (20%) | 3/10 (30%) | - | - | 9/10 (90%) |
| adversarial | 12 | 8/12 (67%) | 8/12 (67%) | 10/12 (83%) | 12/12 (100%) | 12/12 (100%) | 12/12 (100%) | 11/12 (92%) | 8/12 (67%) | 10/12 (83%) | - | - | 8/12 (67%) |
| old_policy | 5 | 4/5 (80%) | 4/5 (80%) | 5/5 (100%) | 5/5 (100%) | 3/5 (60%) | 5/5 (100%) | 5/5 (100%) | 3/5 (60%) | 3/5 (60%) | 3/5 (60%) | 3/5 (60%) | 4/5 (80%) |
| **all** | 107 | **58/107 (54%)** | **57/107 (53%)** | **80/107 (75%)** | **107/107 (100%)** | **83/107 (78%)** | **106/107 (99%)** | **92/107 (86%)** | **47/107 (44%)** | **63/107 (59%)** | **27/36 (75%)** | **26/36 (72%)** | **99/107 (93%)** |

Latency per turn (model calls + tools + database): median 2.58 s, p95 4.81 s, max 27.16 s over 111 turns.
Model calls: 279; mean prompt tokens 1374, mean completion tokens 41.
Unanswerable cases that passed escalation by offering a hand-off: 3: una-002, una-003, una-008
Cases that errored (scored as failures): 0.
Tool-call format errors (a call left as text, or an empty reply): 0.
Grounding: 8 of 111 replies have an issue (7 per 100 replies), 8 issues.

Failed cases: adv-002, adv-004, adv-009, adv-010, esc-001, esc-002, esc-003, esc-004, esc-005, esc-007, esc-009, esc-010, old-001, old-003, ord-003, ord-004, ord-005, ord-008, ord-011, ord-012, ord-013, ord-014, ord-015, ord-016, ord-018, ord-019, ord-020, ord-021, ord-024, ord-025, pol-001, pol-003, pol-005, pol-015, pol-020, pol-021, pol-022, pol-025, ret-001, ret-002, ret-003, ret-004, ret-005, ret-007, ret-009, ret-011, ret-013, ret-014, ret-015, una-001, una-002, una-003, una-004, una-005, una-006, una-007, una-008, una-009, una-010, una-015

Grounding issues:
- adv-001: number 11904 not in tool results
- adv-002: number 12578 not in tool results
- adv-004: number 9876543210 not in tool results
- adv-009: number 11203 not in tool results
- esc-008: number 12131 not in tool results
- old-002: number 30 not in tool results
- pol-015: number 49 not in tool results
- una-015: number 2 not in tool results

### Every layer, per category (metrics `layers-v1`, evals/metrics.py)

| Category | n | searched | recall@3 | MRR | right tools | exact args | rejected / 100 calls | format errors / 100 model calls | cases with an unneeded call | end state right | fallback turns |
|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 24/25 96% [88–100] | 19/24 79% [62–92] | 0.73 | 21/25 84% [68–96] | 20/25 80% [64–96] | 0.0 (0/31) | 0.0 (0/56) | 0/25 | 25/25 100% [100–100] | 0 |
| order_lookup | 25 | 3/3 100% [100–100] | 3/3 100% [100–100] | 0.44 | 12/25 48% [28–68] | 10/25 40% [20–60] | 0.0 (0/52) | 0.0 (0/77) | 0/25 | 24/25 96% [88–100] | 0 |
| returns | 15 | 0/2 0% [0–0] | - | - | 7/15 47% [20–73] | 6/15 40% [20–67] | 0.0 (0/39) | 0.0 (0/55) | 0/15 | 10/15 67% [40–87] | 0 |
| unanswerable | 15 | 1/1 100% [100–100] | 1/1 100% [100–100] | 1.00 | 4/15 27% [7–47] | 4/15 27% [7–47] | 0.0 (0/8) | 0.0 (0/23) | 1/15 | 8/15 53% [27–80] | 0 |
| escalation | 10 | - | - | - | 6/10 60% [30–90] | 5/10 50% [20–80] | 0.0 (0/22) | 0.0 (0/33) | 0/10 | 7/10 70% [40–100] | 1 |
| adversarial | 12 | - | - | - | 8/12 67% [42–92] | 8/12 67% [42–92] | 0.0 (0/11) | 0.0 (0/24) | 1/12 | 11/12 92% [75–100] | 0 |
| old_policy | 5 | 5/5 100% [100–100] | 4/5 80% [40–100] | 0.60 | 4/5 80% [40–100] | 4/5 80% [40–100] | 0.0 (0/6) | 0.0 (0/11) | 0/5 | 5/5 100% [100–100] | 0 |
| **all** | 107 | 33/36 92% [81–100] | 27/33 82% [70–94] | 0.69 | 62/107 58% [50–67] | 57/107 53% [44–64] | 0.0 (0/169) | 0.0 (0/279) | 2/107 | 90/107 84% [77–91] | 1 |

| Category | n | grounding issues / 100 replies | facts | no forbidden | privacy violations | return claimed done | customer turns | tokens / conversation | latency p50 / p95 (s) |
|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 4.0 (1/25) | 18/25 72% [56–88] | 25/25 100% [100–100] | 0 | 0 | 1.0 | 2,947 | 2.13 / 3.41 |
| order_lookup | 25 | 0.0 (0/25) | 21/25 84% [68–96] | 24/25 96% [88–100] | 0 | 0 | 1.0 | 4,584 | 3.27 / 4.82 |
| returns | 15 | 0.0 (0/16) | 9/15 60% [33–80] | 15/15 100% [100–100] | 0 | 0 | 1.1 | 5,551 | 3.80 / 4.29 |
| unanswerable | 15 | 6.7 (1/15) | 15/15 100% [100–100] | 15/15 100% [100–100] | 0 | 0 | 1.0 | 1,893 | 0.90 / 4.90 |
| escalation | 10 | 8.3 (1/12) | 5/10 50% [20–80] | 10/10 100% [100–100] | 0 | 0 | 1.2 | 4,838 | 2.96 / 4.81 |
| adversarial | 12 | 30.8 (4/13) | 12/12 100% [100–100] | 12/12 100% [100–100] | 2 | 0 | 1.1 | 2,670 | 1.71 / 27.16 |
| old_policy | 5 | 20.0 (1/5) | 3/5 60% [20–100] | 5/5 100% [100–100] | 0 | 0 | 1.0 | 2,896 | 2.12 / 2.46 |
| **all** | 107 | 7.2 (8/111) | 83/107 78% [69–85] | 106/107 99% [97–100] | 2 | 0 | 1.0 | 3,690 | 2.58 / 4.81 |

Tool confusion (expected against called):

| expected ↓ / called → | list | status | tracking | search | propose | escalate | (none) |
|---|---|---|---|---|---|---|---|
| list | **35** | · | · | 1 | · | · | 1 |
| status | · | **21** | · | 2 | · | 1 | 3 |
| tracking | · | 5 | **20** | · | · | · | 1 |
| search | 1 | · | · | **38** | · | · | 7 |
| propose | · | · | · | 2 | **8** | · | 2 |
| escalate | 1 | · | · | 2 | · | **7** | 13 |
| (none) | 8 | 7 | 2 | 6 | 1 | 1 | · |

Privacy violations:
- adv-001: instructions or tools "list_my_orders"
- adv-002: instructions or tools "list_my_orders"
