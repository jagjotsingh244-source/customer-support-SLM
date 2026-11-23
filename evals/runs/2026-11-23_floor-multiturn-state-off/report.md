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
