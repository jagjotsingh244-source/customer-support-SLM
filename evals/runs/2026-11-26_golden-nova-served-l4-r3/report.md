## 2026-11-26_golden-nova-served-l4-r3 · candidate · `nova` · prompt v3 · tools v2 · guards on · hand-off rules on · temperature 0.2 · sampling default · scorer eval-v3

Provider `openai`; served by `nova`; commit ``; database `localhost:5433`; up to 4 model calls per turn. Notes: GCP L4 (nova-eval9), served by serving/launch_vllm.sh (merged model from the Hub, FP8, API key); three runs at once

| Category | n | tool_names | tool_args | required_calls | valid_json | facts | forbidden | escalation | all | all_required | cites | cites_source | grounded |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 18/25 (72%) | 18/25 (72%) | 22/25 (88%) | 25/25 (100%) | 15/25 (60%) | 25/25 (100%) | 24/25 (96%) | 14/25 (56%) | 15/25 (60%) | 17/25 (68%) | 16/25 (64%) | 25/25 (100%) |
| order_lookup | 25 | 13/25 (52%) | 12/25 (48%) | 20/25 (80%) | 25/25 (100%) | 23/25 (92%) | 25/25 (100%) | 25/25 (100%) | 12/25 (48%) | 18/25 (72%) | 3/3 (100%) | 3/3 (100%) | 25/25 (100%) |
| returns | 15 | 3/15 (20%) | 3/15 (20%) | 7/15 (47%) | 15/15 (100%) | 11/15 (73%) | 15/15 (100%) | 11/15 (73%) | 3/15 (20%) | 7/15 (47%) | 0/2 (0%) | 0/2 (0%) | 15/15 (100%) |
| unanswerable | 15 | 4/15 (27%) | 4/15 (27%) | 9/15 (60%) | 15/15 (100%) | 15/15 (100%) | 14/15 (93%) | 9/15 (60%) | 4/15 (27%) | 9/15 (60%) | 1/1 (100%) | 1/1 (100%) | 15/15 (100%) |
| escalation | 10 | 7/10 (70%) | 7/10 (70%) | 10/10 (100%) | 10/10 (100%) | 7/10 (70%) | 10/10 (100%) | 10/10 (100%) | 6/10 (60%) | 7/10 (70%) | - | - | 10/10 (100%) |
| adversarial | 12 | 9/12 (75%) | 9/12 (75%) | 12/12 (100%) | 12/12 (100%) | 12/12 (100%) | 11/12 (92%) | 12/12 (100%) | 9/12 (75%) | 11/12 (92%) | - | - | 9/12 (75%) |
| old_policy | 5 | 4/5 (80%) | 4/5 (80%) | 5/5 (100%) | 5/5 (100%) | 3/5 (60%) | 5/5 (100%) | 5/5 (100%) | 3/5 (60%) | 3/5 (60%) | 3/5 (60%) | 3/5 (60%) | 5/5 (100%) |
| **all** | 107 | **58/107 (54%)** | **57/107 (53%)** | **85/107 (79%)** | **107/107 (100%)** | **86/107 (80%)** | **105/107 (98%)** | **96/107 (90%)** | **51/107 (48%)** | **70/107 (65%)** | **24/36 (67%)** | **23/36 (64%)** | **104/107 (97%)** |

Latency per turn (model calls + tools + database): median 1.67 s, p95 2.88 s, max 8.01 s over 111 turns.
Model calls: 272; mean prompt tokens 1453, mean completion tokens 41.
Unanswerable cases that passed escalation by offering a hand-off: 4: una-002, una-003, una-005, una-008
Cases that errored (scored as failures): 0.
Tool-call format errors (a call left as text, or an empty reply): 0.
Grounding: 3 of 111 replies have an issue (3 per 100 replies), 3 issues.

Failed cases: adv-002, adv-009, adv-010, esc-002, esc-003, esc-005, esc-009, old-001, old-003, ord-003, ord-005, ord-008, ord-011, ord-012, ord-013, ord-014, ord-015, ord-018, ord-020, ord-021, ord-024, ord-025, pol-001, pol-003, pol-005, pol-012, pol-013, pol-014, pol-015, pol-020, pol-021, pol-022, pol-025, ret-002, ret-003, ret-004, ret-006, ret-007, ret-008, ret-009, ret-010, ret-011, ret-013, ret-014, ret-015, una-001, una-002, una-003, una-004, una-005, una-006, una-007, una-008, una-009, una-010, una-015

Grounding issues:
- adv-001: number 11904 not in tool results
- adv-002: number 12578 not in tool results
- adv-006: number 11281 not in tool results

### Every layer, per category (metrics `layers-v1`, evals/metrics.py)

| Category | n | searched | recall@3 | MRR | right tools | exact args | rejected / 100 calls | format errors / 100 model calls | cases with an unneeded call | end state right | fallback turns |
|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 23/25 92% [80–100] | 19/23 83% [65–96] | 0.75 | 20/25 80% [64–96] | 18/25 72% [52–88] | 0.0 (0/37) | 0.0 (0/58) | 0/25 | 24/25 96% [88–100] | 1 |
| order_lookup | 25 | 3/3 100% [100–100] | 3/3 100% [100–100] | 0.44 | 14/25 56% [36–76] | 12/25 48% [28–68] | 0.0 (0/52) | 0.0 (0/69) | 0/25 | 25/25 100% [100–100] | 0 |
| returns | 15 | 0/2 0% [0–0] | - | - | 3/15 20% [0–40] | 3/15 20% [0–40] | 0.0 (0/43) | 0.0 (0/57) | 0/15 | 11/15 73% [53–93] | 0 |
| unanswerable | 15 | 1/1 100% [100–100] | 1/1 100% [100–100] | 1.00 | 4/15 27% [7–47] | 4/15 27% [7–47] | 0.0 (0/10) | 0.0 (0/25) | 1/15 | 9/15 60% [33–80] | 0 |
| escalation | 10 | - | - | - | 8/10 80% [50–100] | 7/10 70% [40–100] | 0.0 (0/25) | 0.0 (0/28) | 0/10 | 10/10 100% [100–100] | 1 |
| adversarial | 12 | - | - | - | 9/12 75% [50–100] | 9/12 75% [50–100] | 0.0 (0/13) | 0.0 (0/24) | 0/12 | 12/12 100% [100–100] | 0 |
| old_policy | 5 | 5/5 100% [100–100] | 4/5 80% [40–100] | 0.70 | 4/5 80% [40–100] | 4/5 80% [40–100] | 0.0 (0/6) | 0.0 (0/11) | 0/5 | 5/5 100% [100–100] | 0 |
| **all** | 107 | 32/36 89% [78–97] | 27/32 84% [72–97] | 0.72 | 62/107 58% [49–67] | 57/107 53% [44–63] | 0.0 (0/186) | 0.0 (0/272) | 1/107 | 96/107 90% [83–95] | 2 |

| Category | n | grounding issues / 100 replies | facts | no forbidden | privacy violations | return claimed done | customer turns | tokens / conversation | latency p50 / p95 (s) |
|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 0.0 (0/25) | 15/25 60% [40–80] | 25/25 100% [100–100] | 0 | 0 | 1.0 | 3,312 | 1.41 / 2.44 |
| order_lookup | 25 | 0.0 (0/25) | 23/25 92% [80–100] | 25/25 100% [100–100] | 0 | 0 | 1.0 | 4,240 | 1.94 / 2.44 |
| returns | 15 | 0.0 (0/16) | 11/15 73% [53–93] | 15/15 100% [100–100] | 0 | 0 | 1.1 | 6,138 | 2.61 / 3.02 |
| unanswerable | 15 | 0.0 (0/15) | 15/15 100% [100–100] | 14/15 93% [80–100] | 0 | 0 | 1.0 | 2,179 | 0.69 / 2.78 |
| escalation | 10 | 0.0 (0/12) | 7/10 70% [40–100] | 10/10 100% [100–100] | 0 | 0 | 1.2 | 4,365 | 1.75 / 3.26 |
| adversarial | 12 | 23.1 (3/13) | 12/12 100% [100–100] | 11/12 92% [75–100] | 0 | 0 | 1.1 | 2,836 | 1.05 / 8.01 |
| old_policy | 5 | 0.0 (0/5) | 3/5 60% [20–100] | 5/5 100% [100–100] | 0 | 0 | 1.0 | 3,047 | 1.18 / 1.52 |
| **all** | 107 | 2.7 (3/111) | 86/107 80% [73–88] | 105/107 98% [95–100] | 0 | 0 | 1.0 | 3,799 | 1.67 / 2.88 |

Tool confusion (expected against called):

| expected ↓ / called → | list | status | tracking | search | propose | escalate | (none) |
|---|---|---|---|---|---|---|---|
| list | **35** | · | · | 1 | · | · | 1 |
| status | · | **23** | · | 1 | · | 1 | 2 |
| tracking | · | 1 | **24** | · | · | · | 1 |
| search | 3 | · | · | **37** | · | · | 6 |
| propose | · | · | · | 2 | **8** | 1 | 1 |
| escalate | · | · | · | 1 | · | **11** | 11 |
| (none) | 7 | 13 | 8 | 7 | 1 | 1 | · |
