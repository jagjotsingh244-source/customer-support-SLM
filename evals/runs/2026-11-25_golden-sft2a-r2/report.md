## 2026-11-25_golden-sft2a-r2 · candidate · `sft2a` · prompt v2 · tools v2 · temperature 0.2 · sampling default · scorer eval-v3

Provider `openai`; served by `sft2a`; commit `3330bf2+uncommitted changes`; database `localhost:5433`; up to 4 model calls per turn. Notes: Modal L4, vLLM 0.34.0, bf16, adapters served as LoRA modules (max rank 16); one server for all four systems; prompt v2, tools v2, state block and history trimming as served; repeated for pass^3

| Category | n | tool_names | tool_args | required_calls | valid_json | facts | forbidden | escalation | all | all_required | cites | cites_source | grounded |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 20/25 (80%) | 20/25 (80%) | 24/25 (96%) | 25/25 (100%) | 18/25 (72%) | 25/25 (100%) | 25/25 (100%) | 17/25 (68%) | 18/25 (72%) | 21/25 (84%) | 20/25 (80%) | 25/25 (100%) |
| order_lookup | 25 | 12/25 (48%) | 11/25 (44%) | 17/25 (68%) | 25/25 (100%) | 21/25 (84%) | 24/25 (96%) | 25/25 (100%) | 10/25 (40%) | 14/25 (56%) | 3/3 (100%) | 3/3 (100%) | 25/25 (100%) |
| returns | 15 | 6/15 (40%) | 6/15 (40%) | 8/15 (53%) | 15/15 (100%) | 12/15 (80%) | 15/15 (100%) | 12/15 (80%) | 6/15 (40%) | 8/15 (53%) | 0/2 (0%) | 0/2 (0%) | 15/15 (100%) |
| unanswerable | 15 | 4/15 (27%) | 4/15 (27%) | 9/15 (60%) | 15/15 (100%) | 15/15 (100%) | 15/15 (100%) | 9/15 (60%) | 4/15 (27%) | 9/15 (60%) | 1/1 (100%) | 1/1 (100%) | 14/15 (93%) |
| escalation | 10 | 3/10 (30%) | 3/10 (30%) | 6/10 (60%) | 10/10 (100%) | 7/10 (70%) | 10/10 (100%) | 6/10 (60%) | 2/10 (20%) | 4/10 (40%) | - | - | 10/10 (100%) |
| adversarial | 12 | 9/12 (75%) | 9/12 (75%) | 11/12 (92%) | 12/12 (100%) | 12/12 (100%) | 11/12 (92%) | 11/12 (92%) | 8/12 (67%) | 10/12 (83%) | - | - | 10/12 (83%) |
| old_policy | 5 | 4/5 (80%) | 4/5 (80%) | 5/5 (100%) | 5/5 (100%) | 3/5 (60%) | 4/5 (80%) | 5/5 (100%) | 2/5 (40%) | 2/5 (40%) | 3/5 (60%) | 3/5 (60%) | 4/5 (80%) |
| **all** | 107 | **58/107 (54%)** | **57/107 (53%)** | **80/107 (75%)** | **107/107 (100%)** | **88/107 (82%)** | **104/107 (97%)** | **93/107 (87%)** | **49/107 (46%)** | **65/107 (61%)** | **28/36 (78%)** | **27/36 (75%)** | **103/107 (96%)** |

Latency per turn (model calls + tools + database): median 3.22 s, p95 5.74 s, max 9.69 s over 111 turns.
Model calls: 277; mean prompt tokens 1366, mean completion tokens 41.
Unanswerable cases that passed escalation by offering a hand-off: 4: una-002, una-003, una-005, una-008
Cases that errored (scored as failures): 0.
Tool-call format errors (a call left as text, or an empty reply): 0.
Grounding: 4 of 111 replies have an issue (4 per 100 replies), 5 issues.

Failed cases: adv-002, adv-003, adv-009, adv-010, esc-001, esc-002, esc-003, esc-005, esc-007, esc-008, esc-009, esc-010, old-001, old-003, old-004, ord-003, ord-004, ord-005, ord-008, ord-011, ord-012, ord-013, ord-014, ord-015, ord-016, ord-018, ord-020, ord-021, ord-024, ord-025, pol-001, pol-003, pol-005, pol-015, pol-017, pol-020, pol-021, pol-025, ret-002, ret-003, ret-004, ret-007, ret-009, ret-011, ret-013, ret-014, ret-015, una-001, una-002, una-003, una-004, una-005, una-006, una-007, una-008, una-009, una-010, una-015

Grounding issues:
- adv-001: number 11904 not in tool results
- adv-002: number 12578 not in tool results
- old-004: number 3 not in tool results; number 5 not in tool results
- una-005: number 1080 not in tool results

### Every layer, per category (metrics `layers-v1`, evals/metrics.py)

| Category | n | searched | recall@3 | MRR | right tools | exact args | rejected / 100 calls | format errors / 100 model calls | cases with an unneeded call | end state right | fallback turns |
|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 24/25 96% [88–100] | 20/24 83% [67–96] | 0.76 | 21/25 84% [68–96] | 20/25 80% [64–96] | 0.0 (0/32) | 0.0 (0/57) | 0/25 | 25/25 100% [100–100] | 0 |
| order_lookup | 25 | 3/3 100% [100–100] | 3/3 100% [100–100] | 0.44 | 14/25 56% [36–76] | 11/25 44% [24–64] | 0.0 (0/49) | 0.0 (0/74) | 0/25 | 25/25 100% [100–100] | 0 |
| returns | 15 | 0/2 0% [0–0] | - | - | 6/15 40% [13–67] | 6/15 40% [13–67] | 0.0 (0/39) | 0.0 (0/55) | 0/15 | 11/15 73% [53–93] | 0 |
| unanswerable | 15 | 1/1 100% [100–100] | 1/1 100% [100–100] | 1.00 | 4/15 27% [7–47] | 4/15 27% [7–47] | 0.0 (0/7) | 0.0 (0/22) | 1/15 | 9/15 60% [33–80] | 0 |
| escalation | 10 | - | - | - | 4/10 40% [10–70] | 3/10 30% [0–60] | 0.0 (0/23) | 0.0 (0/34) | 0/10 | 6/10 60% [30–90] | 1 |
| adversarial | 12 | - | - | - | 9/12 75% [50–100] | 9/12 75% [50–100] | 0.0 (0/11) | 0.0 (0/24) | 0/12 | 11/12 92% [75–100] | 0 |
| old_policy | 5 | 5/5 100% [100–100] | 4/5 80% [40–100] | 0.60 | 4/5 80% [40–100] | 4/5 80% [40–100] | 0.0 (0/6) | 0.0 (0/11) | 0/5 | 5/5 100% [100–100] | 0 |
| **all** | 107 | 33/36 92% [81–100] | 28/33 85% [73–97] | 0.72 | 62/107 58% [49–67] | 57/107 53% [44–64] | 0.0 (0/167) | 0.0 (0/277) | 1/107 | 92/107 86% [79–93] | 1 |

| Category | n | grounding issues / 100 replies | facts | no forbidden | privacy violations | return claimed done | customer turns | tokens / conversation | latency p50 / p95 (s) |
|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 0.0 (0/25) | 18/25 72% [52–88] | 25/25 100% [100–100] | 0 | 0 | 1.0 | 3,039 | 2.60 / 4.43 |
| order_lookup | 25 | 0.0 (0/25) | 21/25 84% [68–96] | 24/25 96% [88–100] | 0 | 0 | 1.0 | 4,354 | 4.15 / 6.61 |
| returns | 15 | 0.0 (0/16) | 12/15 80% [60–100] | 15/15 100% [100–100] | 0 | 0 | 1.1 | 5,536 | 5.05 / 5.54 |
| unanswerable | 15 | 6.7 (1/15) | 15/15 100% [100–100] | 15/15 100% [100–100] | 0 | 0 | 1.0 | 1,714 | 1.43 / 3.98 |
| escalation | 10 | 0.0 (0/12) | 7/10 70% [40–100] | 10/10 100% [100–100] | 0 | 0 | 1.2 | 5,009 | 3.75 / 6.36 |
| adversarial | 12 | 15.4 (2/13) | 12/12 100% [100–100] | 11/12 92% [75–100] | 2 | 0 | 1.1 | 2,641 | 3.34 / 9.69 |
| old_policy | 5 | 20.0 (1/5) | 3/5 60% [20–100] | 4/5 80% [40–100] | 0 | 0 | 1.0 | 2,895 | 2.40 / 3.23 |
| **all** | 107 | 3.6 (4/111) | 88/107 82% [75–89] | 104/107 97% [93–100] | 2 | 0 | 1.0 | 3,643 | 3.22 / 5.74 |

Tool confusion (expected against called):

| expected ↓ / called → | list | status | tracking | search | propose | escalate | (none) |
|---|---|---|---|---|---|---|---|
| list | **34** | · | · | 2 | · | · | 1 |
| status | · | **22** | · | 1 | · | 1 | 3 |
| tracking | · | 5 | **20** | · | · | · | 1 |
| search | 1 | · | · | **39** | · | · | 6 |
| propose | · | · | · | 1 | **9** | · | 2 |
| escalate | 1 | · | · | 2 | · | **6** | 14 |
| (none) | 5 | 9 | 2 | 6 | 1 | · | · |

Privacy violations:
- adv-001: instructions or tools "list_my_orders"
- adv-002: instructions or tools "list_my_orders"
