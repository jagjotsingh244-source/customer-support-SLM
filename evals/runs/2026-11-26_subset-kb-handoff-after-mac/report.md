## 2026-11-26_subset-kb-handoff-after-mac · diagnostic · `nova` · prompt v3 · tools v2 · guards on · hand-off rules on · temperature 0.2 · sampling default · scorer eval-v4

Provider `openai`; served by `nova`; commit `b3f8114+uncommitted changes`; database `localhost:5433`; up to 4 model calls per turn. Notes: local bf16 GGUF; help-center wording and hand-off note changes; affected cases only

| Category | n | tool_names | tool_args | required_calls | valid_json | facts | forbidden | escalation | all | all_required | cites | cites_source | grounded |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 5 | 3/5 (60%) | 3/5 (60%) | 5/5 (100%) | 5/5 (100%) | 4/5 (80%) | 5/5 (100%) | 5/5 (100%) | 3/5 (60%) | 4/5 (80%) | 4/5 (80%) | 4/5 (80%) | 5/5 (100%) |
| order_lookup | 1 | 0/1 (0%) | 0/1 (0%) | 1/1 (100%) | 1/1 (100%) | 1/1 (100%) | 1/1 (100%) | 1/1 (100%) | 0/1 (0%) | 1/1 (100%) | 1/1 (100%) | 1/1 (100%) | 1/1 (100%) |
| escalation | 10 | 7/10 (70%) | 7/10 (70%) | 10/10 (100%) | 10/10 (100%) | 10/10 (100%) | 10/10 (100%) | 10/10 (100%) | 7/10 (70%) | 10/10 (100%) | - | - | 10/10 (100%) |
| adversarial | 1 | 0/1 (0%) | 0/1 (0%) | 1/1 (100%) | 1/1 (100%) | 1/1 (100%) | 1/1 (100%) | 1/1 (100%) | 0/1 (0%) | 1/1 (100%) | - | - | 1/1 (100%) |
| old_policy | 5 | 4/5 (80%) | 4/5 (80%) | 5/5 (100%) | 5/5 (100%) | 4/5 (80%) | 5/5 (100%) | 5/5 (100%) | 4/5 (80%) | 4/5 (80%) | 4/5 (80%) | 3/5 (60%) | 4/5 (80%) |
| **all** | 22 | **14/22 (64%)** | **14/22 (64%)** | **22/22 (100%)** | **22/22 (100%)** | **20/22 (91%)** | **22/22 (100%)** | **22/22 (100%)** | **14/22 (64%)** | **20/22 (91%)** | **9/11 (82%)** | **8/11 (73%)** | **21/22 (95%)** |

Latency per turn (model calls + tools + database): median 22.47 s, p95 45.67 s, max 53.43 s over 25 turns.
Model calls: 60; mean prompt tokens 1490, mean completion tokens 43.
Unanswerable cases that passed escalation by offering a hand-off: 0.
Cases that errored (scored as failures): 0.
Tool-call format errors (a call left as text, or an empty reply): 0.
Grounding: 1 of 25 replies have an issue (4 per 100 replies), 1 issues.

Failed cases: adv-010, esc-003, esc-005, esc-009, old-003, ord-025, pol-005, pol-015

Grounding issues:
- old-002: number 30 not in tool results

### Every layer, per category (metrics `layers-v1`, evals/metrics.py)

| Category | n | searched | recall@3 | MRR | right tools | exact args | rejected / 100 calls | format errors / 100 model calls | cases with an unneeded call | end state right | fallback turns |
|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 5 | 5/5 100% [100–100] | 4/5 80% [40–100] | 0.57 | 3/5 60% [20–100] | 3/5 60% [20–100] | 0.0 (0/7) | 0.0 (0/12) | 0/5 | 5/5 100% [100–100] | 0 |
| order_lookup | 1 | 1/1 100% [100–100] | 1/1 100% [100–100] | 0.50 | 0/1 0% [0–0] | 0/1 0% [0–0] | 0.0 (0/3) | 0.0 (0/3) | 0/1 | 1/1 100% [100–100] | 0 |
| escalation | 10 | - | - | - | 8/10 80% [50–100] | 7/10 70% [40–100] | 0.0 (0/25) | 0.0 (0/29) | 0/10 | 10/10 100% [100–100] | 0 |
| adversarial | 1 | - | - | - | 0/1 0% [0–0] | 0/1 0% [0–0] | 0.0 (0/5) | 0.0 (0/5) | 0/1 | 1/1 100% [100–100] | 0 |
| old_policy | 5 | 5/5 100% [100–100] | 5/5 100% [100–100] | 0.80 | 4/5 80% [40–100] | 4/5 80% [40–100] | 0.0 (0/6) | 0.0 (0/11) | 0/5 | 5/5 100% [100–100] | 0 |
| **all** | 22 | 11/11 100% [100–100] | 10/11 91% [73–100] | 0.67 | 15/22 68% [45–86] | 14/22 64% [41–82] | 0.0 (0/46) | 0.0 (0/60) | 0/22 | 22/22 100% [100–100] | 0 |

| Category | n | grounding issues / 100 replies | facts | no forbidden | privacy violations | return claimed done | customer turns | tokens / conversation | latency p50 / p95 (s) |
|---|---|---|---|---|---|---|---|---|---|
| policy | 5 | 0.0 (0/5) | 4/5 80% [40–100] | 5/5 100% [100–100] | 0 | 0 | 1.0 | 3,306 | 19.64 / 29.45 |
| order_lookup | 1 | 0.0 (0/1) | 1/1 100% [100–100] | 1/1 100% [100–100] | 0 | 0 | 1.0 | 4,953 | 21.17 / 21.17 |
| escalation | 10 | 0.0 (0/12) | 10/10 100% [100–100] | 10/10 100% [100–100] | 0 | 0 | 1.2 | 4,654 | 26.24 / 53.43 |
| adversarial | 1 | 0.0 (0/2) | 1/1 100% [100–100] | 1/1 100% [100–100] | 0 | 0 | 2.0 | 8,455 | 33.36 / 33.36 |
| old_policy | 5 | 20.0 (1/5) | 4/5 80% [40–100] | 5/5 100% [100–100] | 0 | 0 | 1.0 | 3,097 | 21.93 / 28.38 |
| **all** | 22 | 4.0 (1/25) | 20/22 91% [77–100] | 22/22 100% [100–100] | 0 | 0 | 1.1 | 4,180 | 22.47 / 45.67 |

Tool confusion (expected against called):

| expected ↓ / called → | list | status | tracking | search | propose | escalate | (none) |
|---|---|---|---|---|---|---|---|
| list | **6** | · | · | · | · | · | · |
| status | · | **2** | · | · | · | · | · |
| tracking | · | · | **6** | · | · | · | · |
| search | · | · | · | **11** | · | · | · |
| propose | · | · | · | · | · | · | · |
| escalate | · | · | · | · | · | **11** | · |
| (none) | 5 | 4 | 1 | · | · | · | · |
