## 2026-11-23_floor-twins · floor · `Qwen/Qwen3.5-2B` · prompt v0 · temperature 0.2 · sampling default · scorer eval-v1

Provider `local`; served by `Qwen/Qwen3.5-2B`; commit `3a99d84`; database `localhost:5433`; up to 4 model calls per turn. Notes: rerun of the 12 golden cases the phrasing probes reword, to measure run-to-run variation; same setup as 2026-11-22_floor

| Category | n | tool_names | tool_args | required_calls | valid_json | facts | forbidden | escalation | all | all_required |
|---|---|---|---|---|---|---|---|---|---|---|
| policy | 3 | 1/3 (33%) | 1/3 (33%) | 3/3 (100%) | 3/3 (100%) | 0/3 (0%) | 3/3 (100%) | 2/3 (67%) | 0/3 (0%) | 0/3 (0%) |
| order_lookup | 4 | 2/4 (50%) | 2/4 (50%) | 3/4 (75%) | 4/4 (100%) | 1/4 (25%) | 4/4 (100%) | 3/4 (75%) | 1/4 (25%) | 1/4 (25%) |
| returns | 3 | 1/3 (33%) | 1/3 (33%) | 1/3 (33%) | 3/3 (100%) | 2/3 (67%) | 3/3 (100%) | 3/3 (100%) | 1/3 (33%) | 1/3 (33%) |
| unanswerable | 1 | 0/1 (0%) | 0/1 (0%) | 0/1 (0%) | 1/1 (100%) | 1/1 (100%) | 1/1 (100%) | 0/1 (0%) | 0/1 (0%) | 0/1 (0%) |
| escalation | 1 | 0/1 (0%) | 0/1 (0%) | 0/1 (0%) | 1/1 (100%) | 0/1 (0%) | 1/1 (100%) | 0/1 (0%) | 0/1 (0%) | 0/1 (0%) |
| **all** | 12 | **4/12 (33%)** | **4/12 (33%)** | **7/12 (58%)** | **12/12 (100%)** | **4/12 (33%)** | **12/12 (100%)** | **8/12 (67%)** | **2/12 (17%)** | **2/12 (17%)** |

Latency per turn (model calls + tools + database): median 10.17 s, p95 17.36 s, max 17.36 s over 12 turns.
Model calls: 36; mean prompt tokens 1199, mean completion tokens 39.
Unanswerable cases that passed escalation by offering a hand-off: 0.
Cases that errored (scored as failures): 0.

Failed cases: esc-004, ord-003, ord-006, ord-017, pol-001, pol-009, pol-010, ret-004, ret-013, una-002
