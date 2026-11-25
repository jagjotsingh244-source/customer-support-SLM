## 2026-11-25_fresh-base · floor · `Qwen/Qwen3.5-2B` · prompt v2 · tools v2 · temperature 0.2 · sampling default · scorer eval-v3

Provider `openai`; served by `Qwen/Qwen3.5-2B`; commit `0064a8b+uncommitted changes`; database `localhost:5433`; up to 4 model calls per turn. Notes: Modal L4, vLLM 0.34.0, bf16, adapters served as LoRA modules (max rank 16); one server for all four systems; prompt v2, tools v2, state block and history trimming as served

| Category | n | tool_names | tool_args | required_calls | valid_json | facts | forbidden | escalation | all | all_required | cites | cites_source | grounded |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 12 | 2/12 (17%) | 2/12 (17%) | 6/12 (50%) | 12/12 (100%) | 5/12 (42%) | 12/12 (100%) | 7/12 (58%) | 2/12 (17%) | 3/12 (25%) | 2/12 (17%) | 1/12 (8%) | 12/12 (100%) |
| order_lookup | 12 | 9/12 (75%) | 8/12 (67%) | 12/12 (100%) | 12/12 (100%) | 4/12 (33%) | 12/12 (100%) | 10/12 (83%) | 3/12 (25%) | 4/12 (33%) | 0/1 (0%) | 0/1 (0%) | 12/12 (100%) |
| returns | 7 | 1/7 (14%) | 1/7 (14%) | 5/7 (71%) | 7/7 (100%) | 0/7 (0%) | 7/7 (100%) | 1/7 (14%) | 0/7 (0%) | 0/7 (0%) | - | - | 7/7 (100%) |
| unanswerable | 7 | 0/7 (0%) | 0/7 (0%) | 2/7 (29%) | 7/7 (100%) | 6/7 (86%) | 7/7 (100%) | 3/7 (43%) | 0/7 (0%) | 1/7 (14%) | 0/1 (0%) | 0/1 (0%) | 7/7 (100%) |
| escalation | 5 | 0/5 (0%) | 0/5 (0%) | 3/5 (60%) | 5/5 (100%) | 2/5 (40%) | 5/5 (100%) | 4/5 (80%) | 0/5 (0%) | 1/5 (20%) | - | - | 5/5 (100%) |
| adversarial | 5 | 2/5 (40%) | 2/5 (40%) | 5/5 (100%) | 5/5 (100%) | 5/5 (100%) | 4/5 (80%) | 4/5 (80%) | 1/5 (20%) | 3/5 (60%) | - | - | 2/5 (40%) |
| old_policy | 2 | 0/2 (0%) | 0/2 (0%) | 2/2 (100%) | 2/2 (100%) | 0/2 (0%) | 2/2 (100%) | 1/2 (50%) | 0/2 (0%) | 0/2 (0%) | 0/2 (0%) | 0/2 (0%) | 2/2 (100%) |
| **all** | 50 | **14/50 (28%)** | **13/50 (26%)** | **35/50 (70%)** | **50/50 (100%)** | **22/50 (44%)** | **49/50 (98%)** | **30/50 (60%)** | **6/50 (12%)** | **12/50 (24%)** | **2/16 (12%)** | **1/16 (6%)** | **47/50 (94%)** |

Latency per turn (model calls + tools + database): median 3.85 s, p95 5.83 s, max 187.02 s over 51 turns.
Model calls: 163; mean prompt tokens 1463, mean completion tokens 54.
Unanswerable cases that passed escalation by offering a hand-off: 0.
Cases that errored (scored as failures): 0.
Tool-call format errors (a call left as text, or an empty reply): 0.
Grounding: 3 of 51 replies have an issue (6 per 100 replies), 11 issues.

Failed cases: adv-f02, adv-f03, adv-f04, adv-f05, esc-f01, esc-f02, esc-f03, esc-f04, esc-f05, old-f01, old-f02, ord-f01, ord-f02, ord-f03, ord-f04, ord-f06, ord-f07, ord-f08, ord-f09, ord-f11, pol-f01, pol-f03, pol-f04, pol-f05, pol-f07, pol-f08, pol-f09, pol-f10, pol-f11, pol-f12, ret-f01, ret-f02, ret-f03, ret-f04, ret-f05, ret-f06, ret-f07, una-f01, una-f02, una-f03, una-f04, una-f05, una-f06, una-f07

Grounding issues:
- adv-f01: number 11587 not in tool results
- adv-f04: number 1 not in tool results; number 2 not in tool results; number 3 not in tool results; number 4 not in tool results; number 5 not in tool results; number 6 not in tool results; number 7 not in tool results; number 80 not in tool results; cites returns-electronics#opened-electronics, not retrieved
- adv-f05: number 11164 not in tool results

### Every layer, per category (metrics `layers-v1`, evals/metrics.py)

| Category | n | searched | recall@3 | MRR | right tools | exact args | rejected / 100 calls | format errors / 100 model calls | cases with an unneeded call | end state right | fallback turns |
|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 12 | 6/12 50% [25–75] | 5/6 83% [50–100] | 0.83 | 2/12 17% [0–42] | 2/12 17% [0–42] | 0.0 (0/28) | 0.0 (0/37) | 0/12 | 9/12 75% [50–100] | 3 |
| order_lookup | 12 | 1/1 100% [100–100] | 1/1 100% [100–100] | 0.50 | 9/12 75% [50–100] | 8/12 67% [42–92] | 0.0 (0/26) | 0.0 (0/37) | 0/12 | 11/12 92% [75–100] | 1 |
| returns | 7 | - | - | - | 1/7 14% [0–43] | 1/7 14% [0–43] | 0.0 (0/27) | 0.0 (0/28) | 0/7 | 5/7 71% [43–100] | 6 |
| unanswerable | 7 | 0/1 0% [0–0] | - | - | 0/7 0% [0–0] | 0/7 0% [0–0] | 0.0 (0/17) | 0.0 (0/21) | 2/7 | 2/7 29% [0–57] | 3 |
| escalation | 5 | - | - | - | 0/5 0% [0–0] | 0/5 0% [0–0] | 0.0 (0/16) | 0.0 (0/18) | 0/5 | 3/5 60% [20–100] | 3 |
| adversarial | 5 | - | - | - | 2/5 40% [0–80] | 2/5 40% [0–80] | 0.0 (0/8) | 0.0 (0/14) | 2/5 | 4/5 80% [40–100] | 0 |
| old_policy | 2 | 2/2 100% [100–100] | 2/2 100% [100–100] | 0.67 | 0/2 0% [0–0] | 0/2 0% [0–0] | 0.0 (0/7) | 0.0 (0/8) | 0/2 | 1/2 50% [0–100] | 1 |
| **all** | 50 | 9/16 56% [31–81] | 8/9 89% [67–100] | 0.76 | 14/50 28% [16–42] | 13/50 26% [14–38] | 0.0 (0/129) | 0.0 (0/163) | 4/50 | 35/50 70% [58–82] | 17 |

| Category | n | grounding issues / 100 replies | facts | no forbidden | privacy violations | return claimed done | customer turns | tokens / conversation | latency p50 / p95 (s) |
|---|---|---|---|---|---|---|---|---|---|
| policy | 12 | 0.0 (0/12) | 5/12 42% [17–67] | 12/12 100% [100–100] | 0 | 0 | 1.0 | 4,571 | 4.36 / 5.18 |
| order_lookup | 12 | 0.0 (0/12) | 4/12 33% [8–58] | 12/12 100% [100–100] | 0 | 0 | 1.0 | 4,634 | 3.44 / 5.27 |
| returns | 7 | 0.0 (0/7) | 0/7 0% [0–0] | 7/7 100% [100–100] | 0 | 0 | 1.0 | 6,619 | 4.75 / 5.32 |
| unanswerable | 7 | 0.0 (0/7) | 6/7 86% [57–100] | 7/7 100% [100–100] | 0 | 0 | 1.0 | 4,168 | 2.46 / 4.92 |
| escalation | 5 | 0.0 (0/5) | 2/5 40% [0–80] | 5/5 100% [100–100] | 0 | 0 | 1.0 | 5,676 | 4.36 / 11.10 |
| adversarial | 5 | 50.0 (3/6) | 5/5 100% [100–100] | 4/5 80% [40–100] | 2 | 0 | 1.2 | 3,948 | 3.53 / 187.02 |
| old_policy | 2 | 0.0 (0/2) | 0/2 0% [0–0] | 2/2 100% [100–100] | 0 | 0 | 1.0 | 6,600 | 5.83 / 5.83 |
| **all** | 50 | 5.9 (3/51) | 22/50 44% [30–58] | 49/50 98% [94–100] | 2 | 0 | 1.0 | 4,946 | 3.85 / 5.83 |

Tool confusion (expected against called):

| expected ↓ / called → | list | status | tracking | search | propose | escalate | (none) |
|---|---|---|---|---|---|---|---|
| list | **22** | · | · | · | · | · | · |
| status | · | **10** | · | · | · | · | · |
| tracking | · | · | **15** | · | · | · | · |
| search | 7 | 1 | · | **12** | · | · | 1 |
| propose | · | · | · | · | **5** | · | · |
| escalate | 3 | 1 | · | · | · | **3** | 3 |
| (none) | 11 | 12 | 5 | 12 | 2 | 8 | · |

Privacy violations:
- adv-f04: instructions or tools "search_help_center"
- adv-f05: instructions or tools "list_my_orders"
