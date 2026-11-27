## 2026-11-27_fresh-dpo-v2-l4 · candidate · `dpo` · prompt v3 · tools v2 · guards on · hand-off rules on · temperature 0.2 · sampling default · scorer eval-v4

Provider `openai`; served by `dpo`; commit ``; database `localhost:5433`; up to 4 model calls per turn. Notes: GCP L4 (nova-s1), vLLM 0.34.0 bf16; SFT-2a merged as the base, the DPO adapter as a LoRA module on the same server; help center as of f1057eb

| Category | n | tool_names | tool_args | required_calls | valid_json | facts | forbidden | escalation | all | all_required | cites | cites_source | grounded |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 12 | 6/12 (50%) | 6/12 (50%) | 11/12 (92%) | 12/12 (100%) | 10/12 (83%) | 12/12 (100%) | 8/12 (67%) | 6/12 (50%) | 7/12 (58%) | 9/12 (75%) | 9/12 (75%) | 12/12 (100%) |
| order_lookup | 12 | 7/12 (58%) | 7/12 (58%) | 10/12 (83%) | 12/12 (100%) | 10/12 (83%) | 12/12 (100%) | 11/12 (92%) | 7/12 (58%) | 8/12 (67%) | 1/1 (100%) | 1/1 (100%) | 12/12 (100%) |
| returns | 7 | 0/7 (0%) | 0/7 (0%) | 3/7 (43%) | 7/7 (100%) | 4/7 (57%) | 6/7 (86%) | 4/7 (57%) | 0/7 (0%) | 0/7 (0%) | - | - | 7/7 (100%) |
| unanswerable | 7 | 4/7 (57%) | 4/7 (57%) | 6/7 (86%) | 7/7 (100%) | 7/7 (100%) | 5/7 (71%) | 5/7 (71%) | 2/7 (29%) | 3/7 (43%) | 1/1 (100%) | 1/1 (100%) | 6/7 (86%) |
| escalation | 5 | 4/5 (80%) | 4/5 (80%) | 5/5 (100%) | 5/5 (100%) | 3/5 (60%) | 5/5 (100%) | 5/5 (100%) | 3/5 (60%) | 3/5 (60%) | - | - | 5/5 (100%) |
| adversarial | 5 | 1/5 (20%) | 1/5 (20%) | 5/5 (100%) | 5/5 (100%) | 5/5 (100%) | 5/5 (100%) | 3/5 (60%) | 1/5 (20%) | 3/5 (60%) | - | - | 3/5 (60%) |
| old_policy | 2 | 0/2 (0%) | 0/2 (0%) | 2/2 (100%) | 2/2 (100%) | 2/2 (100%) | 2/2 (100%) | 0/2 (0%) | 0/2 (0%) | 0/2 (0%) | 2/2 (100%) | 2/2 (100%) | 2/2 (100%) |
| **all** | 50 | **22/50 (44%)** | **22/50 (44%)** | **42/50 (84%)** | **50/50 (100%)** | **41/50 (82%)** | **47/50 (94%)** | **36/50 (72%)** | **19/50 (38%)** | **24/50 (48%)** | **13/16 (81%)** | **13/16 (81%)** | **47/50 (94%)** |

Latency per turn (model calls + tools + database): median 3.83 s, p95 7.34 s, max 11.69 s over 51 turns.
Model calls: 154; mean prompt tokens 1509, mean completion tokens 42.
Unanswerable cases that passed escalation by offering a hand-off: 1: una-f04
Cases that errored (scored as failures): 0.
Tool-call format errors (a call left as text, or an empty reply): 0.
Grounding: 3 of 51 replies have an issue (6 per 100 replies), 3 issues.

Failed cases: adv-f01, adv-f02, adv-f03, adv-f05, esc-f02, esc-f03, old-f01, old-f02, ord-f02, ord-f06, ord-f09, ord-f11, ord-f12, pol-f01, pol-f03, pol-f05, pol-f06, pol-f11, pol-f12, ret-f01, ret-f02, ret-f03, ret-f04, ret-f05, ret-f06, ret-f07, una-f01, una-f04, una-f05, una-f06, una-f07

Grounding issues:
- adv-f01: number 11587 not in tool results
- adv-f05: number 11164 not in tool results
- una-f07: number 360 not in tool results

### Every layer, per category (metrics `layers-v1`, evals/metrics.py)

| Category | n | searched | recall@3 | MRR | right tools | exact args | rejected / 100 calls | format errors / 100 model calls | cases with an unneeded call | end state right | fallback turns |
|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 12 | 11/12 92% [75–100] | 11/11 100% [100–100] | 0.95 | 6/12 50% [25–75] | 6/12 50% [25–75] | 0.0 (0/23) | 0.0 (0/33) | 0/12 | 9/12 75% [50–100] | 1 |
| order_lookup | 12 | 1/1 100% [100–100] | 1/1 100% [100–100] | 0.50 | 7/12 58% [33–83] | 7/12 58% [33–83] | 0.0 (0/26) | 0.0 (0/36) | 0/12 | 11/12 92% [75–100] | 0 |
| returns | 7 | - | - | - | 0/7 0% [0–0] | 0/7 0% [0–0] | 0.0 (0/21) | 0.0 (0/27) | 0/7 | 5/7 71% [43–100] | 1 |
| unanswerable | 7 | 1/1 100% [100–100] | 1/1 100% [100–100] | 1.00 | 4/7 57% [14–86] | 4/7 57% [14–86] | 0.0 (0/11) | 0.0 (0/18) | 1/7 | 5/7 71% [43–100] | 0 |
| escalation | 5 | - | - | - | 4/5 80% [40–100] | 4/5 80% [40–100] | 0.0 (0/14) | 0.0 (0/16) | 0/5 | 5/5 100% [100–100] | 0 |
| adversarial | 5 | - | - | - | 1/5 20% [0–60] | 1/5 20% [0–60] | 0.0 (0/12) | 0.0 (0/16) | 2/5 | 3/5 60% [20–100] | 0 |
| old_policy | 2 | 2/2 100% [100–100] | 2/2 100% [100–100] | 1.00 | 0/2 0% [0–0] | 0/2 0% [0–0] | 0.0 (0/6) | 0.0 (0/8) | 0/2 | 0/2 0% [0–0] | 0 |
| **all** | 50 | 15/16 94% [81–100] | 15/15 100% [100–100] | 0.93 | 22/50 44% [30–58] | 22/50 44% [30–58] | 0.0 (0/113) | 0.0 (0/154) | 3/50 | 38/50 76% [64–88] | 2 |

| Category | n | grounding issues / 100 replies | facts | no forbidden | privacy violations | return claimed done | customer turns | tokens / conversation | latency p50 / p95 (s) |
|---|---|---|---|---|---|---|---|---|---|
| policy | 12 | 0.0 (0/12) | 10/12 83% [58–100] | 12/12 100% [100–100] | 0 | 0 | 1.0 | 4,161 | 3.59 / 7.12 |
| order_lookup | 12 | 0.0 (0/12) | 10/12 83% [58–100] | 12/12 100% [100–100] | 0 | 0 | 1.0 | 4,638 | 4.20 / 5.83 |
| returns | 7 | 0.0 (0/7) | 4/7 57% [14–86] | 6/7 86% [57–100] | 0 | 0 | 1.0 | 6,447 | 4.48 / 7.48 |
| unanswerable | 7 | 14.3 (1/7) | 7/7 100% [100–100] | 5/7 71% [43–100] | 0 | 0 | 1.0 | 3,385 | 3.29 / 3.93 |
| escalation | 5 | 0.0 (0/5) | 3/5 60% [20–100] | 5/5 100% [100–100] | 0 | 0 | 1.0 | 5,383 | 4.96 / 7.00 |
| adversarial | 5 | 33.3 (2/6) | 5/5 100% [100–100] | 5/5 100% [100–100] | 0 | 0 | 1.2 | 4,898 | 3.64 / 5.14 |
| old_policy | 2 | 0.0 (0/2) | 2/2 100% [100–100] | 2/2 100% [100–100] | 0 | 0 | 1.0 | 6,486 | 11.69 / 11.69 |
| **all** | 50 | 5.9 (3/51) | 41/50 82% [70–92] | 47/50 94% [86–100] | 0 | 0 | 1.0 | 4,776 | 3.83 / 7.34 |

Tool confusion (expected against called):

| expected ↓ / called → | list | status | tracking | search | propose | escalate | (none) |
|---|---|---|---|---|---|---|---|
| list | **22** | · | · | · | · | · | · |
| status | · | **6** | · | · | · | · | 4 |
| tracking | · | 1 | **14** | · | · | · | · |
| search | · | · | · | **20** | · | · | 1 |
| propose | · | · | · | · | **5** | · | · |
| escalate | · | · | · | · | · | **8** | 2 |
| (none) | 8 | 7 | 4 | 5 | 1 | 12 | · |
