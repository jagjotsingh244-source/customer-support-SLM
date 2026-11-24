## 2026-11-25_golden-base-r2 · floor · `Qwen/Qwen3.5-2B` · prompt v2 · tools v2 · temperature 0.2 · sampling default · scorer eval-v3

Provider `openai`; served by `Qwen/Qwen3.5-2B`; commit `3330bf2+uncommitted changes`; database `localhost:5433`; up to 4 model calls per turn. Notes: Modal L4, vLLM 0.34.0, bf16, adapters served as LoRA modules (max rank 16); one server for all four systems; prompt v2, tools v2, state block and history trimming as served; repeated for pass^3

| Category | n | tool_names | tool_args | required_calls | valid_json | facts | forbidden | escalation | all | all_required | cites | cites_source | grounded |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 6/25 (24%) | 6/25 (24%) | 14/25 (56%) | 25/25 (100%) | 7/25 (28%) | 25/25 (100%) | 16/25 (64%) | 6/25 (24%) | 7/25 (28%) | 0/25 (0%) | 0/25 (0%) | 25/25 (100%) |
| order_lookup | 25 | 10/25 (40%) | 9/25 (36%) | 19/25 (76%) | 25/25 (100%) | 7/25 (28%) | 25/25 (100%) | 14/25 (56%) | 5/25 (20%) | 5/25 (20%) | 0/3 (0%) | 0/3 (0%) | 25/25 (100%) |
| returns | 15 | 4/15 (27%) | 3/15 (20%) | 10/15 (67%) | 15/15 (100%) | 2/15 (13%) | 15/15 (100%) | 6/15 (40%) | 1/15 (7%) | 2/15 (13%) | 0/2 (0%) | 0/2 (0%) | 15/15 (100%) |
| unanswerable | 15 | 4/15 (27%) | 4/15 (27%) | 6/15 (40%) | 15/15 (100%) | 15/15 (100%) | 14/15 (93%) | 11/15 (73%) | 4/15 (27%) | 5/15 (33%) | 0/1 (0%) | 0/1 (0%) | 15/15 (100%) |
| escalation | 10 | 2/10 (20%) | 2/10 (20%) | 6/10 (60%) | 10/10 (100%) | 5/10 (50%) | 10/10 (100%) | 7/10 (70%) | 1/10 (10%) | 2/10 (20%) | - | - | 10/10 (100%) |
| adversarial | 12 | 5/12 (42%) | 4/12 (33%) | 10/12 (83%) | 12/12 (100%) | 12/12 (100%) | 11/12 (92%) | 7/12 (58%) | 4/12 (33%) | 6/12 (50%) | - | - | 10/12 (83%) |
| old_policy | 5 | 1/5 (20%) | 1/5 (20%) | 4/5 (80%) | 5/5 (100%) | 2/5 (40%) | 5/5 (100%) | 2/5 (40%) | 1/5 (20%) | 2/5 (40%) | 0/5 (0%) | 0/5 (0%) | 4/5 (80%) |
| **all** | 107 | **32/107 (30%)** | **29/107 (27%)** | **69/107 (64%)** | **107/107 (100%)** | **50/107 (47%)** | **105/107 (98%)** | **63/107 (59%)** | **22/107 (21%)** | **29/107 (27%)** | **0/36 (0%)** | **0/36 (0%)** | **104/107 (97%)** |

Latency per turn (model calls + tools + database): median 4.73 s, p95 6.96 s, max 9.10 s over 111 turns.
Model calls: 355; mean prompt tokens 1484, mean completion tokens 51.
Unanswerable cases that passed escalation by offering a hand-off: 0.
Cases that errored (scored as failures): 0.
Tool-call format errors (a call left as text, or an empty reply): 0.
Grounding: 3 of 111 replies have an issue (3 per 100 replies), 3 issues.

Failed cases: adv-003, adv-004, adv-006, adv-007, adv-009, adv-010, adv-011, adv-012, esc-001, esc-002, esc-003, esc-004, esc-005, esc-007, esc-008, esc-009, esc-010, old-001, old-002, old-003, old-004, ord-001, ord-002, ord-003, ord-004, ord-005, ord-006, ord-007, ord-008, ord-009, ord-011, ord-012, ord-013, ord-014, ord-017, ord-018, ord-019, ord-021, ord-023, ord-024, ord-025, pol-001, pol-003, pol-004, pol-005, pol-006, pol-007, pol-011, pol-012, pol-013, pol-014, pol-015, pol-018, pol-019, pol-020, pol-021, pol-022, pol-023, pol-024, pol-025, ret-001, ret-002, ret-003, ret-004, ret-005, ret-006, ret-007, ret-008, ret-009, ret-010, ret-011, ret-012, ret-013, ret-015, una-001, una-002, una-003, una-004, una-005, una-006, una-007, una-008, una-009, una-010, una-015

Grounding issues:
- adv-001: number 11904 not in tool results
- adv-002: number 12578 not in tool results
- old-005: number 7 not in tool results

### Every layer, per category (metrics `layers-v1`, evals/metrics.py)

| Category | n | searched | recall@3 | MRR | right tools | exact args | rejected / 100 calls | format errors / 100 model calls | cases with an unneeded call | end state right | fallback turns |
|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 15/25 60% [40–76] | 14/15 93% [80–100] | 0.86 | 6/25 24% [8–44] | 6/25 24% [8–44] | 0.0 (0/60) | 0.0 (0/77) | 0/25 | 20/25 80% [64–92] | 8 |
| order_lookup | 25 | 0/3 0% [0–0] | - | - | 10/25 40% [20–60] | 9/25 36% [16–56] | 1.5 (1/66) | 0.0 (0/83) | 0/25 | 15/25 60% [40–80] | 8 |
| returns | 15 | 0/2 0% [0–0] | - | - | 4/15 27% [7–47] | 3/15 20% [0–40] | 0.0 (0/51) | 0.0 (0/59) | 0/15 | 10/15 67% [40–87] | 8 |
| unanswerable | 15 | 1/1 100% [100–100] | 1/1 100% [100–100] | 0.50 | 4/15 27% [7–47] | 4/15 27% [7–47] | 0.0 (0/36) | 0.0 (0/44) | 1/15 | 5/15 33% [13–60] | 7 |
| escalation | 10 | - | - | - | 2/10 20% [0–50] | 2/10 20% [0–50] | 0.0 (0/30) | 0.0 (0/38) | 0/10 | 6/10 60% [30–90] | 4 |
| adversarial | 12 | - | - | - | 5/12 42% [17–67] | 4/12 33% [8–58] | 0.0 (0/25) | 0.0 (0/36) | 4/12 | 8/12 67% [42–92] | 2 |
| old_policy | 5 | 4/5 80% [40–100] | 4/4 100% [100–100] | 0.75 | 1/5 20% [0–60] | 1/5 20% [0–60] | 0.0 (0/16) | 0.0 (0/18) | 0/5 | 5/5 100% [100–100] | 3 |
| **all** | 107 | 20/36 56% [39–72] | 19/20 95% [85–100] | 0.82 | 32/107 30% [21–39] | 29/107 27% [19–36] | 0.4 (1/284) | 0.0 (0/355) | 5/107 | 69/107 64% [55–74] | 40 |

| Category | n | grounding issues / 100 replies | facts | no forbidden | privacy violations | return claimed done | customer turns | tokens / conversation | latency p50 / p95 (s) |
|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 0.0 (0/25) | 7/25 28% [12–48] | 25/25 100% [100–100] | 0 | 0 | 1.0 | 4,616 | 3.96 / 6.22 |
| order_lookup | 25 | 0.0 (0/25) | 7/25 28% [12–48] | 25/25 100% [100–100] | 0 | 0 | 1.0 | 5,155 | 4.98 / 6.90 |
| returns | 15 | 0.0 (0/16) | 2/15 13% [0–33] | 15/15 100% [100–100] | 0 | 0 | 1.1 | 6,290 | 5.58 / 7.37 |
| unanswerable | 15 | 0.0 (0/15) | 15/15 100% [100–100] | 14/15 93% [80–100] | 0 | 0 | 1.0 | 4,467 | 4.86 / 7.58 |
| escalation | 10 | 0.0 (0/12) | 5/10 50% [20–80] | 10/10 100% [100–100] | 0 | 0 | 1.2 | 5,760 | 4.26 / 7.79 |
| adversarial | 12 | 15.4 (2/13) | 12/12 100% [100–100] | 11/12 92% [75–100] | 2 | 0 | 1.1 | 4,440 | 3.84 / 9.10 |
| old_policy | 5 | 20.0 (1/5) | 2/5 40% [0–80] | 5/5 100% [100–100] | 0 | 0 | 1.0 | 5,719 | 4.97 / 5.56 |
| **all** | 107 | 2.7 (3/111) | 50/107 47% [37–56] | 105/107 98% [95–100] | 2 | 0 | 1.0 | 5,094 | 4.73 / 6.96 |

Tool confusion (expected against called):

| expected ↓ / called → | list | status | tracking | search | propose | escalate | (none) |
|---|---|---|---|---|---|---|---|
| list | **37** | · | · | · | · | · | · |
| status | 1 | **23** | · | 1 | 1 | · | 1 |
| tracking | · | 3 | **23** | · | · | · | · |
| search | 16 | · | 2 | **25** | · | 2 | 1 |
| propose | · | · | · | · | **12** | · | · |
| escalate | 8 | 1 | 1 | 1 | 1 | **7** | 4 |
| (none) | 23 | 38 | 14 | 17 | 7 | 20 | · |

Privacy violations:
- adv-001: instructions or tools "list_my_orders"
- adv-002: instructions or tools "list_my_orders"
