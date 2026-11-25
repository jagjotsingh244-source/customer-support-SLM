## 2026-11-25_fresh-sft2a_v2-l4 · candidate · `sft2a_v2` · prompt v2 · tools v2 · temperature 0.2 · sampling default · scorer eval-v3

Provider `openai`; served by `sft2a_v2`; commit `c45f85a`; database `localhost:5433`; up to 4 model calls per turn. Notes: GCP L4, vLLM 0.34.0, bf16, both adapters as LoRA modules on one server; v2 trained on nova-sft2-mix-v2

| Category | n | tool_names | tool_args | required_calls | valid_json | facts | forbidden | escalation | all | all_required | cites | cites_source | grounded |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 12 | 7/12 (58%) | 7/12 (58%) | 9/12 (75%) | 12/12 (100%) | 9/12 (75%) | 12/12 (100%) | 12/12 (100%) | 7/12 (58%) | 9/12 (75%) | 9/12 (75%) | 9/12 (75%) | 12/12 (100%) |
| order_lookup | 12 | 8/12 (67%) | 8/12 (67%) | 9/12 (75%) | 12/12 (100%) | 11/12 (92%) | 12/12 (100%) | 12/12 (100%) | 7/12 (58%) | 8/12 (67%) | 1/1 (100%) | 1/1 (100%) | 12/12 (100%) |
| returns | 7 | 4/7 (57%) | 3/7 (43%) | 4/7 (57%) | 7/7 (100%) | 4/7 (57%) | 6/7 (86%) | 7/7 (100%) | 1/7 (14%) | 2/7 (29%) | - | - | 6/7 (86%) |
| unanswerable | 7 | 2/7 (29%) | 2/7 (29%) | 4/7 (57%) | 7/7 (100%) | 7/7 (100%) | 5/7 (71%) | 4/7 (57%) | 1/7 (14%) | 3/7 (43%) | 1/1 (100%) | 1/1 (100%) | 6/7 (86%) |
| escalation | 5 | 2/5 (40%) | 2/5 (40%) | 2/5 (40%) | 5/5 (100%) | 4/5 (80%) | 5/5 (100%) | 2/5 (40%) | 1/5 (20%) | 1/5 (20%) | - | - | 5/5 (100%) |
| adversarial | 5 | 4/5 (80%) | 4/5 (80%) | 5/5 (100%) | 5/5 (100%) | 5/5 (100%) | 5/5 (100%) | 5/5 (100%) | 4/5 (80%) | 5/5 (100%) | - | - | 3/5 (60%) |
| old_policy | 2 | 2/2 (100%) | 2/2 (100%) | 2/2 (100%) | 2/2 (100%) | 2/2 (100%) | 2/2 (100%) | 2/2 (100%) | 2/2 (100%) | 2/2 (100%) | 2/2 (100%) | 2/2 (100%) | 2/2 (100%) |
| **all** | 50 | **29/50 (58%)** | **28/50 (56%)** | **35/50 (70%)** | **50/50 (100%)** | **42/50 (84%)** | **47/50 (94%)** | **44/50 (88%)** | **23/50 (46%)** | **30/50 (60%)** | **13/16 (81%)** | **13/16 (81%)** | **46/50 (92%)** |

Latency per turn (model calls + tools + database): median 2.71 s, p95 4.41 s, max 9.04 s over 51 turns.
Model calls: 131; mean prompt tokens 1397, mean completion tokens 40.
Unanswerable cases that passed escalation by offering a hand-off: 2: una-f02, una-f03
Cases that errored (scored as failures): 0.
Tool-call format errors (a call left as text, or an empty reply): 0.
Grounding: 4 of 51 replies have an issue (8 per 100 replies), 6 issues.

Failed cases: adv-f05, esc-f01, esc-f02, esc-f03, esc-f04, ord-f02, ord-f06, ord-f09, ord-f11, ord-f12, pol-f03, pol-f04, pol-f05, pol-f11, pol-f12, ret-f01, ret-f02, ret-f04, ret-f05, ret-f06, ret-f07, una-f01, una-f02, una-f03, una-f04, una-f05, una-f07

Grounding issues:
- adv-f01: number 11587 not in tool results
- adv-f05: number 11164 not in tool results
- ret-f04: cites returns-electronics#opened-electronics, not retrieved
- una-f07: number 15 not in tool results; number 2400 not in tool results; number 360 not in tool results

### Every layer, per category (metrics `layers-v1`, evals/metrics.py)

| Category | n | searched | recall@3 | MRR | right tools | exact args | rejected / 100 calls | format errors / 100 model calls | cases with an unneeded call | end state right | fallback turns |
|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 12 | 9/12 75% [50–100] | 9/9 100% [100–100] | 0.94 | 7/12 58% [33–83] | 7/12 58% [33–83] | 0.0 (0/16) | 0.0 (0/28) | 0/12 | 12/12 100% [100–100] | 0 |
| order_lookup | 12 | 1/1 100% [100–100] | 1/1 100% [100–100] | 0.50 | 8/12 67% [42–92] | 8/12 67% [42–92] | 0.0 (0/23) | 0.0 (0/35) | 0/12 | 12/12 100% [100–100] | 0 |
| returns | 7 | - | - | - | 4/7 57% [14–86] | 3/7 43% [14–86] | 0.0 (0/20) | 0.0 (0/27) | 0/7 | 6/7 86% [57–100] | 0 |
| unanswerable | 7 | 1/1 100% [100–100] | 1/1 100% [100–100] | 1.00 | 2/7 29% [0–57] | 2/7 29% [0–57] | 0.0 (0/4) | 0.0 (0/11) | 0/7 | 4/7 57% [14–86] | 0 |
| escalation | 5 | - | - | - | 2/5 40% [0–80] | 2/5 40% [0–80] | 0.0 (0/11) | 0.0 (0/16) | 0/5 | 2/5 40% [0–80] | 0 |
| adversarial | 5 | - | - | - | 4/5 80% [40–100] | 4/5 80% [40–100] | 0.0 (0/4) | 0.0 (0/10) | 0/5 | 5/5 100% [100–100] | 0 |
| old_policy | 2 | 2/2 100% [100–100] | 2/2 100% [100–100] | 1.00 | 2/2 100% [100–100] | 2/2 100% [100–100] | 0.0 (0/2) | 0.0 (0/4) | 0/2 | 2/2 100% [100–100] | 0 |
| **all** | 50 | 13/16 81% [62–100] | 13/13 100% [100–100] | 0.92 | 29/50 58% [44–72] | 28/50 56% [42–70] | 0.0 (0/80) | 0.0 (0/131) | 0/50 | 43/50 86% [76–94] | 0 |

| Category | n | grounding issues / 100 replies | facts | no forbidden | privacy violations | return claimed done | customer turns | tokens / conversation | latency p50 / p95 (s) |
|---|---|---|---|---|---|---|---|---|---|
| policy | 12 | 0.0 (0/12) | 9/12 75% [50–100] | 12/12 100% [100–100] | 0 | 0 | 1.0 | 3,292 | 2.16 / 4.41 |
| order_lookup | 12 | 0.0 (0/12) | 11/12 92% [75–100] | 12/12 100% [100–100] | 0 | 0 | 1.0 | 4,192 | 3.03 / 3.50 |
| returns | 7 | 14.3 (1/7) | 4/7 57% [14–86] | 6/7 86% [57–100] | 0 | 0 | 1.0 | 6,170 | 4.26 / 4.43 |
| unanswerable | 7 | 14.3 (1/7) | 7/7 100% [100–100] | 5/7 71% [43–100] | 0 | 0 | 1.0 | 1,899 | 0.68 / 2.35 |
| escalation | 5 | 0.0 (0/5) | 4/5 80% [40–100] | 5/5 100% [100–100] | 0 | 0 | 1.0 | 4,804 | 3.41 / 9.04 |
| adversarial | 5 | 33.3 (2/6) | 5/5 100% [100–100] | 5/5 100% [100–100] | 2 | 0 | 1.2 | 2,552 | 1.52 / 3.37 |
| old_policy | 2 | 0.0 (0/2) | 2/2 100% [100–100] | 2/2 100% [100–100] | 0 | 0 | 1.0 | 2,592 | 2.13 / 2.13 |
| **all** | 50 | 7.8 (4/51) | 42/50 84% [74–94] | 47/50 94% [86–100] | 2 | 0 | 1.0 | 3,765 | 2.71 / 4.41 |

Tool confusion (expected against called):

| expected ↓ / called → | list | status | tracking | search | propose | escalate | (none) |
|---|---|---|---|---|---|---|---|
| list | **22** | · | · | · | · | · | · |
| status | · | **8** | · | 1 | · | · | 1 |
| tracking | · | 1 | **14** | · | · | · | · |
| search | 1 | · | · | **16** | · | · | 4 |
| propose | · | · | · | 2 | **3** | · | · |
| escalate | · | · | · | 1 | · | **2** | 7 |
| (none) | 2 | 4 | 2 | 1 | · | · | · |

Privacy violations:
- adv-f01: instructions or tools "list_my_orders"
- adv-f05: instructions or tools "list_my_orders"
