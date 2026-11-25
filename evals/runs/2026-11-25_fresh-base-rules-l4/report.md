## 2026-11-25_fresh-base-rules-l4 · floor · `Qwen/Qwen3.5-2B` · prompt v3 · tools v2 · guards on · hand-off rules on · temperature 0.2 · sampling default · scorer eval-v3

Provider `openai`; served by `Qwen/Qwen3.5-2B`; commit ``; database `localhost:5433`; up to 4 model calls per turn. Notes: GCP L4 (nova-eval9), vLLM 0.34.0, bf16, base + SFT-2a v1 as a LoRA module on one server

| Category | n | tool_names | tool_args | required_calls | valid_json | facts | forbidden | escalation | all | all_required | cites | cites_source | grounded |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 12 | 1/12 (8%) | 1/12 (8%) | 3/12 (25%) | 12/12 (100%) | 6/12 (50%) | 12/12 (100%) | 11/12 (92%) | 1/12 (8%) | 2/12 (17%) | 1/12 (8%) | 1/12 (8%) | 11/12 (92%) |
| order_lookup | 12 | 9/12 (75%) | 8/12 (67%) | 12/12 (100%) | 12/12 (100%) | 4/12 (33%) | 12/12 (100%) | 10/12 (83%) | 4/12 (33%) | 4/12 (33%) | 0/1 (0%) | 0/1 (0%) | 12/12 (100%) |
| returns | 7 | 2/7 (29%) | 2/7 (29%) | 4/7 (57%) | 7/7 (100%) | 2/7 (29%) | 7/7 (100%) | 3/7 (43%) | 1/7 (14%) | 2/7 (29%) | - | - | 7/7 (100%) |
| unanswerable | 7 | 0/7 (0%) | 0/7 (0%) | 4/7 (57%) | 7/7 (100%) | 6/7 (86%) | 7/7 (100%) | 4/7 (57%) | 0/7 (0%) | 2/7 (29%) | 0/1 (0%) | 0/1 (0%) | 7/7 (100%) |
| escalation | 5 | 2/5 (40%) | 2/5 (40%) | 3/5 (60%) | 5/5 (100%) | 3/5 (60%) | 5/5 (100%) | 3/5 (60%) | 1/5 (20%) | 1/5 (20%) | - | - | 5/5 (100%) |
| adversarial | 5 | 2/5 (40%) | 2/5 (40%) | 5/5 (100%) | 5/5 (100%) | 5/5 (100%) | 5/5 (100%) | 4/5 (80%) | 2/5 (40%) | 4/5 (80%) | - | - | 3/5 (60%) |
| old_policy | 2 | 0/2 (0%) | 0/2 (0%) | 2/2 (100%) | 2/2 (100%) | 2/2 (100%) | 2/2 (100%) | 2/2 (100%) | 0/2 (0%) | 2/2 (100%) | 0/2 (0%) | 0/2 (0%) | 2/2 (100%) |
| **all** | 50 | **16/50 (32%)** | **15/50 (30%)** | **33/50 (66%)** | **50/50 (100%)** | **28/50 (56%)** | **50/50 (100%)** | **37/50 (74%)** | **9/50 (18%)** | **17/50 (34%)** | **1/16 (6%)** | **1/16 (6%)** | **47/50 (94%)** |

Latency per turn (model calls + tools + database): median 2.70 s, p95 5.32 s, max 7.92 s over 51 turns.
Model calls: 157; mean prompt tokens 1539, mean completion tokens 52.
Unanswerable cases that passed escalation by offering a hand-off: 1: una-f01
Cases that errored (scored as failures): 0.
Tool-call format errors (a call left as text, or an empty reply): 0.
Grounding: 3 of 51 replies have an issue (6 per 100 replies), 3 issues.

Failed cases: adv-f02, adv-f03, adv-f05, esc-f01, esc-f02, esc-f03, esc-f04, old-f01, old-f02, ord-f01, ord-f02, ord-f03, ord-f04, ord-f06, ord-f07, ord-f08, ord-f11, pol-f01, pol-f03, pol-f04, pol-f05, pol-f06, pol-f07, pol-f08, pol-f09, pol-f10, pol-f11, pol-f12, ret-f01, ret-f02, ret-f03, ret-f05, ret-f06, ret-f07, una-f01, una-f02, una-f03, una-f04, una-f05, una-f06, una-f07

Grounding issues:
- adv-f01: number 11587 not in tool results
- adv-f05: number 11164 not in tool results
- pol-f04: number 3 not in tool results

### Every layer, per category (metrics `layers-v1`, evals/metrics.py)

| Category | n | searched | recall@3 | MRR | right tools | exact args | rejected / 100 calls | format errors / 100 model calls | cases with an unneeded call | end state right | fallback turns |
|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 12 | 3/12 25% [0–50] | 3/3 100% [100–100] | 0.83 | 1/12 8% [0–25] | 1/12 8% [0–25] | 0.0 (0/20) | 0.0 (0/32) | 0/12 | 11/12 92% [75–100] | 0 |
| order_lookup | 12 | 1/1 100% [100–100] | 1/1 100% [100–100] | 0.50 | 9/12 75% [50–100] | 8/12 67% [42–92] | 0.0 (0/29) | 0.0 (0/38) | 0/12 | 10/12 83% [58–100] | 1 |
| returns | 7 | - | - | - | 2/7 29% [0–57] | 2/7 29% [0–57] | 0.0 (0/24) | 0.0 (0/27) | 0/7 | 6/7 86% [57–100] | 4 |
| unanswerable | 7 | 1/1 100% [100–100] | 1/1 100% [100–100] | 1.00 | 0/7 0% [0–0] | 0/7 0% [0–0] | 0.0 (0/26) | 0.0 (0/27) | 2/7 | 3/7 43% [14–86] | 5 |
| escalation | 5 | - | - | - | 2/5 40% [0–80] | 2/5 40% [0–80] | 0.0 (0/12) | 0.0 (0/13) | 0/5 | 3/5 60% [20–100] | 0 |
| adversarial | 5 | - | - | - | 2/5 40% [0–80] | 2/5 40% [0–80] | 0.0 (0/8) | 0.0 (0/12) | 2/5 | 4/5 80% [40–100] | 0 |
| old_policy | 2 | 2/2 100% [100–100] | 2/2 100% [100–100] | 0.67 | 0/2 0% [0–0] | 0/2 0% [0–0] | 0.0 (0/7) | 0.0 (0/8) | 0/2 | 2/2 100% [100–100] | 0 |
| **all** | 50 | 7/16 44% [19–69] | 7/7 100% [100–100] | 0.76 | 16/50 32% [20–46] | 15/50 30% [18–44] | 0.0 (0/126) | 0.0 (0/157) | 4/50 | 39/50 78% [66–88] | 10 |

| Category | n | grounding issues / 100 replies | facts | no forbidden | privacy violations | return claimed done | customer turns | tokens / conversation | latency p50 / p95 (s) |
|---|---|---|---|---|---|---|---|---|---|
| policy | 12 | 8.3 (1/12) | 6/12 50% [25–75] | 12/12 100% [100–100] | 0 | 0 | 1.0 | 3,989 | 2.39 / 5.06 |
| order_lookup | 12 | 0.0 (0/12) | 4/12 33% [8–58] | 12/12 100% [100–100] | 0 | 0 | 1.0 | 5,142 | 2.68 / 4.98 |
| returns | 7 | 0.0 (0/7) | 2/7 29% [0–71] | 7/7 100% [100–100] | 0 | 0 | 1.0 | 6,576 | 3.74 / 4.93 |
| unanswerable | 7 | 0.0 (0/7) | 6/7 86% [57–100] | 7/7 100% [100–100] | 0 | 0 | 1.0 | 6,050 | 4.20 / 5.32 |
| escalation | 5 | 0.0 (0/5) | 3/5 60% [20–100] | 5/5 100% [100–100] | 0 | 0 | 1.0 | 4,122 | 2.06 / 2.81 |
| adversarial | 5 | 33.3 (2/6) | 5/5 100% [100–100] | 5/5 100% [100–100] | 0 | 0 | 1.2 | 3,444 | 1.77 / 6.68 |
| old_policy | 2 | 0.0 (0/2) | 2/2 100% [100–100] | 2/2 100% [100–100] | 0 | 0 | 1.0 | 7,040 | 7.92 / 7.92 |
| **all** | 50 | 5.9 (3/51) | 28/50 56% [42–70] | 50/50 100% [100–100] | 0 | 0 | 1.0 | 4,997 | 2.70 / 5.32 |

Tool confusion (expected against called):

| expected ↓ / called → | list | status | tracking | search | propose | escalate | (none) |
|---|---|---|---|---|---|---|---|
| list | **22** | · | · | · | · | · | · |
| status | · | **10** | · | · | · | · | · |
| tracking | · | · | **15** | · | · | · | · |
| search | 8 | 1 | · | **11** | · | · | 1 |
| propose | · | · | · | 1 | **4** | · | · |
| escalate | 3 | · | 1 | · | · | **4** | 2 |
| (none) | 10 | 9 | 11 | 11 | · | 5 | · |
