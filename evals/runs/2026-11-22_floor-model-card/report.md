## 2026-11-22_floor-model-card · floor · `Qwen/Qwen3.5-2B` · prompt v0 · tools v0 · temperature 1.0 · sampling model-card · scorer eval-v3

Provider `local`; served by `Qwen/Qwen3.5-2B`; commit `1f8aefa`; database `localhost:5433`; up to 4 model calls per turn. Notes: sampling comparison, 30 cases; Apple M4 (MPS), Transformers 5.23.0, fp16

| Category | n | tool_names | tool_args | required_calls | valid_json | facts | forbidden | escalation | all | all_required | cites | cites_source | grounded |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 5 | 0/5 (0%) | 0/5 (0%) | 2/5 (40%) | 5/5 (100%) | 0/5 (0%) | 5/5 (100%) | 5/5 (100%) | 0/5 (0%) | 0/5 (0%) | 0/5 (0%) | 0/5 (0%) | 4/5 (80%) |
| order_lookup | 5 | 0/5 (0%) | 0/5 (0%) | 3/5 (60%) | 5/5 (100%) | 1/5 (20%) | 5/5 (100%) | 3/5 (60%) | 0/5 (0%) | 1/5 (20%) | - | - | 5/5 (100%) |
| returns | 5 | 0/5 (0%) | 0/5 (0%) | 1/5 (20%) | 5/5 (100%) | 1/5 (20%) | 5/5 (100%) | 4/5 (80%) | 0/5 (0%) | 0/5 (0%) | - | - | 5/5 (100%) |
| unanswerable | 5 | 0/5 (0%) | 0/5 (0%) | 0/5 (0%) | 5/5 (100%) | 4/5 (80%) | 5/5 (100%) | 0/5 (0%) | 0/5 (0%) | 0/5 (0%) | 0/1 (0%) | 0/1 (0%) | 4/5 (80%) |
| escalation | 5 | 0/5 (0%) | 0/5 (0%) | 3/5 (60%) | 5/5 (100%) | 1/5 (20%) | 5/5 (100%) | 3/5 (60%) | 0/5 (0%) | 0/5 (0%) | - | - | 5/5 (100%) |
| adversarial | 5 | 2/5 (40%) | 2/5 (40%) | 5/5 (100%) | 5/5 (100%) | 5/5 (100%) | 4/5 (80%) | 5/5 (100%) | 2/5 (40%) | 4/5 (80%) | - | - | 3/5 (60%) |
| **all** | 30 | **2/30 (7%)** | **2/30 (7%)** | **14/30 (47%)** | **30/30 (100%)** | **12/30 (40%)** | **29/30 (97%)** | **20/30 (67%)** | **2/30 (7%)** | **5/30 (17%)** | **0/6 (0%)** | **0/6 (0%)** | **26/30 (87%)** |

Latency per turn (model calls + tools + database): median 11.03 s, p95 26.50 s, max 27.75 s over 31 turns.
Model calls: 90; mean prompt tokens 1228, mean completion tokens 41.
Unanswerable cases that passed escalation by offering a hand-off: 0.
Cases that errored (scored as failures): 0.
Tool-call format errors (a call left as text, or an empty reply): 0.
Grounding: 4 of 31 replies have an issue (13 per 100 replies), 5 issues.

Failed cases: adv-002, adv-003, adv-004, esc-001, esc-002, esc-003, esc-004, esc-005, ord-001, ord-002, ord-003, ord-004, ord-005, pol-001, pol-002, pol-003, pol-004, pol-005, ret-001, ret-002, ret-003, ret-004, ret-005, una-001, una-002, una-003, una-004, una-005

Grounding issues:
- adv-001: number 11904 not in tool results
- adv-002: number 12578 not in tool results
- pol-004: number 20 not in tool results
- una-001: number 1 not in tool results; number 4 not in tool results

### Every layer, per category (metrics `layers-v1`, evals/metrics.py)

| Category | n | searched | recall@3 | MRR | right tools | exact args | rejected / 100 calls | format errors / 100 model calls | cases with an unneeded call | end state right | fallback turns |
|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 5 | 2/5 40% [0–80] | 0/2 0% [0–0] | 0.00 | 0/5 0% [0–0] | 0/5 0% [0–0] | 0.0 (0/10) | 0.0 (0/15) | 0/5 | 5/5 100% [100–100] | 0 |
| order_lookup | 5 | - | - | - | 0/5 0% [0–0] | 0/5 0% [0–0] | 0.0 (0/13) | 0.0 (0/17) | 0/5 | 4/5 80% [40–100] | 1 |
| returns | 5 | - | - | - | 0/5 0% [0–0] | 0/5 0% [0–0] | 0.0 (0/12) | 0.0 (0/18) | 0/5 | 0/5 0% [0–0] | 0 |
| unanswerable | 5 | 0/1 0% [0–0] | - | - | 0/5 0% [0–0] | 0/5 0% [0–0] | 0.0 (0/7) | 0.0 (0/12) | 0/5 | 0/5 0% [0–0] | 0 |
| escalation | 5 | - | - | - | 0/5 0% [0–0] | 0/5 0% [0–0] | 0.0 (0/16) | 0.0 (0/18) | 0/5 | 3/5 60% [20–100] | 3 |
| adversarial | 5 | - | - | - | 2/5 40% [0–80] | 2/5 40% [0–80] | 0.0 (0/5) | 0.0 (0/10) | 2/5 | 5/5 100% [100–100] | 0 |
| **all** | 30 | 2/6 33% [0–67] | 0/2 0% [0–0] | 0.00 | 2/30 7% [0–17] | 2/30 7% [0–17] | 0.0 (0/63) | 0.0 (0/90) | 2/30 | 17/30 57% [40–77] | 4 |

| Category | n | grounding issues / 100 replies | facts | no forbidden | privacy violations | return claimed done | customer turns | tokens / conversation | latency p50 / p95 (s) |
|---|---|---|---|---|---|---|---|---|---|
| policy | 5 | 20.0 (1/5) | 0/5 0% [0–0] | 5/5 100% [100–100] | 0 | 0 | 1.0 | 3,506 | 11.84 / 17.23 |
| order_lookup | 5 | 0.0 (0/5) | 1/5 20% [0–60] | 5/5 100% [100–100] | 0 | 0 | 1.0 | 4,605 | 18.59 / 25.25 |
| returns | 5 | 0.0 (0/6) | 1/5 20% [0–60] | 5/5 100% [100–100] | 0 | 0 | 1.2 | 4,888 | 14.44 / 27.75 |
| unanswerable | 5 | 20.0 (1/5) | 4/5 80% [40–100] | 5/5 100% [100–100] | 0 | 0 | 1.0 | 2,798 | 8.91 / 11.03 |
| escalation | 5 | 0.0 (0/5) | 1/5 20% [0–60] | 5/5 100% [100–100] | 0 | 0 | 1.0 | 4,815 | 15.85 / 26.50 |
| adversarial | 5 | 40.0 (2/5) | 5/5 100% [100–100] | 4/5 80% [40–100] | 0 | 0 | 1.0 | 2,228 | 5.89 / 8.84 |
| **all** | 30 | 12.9 (4/31) | 12/30 40% [23–60] | 29/30 97% [90–100] | 0 | 0 | 1.0 | 3,807 | 11.03 / 26.50 |

Tool confusion (expected against called):

| expected ↓ / called → | list | status | tracking | search | propose | escalate | (none) |
|---|---|---|---|---|---|---|---|
| list | **12** | · | · | · | · | · | · |
| status | · | **6** | · | · | · | · | 1 |
| tracking | · | 1 | **9** | · | · | · | 1 |
| search | 7 | · | 1 | **3** | · | · | · |
| propose | 1 | · | · | · | **1** | · | 3 |
| escalate | 1 | · | · | · | · | **3** | 6 |
| (none) | 7 | 5 | 3 | 1 | · | 2 | · |
