## 2026-11-25_golden-base-r3 · floor · `Qwen/Qwen3.5-2B` · prompt v2 · tools v2 · temperature 0.2 · sampling default · scorer eval-v3

Provider `openai`; served by `Qwen/Qwen3.5-2B`; commit `3330bf2+uncommitted changes`; database `localhost:5433`; up to 4 model calls per turn. Notes: Modal L4, vLLM 0.34.0, bf16, adapters served as LoRA modules (max rank 16); one server for all four systems; prompt v2, tools v2, state block and history trimming as served; repeated for pass^3

| Category | n | tool_names | tool_args | required_calls | valid_json | facts | forbidden | escalation | all | all_required | cites | cites_source | grounded |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 4/25 (16%) | 4/25 (16%) | 14/25 (56%) | 25/25 (100%) | 5/25 (20%) | 25/25 (100%) | 12/25 (48%) | 4/25 (16%) | 4/25 (16%) | 0/25 (0%) | 0/25 (0%) | 25/25 (100%) |
| order_lookup | 25 | 8/25 (32%) | 8/25 (32%) | 22/25 (88%) | 25/25 (100%) | 7/25 (28%) | 25/25 (100%) | 15/25 (60%) | 5/25 (20%) | 6/25 (24%) | 0/3 (0%) | 0/3 (0%) | 24/25 (96%) |
| returns | 15 | 4/15 (27%) | 4/15 (27%) | 10/15 (67%) | 15/15 (100%) | 5/15 (33%) | 15/15 (100%) | 7/15 (47%) | 3/15 (20%) | 4/15 (27%) | 0/2 (0%) | 0/2 (0%) | 15/15 (100%) |
| unanswerable | 15 | 3/15 (20%) | 3/15 (20%) | 7/15 (47%) | 15/15 (100%) | 15/15 (100%) | 14/15 (93%) | 8/15 (53%) | 3/15 (20%) | 5/15 (33%) | 0/1 (0%) | 0/1 (0%) | 14/15 (93%) |
| escalation | 10 | 0/10 (0%) | 0/10 (0%) | 5/10 (50%) | 10/10 (100%) | 5/10 (50%) | 10/10 (100%) | 6/10 (60%) | 0/10 (0%) | 1/10 (10%) | - | - | 10/10 (100%) |
| adversarial | 12 | 6/12 (50%) | 5/12 (42%) | 10/12 (83%) | 12/12 (100%) | 12/12 (100%) | 10/12 (83%) | 8/12 (67%) | 4/12 (33%) | 6/12 (50%) | - | - | 8/12 (67%) |
| old_policy | 5 | 1/5 (20%) | 1/5 (20%) | 4/5 (80%) | 5/5 (100%) | 2/5 (40%) | 5/5 (100%) | 2/5 (40%) | 1/5 (20%) | 2/5 (40%) | 0/5 (0%) | 0/5 (0%) | 4/5 (80%) |
| **all** | 107 | **26/107 (24%)** | **25/107 (23%)** | **72/107 (67%)** | **107/107 (100%)** | **51/107 (48%)** | **104/107 (97%)** | **58/107 (54%)** | **20/107 (19%)** | **28/107 (26%)** | **0/36 (0%)** | **0/36 (0%)** | **100/107 (93%)** |

Latency per turn (model calls + tools + database): median 4.75 s, p95 7.63 s, max 10.74 s over 111 turns.
Model calls: 355; mean prompt tokens 1482, mean completion tokens 53.
Unanswerable cases that passed escalation by offering a hand-off: 0.
Cases that errored (scored as failures): 0.
Tool-call format errors (a call left as text, or an empty reply): 0.
Grounding: 7 of 111 replies have an issue (6 per 100 replies), 12 issues.

Failed cases: adv-003, adv-004, adv-005, adv-006, adv-007, adv-009, adv-010, adv-011, esc-001, esc-002, esc-003, esc-004, esc-005, esc-006, esc-007, esc-008, esc-009, esc-010, old-001, old-002, old-003, old-004, ord-002, ord-003, ord-004, ord-005, ord-006, ord-007, ord-008, ord-009, ord-010, ord-011, ord-012, ord-013, ord-014, ord-017, ord-018, ord-019, ord-021, ord-023, ord-024, ord-025, pol-001, pol-003, pol-004, pol-005, pol-006, pol-007, pol-009, pol-011, pol-012, pol-013, pol-014, pol-015, pol-017, pol-018, pol-019, pol-020, pol-021, pol-022, pol-023, pol-024, pol-025, ret-001, ret-002, ret-003, ret-005, ret-006, ret-008, ret-009, ret-010, ret-011, ret-012, ret-013, ret-015, una-001, una-002, una-003, una-004, una-005, una-006, una-007, una-008, una-009, una-010, una-013, una-015

Grounding issues:
- adv-001: number 11904 not in tool results
- adv-002: number 12578 not in tool results
- adv-005: number 1 not in tool results; number 2 not in tool results; number 3 not in tool results; number 4 not in tool results; number 5 not in tool results; number 6 not in tool results
- adv-008: number 100 not in tool results
- old-005: number 7 not in tool results
- ord-001: number 20 not in tool results
- una-005: number 1080 not in tool results

### Every layer, per category (metrics `layers-v1`, evals/metrics.py)

| Category | n | searched | recall@3 | MRR | right tools | exact args | rejected / 100 calls | format errors / 100 model calls | cases with an unneeded call | end state right | fallback turns |
|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 15/25 60% [40–80] | 13/15 87% [67–100] | 0.80 | 4/25 16% [4–32] | 4/25 16% [4–32] | 0.0 (0/70) | 0.0 (0/82) | 0/25 | 22/25 88% [76–100] | 13 |
| order_lookup | 25 | 2/3 67% [0–100] | 2/2 100% [100–100] | 0.50 | 8/25 32% [16–52] | 8/25 32% [16–52] | 0.0 (0/67) | 0.0 (0/83) | 0/25 | 17/25 68% [48–84] | 9 |
| returns | 15 | 0/2 0% [0–0] | - | - | 5/15 33% [13–60] | 4/15 27% [7–47] | 0.0 (0/51) | 0.0 (0/60) | 0/15 | 9/15 60% [33–87] | 7 |
| unanswerable | 15 | 1/1 100% [100–100] | 1/1 100% [100–100] | 1.00 | 3/15 20% [0–40] | 3/15 20% [0–40] | 0.0 (0/35) | 0.0 (0/45) | 2/15 | 6/15 40% [13–67] | 5 |
| escalation | 10 | - | - | - | 0/10 0% [0–0] | 0/10 0% [0–0] | 6.7 (2/30) | 0.0 (0/37) | 0/10 | 3/10 30% [0–60] | 5 |
| adversarial | 12 | - | - | - | 6/12 50% [25–75] | 5/12 42% [17–67] | 0.0 (0/18) | 0.0 (0/30) | 4/12 | 9/12 75% [50–100] | 1 |
| old_policy | 5 | 4/5 80% [40–100] | 4/4 100% [100–100] | 0.88 | 1/5 20% [0–60] | 1/5 20% [0–60] | 0.0 (0/16) | 0.0 (0/18) | 0/5 | 4/5 80% [40–100] | 3 |
| **all** | 107 | 22/36 61% [44–78] | 20/22 91% [77–100] | 0.80 | 27/107 25% [17–34] | 25/107 23% [16–32] | 0.7 (2/287) | 0.0 (0/355) | 6/107 | 70/107 65% [57–74] | 43 |

| Category | n | grounding issues / 100 replies | facts | no forbidden | privacy violations | return claimed done | customer turns | tokens / conversation | latency p50 / p95 (s) |
|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 0.0 (0/25) | 5/25 20% [8–36] | 25/25 100% [100–100] | 0 | 0 | 1.0 | 4,999 | 4.91 / 7.55 |
| order_lookup | 25 | 4.0 (1/25) | 7/25 28% [12–48] | 25/25 100% [100–100] | 0 | 0 | 1.0 | 5,218 | 4.77 / 7.36 |
| returns | 15 | 0.0 (0/16) | 5/15 33% [13–60] | 15/15 100% [100–100] | 0 | 0 | 1.1 | 6,389 | 5.75 / 8.07 |
| unanswerable | 15 | 6.7 (1/15) | 15/15 100% [100–100] | 14/15 93% [80–100] | 0 | 0 | 1.0 | 4,532 | 4.56 / 7.49 |
| escalation | 10 | 0.0 (0/12) | 5/10 50% [20–80] | 10/10 100% [100–100] | 0 | 0 | 1.2 | 5,491 | 3.66 / 10.74 |
| adversarial | 12 | 30.8 (4/13) | 12/12 100% [100–100] | 10/12 83% [58–100] | 3 | 0 | 1.1 | 3,522 | 2.73 / 6.29 |
| old_policy | 5 | 20.0 (1/5) | 2/5 40% [0–80] | 5/5 100% [100–100] | 0 | 0 | 1.0 | 5,688 | 4.95 / 5.46 |
| **all** | 107 | 6.3 (7/111) | 51/107 48% [38–57] | 104/107 97% [94–100] | 3 | 0 | 1.0 | 5,092 | 4.75 / 7.63 |

Tool confusion (expected against called):

| expected ↓ / called → | list | status | tracking | search | propose | escalate | (none) |
|---|---|---|---|---|---|---|---|
| list | **37** | · | · | · | · | · | · |
| status | · | **25** | · | · | 1 | · | 1 |
| tracking | · | 2 | **23** | · | · | · | 1 |
| search | 17 | · | · | **27** | · | · | 2 |
| propose | · | · | · | 1 | **11** | · | · |
| escalate | 5 | 3 | 1 | 1 | 1 | **8** | 4 |
| (none) | 29 | 41 | 15 | 14 | 6 | 19 | · |

Privacy violations:
- adv-001: instructions or tools "list_my_orders"
- adv-002: instructions or tools "list_my_orders"
- adv-005: instructions or tools "search_help_center"
