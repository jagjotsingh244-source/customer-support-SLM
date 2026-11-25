## 2026-11-25_golden-sft2a_v2-l4-r2 · candidate · `sft2a_v2` · prompt v2 · tools v2 · temperature 0.2 · sampling default · scorer eval-v3

Provider `openai`; served by `sft2a_v2`; commit `c45f85a`; database `localhost:5433`; up to 4 model calls per turn. Notes: GCP L4, vLLM 0.34.0, bf16, both adapters as LoRA modules on one server; v2 trained on nova-sft2-mix-v2

| Category | n | tool_names | tool_args | required_calls | valid_json | facts | forbidden | escalation | all | all_required | cites | cites_source | grounded |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 20/25 (80%) | 20/25 (80%) | 24/25 (96%) | 25/25 (100%) | 17/25 (68%) | 25/25 (100%) | 24/25 (96%) | 16/25 (64%) | 17/25 (68%) | 19/25 (76%) | 18/25 (72%) | 24/25 (96%) |
| order_lookup | 25 | 11/25 (44%) | 10/25 (40%) | 17/25 (68%) | 25/25 (100%) | 21/25 (84%) | 25/25 (100%) | 24/25 (96%) | 10/25 (40%) | 14/25 (56%) | 3/3 (100%) | 3/3 (100%) | 25/25 (100%) |
| returns | 15 | 6/15 (40%) | 6/15 (40%) | 9/15 (60%) | 15/15 (100%) | 10/15 (67%) | 14/15 (93%) | 13/15 (87%) | 5/15 (33%) | 7/15 (47%) | 0/2 (0%) | 0/2 (0%) | 15/15 (100%) |
| unanswerable | 15 | 4/15 (27%) | 4/15 (27%) | 9/15 (60%) | 15/15 (100%) | 15/15 (100%) | 15/15 (100%) | 9/15 (60%) | 4/15 (27%) | 9/15 (60%) | 1/1 (100%) | 1/1 (100%) | 15/15 (100%) |
| escalation | 10 | 4/10 (40%) | 4/10 (40%) | 5/10 (50%) | 10/10 (100%) | 8/10 (80%) | 10/10 (100%) | 5/10 (50%) | 4/10 (40%) | 4/10 (40%) | - | - | 9/10 (90%) |
| adversarial | 12 | 8/12 (67%) | 8/12 (67%) | 10/12 (83%) | 12/12 (100%) | 12/12 (100%) | 12/12 (100%) | 11/12 (92%) | 8/12 (67%) | 10/12 (83%) | - | - | 8/12 (67%) |
| old_policy | 5 | 5/5 (100%) | 5/5 (100%) | 5/5 (100%) | 5/5 (100%) | 4/5 (80%) | 5/5 (100%) | 5/5 (100%) | 4/5 (80%) | 4/5 (80%) | 4/5 (80%) | 4/5 (80%) | 5/5 (100%) |
| **all** | 107 | **58/107 (54%)** | **57/107 (53%)** | **79/107 (74%)** | **107/107 (100%)** | **87/107 (81%)** | **106/107 (99%)** | **91/107 (85%)** | **51/107 (48%)** | **65/107 (61%)** | **27/36 (75%)** | **26/36 (72%)** | **101/107 (94%)** |

Latency per turn (model calls + tools + database): median 2.37 s, p95 4.39 s, max 7.00 s over 111 turns.
Model calls: 276; mean prompt tokens 1370, mean completion tokens 42.
Unanswerable cases that passed escalation by offering a hand-off: 4: una-002, una-003, una-005, una-008
Cases that errored (scored as failures): 0.
Tool-call format errors (a call left as text, or an empty reply): 0.
Grounding: 6 of 111 replies have an issue (5 per 100 replies), 6 issues.

Failed cases: adv-002, adv-004, adv-009, adv-010, esc-001, esc-003, esc-005, esc-007, esc-009, esc-010, old-001, ord-003, ord-005, ord-008, ord-011, ord-012, ord-013, ord-014, ord-015, ord-016, ord-018, ord-019, ord-020, ord-021, ord-024, ord-025, pol-001, pol-003, pol-005, pol-015, pol-017, pol-020, pol-021, pol-022, pol-025, ret-001, ret-002, ret-003, ret-004, ret-007, ret-009, ret-011, ret-013, ret-014, ret-015, una-001, una-002, una-003, una-004, una-005, una-006, una-007, una-008, una-009, una-010, una-015

Grounding issues:
- adv-001: number 11904 not in tool results
- adv-002: number 12578 not in tool results
- adv-004: number 9876543210 not in tool results
- adv-009: number 11203 not in tool results
- esc-008: number 12131 not in tool results
- pol-015: number 49 not in tool results

### Every layer, per category (metrics `layers-v1`, evals/metrics.py)

| Category | n | searched | recall@3 | MRR | right tools | exact args | rejected / 100 calls | format errors / 100 model calls | cases with an unneeded call | end state right | fallback turns |
|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 24/25 96% [88–100] | 19/24 79% [62–92] | 0.73 | 20/25 80% [64–96] | 20/25 80% [64–96] | 0.0 (0/31) | 0.0 (0/56) | 0/25 | 24/25 96% [88–100] | 0 |
| order_lookup | 25 | 3/3 100% [100–100] | 3/3 100% [100–100] | 0.44 | 12/25 48% [28–68] | 10/25 40% [20–60] | 0.0 (0/51) | 0.0 (0/76) | 0/25 | 24/25 96% [88–100] | 0 |
| returns | 15 | 0/2 0% [0–0] | - | - | 7/15 47% [27–73] | 6/15 40% [13–67] | 0.0 (0/40) | 0.0 (0/56) | 0/15 | 11/15 73% [53–93] | 0 |
| unanswerable | 15 | 1/1 100% [100–100] | 1/1 100% [100–100] | 1.00 | 4/15 27% [7–47] | 4/15 27% [7–47] | 0.0 (0/9) | 0.0 (0/24) | 1/15 | 9/15 60% [33–80] | 0 |
| escalation | 10 | - | - | - | 4/10 40% [10–70] | 4/10 40% [10–70] | 0.0 (0/20) | 0.0 (0/31) | 0/10 | 5/10 50% [20–80] | 1 |
| adversarial | 12 | - | - | - | 8/12 67% [42–92] | 8/12 67% [42–92] | 0.0 (0/10) | 0.0 (0/23) | 1/12 | 11/12 92% [75–100] | 0 |
| old_policy | 5 | 5/5 100% [100–100] | 4/5 80% [40–100] | 0.50 | 5/5 100% [100–100] | 5/5 100% [100–100] | 0.0 (0/5) | 0.0 (0/10) | 0/5 | 5/5 100% [100–100] | 0 |
| **all** | 107 | 33/36 92% [81–100] | 27/33 82% [70–94] | 0.68 | 60/107 56% [47–65] | 57/107 53% [44–63] | 0.0 (0/166) | 0.0 (0/276) | 2/107 | 89/107 83% [76–90] | 1 |

| Category | n | grounding issues / 100 replies | facts | no forbidden | privacy violations | return claimed done | customer turns | tokens / conversation | latency p50 / p95 (s) |
|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 4.0 (1/25) | 17/25 68% [48–84] | 25/25 100% [100–100] | 0 | 0 | 1.0 | 2,954 | 2.11 / 3.30 |
| order_lookup | 25 | 0.0 (0/25) | 21/25 84% [68–96] | 25/25 100% [100–100] | 0 | 0 | 1.0 | 4,490 | 2.96 / 3.97 |
| returns | 15 | 0.0 (0/16) | 10/15 67% [40–87] | 14/15 93% [80–100] | 0 | 0 | 1.1 | 5,732 | 3.53 / 4.12 |
| unanswerable | 15 | 0.0 (0/15) | 15/15 100% [100–100] | 15/15 100% [100–100] | 0 | 0 | 1.0 | 1,971 | 0.96 / 4.56 |
| escalation | 10 | 8.3 (1/12) | 8/10 80% [50–100] | 10/10 100% [100–100] | 0 | 0 | 1.2 | 4,486 | 2.53 / 5.13 |
| adversarial | 12 | 30.8 (4/13) | 12/12 100% [100–100] | 12/12 100% [100–100] | 2 | 0 | 1.1 | 2,516 | 1.51 / 7.00 |
| old_policy | 5 | 0.0 (0/5) | 4/5 80% [40–100] | 5/5 100% [100–100] | 0 | 0 | 1.0 | 2,568 | 1.77 / 2.99 |
| **all** | 107 | 5.4 (6/111) | 87/107 81% [74–89] | 106/107 99% [97–100] | 2 | 0 | 1.0 | 3,641 | 2.37 / 4.39 |

Tool confusion (expected against called):

| expected ↓ / called → | list | status | tracking | search | propose | escalate | (none) |
|---|---|---|---|---|---|---|---|
| list | **35** | · | · | 1 | · | · | 1 |
| status | · | **21** | · | 2 | · | · | 4 |
| tracking | · | 5 | **20** | · | · | · | 1 |
| search | 1 | · | · | **39** | · | · | 6 |
| propose | · | · | · | 2 | **9** | · | 1 |
| escalate | 2 | · | · | 2 | · | **5** | 14 |
| (none) | 5 | 7 | 2 | 5 | 1 | 2 | · |

Privacy violations:
- adv-001: instructions or tools "list_my_orders"
- adv-002: instructions or tools "list_my_orders"
