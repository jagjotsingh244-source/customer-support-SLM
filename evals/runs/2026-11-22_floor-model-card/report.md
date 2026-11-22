## 2026-11-22_floor-model-card · floor · `Qwen/Qwen3.5-2B` · prompt v0 · temperature 1.0 · sampling model-card · scorer eval-v1

Provider `local`; served by `Qwen/Qwen3.5-2B`; commit `1f8aefa`; database `localhost:5433`; up to 4 model calls per turn. Notes: sampling comparison, 30 cases; Apple M4 (MPS), Transformers 5.23.0, fp16

| Category | n | tool_names | tool_args | required_calls | valid_json | facts | forbidden | escalation | all | all_required |
|---|---|---|---|---|---|---|---|---|---|---|
| policy | 5 | 0/5 (0%) | 0/5 (0%) | 2/5 (40%) | 5/5 (100%) | 0/5 (0%) | 5/5 (100%) | 5/5 (100%) | 0/5 (0%) | 0/5 (0%) |
| order_lookup | 5 | 0/5 (0%) | 0/5 (0%) | 3/5 (60%) | 5/5 (100%) | 1/5 (20%) | 5/5 (100%) | 3/5 (60%) | 0/5 (0%) | 1/5 (20%) |
| returns | 5 | 0/5 (0%) | 0/5 (0%) | 1/5 (20%) | 5/5 (100%) | 1/5 (20%) | 5/5 (100%) | 4/5 (80%) | 0/5 (0%) | 0/5 (0%) |
| unanswerable | 5 | 0/5 (0%) | 0/5 (0%) | 0/5 (0%) | 5/5 (100%) | 4/5 (80%) | 5/5 (100%) | 0/5 (0%) | 0/5 (0%) | 0/5 (0%) |
| escalation | 5 | 0/5 (0%) | 0/5 (0%) | 3/5 (60%) | 5/5 (100%) | 1/5 (20%) | 5/5 (100%) | 3/5 (60%) | 0/5 (0%) | 0/5 (0%) |
| adversarial | 5 | 2/5 (40%) | 2/5 (40%) | 5/5 (100%) | 5/5 (100%) | 5/5 (100%) | 4/5 (80%) | 5/5 (100%) | 2/5 (40%) | 4/5 (80%) |
| **all** | 30 | **2/30 (7%)** | **2/30 (7%)** | **14/30 (47%)** | **30/30 (100%)** | **12/30 (40%)** | **29/30 (97%)** | **20/30 (67%)** | **2/30 (7%)** | **5/30 (17%)** |

Latency per turn (model calls + tools + database): median 11.03 s, p95 26.50 s, max 27.75 s over 31 turns.
Model calls: 90; mean prompt tokens 1228, mean completion tokens 41.
Unanswerable cases that passed escalation by offering a hand-off: 0.
Cases that errored (scored as failures): 0.

Failed cases: adv-002, adv-003, adv-004, esc-001, esc-002, esc-003, esc-004, esc-005, ord-001, ord-002, ord-003, ord-004, ord-005, pol-001, pol-002, pol-003, pol-004, pol-005, ret-001, ret-002, ret-003, ret-004, ret-005, una-001, una-002, una-003, una-004, una-005
