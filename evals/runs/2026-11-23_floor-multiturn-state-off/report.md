## 2026-11-23_floor-multiturn-state-off · diagnostic · `Qwen/Qwen3.5-2B` · prompt v2 · tools v2 · temperature 0.2 · sampling default · scorer eval-v3

Provider `local`; served by `Qwen/Qwen3.5-2B`; commit `5e35e04+uncommitted changes`; database `localhost:5433`; up to 4 model calls per turn. Notes: Apple M4 (MPS), Transformers 5.23.0, fp16, in-process; tools v2, prompt v2; the multi-turn golden cases; state off

| Category | n | tool_names | tool_args | required_calls | valid_json | facts | forbidden | escalation | all | all_required | cites | cites_source | grounded |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| returns | 1 | 0/1 (0%) | 0/1 (0%) | 1/1 (100%) | 1/1 (100%) | 0/1 (0%) | 1/1 (100%) | 0/1 (0%) | 0/1 (0%) | 0/1 (0%) | - | - | 1/1 (100%) |
| escalation | 1 | 0/1 (0%) | 0/1 (0%) | 1/1 (100%) | 1/1 (100%) | 0/1 (0%) | 1/1 (100%) | 1/1 (100%) | 0/1 (0%) | 0/1 (0%) | - | - | 1/1 (100%) |
| adversarial | 1 | 0/1 (0%) | 0/1 (0%) | 0/1 (0%) | 1/1 (100%) | 1/1 (100%) | 1/1 (100%) | 0/1 (0%) | 0/1 (0%) | 0/1 (0%) | - | - | 1/1 (100%) |
| **all** | 3 | **0/3 (0%)** | **0/3 (0%)** | **2/3 (67%)** | **3/3 (100%)** | **1/3 (33%)** | **3/3 (100%)** | **1/3 (33%)** | **0/3 (0%)** | **0/3 (0%)** | **-** | **-** | **3/3 (100%)** |

Latency per turn (model calls + tools + database): median 12.64 s, p95 21.38 s, max 21.38 s over 7 turns.
Model calls: 19; mean prompt tokens 1867, mean completion tokens 54.
Unanswerable cases that passed escalation by offering a hand-off: 0.
Cases that errored (scored as failures): 0.
Tool-call format errors (a call left as text, or an empty reply): 0.
Grounding: 0 of 7 replies have an issue (0 per 100 replies), 0 issues.

Failed cases: adv-010, esc-009, ret-002

### Every layer, per category (metrics `layers-v1`, evals/metrics.py)

| Category | n | searched | recall@3 | MRR | right tools | exact args | rejected / 100 calls | format errors / 100 model calls | cases with an unneeded call | end state right | fallback turns |
|---|---|---|---|---|---|---|---|---|---|---|---|
| returns | 1 | - | - | - | 0/1 0% [0–0] | 0/1 0% [0–0] | 0.0 (0/5) | 0.0 (0/6) | 0/1 | 0/1 0% [0–0] | 1 |
| escalation | 1 | - | - | - | 1/1 100% [100–100] | 0/1 0% [0–0] | 0.0 (0/6) | 0.0 (0/8) | 0/1 | 1/1 100% [100–100] | 1 |
| adversarial | 1 | - | - | - | 0/1 0% [0–0] | 0/1 0% [0–0] | 0.0 (0/3) | 0.0 (0/5) | 0/1 | 0/1 0% [0–0] | 0 |
| **all** | 3 | - | - | - | 1/3 33% [0–100] | 0/3 0% [0–0] | 0.0 (0/14) | 0.0 (0/19) | 0/3 | 1/3 33% [0–100] | 2 |

| Category | n | grounding issues / 100 replies | facts | no forbidden | privacy violations | return claimed done | customer turns | tokens / conversation | latency p50 / p95 (s) |
|---|---|---|---|---|---|---|---|---|---|
| returns | 1 | 0.0 (0/2) | 0/1 0% [0–0] | 1/1 100% [100–100] | 0 | 0 | 2.0 | 10,600 | 21.38 / 21.38 |
| escalation | 1 | 0.0 (0/3) | 0/1 0% [0–0] | 1/1 100% [100–100] | 0 | 0 | 3.0 | 17,550 | 12.64 / 17.02 |
| adversarial | 1 | 0.0 (0/2) | 1/1 100% [100–100] | 1/1 100% [100–100] | 0 | 0 | 2.0 | 8,353 | 16.15 / 16.15 |
| **all** | 3 | 0.0 (0/7) | 1/3 33% [0–100] | 3/3 100% [100–100] | 0 | 0 | 2.3 | 12,168 | 12.64 / 21.38 |

Tool confusion (expected against called):

| expected ↓ / called → | list | status | tracking | search | propose | escalate | (none) |
|---|---|---|---|---|---|---|---|
| list | **3** | · | · | · | · | · | · |
| status | · | **2** | · | · | · | · | · |
| tracking | · | 1 | · | · | · | · | · |
| search | · | · | · | · | · | · | · |
| propose | · | · | · | · | **1** | · | · |
| escalate | 1 | · | · | · | · | **1** | · |
| (none) | · | 3 | · | 1 | · | 1 | · |
