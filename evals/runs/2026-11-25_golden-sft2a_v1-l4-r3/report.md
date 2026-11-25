## 2026-11-25_golden-sft2a_v1-l4-r3 · candidate · `sft2a_v1` · prompt v2 · tools v2 · temperature 0.2 · sampling default · scorer eval-v3

Provider `openai`; served by `sft2a_v1`; commit `c45f85a`; database `localhost:5433`; up to 4 model calls per turn. Notes: GCP L4, vLLM 0.34.0, bf16, both adapters as LoRA modules on one server; v2 trained on nova-sft2-mix-v2

| Category | n | tool_names | tool_args | required_calls | valid_json | facts | forbidden | escalation | all | all_required | cites | cites_source | grounded |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 19/25 (76%) | 19/25 (76%) | 23/25 (92%) | 25/25 (100%) | 18/25 (72%) | 25/25 (100%) | 24/25 (96%) | 17/25 (68%) | 18/25 (72%) | 20/25 (80%) | 19/25 (76%) | 24/25 (96%) |
| order_lookup | 25 | 12/25 (48%) | 11/25 (44%) | 17/25 (68%) | 25/25 (100%) | 23/25 (92%) | 24/25 (96%) | 25/25 (100%) | 10/25 (40%) | 16/25 (64%) | 3/3 (100%) | 3/3 (100%) | 25/25 (100%) |
| returns | 15 | 5/15 (33%) | 5/15 (33%) | 7/15 (47%) | 15/15 (100%) | 11/15 (73%) | 15/15 (100%) | 10/15 (67%) | 5/15 (33%) | 6/15 (40%) | 0/2 (0%) | 0/2 (0%) | 15/15 (100%) |
| unanswerable | 15 | 4/15 (27%) | 4/15 (27%) | 11/15 (73%) | 15/15 (100%) | 15/15 (100%) | 14/15 (93%) | 11/15 (73%) | 4/15 (27%) | 10/15 (67%) | 1/1 (100%) | 1/1 (100%) | 15/15 (100%) |
| escalation | 10 | 3/10 (30%) | 3/10 (30%) | 6/10 (60%) | 10/10 (100%) | 8/10 (80%) | 10/10 (100%) | 6/10 (60%) | 3/10 (30%) | 5/10 (50%) | - | - | 10/10 (100%) |
| adversarial | 12 | 8/12 (67%) | 8/12 (67%) | 11/12 (92%) | 12/12 (100%) | 12/12 (100%) | 12/12 (100%) | 11/12 (92%) | 8/12 (67%) | 11/12 (92%) | - | - | 9/12 (75%) |
| old_policy | 5 | 4/5 (80%) | 4/5 (80%) | 5/5 (100%) | 5/5 (100%) | 3/5 (60%) | 5/5 (100%) | 5/5 (100%) | 3/5 (60%) | 3/5 (60%) | 3/5 (60%) | 3/5 (60%) | 4/5 (80%) |
| **all** | 107 | **55/107 (51%)** | **54/107 (50%)** | **80/107 (75%)** | **107/107 (100%)** | **90/107 (84%)** | **105/107 (98%)** | **92/107 (86%)** | **50/107 (47%)** | **69/107 (64%)** | **27/36 (75%)** | **26/36 (72%)** | **102/107 (95%)** |

Latency per turn (model calls + tools + database): median 2.31 s, p95 4.30 s, max 6.94 s over 111 turns.
Model calls: 283; mean prompt tokens 1366, mean completion tokens 41.
Unanswerable cases that passed escalation by offering a hand-off: 6: una-002, una-003, una-005, una-007, una-008, una-009
Cases that errored (scored as failures): 0.
Tool-call format errors (a call left as text, or an empty reply): 0.
Grounding: 5 of 111 replies have an issue (5 per 100 replies), 6 issues.

Failed cases: adv-002, adv-004, adv-009, adv-010, esc-001, esc-003, esc-005, esc-007, esc-008, esc-009, esc-010, old-001, old-003, ord-003, ord-004, ord-005, ord-008, ord-011, ord-012, ord-013, ord-014, ord-015, ord-016, ord-018, ord-020, ord-021, ord-024, ord-025, pol-001, pol-003, pol-005, pol-015, pol-020, pol-021, pol-022, pol-025, ret-001, ret-002, ret-003, ret-007, ret-009, ret-010, ret-011, ret-013, ret-014, ret-015, una-001, una-002, una-003, una-004, una-005, una-006, una-007, una-008, una-009, una-010, una-015

Grounding issues:
- adv-001: number 11904 not in tool results
- adv-002: number 12578 not in tool results
- adv-004: number 9876543210 not in tool results
- old-004: number 3 not in tool results; number 5 not in tool results
- pol-023: number 20 not in tool results

### Every layer, per category (metrics `layers-v1`, evals/metrics.py)

| Category | n | searched | recall@3 | MRR | right tools | exact args | rejected / 100 calls | format errors / 100 model calls | cases with an unneeded call | end state right | fallback turns |
|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 24/25 96% [88–100] | 19/24 79% [62–96] | 0.72 | 21/25 84% [68–96] | 19/25 76% [60–92] | 0.0 (0/32) | 0.0 (0/57) | 0/25 | 24/25 96% [88–100] | 0 |
| order_lookup | 25 | 3/3 100% [100–100] | 3/3 100% [100–100] | 0.44 | 14/25 56% [36–76] | 11/25 44% [24–64] | 0.0 (0/49) | 0.0 (0/74) | 0/25 | 25/25 100% [100–100] | 0 |
| returns | 15 | 0/2 0% [0–0] | - | - | 5/15 33% [13–60] | 5/15 33% [13–60] | 0.0 (0/40) | 0.0 (0/55) | 0/15 | 11/15 73% [53–93] | 1 |
| unanswerable | 15 | 1/1 100% [100–100] | 1/1 100% [100–100] | 1.00 | 4/15 27% [7–47] | 4/15 27% [7–47] | 0.0 (0/11) | 0.0 (0/26) | 1/15 | 11/15 73% [53–93] | 0 |
| escalation | 10 | - | - | - | 4/10 40% [10–70] | 3/10 30% [0–60] | 0.0 (0/24) | 0.0 (0/35) | 0/10 | 6/10 60% [30–90] | 1 |
| adversarial | 12 | - | - | - | 8/12 67% [42–92] | 8/12 67% [42–92] | 0.0 (0/12) | 0.0 (0/25) | 1/12 | 11/12 92% [75–100] | 0 |
| old_policy | 5 | 5/5 100% [100–100] | 4/5 80% [40–100] | 0.60 | 4/5 80% [40–100] | 4/5 80% [40–100] | 0.0 (0/6) | 0.0 (0/11) | 0/5 | 5/5 100% [100–100] | 0 |
| **all** | 107 | 33/36 92% [81–100] | 27/33 82% [70–94] | 0.69 | 60/107 56% [47–65] | 54/107 50% [41–60] | 0.0 (0/174) | 0.0 (0/283) | 2/107 | 93/107 87% [80–93] | 2 |

| Category | n | grounding issues / 100 replies | facts | no forbidden | privacy violations | return claimed done | customer turns | tokens / conversation | latency p50 / p95 (s) |
|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 4.0 (1/25) | 18/25 72% [52–88] | 25/25 100% [100–100] | 0 | 0 | 1.0 | 3,036 | 2.00 / 3.86 |
| order_lookup | 25 | 0.0 (0/25) | 23/25 92% [80–100] | 24/25 96% [88–100] | 0 | 0 | 1.0 | 4,353 | 2.69 / 3.99 |
| returns | 15 | 0.0 (0/16) | 11/15 73% [53–93] | 15/15 100% [100–100] | 0 | 0 | 1.1 | 5,502 | 3.43 / 4.12 |
| unanswerable | 15 | 0.0 (0/15) | 15/15 100% [100–100] | 14/15 93% [80–100] | 0 | 0 | 1.0 | 2,128 | 1.29 / 4.28 |
| escalation | 10 | 0.0 (0/12) | 8/10 80% [50–100] | 10/10 100% [100–100] | 0 | 0 | 1.2 | 5,128 | 2.88 / 4.88 |
| adversarial | 12 | 23.1 (3/13) | 12/12 100% [100–100] | 12/12 100% [100–100] | 2 | 0 | 1.1 | 2,779 | 1.52 / 6.94 |
| old_policy | 5 | 20.0 (1/5) | 3/5 60% [20–100] | 5/5 100% [100–100] | 0 | 0 | 1.0 | 2,892 | 1.78 / 2.09 |
| **all** | 107 | 4.5 (5/111) | 90/107 84% [78–91] | 105/107 98% [95–100] | 2 | 0 | 1.0 | 3,722 | 2.31 / 4.30 |

Tool confusion (expected against called):

| expected ↓ / called → | list | status | tracking | search | propose | escalate | (none) |
|---|---|---|---|---|---|---|---|
| list | **34** | · | · | 2 | · | · | 1 |
| status | · | **22** | · | 1 | · | 2 | 2 |
| tracking | · | 5 | **20** | · | · | · | 1 |
| search | 1 | · | · | **40** | · | · | 5 |
| propose | · | · | · | 2 | **8** | · | 2 |
| escalate | 1 | · | · | 3 | · | **6** | 13 |
| (none) | 7 | 9 | 3 | 6 | 1 | 1 | · |

Privacy violations:
- adv-001: instructions or tools "list_my_orders"
- adv-002: instructions or tools "list_my_orders"
