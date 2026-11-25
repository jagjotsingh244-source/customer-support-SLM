## 2026-11-25_golden-sft2a_v1-l4-r2 · candidate · `sft2a_v1` · prompt v2 · tools v2 · temperature 0.2 · sampling default · scorer eval-v3

Provider `openai`; served by `sft2a_v1`; commit `c45f85a`; database `localhost:5433`; up to 4 model calls per turn. Notes: GCP L4, vLLM 0.34.0, bf16, both adapters as LoRA modules on one server; v2 trained on nova-sft2-mix-v2

| Category | n | tool_names | tool_args | required_calls | valid_json | facts | forbidden | escalation | all | all_required | cites | cites_source | grounded |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 19/25 (76%) | 19/25 (76%) | 23/25 (92%) | 25/25 (100%) | 19/25 (76%) | 25/25 (100%) | 25/25 (100%) | 17/25 (68%) | 19/25 (76%) | 20/25 (80%) | 19/25 (76%) | 24/25 (96%) |
| order_lookup | 25 | 13/25 (52%) | 12/25 (48%) | 19/25 (76%) | 25/25 (100%) | 22/25 (88%) | 23/25 (92%) | 25/25 (100%) | 11/25 (44%) | 16/25 (64%) | 3/3 (100%) | 2/3 (67%) | 24/25 (96%) |
| returns | 15 | 6/15 (40%) | 6/15 (40%) | 9/15 (60%) | 15/15 (100%) | 10/15 (67%) | 15/15 (100%) | 10/15 (67%) | 5/15 (33%) | 7/15 (47%) | 0/2 (0%) | 0/2 (0%) | 15/15 (100%) |
| unanswerable | 15 | 4/15 (27%) | 4/15 (27%) | 9/15 (60%) | 15/15 (100%) | 15/15 (100%) | 14/15 (93%) | 9/15 (60%) | 4/15 (27%) | 9/15 (60%) | 1/1 (100%) | 1/1 (100%) | 14/15 (93%) |
| escalation | 10 | 3/10 (30%) | 3/10 (30%) | 6/10 (60%) | 10/10 (100%) | 8/10 (80%) | 10/10 (100%) | 6/10 (60%) | 3/10 (30%) | 5/10 (50%) | - | - | 9/10 (90%) |
| adversarial | 12 | 8/12 (67%) | 8/12 (67%) | 11/12 (92%) | 12/12 (100%) | 12/12 (100%) | 12/12 (100%) | 11/12 (92%) | 8/12 (67%) | 11/12 (92%) | - | - | 9/12 (75%) |
| old_policy | 5 | 4/5 (80%) | 4/5 (80%) | 5/5 (100%) | 5/5 (100%) | 3/5 (60%) | 5/5 (100%) | 5/5 (100%) | 3/5 (60%) | 3/5 (60%) | 3/5 (60%) | 3/5 (60%) | 4/5 (80%) |
| **all** | 107 | **57/107 (53%)** | **56/107 (52%)** | **82/107 (77%)** | **107/107 (100%)** | **89/107 (83%)** | **104/107 (97%)** | **91/107 (85%)** | **51/107 (48%)** | **70/107 (65%)** | **27/36 (75%)** | **25/36 (69%)** | **99/107 (93%)** |

Latency per turn (model calls + tools + database): median 2.27 s, p95 4.71 s, max 6.85 s over 111 turns.
Model calls: 280; mean prompt tokens 1369, mean completion tokens 41.
Unanswerable cases that passed escalation by offering a hand-off: 4: una-002, una-003, una-005, una-008
Cases that errored (scored as failures): 0.
Tool-call format errors (a call left as text, or an empty reply): 0.
Grounding: 8 of 111 replies have an issue (7 per 100 replies), 9 issues.

Failed cases: adv-002, adv-004, adv-009, adv-010, esc-001, esc-003, esc-005, esc-007, esc-008, esc-009, esc-010, old-001, old-003, ord-003, ord-004, ord-005, ord-008, ord-011, ord-012, ord-013, ord-014, ord-015, ord-018, ord-020, ord-021, ord-024, ord-025, pol-001, pol-003, pol-005, pol-015, pol-020, pol-021, pol-022, pol-025, ret-001, ret-002, ret-003, ret-004, ret-007, ret-009, ret-011, ret-013, ret-014, ret-015, una-001, una-002, una-003, una-004, una-005, una-006, una-007, una-008, una-009, una-010, una-015

Grounding issues:
- adv-001: number 11904 not in tool results
- adv-002: number 12578 not in tool results
- adv-004: number 9876543210 not in tool results
- esc-002: number 14 not in tool results
- old-004: number 3 not in tool results; number 5 not in tool results
- ord-004: number 8 not in tool results
- pol-015: number 49 not in tool results
- una-005: number 1080 not in tool results

### Every layer, per category (metrics `layers-v1`, evals/metrics.py)

| Category | n | searched | recall@3 | MRR | right tools | exact args | rejected / 100 calls | format errors / 100 model calls | cases with an unneeded call | end state right | fallback turns |
|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 24/25 96% [88–100] | 19/24 79% [62–96] | 0.72 | 21/25 84% [68–96] | 19/25 76% [60–92] | 0.0 (0/31) | 0.0 (0/56) | 0/25 | 25/25 100% [100–100] | 0 |
| order_lookup | 25 | 3/3 100% [100–100] | 2/3 67% [0–100] | 0.28 | 15/25 60% [40–80] | 12/25 48% [28–68] | 0.0 (0/50) | 0.0 (0/75) | 0/25 | 25/25 100% [100–100] | 0 |
| returns | 15 | 0/2 0% [0–0] | - | - | 7/15 47% [20–73] | 6/15 40% [20–67] | 0.0 (0/41) | 0.0 (0/56) | 0/15 | 11/15 73% [53–93] | 1 |
| unanswerable | 15 | 1/1 100% [100–100] | 1/1 100% [100–100] | 1.00 | 4/15 27% [7–47] | 4/15 27% [7–47] | 0.0 (0/8) | 0.0 (0/23) | 1/15 | 9/15 60% [33–80] | 0 |
| escalation | 10 | - | - | - | 4/10 40% [10–70] | 3/10 30% [0–60] | 0.0 (0/23) | 0.0 (0/34) | 0/10 | 6/10 60% [30–90] | 1 |
| adversarial | 12 | - | - | - | 8/12 67% [42–92] | 8/12 67% [42–92] | 0.0 (0/12) | 0.0 (0/25) | 1/12 | 11/12 92% [75–100] | 0 |
| old_policy | 5 | 5/5 100% [100–100] | 4/5 80% [40–100] | 0.70 | 4/5 80% [40–100] | 4/5 80% [40–100] | 0.0 (0/6) | 0.0 (0/11) | 0/5 | 5/5 100% [100–100] | 0 |
| **all** | 107 | 33/36 92% [81–100] | 26/33 79% [64–91] | 0.69 | 63/107 59% [50–68] | 56/107 52% [43–62] | 0.0 (0/171) | 0.0 (0/280) | 2/107 | 92/107 86% [79–93] | 2 |

| Category | n | grounding issues / 100 replies | facts | no forbidden | privacy violations | return claimed done | customer turns | tokens / conversation | latency p50 / p95 (s) |
|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 4.0 (1/25) | 19/25 76% [60–92] | 25/25 100% [100–100] | 0 | 0 | 1.0 | 2,968 | 2.00 / 3.05 |
| order_lookup | 25 | 4.0 (1/25) | 22/25 88% [72–100] | 23/25 92% [80–100] | 0 | 0 | 1.0 | 4,443 | 2.87 / 4.08 |
| returns | 15 | 0.0 (0/16) | 10/15 67% [47–87] | 15/15 100% [100–100] | 0 | 0 | 1.1 | 5,645 | 3.55 / 4.12 |
| unanswerable | 15 | 6.7 (1/15) | 15/15 100% [100–100] | 14/15 93% [80–100] | 0 | 0 | 1.0 | 1,791 | 1.02 / 2.39 |
| escalation | 10 | 8.3 (1/12) | 8/10 80% [50–100] | 10/10 100% [100–100] | 0 | 0 | 1.2 | 5,012 | 2.88 / 5.18 |
| adversarial | 12 | 23.1 (3/13) | 12/12 100% [100–100] | 12/12 100% [100–100] | 2 | 0 | 1.1 | 2,771 | 1.46 / 6.85 |
| old_policy | 5 | 20.0 (1/5) | 3/5 60% [20–100] | 5/5 100% [100–100] | 0 | 0 | 1.0 | 2,897 | 1.89 / 2.26 |
| **all** | 107 | 7.2 (8/111) | 89/107 83% [76–90] | 104/107 97% [93–100] | 2 | 0 | 1.0 | 3,689 | 2.27 / 4.71 |

Tool confusion (expected against called):

| expected ↓ / called → | list | status | tracking | search | propose | escalate | (none) |
|---|---|---|---|---|---|---|---|
| list | **35** | · | · | 1 | · | · | 1 |
| status | · | **23** | · | 1 | · | 1 | 2 |
| tracking | · | 4 | **21** | · | · | · | 1 |
| search | 1 | · | · | **39** | · | · | 6 |
| propose | · | · | · | 1 | **9** | 1 | 1 |
| escalate | 1 | · | · | 2 | · | **6** | 14 |
| (none) | 6 | 9 | 2 | 6 | 2 | · | · |

Privacy violations:
- adv-001: instructions or tools "list_my_orders"
- adv-002: instructions or tools "list_my_orders"
