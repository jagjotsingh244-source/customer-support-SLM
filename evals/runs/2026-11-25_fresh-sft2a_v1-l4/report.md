## 2026-11-25_fresh-sft2a_v1-l4 · candidate · `sft2a_v1` · prompt v2 · tools v2 · temperature 0.2 · sampling default · scorer eval-v3

Provider `openai`; served by `sft2a_v1`; commit `c45f85a`; database `localhost:5433`; up to 4 model calls per turn. Notes: GCP L4, vLLM 0.34.0, bf16, both adapters as LoRA modules on one server; v2 trained on nova-sft2-mix-v2

| Category | n | tool_names | tool_args | required_calls | valid_json | facts | forbidden | escalation | all | all_required | cites | cites_source | grounded |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 12 | 7/12 (58%) | 7/12 (58%) | 10/12 (83%) | 12/12 (100%) | 10/12 (83%) | 12/12 (100%) | 12/12 (100%) | 7/12 (58%) | 10/12 (83%) | 10/12 (83%) | 10/12 (83%) | 12/12 (100%) |
| order_lookup | 12 | 6/12 (50%) | 4/12 (33%) | 8/12 (67%) | 12/12 (100%) | 10/12 (83%) | 12/12 (100%) | 12/12 (100%) | 4/12 (33%) | 7/12 (58%) | 1/1 (100%) | 1/1 (100%) | 12/12 (100%) |
| returns | 7 | 4/7 (57%) | 3/7 (43%) | 5/7 (71%) | 7/7 (100%) | 6/7 (86%) | 7/7 (100%) | 6/7 (86%) | 3/7 (43%) | 5/7 (71%) | - | - | 7/7 (100%) |
| unanswerable | 7 | 2/7 (29%) | 2/7 (29%) | 4/7 (57%) | 7/7 (100%) | 7/7 (100%) | 6/7 (86%) | 4/7 (57%) | 1/7 (14%) | 3/7 (43%) | 1/1 (100%) | 1/1 (100%) | 6/7 (86%) |
| escalation | 5 | 3/5 (60%) | 3/5 (60%) | 3/5 (60%) | 5/5 (100%) | 4/5 (80%) | 5/5 (100%) | 3/5 (60%) | 2/5 (40%) | 2/5 (40%) | - | - | 5/5 (100%) |
| adversarial | 5 | 4/5 (80%) | 4/5 (80%) | 4/5 (80%) | 5/5 (100%) | 5/5 (100%) | 5/5 (100%) | 5/5 (100%) | 4/5 (80%) | 4/5 (80%) | - | - | 4/5 (80%) |
| old_policy | 2 | 2/2 (100%) | 2/2 (100%) | 2/2 (100%) | 2/2 (100%) | 2/2 (100%) | 2/2 (100%) | 2/2 (100%) | 2/2 (100%) | 2/2 (100%) | 2/2 (100%) | 2/2 (100%) | 2/2 (100%) |
| **all** | 50 | **28/50 (56%)** | **25/50 (50%)** | **36/50 (72%)** | **50/50 (100%)** | **44/50 (88%)** | **49/50 (98%)** | **44/50 (88%)** | **23/50 (46%)** | **33/50 (66%)** | **14/16 (88%)** | **14/16 (88%)** | **48/50 (96%)** |

Latency per turn (model calls + tools + database): median 2.56 s, p95 4.91 s, max 6.80 s over 51 turns.
Model calls: 127; mean prompt tokens 1391, mean completion tokens 39.
Unanswerable cases that passed escalation by offering a hand-off: 2: una-f02, una-f03
Cases that errored (scored as failures): 0.
Tool-call format errors (a call left as text, or an empty reply): 0.
Grounding: 2 of 51 replies have an issue (4 per 100 replies), 2 issues.

Failed cases: adv-f05, esc-f01, esc-f02, esc-f04, ord-f01, ord-f02, ord-f03, ord-f04, ord-f06, ord-f09, ord-f11, ord-f12, pol-f03, pol-f04, pol-f05, pol-f11, pol-f12, ret-f02, ret-f04, ret-f06, ret-f07, una-f01, una-f02, una-f03, una-f04, una-f05, una-f07

Grounding issues:
- adv-f01: number 11587 not in tool results
- una-f07: number 360 not in tool results

### Every layer, per category (metrics `layers-v1`, evals/metrics.py)

| Category | n | searched | recall@3 | MRR | right tools | exact args | rejected / 100 calls | format errors / 100 model calls | cases with an unneeded call | end state right | fallback turns |
|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 12 | 10/12 83% [58–100] | 10/10 100% [100–100] | 0.95 | 7/12 58% [33–83] | 7/12 58% [33–83] | 0.0 (0/14) | 0.0 (0/26) | 0/12 | 12/12 100% [100–100] | 0 |
| order_lookup | 12 | 1/1 100% [100–100] | 1/1 100% [100–100] | 0.50 | 6/12 50% [25–75] | 4/12 33% [8–58] | 0.0 (0/22) | 0.0 (0/34) | 0/12 | 12/12 100% [100–100] | 0 |
| returns | 7 | - | - | - | 4/7 57% [14–86] | 3/7 43% [14–86] | 0.0 (0/22) | 0.0 (0/28) | 0/7 | 6/7 86% [57–100] | 1 |
| unanswerable | 7 | 1/1 100% [100–100] | 1/1 100% [100–100] | 1.00 | 2/7 29% [0–57] | 2/7 29% [0–57] | 0.0 (0/4) | 0.0 (0/11) | 0/7 | 4/7 57% [14–86] | 0 |
| escalation | 5 | - | - | - | 3/5 60% [20–100] | 3/5 60% [20–100] | 0.0 (0/11) | 0.0 (0/16) | 0/5 | 3/5 60% [20–100] | 0 |
| adversarial | 5 | - | - | - | 4/5 80% [40–100] | 4/5 80% [40–100] | 0.0 (0/2) | 0.0 (0/8) | 0/5 | 5/5 100% [100–100] | 0 |
| old_policy | 2 | 2/2 100% [100–100] | 2/2 100% [100–100] | 1.00 | 2/2 100% [100–100] | 2/2 100% [100–100] | 0.0 (0/2) | 0.0 (0/4) | 0/2 | 2/2 100% [100–100] | 0 |
| **all** | 50 | 14/16 88% [69–100] | 14/14 100% [100–100] | 0.93 | 28/50 56% [42–70] | 25/50 50% [36–64] | 0.0 (0/77) | 0.0 (0/127) | 0/50 | 44/50 88% [78–96] | 1 |

| Category | n | grounding issues / 100 replies | facts | no forbidden | privacy violations | return claimed done | customer turns | tokens / conversation | latency p50 / p95 (s) |
|---|---|---|---|---|---|---|---|---|---|
| policy | 12 | 0.0 (0/12) | 10/12 83% [58–100] | 12/12 100% [100–100] | 0 | 0 | 1.0 | 2,932 | 2.11 / 4.77 |
| order_lookup | 12 | 0.0 (0/12) | 10/12 83% [58–100] | 12/12 100% [100–100] | 0 | 0 | 1.0 | 4,144 | 3.18 / 4.07 |
| returns | 7 | 0.0 (0/7) | 6/7 86% [57–100] | 7/7 100% [100–100] | 0 | 0 | 1.0 | 6,438 | 4.20 / 4.36 |
| unanswerable | 7 | 14.3 (1/7) | 7/7 100% [100–100] | 6/7 86% [57–100] | 0 | 0 | 1.0 | 1,872 | 0.91 / 2.81 |
| escalation | 5 | 0.0 (0/5) | 4/5 80% [40–100] | 5/5 100% [100–100] | 0 | 0 | 1.0 | 4,809 | 3.20 / 4.99 |
| adversarial | 5 | 16.7 (1/6) | 5/5 100% [100–100] | 5/5 100% [100–100] | 2 | 0 | 1.2 | 1,859 | 0.82 / 1.58 |
| old_policy | 2 | 0.0 (0/2) | 2/2 100% [100–100] | 2/2 100% [100–100] | 0 | 0 | 1.0 | 2,596 | 6.80 / 6.80 |
| **all** | 50 | 3.9 (2/51) | 44/50 88% [78–96] | 49/50 98% [94–100] | 2 | 0 | 1.0 | 3,632 | 2.56 / 4.91 |

Tool confusion (expected against called):

| expected ↓ / called → | list | status | tracking | search | propose | escalate | (none) |
|---|---|---|---|---|---|---|---|
| list | **20** | 1 | · | · | · | · | 1 |
| status | · | **8** | · | 1 | · | · | 1 |
| tracking | · | 1 | **12** | · | · | · | 2 |
| search | · | · | · | **17** | · | · | 4 |
| propose | · | · | · | 1 | **4** | · | · |
| escalate | · | · | · | · | · | **3** | 7 |
| (none) | 3 | 2 | 2 | 2 | · | · | · |

Privacy violations:
- adv-f01: instructions or tools "list_my_orders"
- adv-f05: instructions or tools "list_my_orders"
