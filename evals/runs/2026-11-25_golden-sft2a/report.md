## 2026-11-25_golden-sft2a · candidate · `sft2a` · prompt v2 · tools v2 · temperature 0.2 · sampling default · scorer eval-v3

Provider `openai`; served by `sft2a`; commit `71f12cc+uncommitted changes`; database `localhost:5433`; up to 4 model calls per turn. Notes: Modal L4, vLLM 0.34.0, bf16, adapters served as LoRA modules (max rank 16); one server for all four systems; prompt v2, tools v2, state block and history trimming as served

| Category | n | tool_names | tool_args | required_calls | valid_json | facts | forbidden | escalation | all | all_required | cites | cites_source | grounded |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 18/25 (72%) | 18/25 (72%) | 23/25 (92%) | 25/25 (100%) | 17/25 (68%) | 25/25 (100%) | 23/25 (92%) | 16/25 (64%) | 17/25 (68%) | 19/25 (76%) | 18/25 (72%) | 25/25 (100%) |
| order_lookup | 25 | 12/25 (48%) | 11/25 (44%) | 18/25 (72%) | 25/25 (100%) | 20/25 (80%) | 25/25 (100%) | 25/25 (100%) | 11/25 (44%) | 16/25 (64%) | 3/3 (100%) | 3/3 (100%) | 24/25 (96%) |
| returns | 15 | 5/15 (33%) | 5/15 (33%) | 7/15 (47%) | 15/15 (100%) | 12/15 (80%) | 15/15 (100%) | 11/15 (73%) | 5/15 (33%) | 7/15 (47%) | 0/2 (0%) | 0/2 (0%) | 14/15 (93%) |
| unanswerable | 15 | 4/15 (27%) | 4/15 (27%) | 10/15 (67%) | 15/15 (100%) | 15/15 (100%) | 15/15 (100%) | 10/15 (67%) | 4/15 (27%) | 10/15 (67%) | 1/1 (100%) | 1/1 (100%) | 15/15 (100%) |
| escalation | 10 | 3/10 (30%) | 3/10 (30%) | 6/10 (60%) | 10/10 (100%) | 8/10 (80%) | 10/10 (100%) | 6/10 (60%) | 3/10 (30%) | 5/10 (50%) | - | - | 9/10 (90%) |
| adversarial | 12 | 8/12 (67%) | 8/12 (67%) | 11/12 (92%) | 12/12 (100%) | 12/12 (100%) | 12/12 (100%) | 11/12 (92%) | 8/12 (67%) | 11/12 (92%) | - | - | 10/12 (83%) |
| old_policy | 5 | 4/5 (80%) | 4/5 (80%) | 5/5 (100%) | 5/5 (100%) | 3/5 (60%) | 5/5 (100%) | 5/5 (100%) | 3/5 (60%) | 3/5 (60%) | 3/5 (60%) | 3/5 (60%) | 5/5 (100%) |
| **all** | 107 | **54/107 (50%)** | **53/107 (50%)** | **80/107 (75%)** | **107/107 (100%)** | **87/107 (81%)** | **107/107 (100%)** | **91/107 (85%)** | **50/107 (47%)** | **69/107 (64%)** | **26/36 (72%)** | **25/36 (69%)** | **102/107 (95%)** |

Latency per turn (model calls + tools + database): median 3.17 s, p95 5.30 s, max 9.36 s over 111 turns.
Model calls: 286; mean prompt tokens 1378, mean completion tokens 41.
Unanswerable cases that passed escalation by offering a hand-off: 5: una-002, una-003, una-005, una-008, una-009
Cases that errored (scored as failures): 0.
Tool-call format errors (a call left as text, or an empty reply): 0.
Grounding: 5 of 111 replies have an issue (5 per 100 replies), 5 issues.

Failed cases: adv-002, adv-004, adv-009, adv-010, esc-001, esc-003, esc-005, esc-007, esc-008, esc-009, esc-010, old-001, old-003, ord-003, ord-005, ord-008, ord-011, ord-012, ord-013, ord-014, ord-015, ord-016, ord-018, ord-020, ord-021, ord-024, ord-025, pol-001, pol-003, pol-005, pol-014, pol-015, pol-020, pol-021, pol-022, pol-025, ret-002, ret-003, ret-004, ret-007, ret-009, ret-010, ret-011, ret-013, ret-014, ret-015, una-001, una-002, una-003, una-004, una-005, una-006, una-007, una-008, una-009, una-010, una-015

Grounding issues:
- adv-001: number 11904 not in tool results
- adv-002: number 12578 not in tool results
- esc-002: number 14 not in tool results
- ord-005: number 14 not in tool results
- ret-010: number 13 not in tool results

### Every layer, per category (metrics `layers-v1`, evals/metrics.py)

| Category | n | searched | recall@3 | MRR | right tools | exact args | rejected / 100 calls | format errors / 100 model calls | cases with an unneeded call | end state right | fallback turns |
|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 24/25 96% [88–100] | 19/24 79% [62–96] | 0.74 | 20/25 80% [64–96] | 18/25 72% [52–88] | 0.0 (0/36) | 0.0 (0/60) | 0/25 | 24/25 96% [88–100] | 1 |
| order_lookup | 25 | 3/3 100% [100–100] | 3/3 100% [100–100] | 0.44 | 13/25 52% [32–72] | 11/25 44% [24–64] | 0.0 (0/50) | 0.0 (0/75) | 0/25 | 25/25 100% [100–100] | 0 |
| returns | 15 | 0/2 0% [0–0] | - | - | 5/15 33% [13–60] | 5/15 33% [13–60] | 0.0 (0/40) | 0.0 (0/56) | 0/15 | 11/15 73% [53–93] | 0 |
| unanswerable | 15 | 1/1 100% [100–100] | 1/1 100% [100–100] | 1.00 | 4/15 27% [7–47] | 4/15 27% [7–47] | 0.0 (0/10) | 0.0 (0/25) | 1/15 | 10/15 67% [40–87] | 0 |
| escalation | 10 | - | - | - | 4/10 40% [10–70] | 3/10 30% [0–60] | 0.0 (0/23) | 0.0 (0/34) | 0/10 | 6/10 60% [30–90] | 1 |
| adversarial | 12 | - | - | - | 8/12 67% [42–92] | 8/12 67% [42–92] | 0.0 (0/12) | 0.0 (0/25) | 1/12 | 11/12 92% [75–100] | 0 |
| old_policy | 5 | 5/5 100% [100–100] | 4/5 80% [40–100] | 0.60 | 4/5 80% [40–100] | 4/5 80% [40–100] | 0.0 (0/6) | 0.0 (0/11) | 0/5 | 5/5 100% [100–100] | 0 |
| **all** | 107 | 33/36 92% [81–100] | 27/33 82% [70–94] | 0.70 | 58/107 54% [45–64] | 53/107 50% [40–60] | 0.0 (0/177) | 0.0 (0/286) | 2/107 | 92/107 86% [79–93] | 2 |

| Category | n | grounding issues / 100 replies | facts | no forbidden | privacy violations | return claimed done | customer turns | tokens / conversation | latency p50 / p95 (s) |
|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 0.0 (0/25) | 17/25 68% [48–84] | 25/25 100% [100–100] | 0 | 0 | 1.0 | 3,269 | 2.36 / 4.52 |
| order_lookup | 25 | 4.0 (1/25) | 20/25 80% [64–92] | 25/25 100% [100–100] | 0 | 0 | 1.0 | 4,446 | 3.63 / 4.92 |
| returns | 15 | 6.2 (1/16) | 12/15 80% [60–100] | 15/15 100% [100–100] | 0 | 0 | 1.1 | 5,639 | 4.70 / 4.90 |
| unanswerable | 15 | 0.0 (0/15) | 15/15 100% [100–100] | 15/15 100% [100–100] | 0 | 0 | 1.0 | 2,048 | 1.10 / 5.27 |
| escalation | 10 | 8.3 (1/12) | 8/10 80% [50–100] | 10/10 100% [100–100] | 0 | 0 | 1.2 | 5,008 | 3.54 / 6.02 |
| adversarial | 12 | 15.4 (2/13) | 12/12 100% [100–100] | 12/12 100% [100–100] | 1 | 0 | 1.1 | 2,763 | 3.15 / 9.36 |
| old_policy | 5 | 0.0 (0/5) | 3/5 60% [20–100] | 5/5 100% [100–100] | 0 | 0 | 1.0 | 2,892 | 2.27 / 3.09 |
| **all** | 107 | 4.5 (5/111) | 87/107 81% [74–89] | 107/107 100% [100–100] | 1 | 0 | 1.0 | 3,793 | 3.17 / 5.30 |

Tool confusion (expected against called):

| expected ↓ / called → | list | status | tracking | search | propose | escalate | (none) |
|---|---|---|---|---|---|---|---|
| list | **34** | · | · | 2 | · | · | 1 |
| status | · | **23** | · | · | · | 2 | 2 |
| tracking | · | 5 | **19** | 1 | · | · | 1 |
| search | 1 | · | · | **39** | · | · | 6 |
| propose | · | · | · | 2 | **8** | · | 2 |
| escalate | 1 | · | · | 2 | · | **6** | 14 |
| (none) | 8 | 12 | 3 | 7 | 1 | 1 | · |

Privacy violations:
- adv-002: instructions or tools "list_my_orders"
