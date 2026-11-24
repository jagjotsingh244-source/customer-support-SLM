## 2026-11-23_floor-twins · floor · `Qwen/Qwen3.5-2B` · prompt v0 · tools v0 · temperature 0.2 · sampling default · scorer eval-v3

Provider `local`; served by `Qwen/Qwen3.5-2B`; commit `3a99d84`; database `localhost:5433`; up to 4 model calls per turn. Notes: rerun of the 12 golden cases the phrasing probes reword, to measure run-to-run variation; same setup as 2026-11-22_floor

| Category | n | tool_names | tool_args | required_calls | valid_json | facts | forbidden | escalation | all | all_required | cites | cites_source | grounded |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 3 | 1/3 (33%) | 1/3 (33%) | 3/3 (100%) | 3/3 (100%) | 0/3 (0%) | 3/3 (100%) | 2/3 (67%) | 0/3 (0%) | 0/3 (0%) | 0/3 (0%) | 0/3 (0%) | 3/3 (100%) |
| order_lookup | 4 | 2/4 (50%) | 2/4 (50%) | 3/4 (75%) | 4/4 (100%) | 1/4 (25%) | 4/4 (100%) | 3/4 (75%) | 1/4 (25%) | 1/4 (25%) | - | - | 4/4 (100%) |
| returns | 3 | 1/3 (33%) | 1/3 (33%) | 1/3 (33%) | 3/3 (100%) | 2/3 (67%) | 3/3 (100%) | 3/3 (100%) | 1/3 (33%) | 1/3 (33%) | 0/1 (0%) | 0/1 (0%) | 3/3 (100%) |
| unanswerable | 1 | 0/1 (0%) | 0/1 (0%) | 0/1 (0%) | 1/1 (100%) | 1/1 (100%) | 1/1 (100%) | 0/1 (0%) | 0/1 (0%) | 0/1 (0%) | - | - | 1/1 (100%) |
| escalation | 1 | 0/1 (0%) | 0/1 (0%) | 0/1 (0%) | 1/1 (100%) | 0/1 (0%) | 1/1 (100%) | 0/1 (0%) | 0/1 (0%) | 0/1 (0%) | - | - | 1/1 (100%) |
| **all** | 12 | **4/12 (33%)** | **4/12 (33%)** | **7/12 (58%)** | **12/12 (100%)** | **4/12 (33%)** | **12/12 (100%)** | **8/12 (67%)** | **2/12 (17%)** | **2/12 (17%)** | **0/4 (0%)** | **0/4 (0%)** | **12/12 (100%)** |

Latency per turn (model calls + tools + database): median 10.17 s, p95 17.36 s, max 17.36 s over 12 turns.
Model calls: 36; mean prompt tokens 1199, mean completion tokens 39.
Unanswerable cases that passed escalation by offering a hand-off: 0.
Cases that errored (scored as failures): 0.
Tool-call format errors (a call left as text, or an empty reply): 0.
Grounding: 0 of 12 replies have an issue (0 per 100 replies), 0 issues.

Failed cases: esc-004, ord-003, ord-006, ord-017, pol-001, pol-009, pol-010, ret-004, ret-013, una-002

### Every layer, per category (metrics `layers-v1`, evals/metrics.py)

| Category | n | searched | recall@3 | MRR | right tools | exact args | rejected / 100 calls | format errors / 100 model calls | cases with an unneeded call | end state right | fallback turns |
|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 3 | 3/3 100% [100–100] | 0/3 0% [0–0] | 0.00 | 1/3 33% [0–100] | 1/3 33% [0–100] | 0.0 (0/7) | 0.0 (0/9) | 0/3 | 2/3 67% [0–100] | 1 |
| order_lookup | 4 | - | - | - | 2/4 50% [0–100] | 2/4 50% [0–100] | 0.0 (0/8) | 0.0 (0/11) | 0/4 | 4/4 100% [100–100] | 1 |
| returns | 3 | 0/1 0% [0–0] | - | - | 1/3 33% [0–100] | 1/3 33% [0–100] | 0.0 (0/7) | 0.0 (0/10) | 0/3 | 1/3 33% [0–100] | 0 |
| unanswerable | 1 | - | - | - | 0/1 0% [0–0] | 0/1 0% [0–0] | 0.0 (0/1) | 0.0 (0/2) | 0/1 | 0/1 0% [0–0] | 0 |
| escalation | 1 | - | - | - | 0/1 0% [0–0] | 0/1 0% [0–0] | 0.0 (0/3) | 0.0 (0/4) | 0/1 | 0/1 0% [0–0] | 0 |
| **all** | 12 | 3/4 75% [25–100] | 0/3 0% [0–0] | 0.00 | 4/12 33% [8–58] | 4/12 33% [8–58] | 0.0 (0/26) | 0.0 (0/36) | 0/12 | 7/12 58% [33–83] | 2 |

| Category | n | grounding issues / 100 replies | facts | no forbidden | privacy violations | return claimed done | customer turns | tokens / conversation | latency p50 / p95 (s) |
|---|---|---|---|---|---|---|---|---|---|
| policy | 3 | 0.0 (0/3) | 0/3 0% [0–0] | 3/3 100% [100–100] | 0 | 0 | 1.0 | 3,531 | 8.06 / 16.84 |
| order_lookup | 4 | 0.0 (0/4) | 1/4 25% [0–75] | 4/4 100% [100–100] | 0 | 0 | 1.0 | 3,466 | 9.58 / 16.14 |
| returns | 3 | 0.0 (0/3) | 2/3 67% [0–100] | 3/3 100% [100–100] | 0 | 0 | 1.0 | 4,419 | 11.48 / 17.36 |
| unanswerable | 1 | 0.0 (0/1) | 1/1 100% [100–100] | 1/1 100% [100–100] | 0 | 0 | 1.0 | 2,085 | 5.50 / 5.50 |
| escalation | 1 | 0.0 (0/1) | 0/1 0% [0–0] | 1/1 100% [100–100] | 0 | 0 | 1.0 | 4,791 | 12.48 / 12.48 |
| **all** | 12 | 0.0 (0/12) | 4/12 33% [8–58] | 12/12 100% [100–100] | 0 | 0 | 1.0 | 3,716 | 10.77 / 17.36 |

Tool confusion (expected against called):

| expected ↓ / called → | list | status | tracking | search | propose | escalate | (none) |
|---|---|---|---|---|---|---|---|
| list | **5** | · | · | · | · | · | · |
| status | · | **3** | · | · | · | · | · |
| tracking | · | · | **4** | · | · | · | 1 |
| search | 1 | · | · | **3** | · | · | 1 |
| propose | · | · | 1 | · | **1** | · | · |
| escalate | · | 1 | · | · | · | · | 1 |
| (none) | 3 | 2 | · | 1 | · | 1 | · |
