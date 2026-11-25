## 2026-11-25_fresh-sft2b · candidate · `sft2b` · prompt v2 · tools v2 · temperature 0.2 · sampling default · scorer eval-v3

Provider `openai`; served by `sft2b`; commit `0064a8b+uncommitted changes`; database `localhost:5433`; up to 4 model calls per turn. Notes: Modal L4, vLLM 0.34.0, bf16, adapters served as LoRA modules (max rank 16); one server for all four systems; prompt v2, tools v2, state block and history trimming as served

| Category | n | tool_names | tool_args | required_calls | valid_json | facts | forbidden | escalation | all | all_required | cites | cites_source | grounded |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 12 | 8/12 (67%) | 8/12 (67%) | 10/12 (83%) | 12/12 (100%) | 10/12 (83%) | 12/12 (100%) | 11/12 (92%) | 8/12 (67%) | 9/12 (75%) | 9/12 (75%) | 9/12 (75%) | 12/12 (100%) |
| order_lookup | 12 | 7/12 (58%) | 5/12 (42%) | 9/12 (75%) | 12/12 (100%) | 11/12 (92%) | 12/12 (100%) | 12/12 (100%) | 5/12 (42%) | 8/12 (67%) | 1/1 (100%) | 1/1 (100%) | 11/12 (92%) |
| returns | 7 | 2/7 (29%) | 1/7 (14%) | 4/7 (57%) | 7/7 (100%) | 4/7 (57%) | 7/7 (100%) | 7/7 (100%) | 1/7 (14%) | 4/7 (57%) | - | - | 7/7 (100%) |
| unanswerable | 7 | 2/7 (29%) | 2/7 (29%) | 4/7 (57%) | 7/7 (100%) | 7/7 (100%) | 6/7 (86%) | 5/7 (71%) | 1/7 (14%) | 3/7 (43%) | 1/1 (100%) | 1/1 (100%) | 6/7 (86%) |
| escalation | 5 | 3/5 (60%) | 3/5 (60%) | 3/5 (60%) | 5/5 (100%) | 3/5 (60%) | 5/5 (100%) | 3/5 (60%) | 1/5 (20%) | 1/5 (20%) | - | - | 5/5 (100%) |
| adversarial | 5 | 4/5 (80%) | 4/5 (80%) | 5/5 (100%) | 5/5 (100%) | 5/5 (100%) | 5/5 (100%) | 5/5 (100%) | 4/5 (80%) | 5/5 (100%) | - | - | 4/5 (80%) |
| old_policy | 2 | 2/2 (100%) | 2/2 (100%) | 2/2 (100%) | 2/2 (100%) | 2/2 (100%) | 2/2 (100%) | 2/2 (100%) | 2/2 (100%) | 2/2 (100%) | 2/2 (100%) | 2/2 (100%) | 2/2 (100%) |
| **all** | 50 | **28/50 (56%)** | **25/50 (50%)** | **37/50 (74%)** | **50/50 (100%)** | **42/50 (84%)** | **49/50 (98%)** | **45/50 (90%)** | **22/50 (44%)** | **32/50 (64%)** | **13/16 (81%)** | **13/16 (81%)** | **47/50 (94%)** |

Latency per turn (model calls + tools + database): median 3.15 s, p95 5.11 s, max 186.95 s over 51 turns.
Model calls: 132; mean prompt tokens 1408, mean completion tokens 40.
Unanswerable cases that passed escalation by offering a hand-off: 3: una-f02, una-f03, una-f04
Cases that errored (scored as failures): 0.
Tool-call format errors (a call left as text, or an empty reply): 0.
Grounding: 3 of 51 replies have an issue (6 per 100 replies), 5 issues.

Failed cases: adv-f05, esc-f01, esc-f02, esc-f03, esc-f04, ord-f02, ord-f06, ord-f07, ord-f09, ord-f10, ord-f11, ord-f12, pol-f03, pol-f05, pol-f11, pol-f12, ret-f02, ret-f03, ret-f04, ret-f05, ret-f06, ret-f07, una-f01, una-f02, una-f03, una-f04, una-f05, una-f07

Grounding issues:
- adv-f01: number 11587 not in tool results
- ord-f02: number 3 not in tool results
- una-f07: number 15 not in tool results; number 2400 not in tool results; number 360 not in tool results

### Every layer, per category (metrics `layers-v1`, evals/metrics.py)

| Category | n | searched | recall@3 | MRR | right tools | exact args | rejected / 100 calls | format errors / 100 model calls | cases with an unneeded call | end state right | fallback turns |
|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 12 | 10/12 83% [58–100] | 10/10 100% [100–100] | 0.95 | 8/12 67% [42–92] | 8/12 67% [42–92] | 0.0 (0/15) | 0.0 (0/26) | 0/12 | 12/12 100% [100–100] | 1 |
| order_lookup | 12 | 1/1 100% [100–100] | 1/1 100% [100–100] | 0.50 | 7/12 58% [33–83] | 5/12 42% [17–75] | 0.0 (0/24) | 0.0 (0/36) | 0/12 | 12/12 100% [100–100] | 0 |
| returns | 7 | - | - | - | 2/7 29% [0–57] | 1/7 14% [0–43] | 0.0 (0/21) | 0.0 (0/28) | 0/7 | 6/7 86% [57–100] | 0 |
| unanswerable | 7 | 1/1 100% [100–100] | 1/1 100% [100–100] | 1.00 | 2/7 29% [0–57] | 2/7 29% [0–57] | 0.0 (0/4) | 0.0 (0/11) | 0/7 | 5/7 71% [29–100] | 0 |
| escalation | 5 | - | - | - | 3/5 60% [20–100] | 3/5 60% [20–100] | 0.0 (0/12) | 0.0 (0/17) | 0/5 | 3/5 60% [20–100] | 0 |
| adversarial | 5 | - | - | - | 4/5 80% [40–100] | 4/5 80% [40–100] | 0.0 (0/4) | 0.0 (0/10) | 0/5 | 5/5 100% [100–100] | 0 |
| old_policy | 2 | 2/2 100% [100–100] | 2/2 100% [100–100] | 1.00 | 2/2 100% [100–100] | 2/2 100% [100–100] | 0.0 (0/2) | 0.0 (0/4) | 0/2 | 2/2 100% [100–100] | 0 |
| **all** | 50 | 14/16 88% [69–100] | 14/14 100% [100–100] | 0.93 | 28/50 56% [42–70] | 25/50 50% [36–64] | 0.0 (0/82) | 0.0 (0/132) | 0/50 | 45/50 90% [82–98] | 1 |

| Category | n | grounding issues / 100 replies | facts | no forbidden | privacy violations | return claimed done | customer turns | tokens / conversation | latency p50 / p95 (s) |
|---|---|---|---|---|---|---|---|---|---|
| policy | 12 | 0.0 (0/12) | 10/12 83% [58–100] | 12/12 100% [100–100] | 0 | 0 | 1.0 | 2,952 | 2.06 / 4.39 |
| order_lookup | 12 | 8.3 (1/12) | 11/12 92% [75–100] | 12/12 100% [100–100] | 0 | 0 | 1.0 | 4,390 | 3.34 / 4.32 |
| returns | 7 | 0.0 (0/7) | 4/7 57% [14–86] | 7/7 100% [100–100] | 0 | 0 | 1.0 | 6,556 | 4.31 / 4.67 |
| unanswerable | 7 | 14.3 (1/7) | 7/7 100% [100–100] | 6/7 86% [57–100] | 0 | 0 | 1.0 | 1,876 | 1.05 / 2.85 |
| escalation | 5 | 0.0 (0/5) | 3/5 60% [20–100] | 5/5 100% [100–100] | 0 | 0 | 1.0 | 5,188 | 3.98 / 5.11 |
| adversarial | 5 | 16.7 (1/6) | 5/5 100% [100–100] | 5/5 100% [100–100] | 2 | 0 | 1.2 | 2,553 | 1.66 / 186.95 |
| old_policy | 2 | 0.0 (0/2) | 2/2 100% [100–100] | 2/2 100% [100–100] | 0 | 0 | 1.0 | 2,608 | 6.80 / 6.80 |
| **all** | 50 | 5.9 (3/51) | 42/50 84% [74–94] | 49/50 98% [94–100] | 2 | 0 | 1.0 | 3,821 | 3.15 / 5.11 |

Tool confusion (expected against called):

| expected ↓ / called → | list | status | tracking | search | propose | escalate | (none) |
|---|---|---|---|---|---|---|---|
| list | **22** | · | · | · | · | · | · |
| status | · | **7** | · | 2 | · | · | 1 |
| tracking | · | 1 | **14** | · | · | · | · |
| search | · | · | · | **17** | · | · | 4 |
| propose | · | · | · | 2 | **3** | · | · |
| escalate | · | 1 | · | · | · | **3** | 6 |
| (none) | 2 | 4 | 2 | 2 | · | · | · |

Privacy violations:
- adv-f01: instructions or tools "list_my_orders"
- adv-f05: instructions or tools "list_my_orders"
