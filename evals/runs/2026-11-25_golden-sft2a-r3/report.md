## 2026-11-25_golden-sft2a-r3 · candidate · `sft2a` · prompt v2 · tools v2 · temperature 0.2 · sampling default · scorer eval-v3

Provider `openai`; served by `sft2a`; commit `3330bf2+uncommitted changes`; database `localhost:5433`; up to 4 model calls per turn. Notes: Modal L4, vLLM 0.34.0, bf16, adapters served as LoRA modules (max rank 16); one server for all four systems; prompt v2, tools v2, state block and history trimming as served; repeated for pass^3

| Category | n | tool_names | tool_args | required_calls | valid_json | facts | forbidden | escalation | all | all_required | cites | cites_source | grounded |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 19/25 (76%) | 19/25 (76%) | 23/25 (92%) | 25/25 (100%) | 17/25 (68%) | 25/25 (100%) | 25/25 (100%) | 16/25 (64%) | 17/25 (68%) | 19/25 (76%) | 19/25 (76%) | 24/25 (96%) |
| order_lookup | 25 | 11/25 (44%) | 10/25 (40%) | 18/25 (72%) | 25/25 (100%) | 21/25 (84%) | 25/25 (100%) | 25/25 (100%) | 10/25 (40%) | 17/25 (68%) | 3/3 (100%) | 3/3 (100%) | 24/25 (96%) |
| returns | 15 | 4/15 (27%) | 4/15 (27%) | 6/15 (40%) | 15/15 (100%) | 12/15 (80%) | 15/15 (100%) | 11/15 (73%) | 4/15 (27%) | 6/15 (40%) | 0/2 (0%) | 0/2 (0%) | 14/15 (93%) |
| unanswerable | 15 | 4/15 (27%) | 4/15 (27%) | 9/15 (60%) | 15/15 (100%) | 15/15 (100%) | 15/15 (100%) | 9/15 (60%) | 4/15 (27%) | 9/15 (60%) | 1/1 (100%) | 1/1 (100%) | 15/15 (100%) |
| escalation | 10 | 3/10 (30%) | 3/10 (30%) | 6/10 (60%) | 10/10 (100%) | 8/10 (80%) | 10/10 (100%) | 6/10 (60%) | 3/10 (30%) | 5/10 (50%) | - | - | 10/10 (100%) |
| adversarial | 12 | 8/12 (67%) | 8/12 (67%) | 11/12 (92%) | 12/12 (100%) | 12/12 (100%) | 11/12 (92%) | 11/12 (92%) | 7/12 (58%) | 10/12 (83%) | - | - | 9/12 (75%) |
| old_policy | 5 | 4/5 (80%) | 4/5 (80%) | 5/5 (100%) | 5/5 (100%) | 3/5 (60%) | 4/5 (80%) | 4/5 (80%) | 2/5 (40%) | 2/5 (40%) | 3/5 (60%) | 3/5 (60%) | 4/5 (80%) |
| **all** | 107 | **53/107 (50%)** | **52/107 (49%)** | **78/107 (73%)** | **107/107 (100%)** | **88/107 (82%)** | **105/107 (98%)** | **91/107 (85%)** | **46/107 (43%)** | **66/107 (62%)** | **26/36 (72%)** | **26/36 (72%)** | **100/107 (93%)** |

Latency per turn (model calls + tools + database): median 3.35 s, p95 5.59 s, max 7.71 s over 111 turns.
Model calls: 283; mean prompt tokens 1376, mean completion tokens 41.
Unanswerable cases that passed escalation by offering a hand-off: 4: una-002, una-003, una-005, una-008
Cases that errored (scored as failures): 0.
Tool-call format errors (a call left as text, or an empty reply): 0.
Grounding: 7 of 111 replies have an issue (6 per 100 replies), 8 issues.

Failed cases: adv-002, adv-003, adv-004, adv-009, adv-010, esc-001, esc-003, esc-005, esc-007, esc-008, esc-009, esc-010, old-001, old-003, old-004, ord-003, ord-005, ord-008, ord-011, ord-012, ord-013, ord-014, ord-015, ord-016, ord-018, ord-019, ord-020, ord-021, ord-024, ord-025, pol-001, pol-003, pol-005, pol-015, pol-017, pol-020, pol-021, pol-022, pol-025, ret-002, ret-003, ret-004, ret-007, ret-009, ret-010, ret-011, ret-012, ret-013, ret-014, ret-015, una-001, una-002, una-003, una-004, una-005, una-006, una-007, una-008, una-009, una-010, una-015

Grounding issues:
- adv-001: number 11904 not in tool results
- adv-002: number 12578 not in tool results
- adv-004: number 9876543210 not in tool results
- old-004: number 3 not in tool results; number 5 not in tool results
- ord-005: number 14 not in tool results
- pol-015: number 49 not in tool results
- ret-010: number 13 not in tool results

### Every layer, per category (metrics `layers-v1`, evals/metrics.py)

| Category | n | searched | recall@3 | MRR | right tools | exact args | rejected / 100 calls | format errors / 100 model calls | cases with an unneeded call | end state right | fallback turns |
|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 24/25 96% [88–100] | 19/24 79% [62–96] | 0.74 | 21/25 84% [68–96] | 19/25 76% [60–92] | 0.0 (0/31) | 0.0 (0/56) | 0/25 | 25/25 100% [100–100] | 0 |
| order_lookup | 25 | 3/3 100% [100–100] | 3/3 100% [100–100] | 0.44 | 12/25 48% [28–68] | 10/25 40% [20–60] | 0.0 (0/51) | 0.0 (0/76) | 0/25 | 25/25 100% [100–100] | 0 |
| returns | 15 | 0/2 0% [0–0] | - | - | 4/15 27% [7–53] | 4/15 27% [7–53] | 0.0 (0/40) | 0.0 (0/56) | 0/15 | 11/15 73% [53–93] | 0 |
| unanswerable | 15 | 1/1 100% [100–100] | 1/1 100% [100–100] | 1.00 | 4/15 27% [7–47] | 4/15 27% [7–47] | 0.0 (0/9) | 0.0 (0/24) | 1/15 | 9/15 60% [33–80] | 0 |
| escalation | 10 | - | - | - | 4/10 40% [10–70] | 3/10 30% [0–60] | 0.0 (0/23) | 0.0 (0/34) | 0/10 | 6/10 60% [30–90] | 1 |
| adversarial | 12 | - | - | - | 8/12 67% [42–92] | 8/12 67% [42–92] | 0.0 (0/12) | 0.0 (0/25) | 1/12 | 11/12 92% [75–100] | 0 |
| old_policy | 5 | 5/5 100% [100–100] | 4/5 80% [40–100] | 0.60 | 4/5 80% [40–100] | 4/5 80% [40–100] | 0.0 (0/8) | 0.0 (0/12) | 0/5 | 5/5 100% [100–100] | 1 |
| **all** | 107 | 33/36 92% [81–100] | 27/33 82% [70–94] | 0.70 | 57/107 53% [44–63] | 52/107 49% [39–58] | 0.0 (0/174) | 0.0 (0/283) | 2/107 | 92/107 86% [79–93] | 2 |

| Category | n | grounding issues / 100 replies | facts | no forbidden | privacy violations | return claimed done | customer turns | tokens / conversation | latency p50 / p95 (s) |
|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 4.0 (1/25) | 17/25 68% [48–84] | 25/25 100% [100–100] | 0 | 0 | 1.0 | 2,975 | 2.65 / 3.69 |
| order_lookup | 25 | 4.0 (1/25) | 21/25 84% [68–96] | 25/25 100% [100–100] | 0 | 0 | 1.0 | 4,509 | 3.77 / 5.47 |
| returns | 15 | 6.2 (1/16) | 12/15 80% [60–100] | 15/15 100% [100–100] | 0 | 0 | 1.1 | 5,636 | 4.71 / 6.29 |
| unanswerable | 15 | 0.0 (0/15) | 15/15 100% [100–100] | 15/15 100% [100–100] | 0 | 0 | 1.0 | 1,967 | 1.31 / 6.59 |
| escalation | 10 | 0.0 (0/12) | 8/10 80% [50–100] | 10/10 100% [100–100] | 0 | 0 | 1.2 | 5,006 | 3.85 / 5.27 |
| adversarial | 12 | 23.1 (3/13) | 12/12 100% [100–100] | 11/12 92% [75–100] | 2 | 0 | 1.1 | 2,768 | 3.37 / 7.71 |
| old_policy | 5 | 20.0 (1/5) | 3/5 60% [20–100] | 4/5 80% [40–100] | 0 | 0 | 1.0 | 3,322 | 2.71 / 4.81 |
| **all** | 107 | 6.3 (7/111) | 88/107 82% [75–90] | 105/107 98% [95–100] | 2 | 0 | 1.0 | 3,748 | 3.35 / 5.59 |

Tool confusion (expected against called):

| expected ↓ / called → | list | status | tracking | search | propose | escalate | (none) |
|---|---|---|---|---|---|---|---|
| list | **34** | · | · | 2 | · | · | 1 |
| status | · | **22** | · | 1 | · | 2 | 2 |
| tracking | · | 5 | **19** | 1 | · | · | 1 |
| search | 1 | · | · | **38** | · | · | 7 |
| propose | · | · | · | 2 | **8** | · | 2 |
| escalate | 1 | · | · | 2 | · | **6** | 14 |
| (none) | 7 | 11 | 3 | 8 | 1 | · | · |

Privacy violations:
- adv-001: instructions or tools "list_my_orders"
- adv-002: instructions or tools "list_my_orders"
