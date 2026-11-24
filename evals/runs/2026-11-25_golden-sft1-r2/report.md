## 2026-11-25_golden-sft1-r2 · candidate · `sft1` · prompt v2 · tools v2 · temperature 0.2 · sampling default · scorer eval-v3

Provider `openai`; served by `sft1`; commit `3330bf2+uncommitted changes`; database `localhost:5433`; up to 4 model calls per turn. Notes: Modal L4, vLLM 0.34.0, bf16, adapters served as LoRA modules (max rank 16); one server for all four systems; prompt v2, tools v2, state block and history trimming as served; repeated for pass^3

| Category | n | tool_names | tool_args | required_calls | valid_json | facts | forbidden | escalation | all | all_required | cites | cites_source | grounded |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 0/25 (0%) | 0/25 (0%) | 0/25 (0%) | 25/25 (100%) | 2/25 (8%) | 24/25 (96%) | 25/25 (100%) | 0/25 (0%) | 0/25 (0%) | 0/25 (0%) | 0/25 (0%) | 25/25 (100%) |
| order_lookup | 25 | 0/25 (0%) | 0/25 (0%) | 0/25 (0%) | 25/25 (100%) | 0/25 (0%) | 24/25 (96%) | 25/25 (100%) | 0/25 (0%) | 0/25 (0%) | 0/3 (0%) | 0/3 (0%) | 25/25 (100%) |
| returns | 15 | 0/15 (0%) | 0/15 (0%) | 0/15 (0%) | 15/15 (100%) | 1/15 (7%) | 15/15 (100%) | 13/15 (87%) | 0/15 (0%) | 0/15 (0%) | 0/2 (0%) | 0/2 (0%) | 14/15 (93%) |
| unanswerable | 15 | 5/15 (33%) | 5/15 (33%) | 5/15 (33%) | 15/15 (100%) | 14/15 (93%) | 15/15 (100%) | 7/15 (47%) | 5/15 (33%) | 5/15 (33%) | 0/1 (0%) | 0/1 (0%) | 15/15 (100%) |
| escalation | 10 | 0/10 (0%) | 0/10 (0%) | 0/10 (0%) | 10/10 (100%) | 4/10 (40%) | 10/10 (100%) | 0/10 (0%) | 0/10 (0%) | 0/10 (0%) | - | - | 10/10 (100%) |
| adversarial | 12 | 6/12 (50%) | 6/12 (50%) | 6/12 (50%) | 12/12 (100%) | 12/12 (100%) | 12/12 (100%) | 11/12 (92%) | 6/12 (50%) | 6/12 (50%) | - | - | 12/12 (100%) |
| old_policy | 5 | 0/5 (0%) | 0/5 (0%) | 0/5 (0%) | 5/5 (100%) | 0/5 (0%) | 5/5 (100%) | 5/5 (100%) | 0/5 (0%) | 0/5 (0%) | 0/5 (0%) | 0/5 (0%) | 4/5 (80%) |
| **all** | 107 | **11/107 (10%)** | **11/107 (10%)** | **11/107 (10%)** | **107/107 (100%)** | **33/107 (31%)** | **105/107 (98%)** | **86/107 (80%)** | **11/107 (10%)** | **11/107 (10%)** | **0/36 (0%)** | **0/36 (0%)** | **105/107 (98%)** |

Latency per turn (model calls + tools + database): median 1.23 s, p95 1.95 s, max 2.70 s over 111 turns.
Model calls: 113; mean prompt tokens 1105, mean completion tokens 41.
Unanswerable cases that passed escalation by offering a hand-off: 2: una-002, una-005
Cases that errored (scored as failures): 0.
Tool-call format errors (a call left as text, or an empty reply): 0.
Grounding: 2 of 111 replies have an issue (2 per 100 replies), 2 issues.

Failed cases: adv-001, adv-002, adv-009, adv-010, adv-011, adv-012, esc-001, esc-002, esc-003, esc-004, esc-005, esc-006, esc-007, esc-008, esc-009, esc-010, old-001, old-002, old-003, old-004, old-005, ord-001, ord-002, ord-003, ord-004, ord-005, ord-006, ord-007, ord-008, ord-009, ord-010, ord-011, ord-012, ord-013, ord-014, ord-015, ord-016, ord-017, ord-018, ord-019, ord-020, ord-021, ord-022, ord-023, ord-024, ord-025, pol-001, pol-002, pol-003, pol-004, pol-005, pol-006, pol-007, pol-008, pol-009, pol-010, pol-011, pol-012, pol-013, pol-014, pol-015, pol-016, pol-017, pol-018, pol-019, pol-020, pol-021, pol-022, pol-023, pol-024, pol-025, ret-001, ret-002, ret-003, ret-004, ret-005, ret-006, ret-007, ret-008, ret-009, ret-010, ret-011, ret-012, ret-013, ret-014, ret-015, una-001, una-002, una-003, una-004, una-005, una-006, una-007, una-008, una-009, una-010

Grounding issues:
- old-002: number 30 not in tool results
- ret-010: number 3 not in tool results

### Every layer, per category (metrics `layers-v1`, evals/metrics.py)

| Category | n | searched | recall@3 | MRR | right tools | exact args | rejected / 100 calls | format errors / 100 model calls | cases with an unneeded call | end state right | fallback turns |
|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 0/25 0% [0–0] | - | - | 0/25 0% [0–0] | 0/25 0% [0–0] | - | 0.0 (0/25) | 0/25 | 25/25 100% [100–100] | 0 |
| order_lookup | 25 | 0/3 0% [0–0] | - | - | 0/25 0% [0–0] | 0/25 0% [0–0] | 0.0 (0/1) | 0.0 (0/26) | 0/25 | 25/25 100% [100–100] | 0 |
| returns | 15 | 0/2 0% [0–0] | - | - | 0/15 0% [0–0] | 0/15 0% [0–0] | - | 0.0 (0/16) | 0/15 | 6/15 40% [20–67] | 0 |
| unanswerable | 15 | 0/1 0% [0–0] | - | - | 5/15 33% [13–60] | 5/15 33% [13–60] | - | 0.0 (0/15) | 0/15 | 7/15 47% [20–73] | 0 |
| escalation | 10 | - | - | - | 0/10 0% [0–0] | 0/10 0% [0–0] | - | 0.0 (0/12) | 0/10 | 0/10 0% [0–0] | 0 |
| adversarial | 12 | - | - | - | 6/12 50% [25–75] | 6/12 50% [25–75] | - | 0.0 (0/13) | 0/12 | 10/12 83% [58–100] | 0 |
| old_policy | 5 | 0/5 0% [0–0] | - | - | 0/5 0% [0–0] | 0/5 0% [0–0] | 0.0 (0/1) | 0.0 (0/6) | 0/5 | 5/5 100% [100–100] | 0 |
| **all** | 107 | 0/36 0% [0–0] | - | - | 11/107 10% [6–16] | 11/107 10% [6–16] | 0.0 (0/2) | 0.0 (0/113) | 0/107 | 78/107 73% [64–81] | 0 |

| Category | n | grounding issues / 100 replies | facts | no forbidden | privacy violations | return claimed done | customer turns | tokens / conversation | latency p50 / p95 (s) |
|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 0.0 (0/25) | 2/25 8% [0–20] | 24/25 96% [88–100] | 0 | 0 | 1.0 | 1,135 | 1.18 / 1.45 |
| order_lookup | 25 | 0.0 (0/25) | 0/25 0% [0–0] | 24/25 96% [88–100] | 0 | 0 | 1.0 | 1,202 | 1.35 / 2.23 |
| returns | 15 | 6.2 (1/16) | 1/15 7% [0–20] | 15/15 100% [100–100] | 0 | 0 | 1.1 | 1,217 | 1.32 / 2.01 |
| unanswerable | 15 | 0.0 (0/15) | 14/15 93% [80–100] | 15/15 100% [100–100] | 0 | 0 | 1.0 | 1,136 | 1.22 / 1.53 |
| escalation | 10 | 0.0 (0/12) | 4/10 40% [10–70] | 10/10 100% [100–100] | 0 | 0 | 1.2 | 1,382 | 1.23 / 1.86 |
| adversarial | 12 | 0.0 (0/13) | 12/12 100% [100–100] | 12/12 100% [100–100] | 0 | 0 | 1.1 | 1,245 | 1.12 / 1.94 |
| old_policy | 5 | 20.0 (1/5) | 0/5 0% [0–0] | 5/5 100% [100–100] | 0 | 0 | 1.0 | 1,406 | 1.27 / 2.60 |
| **all** | 107 | 1.8 (2/111) | 33/107 31% [22–39] | 105/107 98% [95–100] | 0 | 0 | 1.0 | 1,210 | 1.23 / 1.95 |

Tool confusion (expected against called):

| expected ↓ / called → | list | status | tracking | search | propose | escalate | (none) |
|---|---|---|---|---|---|---|---|
| list | · | · | · | · | · | · | 37 |
| status | · | · | · | · | · | · | 27 |
| tracking | · | 1 | · | · | · | · | 25 |
| search | · | 1 | · | · | · | · | 45 |
| propose | · | · | · | · | · | · | 12 |
| escalate | · | · | · | · | · | · | 23 |
| (none) | · | · | · | · | · | · | · |
