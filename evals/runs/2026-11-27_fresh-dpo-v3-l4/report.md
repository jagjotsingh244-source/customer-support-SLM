## 2026-11-27_fresh-dpo-v3-l4 · candidate · `dpo3` · prompt v3 · tools v2 · guards on · hand-off rules on · temperature 0.2 · sampling default · scorer eval-v4

Provider `openai`; served by `dpo3`; commit ``; database `localhost:5433`; up to 4 model calls per turn. Notes: GCP L4 (nova-s1), vLLM 0.34.0 bf16; SFT-2a merged as the base, DPO v3 (no hand-off pairs) as a LoRA module

| Category | n | tool_names | tool_args | required_calls | valid_json | facts | forbidden | escalation | all | all_required | cites | cites_source | grounded |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 12 | 8/12 (67%) | 8/12 (67%) | 11/12 (92%) | 12/12 (100%) | 11/12 (92%) | 12/12 (100%) | 11/12 (92%) | 8/12 (67%) | 10/12 (83%) | 10/12 (83%) | 10/12 (83%) | 12/12 (100%) |
| order_lookup | 12 | 7/12 (58%) | 7/12 (58%) | 9/12 (75%) | 12/12 (100%) | 9/12 (75%) | 12/12 (100%) | 11/12 (92%) | 7/12 (58%) | 7/12 (58%) | 1/1 (100%) | 1/1 (100%) | 12/12 (100%) |
| returns | 7 | 3/7 (43%) | 3/7 (43%) | 7/7 (100%) | 7/7 (100%) | 5/7 (71%) | 7/7 (100%) | 5/7 (71%) | 3/7 (43%) | 5/7 (71%) | - | - | 7/7 (100%) |
| unanswerable | 7 | 3/7 (43%) | 3/7 (43%) | 6/7 (86%) | 7/7 (100%) | 7/7 (100%) | 6/7 (86%) | 6/7 (86%) | 2/7 (29%) | 5/7 (71%) | 1/1 (100%) | 1/1 (100%) | 6/7 (86%) |
| escalation | 5 | 5/5 (100%) | 5/5 (100%) | 5/5 (100%) | 5/5 (100%) | 3/5 (60%) | 5/5 (100%) | 5/5 (100%) | 3/5 (60%) | 3/5 (60%) | - | - | 5/5 (100%) |
| adversarial | 5 | 1/5 (20%) | 1/5 (20%) | 5/5 (100%) | 5/5 (100%) | 5/5 (100%) | 5/5 (100%) | 4/5 (80%) | 1/5 (20%) | 4/5 (80%) | - | - | 4/5 (80%) |
| old_policy | 2 | 0/2 (0%) | 0/2 (0%) | 2/2 (100%) | 2/2 (100%) | 1/2 (50%) | 2/2 (100%) | 1/2 (50%) | 0/2 (0%) | 1/2 (50%) | 1/2 (50%) | 1/2 (50%) | 2/2 (100%) |
| **all** | 50 | **27/50 (54%)** | **27/50 (54%)** | **45/50 (90%)** | **50/50 (100%)** | **41/50 (82%)** | **49/50 (98%)** | **43/50 (86%)** | **24/50 (48%)** | **35/50 (70%)** | **13/16 (81%)** | **13/16 (81%)** | **48/50 (96%)** |

Latency per turn (model calls + tools + database): median 3.05 s, p95 5.07 s, max 7.72 s over 51 turns.
Model calls: 139; mean prompt tokens 1482, mean completion tokens 39.
Unanswerable cases that passed escalation by offering a hand-off: 3: una-f01, una-f03, una-f04
Cases that errored (scored as failures): 0.
Tool-call format errors (a call left as text, or an empty reply): 0.
Grounding: 2 of 51 replies have an issue (4 per 100 replies), 2 issues.

Failed cases: adv-f01, adv-f02, adv-f03, adv-f05, esc-f02, esc-f03, old-f01, old-f02, ord-f02, ord-f04, ord-f06, ord-f11, ord-f12, pol-f03, pol-f05, pol-f11, pol-f12, ret-f02, ret-f04, ret-f06, ret-f07, una-f01, una-f03, una-f04, una-f05, una-f07

Grounding issues:
- adv-f01: number 11587 not in tool results
- una-f07: number 360 not in tool results

### Every layer, per category (metrics `layers-v1`, evals/metrics.py)

| Category | n | searched | recall@3 | MRR | right tools | exact args | rejected / 100 calls | format errors / 100 model calls | cases with an unneeded call | end state right | fallback turns |
|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 12 | 11/12 92% [75–100] | 11/11 100% [100–100] | 0.95 | 8/12 67% [42–92] | 8/12 67% [42–92] | 0.0 (0/17) | 0.0 (0/28) | 0/12 | 12/12 100% [100–100] | 1 |
| order_lookup | 12 | 1/1 100% [100–100] | 1/1 100% [100–100] | 0.50 | 7/12 58% [25–83] | 7/12 58% [25–83] | 0.0 (0/22) | 0.0 (0/33) | 0/12 | 11/12 92% [75–100] | 0 |
| returns | 7 | - | - | - | 3/7 43% [14–86] | 3/7 43% [14–86] | 0.0 (0/23) | 0.0 (0/28) | 0/7 | 7/7 100% [100–100] | 2 |
| unanswerable | 7 | 1/1 100% [100–100] | 1/1 100% [100–100] | 1.00 | 3/7 43% [14–86] | 3/7 43% [14–86] | 0.0 (0/7) | 0.0 (0/14) | 0/7 | 6/7 86% [57–100] | 0 |
| escalation | 5 | - | - | - | 5/5 100% [100–100] | 5/5 100% [100–100] | 0.0 (0/13) | 0.0 (0/15) | 0/5 | 5/5 100% [100–100] | 0 |
| adversarial | 5 | - | - | - | 1/5 20% [0–60] | 1/5 20% [0–60] | 0.0 (0/10) | 0.0 (0/14) | 2/5 | 4/5 80% [40–100] | 0 |
| old_policy | 2 | 2/2 100% [100–100] | 2/2 100% [100–100] | 1.00 | 2/2 100% [100–100] | 0/2 0% [0–0] | 0.0 (0/6) | 0.0 (0/7) | 0/2 | 2/2 100% [100–100] | 1 |
| **all** | 50 | 15/16 94% [81–100] | 15/15 100% [100–100] | 0.93 | 29/50 58% [44–72] | 27/50 54% [40–68] | 0.0 (0/98) | 0.0 (0/139) | 2/50 | 47/50 94% [88–100] | 4 |

| Category | n | grounding issues / 100 replies | facts | no forbidden | privacy violations | return claimed done | customer turns | tokens / conversation | latency p50 / p95 (s) |
|---|---|---|---|---|---|---|---|---|---|
| policy | 12 | 0.0 (0/12) | 11/12 92% [75–100] | 12/12 100% [100–100] | 0 | 0 | 1.0 | 3,357 | 2.37 / 4.62 |
| order_lookup | 12 | 0.0 (0/12) | 9/12 75% [50–100] | 12/12 100% [100–100] | 0 | 0 | 1.0 | 4,138 | 3.31 / 4.42 |
| returns | 7 | 0.0 (0/7) | 5/7 71% [43–100] | 7/7 100% [100–100] | 0 | 0 | 1.0 | 6,673 | 4.13 / 4.59 |
| unanswerable | 7 | 14.3 (1/7) | 7/7 100% [100–100] | 6/7 86% [57–100] | 0 | 0 | 1.0 | 2,550 | 1.42 / 3.16 |
| escalation | 5 | 0.0 (0/5) | 3/5 60% [20–100] | 5/5 100% [100–100] | 0 | 0 | 1.0 | 4,935 | 3.46 / 5.92 |
| adversarial | 5 | 16.7 (1/6) | 5/5 100% [100–100] | 5/5 100% [100–100] | 0 | 0 | 1.2 | 4,176 | 2.40 / 3.40 |
| old_policy | 2 | 0.0 (0/2) | 1/2 50% [0–100] | 2/2 100% [100–100] | 0 | 0 | 1.0 | 5,689 | 7.72 / 7.72 |
| **all** | 50 | 3.9 (2/51) | 41/50 82% [70–92] | 49/50 98% [94–100] | 0 | 0 | 1.0 | 4,229 | 3.05 / 5.07 |

Tool confusion (expected against called):

| expected ↓ / called → | list | status | tracking | search | propose | escalate | (none) |
|---|---|---|---|---|---|---|---|
| list | **21** | · | · | · | · | · | 1 |
| status | · | **9** | · | · | · | · | 1 |
| tracking | · | 1 | **13** | · | · | · | 1 |
| search | · | · | · | **20** | · | · | 1 |
| propose | · | · | · | · | **5** | · | · |
| escalate | · | · | · | · | · | **6** | 4 |
| (none) | 5 | 4 | 4 | 8 | · | 2 | · |
