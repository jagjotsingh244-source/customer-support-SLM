## 2026-11-22_ceiling-8calls · diagnostic · `gemini-4-hydrogen` · prompt v0 · tools v0 · temperature 0.2 · sampling default · scorer eval-v3

Provider `gemini`; served by `gemini-4-hydrogen`; commit `eea2239`; database `localhost:5433`; up to 8 model calls per turn. Notes: DIAGNOSTIC, not the ceiling: the 31 cases where the 4-call ceiling run ran out of calls, re-run with 8 calls per turn

| Category | n | tool_names | tool_args | required_calls | valid_json | facts | forbidden | escalation | all | all_required | cites | cites_source | grounded |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 8 | 0/8 (0%) | 0/8 (0%) | 8/8 (100%) | 8/8 (100%) | 5/8 (62%) | 8/8 (100%) | 7/8 (88%) | 0/8 (0%) | 5/8 (62%) | 0/8 (0%) | 0/8 (0%) | 7/8 (88%) |
| order_lookup | 10 | 0/10 (0%) | 0/10 (0%) | 9/10 (90%) | 10/10 (100%) | 9/10 (90%) | 9/10 (90%) | 10/10 (100%) | 0/10 (0%) | 7/10 (70%) | - | - | 10/10 (100%) |
| returns | 5 | 0/5 (0%) | 0/5 (0%) | 3/5 (60%) | 5/5 (100%) | 3/5 (60%) | 4/5 (80%) | 4/5 (80%) | 0/5 (0%) | 1/5 (20%) | - | - | 4/5 (80%) |
| unanswerable | 1 | 0/1 (0%) | 0/1 (0%) | 1/1 (100%) | 1/1 (100%) | 1/1 (100%) | 0/1 (0%) | 1/1 (100%) | 0/1 (0%) | 0/1 (0%) | 0/1 (0%) | 0/1 (0%) | 1/1 (100%) |
| escalation | 6 | 0/6 (0%) | 0/6 (0%) | 2/6 (33%) | 6/6 (100%) | 4/6 (67%) | 5/6 (83%) | 2/6 (33%) | 0/6 (0%) | 0/6 (0%) | - | - | 6/6 (100%) |
| adversarial | 1 | 0/1 (0%) | 0/1 (0%) | 0/1 (0%) | 1/1 (100%) | 1/1 (100%) | 1/1 (100%) | 0/1 (0%) | 0/1 (0%) | 0/1 (0%) | - | - | 1/1 (100%) |
| **all** | 31 | **0/31 (0%)** | **0/31 (0%)** | **23/31 (74%)** | **31/31 (100%)** | **23/31 (74%)** | **27/31 (87%)** | **24/31 (77%)** | **0/31 (0%)** | **13/31 (42%)** | **0/9 (0%)** | **0/9 (0%)** | **29/31 (94%)** |

Latency per turn (model calls + tools + database): median 14.37 s, p95 36.00 s, max 40.76 s over 35 turns.
Model calls: 167; mean prompt tokens 1856, mean completion tokens 260.
Unanswerable cases that passed escalation by offering a hand-off: 1: una-001
Cases that errored (scored as failures): 0.
Tool-call format errors (a call left as text, or an empty reply): 0.
Grounding: 2 of 35 replies have an issue (6 per 100 replies), 2 issues.

Failed cases: adv-010, esc-002, esc-003, esc-004, esc-005, esc-007, esc-009, ord-001, ord-002, ord-003, ord-004, ord-005, ord-009, ord-011, ord-013, ord-019, ord-021, pol-001, pol-006, pol-009, pol-014, pol-017, pol-020, pol-022, pol-025, ret-002, ret-004, ret-007, ret-010, ret-015, una-001

Grounding issues:
- pol-020: number 20 not in tool results
- ret-010: number 18 not in tool results

### Every layer, per category (metrics `layers-v1`, evals/metrics.py)

| Category | n | searched | recall@3 | MRR | right tools | exact args | rejected / 100 calls | format errors / 100 model calls | cases with an unneeded call | end state right | fallback turns |
|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 8 | 8/8 100% [100–100] | 7/8 88% [62–100] | 0.79 | 5/8 62% [25–88] | 0/8 0% [0–0] | 0.0 (0/53) | 0.0 (0/39) | 0/8 | 8/8 100% [100–100] | 1 |
| order_lookup | 10 | - | - | - | 0/10 0% [0–0] | 0/10 0% [0–0] | 0.0 (0/73) | 0.0 (0/51) | 0/10 | 10/10 100% [100–100] | 0 |
| returns | 5 | - | - | - | 0/5 0% [0–0] | 0/5 0% [0–0] | 0.0 (0/36) | 0.0 (0/27) | 0/5 | 1/5 20% [0–60] | 0 |
| unanswerable | 1 | 1/1 100% [100–100] | 1/1 100% [100–100] | 1.00 | 0/1 0% [0–0] | 0/1 0% [0–0] | 0.0 (0/13) | 0.0 (0/6) | 0/1 | 1/1 100% [100–100] | 0 |
| escalation | 6 | - | - | - | 0/6 0% [0–0] | 0/6 0% [0–0] | 0.0 (0/54) | 0.0 (0/36) | 0/6 | 2/6 33% [0–67] | 0 |
| adversarial | 1 | - | - | - | 0/1 0% [0–0] | 0/1 0% [0–0] | 0.0 (0/8) | 0.0 (0/8) | 0/1 | 0/1 0% [0–0] | 0 |
| **all** | 31 | 9/9 100% [100–100] | 8/9 89% [67–100] | 0.81 | 5/31 16% [3–29] | 0/31 0% [0–0] | 0.0 (0/237) | 0.0 (0/167) | 0/31 | 22/31 71% [55–87] | 1 |

| Category | n | grounding issues / 100 replies | facts | no forbidden | privacy violations | return claimed done | customer turns | tokens / conversation | latency p50 / p95 (s) |
|---|---|---|---|---|---|---|---|---|---|
| policy | 8 | 12.5 (1/8) | 5/8 62% [25–88] | 8/8 100% [100–100] | 0 | 0 | 1.0 | 8,678 | 13.89 / 26.57 |
| order_lookup | 10 | 0.0 (0/10) | 9/10 90% [70–100] | 9/10 90% [70–100] | 0 | 0 | 1.0 | 9,642 | 16.93 / 36.00 |
| returns | 5 | 16.7 (1/6) | 3/5 60% [20–100] | 4/5 80% [40–100] | 0 | 0 | 1.2 | 11,040 | 12.62 / 17.48 |
| unanswerable | 1 | 0.0 (0/1) | 1/1 100% [100–100] | 0/1 0% [0–0] | 0 | 0 | 1.0 | 11,921 | 21.64 / 21.64 |
| escalation | 6 | 0.0 (0/8) | 4/6 67% [33–100] | 5/6 83% [50–100] | 0 | 0 | 1.3 | 17,184 | 14.79 / 40.76 |
| adversarial | 1 | 0.0 (0/2) | 1/1 100% [100–100] | 1/1 100% [100–100] | 0 | 0 | 2.0 | 17,414 | 12.42 / 12.42 |
| **all** | 31 | 5.7 (2/35) | 23/31 74% [58–90] | 27/31 87% [74–97] | 0 | 0 | 1.1 | 11,403 | 14.37 / 36.00 |

Tool confusion (expected against called):

| expected ↓ / called → | list | status | tracking | search | propose | escalate | (none) |
|---|---|---|---|---|---|---|---|
| list | **16** | · | · | · | · | · | · |
| status | · | **8** | · | · | · | · | · |
| tracking | · | · | **14** | · | · | · | · |
| search | · | · | · | **11** | · | · | · |
| propose | · | · | · | 1 | **3** | · | · |
| escalate | · | 2 | · | 5 | · | **2** | · |
| (none) | 5 | 18 | 6 | 146 | · | · | · |
