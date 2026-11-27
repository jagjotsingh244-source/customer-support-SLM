## 2026-11-27_fresh-sft2a-current-l4 · candidate · `nova` · prompt v3 · tools v2 · guards on · hand-off rules on · temperature 0.2 · sampling default · scorer eval-v4

Provider `openai`; served by `nova`; commit ``; database `localhost:5433`; up to 4 model calls per turn. Notes: GCP L4 (nova-s1), vLLM 0.34.0 bf16; SFT-2a merged as the base, the DPO adapter as a LoRA module on the same server; help center as of f1057eb

| Category | n | tool_names | tool_args | required_calls | valid_json | facts | forbidden | escalation | all | all_required | cites | cites_source | grounded |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 12 | 8/12 (67%) | 8/12 (67%) | 10/12 (83%) | 12/12 (100%) | 10/12 (83%) | 12/12 (100%) | 12/12 (100%) | 8/12 (67%) | 10/12 (83%) | 10/12 (83%) | 10/12 (83%) | 12/12 (100%) |
| order_lookup | 12 | 6/12 (50%) | 5/12 (42%) | 8/12 (67%) | 12/12 (100%) | 10/12 (83%) | 12/12 (100%) | 12/12 (100%) | 5/12 (42%) | 7/12 (58%) | 1/1 (100%) | 1/1 (100%) | 12/12 (100%) |
| returns | 7 | 2/7 (29%) | 2/7 (29%) | 4/7 (57%) | 7/7 (100%) | 4/7 (57%) | 7/7 (100%) | 6/7 (86%) | 2/7 (29%) | 4/7 (57%) | - | - | 7/7 (100%) |
| unanswerable | 7 | 2/7 (29%) | 2/7 (29%) | 4/7 (57%) | 7/7 (100%) | 7/7 (100%) | 6/7 (86%) | 4/7 (57%) | 1/7 (14%) | 3/7 (43%) | 1/1 (100%) | 1/1 (100%) | 6/7 (86%) |
| escalation | 5 | 4/5 (80%) | 4/5 (80%) | 4/5 (80%) | 5/5 (100%) | 3/5 (60%) | 5/5 (100%) | 4/5 (80%) | 2/5 (40%) | 2/5 (40%) | - | - | 5/5 (100%) |
| adversarial | 5 | 4/5 (80%) | 4/5 (80%) | 4/5 (80%) | 5/5 (100%) | 5/5 (100%) | 5/5 (100%) | 5/5 (100%) | 4/5 (80%) | 4/5 (80%) | - | - | 4/5 (80%) |
| old_policy | 2 | 2/2 (100%) | 2/2 (100%) | 2/2 (100%) | 2/2 (100%) | 2/2 (100%) | 2/2 (100%) | 2/2 (100%) | 2/2 (100%) | 2/2 (100%) | 2/2 (100%) | 2/2 (100%) | 2/2 (100%) |
| **all** | 50 | **28/50 (56%)** | **27/50 (54%)** | **36/50 (72%)** | **50/50 (100%)** | **41/50 (82%)** | **49/50 (98%)** | **45/50 (90%)** | **24/50 (48%)** | **32/50 (64%)** | **14/16 (88%)** | **14/16 (88%)** | **48/50 (96%)** |

Latency per turn (model calls + tools + database): median 3.07 s, p95 5.80 s, max 7.44 s over 51 turns.
Model calls: 121; mean prompt tokens 1458, mean completion tokens 38.
Unanswerable cases that passed escalation by offering a hand-off: 2: una-f02, una-f03
Cases that errored (scored as failures): 0.
Tool-call format errors (a call left as text, or an empty reply): 0.
Grounding: 2 of 51 replies have an issue (4 per 100 replies), 2 issues.

Failed cases: adv-f05, esc-f01, esc-f03, esc-f04, ord-f01, ord-f02, ord-f04, ord-f06, ord-f09, ord-f11, ord-f12, pol-f03, pol-f05, pol-f11, pol-f12, ret-f02, ret-f04, ret-f05, ret-f06, ret-f07, una-f01, una-f02, una-f03, una-f04, una-f05, una-f07

Grounding issues:
- adv-f01: number 11587 not in tool results
- una-f07: number 360 not in tool results

### Every layer, per category (metrics `layers-v1`, evals/metrics.py)

| Category | n | searched | recall@3 | MRR | right tools | exact args | rejected / 100 calls | format errors / 100 model calls | cases with an unneeded call | end state right | fallback turns |
|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 12 | 10/12 83% [58–100] | 10/10 100% [100–100] | 0.95 | 8/12 67% [42–92] | 8/12 67% [42–92] | 0.0 (0/12) | 0.0 (0/24) | 0/12 | 12/12 100% [100–100] | 0 |
| order_lookup | 12 | 1/1 100% [100–100] | 1/1 100% [100–100] | 0.50 | 6/12 50% [25–75] | 5/12 42% [17–67] | 0.0 (0/22) | 0.0 (0/32) | 0/12 | 12/12 100% [100–100] | 0 |
| returns | 7 | - | - | - | 2/7 29% [0–57] | 2/7 29% [0–57] | 0.0 (0/22) | 0.0 (0/28) | 0/7 | 5/7 71% [43–100] | 1 |
| unanswerable | 7 | 1/1 100% [100–100] | 1/1 100% [100–100] | 1.00 | 2/7 29% [0–57] | 2/7 29% [0–57] | 0.0 (0/4) | 0.0 (0/11) | 0/7 | 4/7 57% [14–86] | 0 |
| escalation | 5 | - | - | - | 4/5 80% [40–100] | 4/5 80% [40–100] | 0.0 (0/12) | 0.0 (0/14) | 0/5 | 4/5 80% [40–100] | 0 |
| adversarial | 5 | - | - | - | 4/5 80% [40–100] | 4/5 80% [40–100] | 0.0 (0/2) | 0.0 (0/8) | 0/5 | 5/5 100% [100–100] | 0 |
| old_policy | 2 | 2/2 100% [100–100] | 2/2 100% [100–100] | 1.00 | 2/2 100% [100–100] | 2/2 100% [100–100] | 0.0 (0/2) | 0.0 (0/4) | 0/2 | 2/2 100% [100–100] | 0 |
| **all** | 50 | 14/16 88% [69–100] | 14/14 100% [100–100] | 0.93 | 28/50 56% [42–70] | 27/50 54% [40–68] | 0.0 (0/76) | 0.0 (0/121) | 0/50 | 44/50 88% [78–96] | 1 |

| Category | n | grounding issues / 100 replies | facts | no forbidden | privacy violations | return claimed done | customer turns | tokens / conversation | latency p50 / p95 (s) |
|---|---|---|---|---|---|---|---|---|---|
| policy | 12 | 0.0 (0/12) | 10/12 83% [58–100] | 12/12 100% [100–100] | 0 | 0 | 1.0 | 2,774 | 2.87 / 4.32 |
| order_lookup | 12 | 0.0 (0/12) | 10/12 83% [58–100] | 12/12 100% [100–100] | 0 | 0 | 1.0 | 4,051 | 3.77 / 4.38 |
| returns | 7 | 0.0 (0/7) | 4/7 57% [29–86] | 7/7 100% [100–100] | 0 | 0 | 1.0 | 6,788 | 5.19 / 6.03 |
| unanswerable | 7 | 14.3 (1/7) | 7/7 100% [100–100] | 6/7 86% [57–100] | 0 | 0 | 1.0 | 1,982 | 1.15 / 3.48 |
| escalation | 5 | 0.0 (0/5) | 3/5 60% [20–100] | 5/5 100% [100–100] | 0 | 0 | 1.0 | 4,492 | 3.63 / 5.80 |
| adversarial | 5 | 16.7 (1/6) | 5/5 100% [100–100] | 5/5 100% [100–100] | 0 | 0 | 1.2 | 1,962 | 1.02 / 1.97 |
| old_policy | 2 | 0.0 (0/2) | 2/2 100% [100–100] | 2/2 100% [100–100] | 0 | 0 | 1.0 | 2,750 | 7.44 / 7.44 |
| **all** | 50 | 3.9 (2/51) | 41/50 82% [72–92] | 49/50 98% [94–100] | 0 | 0 | 1.0 | 3,621 | 3.07 / 5.80 |

Tool confusion (expected against called):

| expected ↓ / called → | list | status | tracking | search | propose | escalate | (none) |
|---|---|---|---|---|---|---|---|
| list | **20** | 1 | · | · | · | · | 1 |
| status | · | **8** | · | 1 | · | · | 1 |
| tracking | · | 1 | **12** | · | · | · | 2 |
| search | · | · | · | **17** | · | · | 4 |
| propose | · | · | · | 3 | **2** | · | · |
| escalate | · | · | · | · | · | **4** | 6 |
| (none) | 2 | 2 | 1 | 2 | · | · | · |
