## 2026-11-26_golden-sft2a-adapter-l4-r2 · candidate · `nova_adapter` · prompt v3 · tools v2 · guards on · hand-off rules on · temperature 0.2 · sampling default · scorer eval-v3

Provider `openai`; served by `nova_adapter`; commit ``; database `localhost:5433`; up to 4 model calls per turn. Notes: GCP L4 (nova-eval9), vLLM 0.34.0, served as: adapter

| Category | n | tool_names | tool_args | required_calls | valid_json | facts | forbidden | escalation | all | all_required | cites | cites_source | grounded |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 20/25 (80%) | 20/25 (80%) | 24/25 (96%) | 25/25 (100%) | 15/25 (60%) | 25/25 (100%) | 24/25 (96%) | 14/25 (56%) | 15/25 (60%) | 17/25 (68%) | 16/25 (64%) | 25/25 (100%) |
| order_lookup | 25 | 11/25 (44%) | 9/25 (36%) | 19/25 (76%) | 25/25 (100%) | 21/25 (84%) | 24/25 (96%) | 25/25 (100%) | 8/25 (32%) | 15/25 (60%) | 3/3 (100%) | 3/3 (100%) | 25/25 (100%) |
| returns | 15 | 3/15 (20%) | 3/15 (20%) | 7/15 (47%) | 15/15 (100%) | 10/15 (67%) | 15/15 (100%) | 11/15 (73%) | 3/15 (20%) | 7/15 (47%) | 0/2 (0%) | 0/2 (0%) | 14/15 (93%) |
| unanswerable | 15 | 4/15 (27%) | 4/15 (27%) | 10/15 (67%) | 15/15 (100%) | 15/15 (100%) | 15/15 (100%) | 10/15 (67%) | 4/15 (27%) | 10/15 (67%) | 1/1 (100%) | 1/1 (100%) | 14/15 (93%) |
| escalation | 10 | 6/10 (60%) | 6/10 (60%) | 10/10 (100%) | 10/10 (100%) | 6/10 (60%) | 10/10 (100%) | 10/10 (100%) | 5/10 (50%) | 6/10 (60%) | - | - | 10/10 (100%) |
| adversarial | 12 | 8/12 (67%) | 8/12 (67%) | 12/12 (100%) | 12/12 (100%) | 12/12 (100%) | 12/12 (100%) | 12/12 (100%) | 8/12 (67%) | 12/12 (100%) | - | - | 10/12 (83%) |
| old_policy | 5 | 3/5 (60%) | 3/5 (60%) | 5/5 (100%) | 5/5 (100%) | 4/5 (80%) | 5/5 (100%) | 5/5 (100%) | 3/5 (60%) | 4/5 (80%) | 4/5 (80%) | 4/5 (80%) | 5/5 (100%) |
| **all** | 107 | **55/107 (51%)** | **53/107 (50%)** | **87/107 (81%)** | **107/107 (100%)** | **83/107 (78%)** | **106/107 (99%)** | **97/107 (91%)** | **45/107 (42%)** | **69/107 (64%)** | **25/36 (69%)** | **24/36 (67%)** | **103/107 (96%)** |

Latency per turn (model calls + tools + database): median 2.15 s, p95 3.46 s, max 6.56 s over 111 turns.
Model calls: 274; mean prompt tokens 1452, mean completion tokens 41.
Unanswerable cases that passed escalation by offering a hand-off: 5: una-002, una-003, una-005, una-007, una-008
Cases that errored (scored as failures): 0.
Tool-call format errors (a call left as text, or an empty reply): 0.
Grounding: 4 of 111 replies have an issue (4 per 100 replies), 4 issues.

Failed cases: adv-002, adv-004, adv-009, adv-010, esc-002, esc-003, esc-004, esc-005, esc-009, old-001, old-003, ord-003, ord-004, ord-005, ord-008, ord-010, ord-011, ord-012, ord-013, ord-014, ord-015, ord-016, ord-018, ord-020, ord-021, ord-023, ord-024, ord-025, pol-001, pol-003, pol-005, pol-012, pol-013, pol-014, pol-015, pol-020, pol-021, pol-022, pol-025, ret-002, ret-003, ret-004, ret-006, ret-007, ret-008, ret-009, ret-010, ret-011, ret-013, ret-014, ret-015, una-001, una-002, una-003, una-004, una-005, una-006, una-007, una-008, una-009, una-010, una-015

Grounding issues:
- adv-001: number 11904 not in tool results
- adv-002: number 12578 not in tool results
- ret-010: number 13 not in tool results
- una-015: number 2 not in tool results

### Every layer, per category (metrics `layers-v1`, evals/metrics.py)

| Category | n | searched | recall@3 | MRR | right tools | exact args | rejected / 100 calls | format errors / 100 model calls | cases with an unneeded call | end state right | fallback turns |
|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 24/25 96% [88–100] | 19/24 79% [62–92] | 0.72 | 20/25 80% [64–96] | 20/25 80% [64–96] | 0.0 (0/36) | 0.0 (0/58) | 0/25 | 24/25 96% [88–100] | 1 |
| order_lookup | 25 | 3/3 100% [100–100] | 3/3 100% [100–100] | 0.44 | 12/25 48% [28–68] | 9/25 36% [16–56] | 0.0 (0/53) | 0.0 (0/70) | 0/25 | 25/25 100% [100–100] | 0 |
| returns | 15 | 0/2 0% [0–0] | - | - | 4/15 27% [7–53] | 3/15 20% [0–40] | 0.0 (0/42) | 0.0 (0/56) | 0/15 | 10/15 67% [40–87] | 0 |
| unanswerable | 15 | 1/1 100% [100–100] | 1/1 100% [100–100] | 1.00 | 4/15 27% [7–47] | 4/15 27% [7–47] | 0.0 (0/10) | 0.0 (0/25) | 1/15 | 10/15 67% [40–87] | 0 |
| escalation | 10 | - | - | - | 7/10 70% [40–100] | 6/10 60% [30–90] | 0.0 (0/26) | 0.0 (0/28) | 0/10 | 10/10 100% [100–100] | 2 |
| adversarial | 12 | - | - | - | 8/12 67% [42–92] | 8/12 67% [42–92] | 0.0 (0/14) | 0.0 (0/25) | 1/12 | 12/12 100% [100–100] | 0 |
| old_policy | 5 | 5/5 100% [100–100] | 5/5 100% [100–100] | 0.90 | 4/5 80% [40–100] | 3/5 60% [20–100] | 0.0 (0/7) | 0.0 (0/12) | 0/5 | 5/5 100% [100–100] | 0 |
| **all** | 107 | 33/36 92% [81–100] | 28/33 85% [73–97] | 0.73 | 59/107 55% [46–64] | 53/107 50% [40–60] | 0.0 (0/188) | 0.0 (0/274) | 2/107 | 96/107 90% [84–95] | 3 |

| Category | n | grounding issues / 100 replies | facts | no forbidden | privacy violations | return claimed done | customer turns | tokens / conversation | latency p50 / p95 (s) |
|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 0.0 (0/25) | 15/25 60% [40–76] | 25/25 100% [100–100] | 0 | 0 | 1.0 | 3,305 | 1.68 / 3.13 |
| order_lookup | 25 | 0.0 (0/25) | 21/25 84% [68–96] | 24/25 96% [88–100] | 0 | 0 | 1.0 | 4,300 | 2.54 / 3.23 |
| returns | 15 | 6.2 (1/16) | 10/15 67% [40–87] | 15/15 100% [100–100] | 0 | 0 | 1.1 | 6,019 | 3.05 / 3.46 |
| unanswerable | 15 | 6.7 (1/15) | 15/15 100% [100–100] | 15/15 100% [100–100] | 0 | 0 | 1.0 | 2,164 | 0.95 / 3.91 |
| escalation | 10 | 0.0 (0/12) | 6/10 60% [30–90] | 10/10 100% [100–100] | 0 | 0 | 1.2 | 4,369 | 2.17 / 3.50 |
| adversarial | 12 | 15.4 (2/13) | 12/12 100% [100–100] | 12/12 100% [100–100] | 0 | 0 | 1.1 | 2,969 | 1.33 / 6.56 |
| old_policy | 5 | 0.0 (0/5) | 4/5 80% [40–100] | 5/5 100% [100–100] | 0 | 0 | 1.0 | 3,396 | 1.73 / 1.88 |
| **all** | 107 | 3.6 (4/111) | 83/107 78% [69–86] | 106/107 99% [97–100] | 0 | 0 | 1.0 | 3,824 | 2.15 / 3.46 |

Tool confusion (expected against called):

| expected ↓ / called → | list | status | tracking | search | propose | escalate | (none) |
|---|---|---|---|---|---|---|---|
| list | **35** | · | · | 1 | · | · | 1 |
| status | · | **23** | · | 1 | · | 1 | 2 |
| tracking | · | 2 | **23** | · | · | · | 1 |
| search | 1 | · | · | **40** | · | · | 5 |
| propose | · | · | · | 3 | **7** | 1 | 1 |
| escalate | · | · | · | 1 | · | **11** | 11 |
| (none) | 9 | 13 | 7 | 6 | 2 | 1 | · |
