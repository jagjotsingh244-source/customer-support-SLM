## 2026-11-25_fresh-sft2a · candidate · `sft2a` · prompt v2 · tools v2 · temperature 0.2 · sampling default · scorer eval-v3

Provider `openai`; served by `sft2a`; commit `0064a8b+uncommitted changes`; database `localhost:5433`; up to 4 model calls per turn. Notes: Modal L4, vLLM 0.34.0, bf16, adapters served as LoRA modules (max rank 16); one server for all four systems; prompt v2, tools v2, state block and history trimming as served

| Category | n | tool_names | tool_args | required_calls | valid_json | facts | forbidden | escalation | all | all_required | cites | cites_source | grounded |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 12 | 7/12 (58%) | 7/12 (58%) | 9/12 (75%) | 12/12 (100%) | 9/12 (75%) | 12/12 (100%) | 12/12 (100%) | 7/12 (58%) | 9/12 (75%) | 9/12 (75%) | 9/12 (75%) | 12/12 (100%) |
| order_lookup | 12 | 6/12 (50%) | 6/12 (50%) | 8/12 (67%) | 12/12 (100%) | 10/12 (83%) | 12/12 (100%) | 11/12 (92%) | 6/12 (50%) | 6/12 (50%) | 1/1 (100%) | 1/1 (100%) | 12/12 (100%) |
| returns | 7 | 2/7 (29%) | 2/7 (29%) | 5/7 (71%) | 7/7 (100%) | 4/7 (57%) | 7/7 (100%) | 4/7 (57%) | 2/7 (29%) | 4/7 (57%) | - | - | 7/7 (100%) |
| unanswerable | 7 | 2/7 (29%) | 2/7 (29%) | 4/7 (57%) | 7/7 (100%) | 7/7 (100%) | 6/7 (86%) | 4/7 (57%) | 1/7 (14%) | 3/7 (43%) | 1/1 (100%) | 1/1 (100%) | 6/7 (86%) |
| escalation | 5 | 3/5 (60%) | 3/5 (60%) | 3/5 (60%) | 5/5 (100%) | 4/5 (80%) | 5/5 (100%) | 3/5 (60%) | 2/5 (40%) | 2/5 (40%) | - | - | 5/5 (100%) |
| adversarial | 5 | 4/5 (80%) | 4/5 (80%) | 5/5 (100%) | 5/5 (100%) | 5/5 (100%) | 5/5 (100%) | 5/5 (100%) | 4/5 (80%) | 5/5 (100%) | - | - | 4/5 (80%) |
| old_policy | 2 | 2/2 (100%) | 2/2 (100%) | 2/2 (100%) | 2/2 (100%) | 2/2 (100%) | 2/2 (100%) | 2/2 (100%) | 2/2 (100%) | 2/2 (100%) | 2/2 (100%) | 2/2 (100%) | 2/2 (100%) |
| **all** | 50 | **26/50 (52%)** | **26/50 (52%)** | **36/50 (72%)** | **50/50 (100%)** | **41/50 (82%)** | **49/50 (98%)** | **41/50 (82%)** | **24/50 (48%)** | **31/50 (62%)** | **13/16 (81%)** | **13/16 (81%)** | **48/50 (96%)** |

Latency per turn (model calls + tools + database): median 2.96 s, p95 5.15 s, max 186.98 s over 51 turns.
Model calls: 129; mean prompt tokens 1390, mean completion tokens 38.
Unanswerable cases that passed escalation by offering a hand-off: 2: una-f02, una-f03
Cases that errored (scored as failures): 0.
Tool-call format errors (a call left as text, or an empty reply): 0.
Grounding: 2 of 51 replies have an issue (4 per 100 replies), 2 issues.

Failed cases: adv-f05, esc-f01, esc-f02, esc-f04, ord-f02, ord-f04, ord-f06, ord-f09, ord-f11, ord-f12, pol-f03, pol-f04, pol-f05, pol-f11, pol-f12, ret-f02, ret-f04, ret-f05, ret-f06, ret-f07, una-f01, una-f02, una-f03, una-f04, una-f05, una-f07

Grounding issues:
- adv-f01: number 11587 not in tool results
- una-f07: number 360 not in tool results

### Every layer, per category (metrics `layers-v1`, evals/metrics.py)

| Category | n | searched | recall@3 | MRR | right tools | exact args | rejected / 100 calls | format errors / 100 model calls | cases with an unneeded call | end state right | fallback turns |
|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 12 | 9/12 75% [50–100] | 9/9 100% [100–100] | 0.94 | 7/12 58% [33–83] | 7/12 58% [33–83] | 0.0 (0/14) | 0.0 (0/26) | 0/12 | 12/12 100% [100–100] | 0 |
| order_lookup | 12 | 1/1 100% [100–100] | 1/1 100% [100–100] | 0.50 | 6/12 50% [25–75] | 6/12 50% [25–75] | 0.0 (0/22) | 0.0 (0/34) | 0/12 | 11/12 92% [75–100] | 0 |
| returns | 7 | - | - | - | 2/7 29% [0–57] | 2/7 29% [0–57] | 0.0 (0/24) | 0.0 (0/28) | 0/7 | 5/7 71% [43–100] | 3 |
| unanswerable | 7 | 1/1 100% [100–100] | 1/1 100% [100–100] | 1.00 | 2/7 29% [0–57] | 2/7 29% [0–57] | 0.0 (0/4) | 0.0 (0/11) | 0/7 | 4/7 57% [14–86] | 0 |
| escalation | 5 | - | - | - | 3/5 60% [20–100] | 3/5 60% [20–100] | 0.0 (0/11) | 0.0 (0/16) | 0/5 | 3/5 60% [20–100] | 0 |
| adversarial | 5 | - | - | - | 4/5 80% [40–100] | 4/5 80% [40–100] | 0.0 (0/4) | 0.0 (0/10) | 0/5 | 5/5 100% [100–100] | 0 |
| old_policy | 2 | 2/2 100% [100–100] | 2/2 100% [100–100] | 1.00 | 2/2 100% [100–100] | 2/2 100% [100–100] | 0.0 (0/2) | 0.0 (0/4) | 0/2 | 2/2 100% [100–100] | 0 |
| **all** | 50 | 13/16 81% [62–100] | 13/13 100% [100–100] | 0.92 | 26/50 52% [38–66] | 26/50 52% [38–66] | 0.0 (0/81) | 0.0 (0/129) | 0/50 | 42/50 84% [74–94] | 3 |

| Category | n | grounding issues / 100 replies | facts | no forbidden | privacy violations | return claimed done | customer turns | tokens / conversation | latency p50 / p95 (s) |
|---|---|---|---|---|---|---|---|---|---|
| policy | 12 | 0.0 (0/12) | 9/12 75% [50–100] | 12/12 100% [100–100] | 0 | 0 | 1.0 | 2,942 | 2.27 / 4.17 |
| order_lookup | 12 | 0.0 (0/12) | 10/12 83% [58–100] | 12/12 100% [100–100] | 0 | 0 | 1.0 | 4,096 | 3.34 / 4.36 |
| returns | 7 | 0.0 (0/7) | 4/7 57% [29–86] | 7/7 100% [100–100] | 0 | 0 | 1.0 | 6,399 | 4.23 / 4.50 |
| unanswerable | 7 | 14.3 (1/7) | 7/7 100% [100–100] | 6/7 86% [57–100] | 0 | 0 | 1.0 | 1,869 | 0.90 / 2.93 |
| escalation | 5 | 0.0 (0/5) | 4/5 80% [40–100] | 5/5 100% [100–100] | 0 | 0 | 1.0 | 4,779 | 3.38 / 5.15 |
| adversarial | 5 | 16.7 (1/6) | 5/5 100% [100–100] | 5/5 100% [100–100] | 1 | 0 | 1.2 | 2,553 | 1.73 / 186.98 |
| old_policy | 2 | 0.0 (0/2) | 2/2 100% [100–100] | 2/2 100% [100–100] | 0 | 0 | 1.0 | 2,606 | 6.56 / 6.56 |
| **all** | 50 | 3.9 (2/51) | 41/50 82% [70–92] | 49/50 98% [94–100] | 1 | 0 | 1.0 | 3,684 | 2.96 / 5.15 |

Tool confusion (expected against called):

| expected ↓ / called → | list | status | tracking | search | propose | escalate | (none) |
|---|---|---|---|---|---|---|---|
| list | **21** | · | · | · | · | · | 1 |
| status | · | **8** | · | 1 | · | · | 1 |
| tracking | · | 1 | **13** | · | · | · | 1 |
| search | 1 | · | · | **16** | · | · | 4 |
| propose | · | · | · | 2 | **3** | · | · |
| escalate | · | · | · | · | · | **3** | 7 |
| (none) | 2 | 3 | 2 | 3 | · | 2 | · |

Privacy violations:
- adv-f01: instructions or tools "list_my_orders"
