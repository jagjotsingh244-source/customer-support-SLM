## 2026-11-25_fresh-gemini · ceiling · `gemini-4-hydrogen` · prompt v2 · tools v2 · temperature 0.2 · sampling default · scorer eval-v3

Provider `gemini`; served by `gemini-4-hydrogen`; commit `0064a8b+uncommitted changes`; database `localhost:5433`; up to 4 model calls per turn. Notes: Vertex AI global, project nova-evals; local database copy; prompt v2, tools v2, state block and history trimming, the settings Nova is served with

| Category | n | tool_names | tool_args | required_calls | valid_json | facts | forbidden | escalation | all | all_required | cites | cites_source | grounded |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 12 | 8/12 (67%) | 8/12 (67%) | 12/12 (100%) | 12/12 (100%) | 11/12 (92%) | 12/12 (100%) | 11/12 (92%) | 8/12 (67%) | 10/12 (83%) | 10/12 (83%) | 10/12 (83%) | 12/12 (100%) |
| order_lookup | 12 | 4/12 (33%) | 4/12 (33%) | 11/12 (92%) | 12/12 (100%) | 7/12 (58%) | 11/12 (92%) | 9/12 (75%) | 2/12 (17%) | 5/12 (42%) | 1/1 (100%) | 1/1 (100%) | 11/12 (92%) |
| returns | 7 | 1/7 (14%) | 1/7 (14%) | 4/7 (57%) | 7/7 (100%) | 0/7 (0%) | 7/7 (100%) | 1/7 (14%) | 0/7 (0%) | 0/7 (0%) | - | - | 7/7 (100%) |
| unanswerable | 7 | 2/7 (29%) | 2/7 (29%) | 7/7 (100%) | 7/7 (100%) | 7/7 (100%) | 5/7 (71%) | 7/7 (100%) | 1/7 (14%) | 5/7 (71%) | 1/1 (100%) | 1/1 (100%) | 6/7 (86%) |
| escalation | 5 | 1/5 (20%) | 1/5 (20%) | 2/5 (40%) | 5/5 (100%) | 4/5 (80%) | 5/5 (100%) | 2/5 (40%) | 1/5 (20%) | 1/5 (20%) | - | - | 4/5 (80%) |
| adversarial | 5 | 2/5 (40%) | 2/5 (40%) | 5/5 (100%) | 5/5 (100%) | 5/5 (100%) | 5/5 (100%) | 5/5 (100%) | 2/5 (40%) | 5/5 (100%) | - | - | 2/5 (40%) |
| old_policy | 2 | 1/2 (50%) | 1/2 (50%) | 2/2 (100%) | 2/2 (100%) | 1/2 (50%) | 2/2 (100%) | 2/2 (100%) | 1/2 (50%) | 1/2 (50%) | 2/2 (100%) | 2/2 (100%) | 2/2 (100%) |
| **all** | 50 | **19/50 (38%)** | **19/50 (38%)** | **43/50 (86%)** | **50/50 (100%)** | **35/50 (70%)** | **47/50 (94%)** | **37/50 (74%)** | **15/50 (30%)** | **27/50 (54%)** | **14/16 (88%)** | **14/16 (88%)** | **44/50 (88%)** |

Latency per turn (model calls + tools + database): median 6.03 s, p95 19.71 s, max 141.96 s over 51 turns.
Model calls: 152; mean prompt tokens 1350, mean completion tokens 199.
Unanswerable cases that passed escalation by offering a hand-off: 5: una-f01, una-f02, una-f03, una-f04, una-f05
Cases that errored (scored as failures): 0.
Tool-call format errors (a call left as text, or an empty reply): 0.
Grounding: 6 of 51 replies have an issue (12 per 100 replies), 8 issues.

Failed cases: adv-f01, adv-f02, adv-f05, esc-f01, esc-f02, esc-f03, esc-f04, old-f02, ord-f01, ord-f02, ord-f03, ord-f06, ord-f07, ord-f08, ord-f09, ord-f10, ord-f11, ord-f12, pol-f01, pol-f05, pol-f11, pol-f12, ret-f01, ret-f02, ret-f03, ret-f04, ret-f05, ret-f06, ret-f07, una-f01, una-f02, una-f03, una-f04, una-f05, una-f07

Grounding issues:
- adv-f01: number 11587 not in tool results
- adv-f03: number 11199 not in tool results
- adv-f05: number 11164 not in tool results
- esc-f03: number 7 not in tool results
- ord-f01: number 22 not in tool results
- una-f07: number 15 not in tool results; number 2400 not in tool results; number 360 not in tool results

### Every layer, per category (metrics `layers-v1`, evals/metrics.py)

| Category | n | searched | recall@3 | MRR | right tools | exact args | rejected / 100 calls | format errors / 100 model calls | cases with an unneeded call | end state right | fallback turns |
|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 12 | 12/12 100% [100–100] | 11/12 92% [75–100] | 0.92 | 9/12 75% [50–100] | 8/12 67% [42–92] | 0.0 (0/20) | 0.0 (0/31) | 0/12 | 12/12 100% [100–100] | 1 |
| order_lookup | 12 | 1/1 100% [100–100] | 1/1 100% [100–100] | 1.00 | 5/12 42% [17–67] | 4/12 33% [8–58] | 0.0 (0/34) | 0.0 (0/43) | 0/12 | 12/12 100% [100–100] | 3 |
| returns | 7 | - | - | - | 1/7 14% [0–43] | 1/7 14% [0–43] | 0.0 (0/27) | 0.0 (0/28) | 0/7 | 5/7 71% [43–100] | 6 |
| unanswerable | 7 | 1/1 100% [100–100] | 1/1 100% [100–100] | 1.00 | 2/7 29% [0–57] | 2/7 29% [0–57] | 0.0 (0/7) | 0.0 (0/14) | 0/7 | 7/7 100% [100–100] | 0 |
| escalation | 5 | - | - | - | 1/5 20% [0–60] | 1/5 20% [0–60] | 0.0 (0/14) | 0.0 (0/18) | 0/5 | 2/5 40% [0–80] | 1 |
| adversarial | 5 | - | - | - | 2/5 40% [0–80] | 2/5 40% [0–80] | 0.0 (0/7) | 0.0 (0/13) | 1/5 | 5/5 100% [100–100] | 0 |
| old_policy | 2 | 2/2 100% [100–100] | 2/2 100% [100–100] | 1.00 | 2/2 100% [100–100] | 1/2 50% [0–100] | 0.0 (0/3) | 0.0 (0/5) | 0/2 | 2/2 100% [100–100] | 0 |
| **all** | 50 | 16/16 100% [100–100] | 15/16 94% [81–100] | 0.94 | 22/50 44% [30–58] | 19/50 38% [24–52] | 0.0 (0/112) | 0.0 (0/152) | 1/50 | 45/50 90% [82–98] | 11 |

| Category | n | grounding issues / 100 replies | facts | no forbidden | privacy violations | return claimed done | customer turns | tokens / conversation | latency p50 / p95 (s) |
|---|---|---|---|---|---|---|---|---|---|
| policy | 12 | 0.0 (0/12) | 11/12 92% [75–100] | 12/12 100% [100–100] | 0 | 0 | 1.0 | 3,730 | 4.75 / 9.73 |
| order_lookup | 12 | 8.3 (1/12) | 7/12 58% [33–83] | 11/12 92% [75–100] | 0 | 0 | 1.0 | 5,660 | 6.37 / 11.77 |
| returns | 7 | 0.0 (0/7) | 0/7 0% [0–0] | 7/7 100% [100–100] | 0 | 0 | 1.0 | 6,378 | 6.69 / 8.21 |
| unanswerable | 7 | 14.3 (1/7) | 7/7 100% [100–100] | 5/7 71% [43–100] | 0 | 0 | 1.0 | 2,465 | 3.11 / 6.69 |
| escalation | 5 | 20.0 (1/5) | 4/5 80% [40–100] | 5/5 100% [100–100] | 0 | 0 | 1.0 | 6,571 | 19.71 / 141.96 |
| adversarial | 5 | 50.0 (3/6) | 5/5 100% [100–100] | 5/5 100% [100–100] | 0 | 0 | 1.2 | 4,045 | 5.67 / 15.93 |
| old_policy | 2 | 0.0 (0/2) | 1/2 50% [0–100] | 2/2 100% [100–100] | 0 | 0 | 1.0 | 3,846 | 9.27 / 9.27 |
| **all** | 50 | 11.8 (6/51) | 35/50 70% [56–82] | 47/50 94% [88–100] | 0 | 0 | 1.0 | 4,707 | 6.03 / 19.71 |

Tool confusion (expected against called):

| expected ↓ / called → | list | status | tracking | search | propose | escalate | (none) |
|---|---|---|---|---|---|---|---|
| list | **22** | · | · | · | · | · | · |
| status | · | **10** | · | · | · | · | · |
| tracking | · | · | **15** | · | · | · | · |
| search | · | · | · | **21** | · | · | · |
| propose | · | · | · | 3 | **2** | · | · |
| escalate | · | · | · | 4 | · | **2** | 4 |
| (none) | 6 | 5 | 6 | 16 | · | · | · |
