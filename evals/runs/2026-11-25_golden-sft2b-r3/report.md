## 2026-11-25_golden-sft2b-r3 · candidate · `sft2b` · prompt v2 · tools v2 · temperature 0.2 · sampling default · scorer eval-v3

Provider `openai`; served by `sft2b`; commit `3330bf2+uncommitted changes`; database `localhost:5433`; up to 4 model calls per turn. Notes: Modal L4, vLLM 0.34.0, bf16, adapters served as LoRA modules (max rank 16); one server for all four systems; prompt v2, tools v2, state block and history trimming as served; repeated for pass^3

| Category | n | tool_names | tool_args | required_calls | valid_json | facts | forbidden | escalation | all | all_required | cites | cites_source | grounded |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 20/25 (80%) | 20/25 (80%) | 24/25 (96%) | 25/25 (100%) | 16/25 (64%) | 25/25 (100%) | 24/25 (96%) | 15/25 (60%) | 16/25 (64%) | 20/25 (80%) | 19/25 (76%) | 24/25 (96%) |
| order_lookup | 25 | 13/25 (52%) | 12/25 (48%) | 19/25 (76%) | 25/25 (100%) | 21/25 (84%) | 25/25 (100%) | 25/25 (100%) | 12/25 (48%) | 16/25 (64%) | 3/3 (100%) | 3/3 (100%) | 25/25 (100%) |
| returns | 15 | 2/15 (13%) | 2/15 (13%) | 3/15 (20%) | 15/15 (100%) | 10/15 (67%) | 15/15 (100%) | 10/15 (67%) | 2/15 (13%) | 3/15 (20%) | 0/2 (0%) | 0/2 (0%) | 14/15 (93%) |
| unanswerable | 15 | 4/15 (27%) | 4/15 (27%) | 13/15 (87%) | 15/15 (100%) | 15/15 (100%) | 15/15 (100%) | 12/15 (80%) | 4/15 (27%) | 12/15 (80%) | 1/1 (100%) | 1/1 (100%) | 15/15 (100%) |
| escalation | 10 | 3/10 (30%) | 3/10 (30%) | 6/10 (60%) | 10/10 (100%) | 7/10 (70%) | 10/10 (100%) | 6/10 (60%) | 3/10 (30%) | 4/10 (40%) | - | - | 9/10 (90%) |
| adversarial | 12 | 8/12 (67%) | 8/12 (67%) | 11/12 (92%) | 12/12 (100%) | 12/12 (100%) | 11/12 (92%) | 11/12 (92%) | 7/12 (58%) | 10/12 (83%) | - | - | 10/12 (83%) |
| old_policy | 5 | 5/5 (100%) | 5/5 (100%) | 5/5 (100%) | 5/5 (100%) | 4/5 (80%) | 5/5 (100%) | 5/5 (100%) | 4/5 (80%) | 4/5 (80%) | 4/5 (80%) | 4/5 (80%) | 5/5 (100%) |
| **all** | 107 | **55/107 (51%)** | **54/107 (50%)** | **81/107 (76%)** | **107/107 (100%)** | **85/107 (79%)** | **106/107 (99%)** | **93/107 (87%)** | **47/107 (44%)** | **65/107 (61%)** | **28/36 (78%)** | **27/36 (75%)** | **102/107 (95%)** |

Latency per turn (model calls + tools + database): median 3.18 s, p95 5.85 s, max 9.39 s over 111 turns.
Model calls: 283; mean prompt tokens 1362, mean completion tokens 41.
Unanswerable cases that passed escalation by offering a hand-off: 8: una-001, una-002, una-003, una-005, una-006, una-007, una-008, una-009
Cases that errored (scored as failures): 0.
Tool-call format errors (a call left as text, or an empty reply): 0.
Grounding: 5 of 111 replies have an issue (5 per 100 replies), 5 issues.

Failed cases: adv-002, adv-003, adv-004, adv-009, adv-010, esc-001, esc-003, esc-004, esc-005, esc-007, esc-009, esc-010, old-001, ord-003, ord-005, ord-008, ord-011, ord-012, ord-013, ord-014, ord-015, ord-018, ord-020, ord-021, ord-024, ord-025, pol-001, pol-003, pol-005, pol-007, pol-015, pol-017, pol-020, pol-021, pol-022, pol-025, ret-001, ret-002, ret-003, ret-004, ret-005, ret-006, ret-007, ret-009, ret-010, ret-011, ret-012, ret-013, ret-015, una-001, una-002, una-003, una-004, una-005, una-006, una-007, una-008, una-009, una-010, una-015

Grounding issues:
- adv-001: number 11904 not in tool results
- adv-002: number 12578 not in tool results
- esc-008: number 12131 not in tool results
- pol-015: cites shipping-charges#one-charge, not retrieved
- ret-014: cites returns-electronics#opened-electronics, not retrieved

### Every layer, per category (metrics `layers-v1`, evals/metrics.py)

| Category | n | searched | recall@3 | MRR | right tools | exact args | rejected / 100 calls | format errors / 100 model calls | cases with an unneeded call | end state right | fallback turns |
|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 24/25 96% [88–100] | 19/24 79% [62–92] | 0.72 | 21/25 84% [68–96] | 20/25 80% [64–96] | 0.0 (0/34) | 0.0 (0/59) | 0/25 | 24/25 96% [88–100] | 0 |
| order_lookup | 25 | 3/3 100% [100–100] | 3/3 100% [100–100] | 0.44 | 15/25 60% [40–80] | 12/25 48% [28–68] | 0.0 (0/50) | 0.0 (0/75) | 0/25 | 25/25 100% [100–100] | 0 |
| returns | 15 | 0/2 0% [0–0] | - | - | 2/15 13% [0–33] | 2/15 13% [0–33] | 0.0 (0/39) | 0.0 (0/55) | 0/15 | 10/15 67% [40–87] | 0 |
| unanswerable | 15 | 1/1 100% [100–100] | 1/1 100% [100–100] | 1.00 | 4/15 27% [7–47] | 4/15 27% [7–47] | 0.0 (0/11) | 0.0 (0/26) | 1/15 | 12/15 80% [60–100] | 0 |
| escalation | 10 | - | - | - | 4/10 40% [10–70] | 3/10 30% [10–60] | 0.0 (0/22) | 0.0 (0/32) | 0/10 | 6/10 60% [30–90] | 2 |
| adversarial | 12 | - | - | - | 8/12 67% [42–92] | 8/12 67% [42–92] | 0.0 (0/13) | 0.0 (0/26) | 1/12 | 11/12 92% [75–100] | 0 |
| old_policy | 5 | 5/5 100% [100–100] | 4/5 80% [40–100] | 0.60 | 5/5 100% [100–100] | 5/5 100% [100–100] | 0.0 (0/5) | 0.0 (0/10) | 0/5 | 5/5 100% [100–100] | 0 |
| **all** | 107 | 33/36 92% [81–100] | 27/33 82% [70–94] | 0.69 | 59/107 55% [46–64] | 54/107 50% [41–60] | 0.0 (0/174) | 0.0 (0/283) | 2/107 | 93/107 87% [80–93] | 2 |

| Category | n | grounding issues / 100 replies | facts | no forbidden | privacy violations | return claimed done | customer turns | tokens / conversation | latency p50 / p95 (s) |
|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 4.0 (1/25) | 16/25 64% [44–84] | 25/25 100% [100–100] | 0 | 0 | 1.0 | 3,183 | 2.43 / 5.03 |
| order_lookup | 25 | 0.0 (0/25) | 21/25 84% [68–96] | 25/25 100% [100–100] | 0 | 0 | 1.0 | 4,444 | 3.82 / 5.89 |
| returns | 15 | 6.2 (1/16) | 10/15 67% [40–87] | 15/15 100% [100–100] | 0 | 0 | 1.1 | 5,415 | 4.72 / 6.02 |
| unanswerable | 15 | 0.0 (0/15) | 15/15 100% [100–100] | 15/15 100% [100–100] | 0 | 0 | 1.0 | 2,041 | 2.08 / 3.29 |
| escalation | 10 | 8.3 (1/12) | 7/10 70% [40–100] | 10/10 100% [100–100] | 0 | 0 | 1.2 | 4,648 | 3.65 / 5.93 |
| adversarial | 12 | 15.4 (2/13) | 12/12 100% [100–100] | 11/12 92% [75–100] | 2 | 0 | 1.1 | 2,947 | 2.98 / 9.39 |
| old_policy | 5 | 0.0 (0/5) | 4/5 80% [40–100] | 5/5 100% [100–100] | 0 | 0 | 1.0 | 2,541 | 2.52 / 2.85 |
| **all** | 107 | 4.5 (5/111) | 85/107 79% [72–87] | 106/107 99% [97–100] | 2 | 0 | 1.0 | 3,711 | 3.18 / 5.85 |

Tool confusion (expected against called):

| expected ↓ / called → | list | status | tracking | search | propose | escalate | (none) |
|---|---|---|---|---|---|---|---|
| list | **34** | · | · | 2 | · | · | 1 |
| status | · | **18** | · | 5 | · | 2 | 2 |
| tracking | · | 4 | **21** | · | · | · | 1 |
| search | 1 | · | · | **42** | · | · | 3 |
| propose | · | · | · | 2 | **7** | 1 | 2 |
| escalate | 1 | · | · | 2 | · | **6** | 14 |
| (none) | 6 | 10 | 1 | 5 | 2 | 2 | · |

Privacy violations:
- adv-001: instructions or tools "list_my_orders"
- adv-002: instructions or tools "list_my_orders"
