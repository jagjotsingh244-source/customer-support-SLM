## 2026-11-23_floor-tools-v2 · floor · `Qwen/Qwen3.5-2B` · prompt v0 · tools v2 · temperature 0.2 · sampling default · scorer eval-v3

Provider `local`; served by `Qwen/Qwen3.5-2B`; commit `501012e+uncommitted changes`; database `localhost:5433`; up to 4 model calls per turn. Notes: Apple M4 (MPS), Transformers 5.23.0, fp16, in-process; same settings as the first run of this model, tools v2 (typed arguments, errors written for the model, explicit empty results, database roles)

| Category | n | tool_names | tool_args | required_calls | valid_json | facts | forbidden | escalation | all | all_required | cites | cites_source | grounded |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| order_lookup | 25 | 11/25 (44%) | 10/25 (40%) | 21/25 (84%) | 25/25 (100%) | 6/25 (24%) | 24/25 (96%) | 19/25 (76%) | 4/25 (16%) | 5/25 (20%) | 0/3 (0%) | 0/3 (0%) | 25/25 (100%) |
| returns | 15 | 5/15 (33%) | 4/15 (27%) | 10/15 (67%) | 15/15 (100%) | 4/15 (27%) | 15/15 (100%) | 10/15 (67%) | 2/15 (13%) | 3/15 (20%) | 0/2 (0%) | 0/2 (0%) | 15/15 (100%) |
| **all** | 40 | **16/40 (40%)** | **14/40 (35%)** | **31/40 (78%)** | **40/40 (100%)** | **10/40 (25%)** | **39/40 (98%)** | **29/40 (72%)** | **6/40 (15%)** | **8/40 (20%)** | **0/5 (0%)** | **0/5 (0%)** | **40/40 (100%)** |

Latency per turn (model calls + tools + database): median 16.64 s, p95 22.17 s, max 22.89 s over 41 turns.
Model calls: 137; mean prompt tokens 1351, mean completion tokens 45.
Unanswerable cases that passed escalation by offering a hand-off: 0.
Cases that errored (scored as failures): 0.
Tool-call format errors (a call left as text, or an empty reply): 0.
Grounding: 0 of 41 replies have an issue (0 per 100 replies), 0 issues.

Failed cases: ord-002, ord-003, ord-004, ord-005, ord-006, ord-007, ord-008, ord-009, ord-010, ord-011, ord-012, ord-013, ord-014, ord-017, ord-018, ord-020, ord-021, ord-022, ord-023, ord-024, ord-025, ret-001, ret-002, ret-004, ret-006, ret-007, ret-008, ret-009, ret-010, ret-011, ret-012, ret-013, ret-014, ret-015

### Every layer, per category (metrics `layers-v1`, evals/metrics.py)

| Category | n | searched | recall@3 | MRR | right tools | exact args | rejected / 100 calls | format errors / 100 model calls | cases with an unneeded call | end state right | fallback turns |
|---|---|---|---|---|---|---|---|---|---|---|---|
| order_lookup | 25 | 2/3 67% [0–100] | 2/2 100% [100–100] | 0.42 | 11/25 44% [24–64] | 10/25 40% [20–60] | 0.0 (0/59) | 0.0 (0/79) | 0/25 | 21/25 84% [68–96] | 5 |
| returns | 15 | 0/2 0% [0–0] | - | - | 5/15 33% [13–60] | 4/15 27% [7–53] | 0.0 (0/47) | 0.0 (0/58) | 0/15 | 10/15 67% [40–87] | 5 |
| **all** | 40 | 2/5 40% [0–80] | 2/2 100% [100–100] | 0.42 | 16/40 40% [25–55] | 14/40 35% [20–50] | 0.0 (0/106) | 0.0 (0/137) | 0/40 | 31/40 78% [65–90] | 10 |

| Category | n | grounding issues / 100 replies | facts | no forbidden | privacy violations | return claimed done | customer turns | tokens / conversation | latency p50 / p95 (s) |
|---|---|---|---|---|---|---|---|---|---|
| order_lookup | 25 | 0.0 (0/25) | 6/25 24% [8–40] | 24/25 96% [88–100] | 0 | 0 | 1.0 | 4,326 | 11.53 / 19.23 |
| returns | 15 | 0.0 (0/16) | 4/15 27% [7–53] | 15/15 100% [100–100] | 0 | 0 | 1.1 | 5,537 | 18.52 / 22.63 |
| **all** | 40 | 0.0 (0/41) | 10/40 25% [12–40] | 39/40 98% [92–100] | 0 | 0 | 1.0 | 4,780 | 16.64 / 22.17 |

Tool confusion (expected against called):

| expected ↓ / called → | list | status | tracking | search | propose | escalate | (none) |
|---|---|---|---|---|---|---|---|
| list | **29** | · | · | · | · | · | · |
| status | · | **22** | · | · | · | · | 1 |
| tracking | · | 2 | **15** | · | · | · | 1 |
| search | 1 | · | · | **2** | · | · | 2 |
| propose | · | · | · | · | **10** | · | 1 |
| escalate | · | · | · | · | 1 | · | 1 |
| (none) | 4 | 3 | 1 | 8 | 4 | 4 | · |
