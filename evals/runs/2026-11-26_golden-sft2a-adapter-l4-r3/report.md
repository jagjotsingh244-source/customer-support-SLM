## 2026-11-26_golden-sft2a-adapter-l4-r3 · candidate · `nova_adapter` · prompt v3 · tools v2 · guards on · hand-off rules on · temperature 0.2 · sampling default · scorer eval-v3

Provider `openai`; served by `nova_adapter`; commit ``; database `localhost:5433`; up to 4 model calls per turn. Notes: GCP L4 (nova-eval9), vLLM 0.34.0, served as: adapter

| Category | n | tool_names | tool_args | required_calls | valid_json | facts | forbidden | escalation | all | all_required | cites | cites_source | grounded |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 18/25 (72%) | 18/25 (72%) | 23/25 (92%) | 25/25 (100%) | 16/25 (64%) | 24/25 (96%) | 25/25 (100%) | 13/25 (52%) | 15/25 (60%) | 18/25 (72%) | 17/25 (68%) | 25/25 (100%) |
| order_lookup | 25 | 12/25 (48%) | 11/25 (44%) | 19/25 (76%) | 25/25 (100%) | 21/25 (84%) | 23/25 (92%) | 25/25 (100%) | 10/25 (40%) | 14/25 (56%) | 3/3 (100%) | 3/3 (100%) | 25/25 (100%) |
| returns | 15 | 3/15 (20%) | 3/15 (20%) | 6/15 (40%) | 15/15 (100%) | 10/15 (67%) | 15/15 (100%) | 12/15 (80%) | 3/15 (20%) | 6/15 (40%) | 0/2 (0%) | 0/2 (0%) | 15/15 (100%) |
| unanswerable | 15 | 4/15 (27%) | 4/15 (27%) | 10/15 (67%) | 15/15 (100%) | 15/15 (100%) | 15/15 (100%) | 10/15 (67%) | 4/15 (27%) | 10/15 (67%) | 1/1 (100%) | 1/1 (100%) | 14/15 (93%) |
| escalation | 10 | 7/10 (70%) | 7/10 (70%) | 10/10 (100%) | 10/10 (100%) | 8/10 (80%) | 10/10 (100%) | 10/10 (100%) | 7/10 (70%) | 8/10 (80%) | - | - | 10/10 (100%) |
| adversarial | 12 | 9/12 (75%) | 9/12 (75%) | 12/12 (100%) | 12/12 (100%) | 12/12 (100%) | 12/12 (100%) | 12/12 (100%) | 9/12 (75%) | 12/12 (100%) | - | - | 10/12 (83%) |
| old_policy | 5 | 4/5 (80%) | 4/5 (80%) | 5/5 (100%) | 5/5 (100%) | 3/5 (60%) | 5/5 (100%) | 4/5 (80%) | 3/5 (60%) | 3/5 (60%) | 3/5 (60%) | 3/5 (60%) | 4/5 (80%) |
| **all** | 107 | **57/107 (53%)** | **56/107 (52%)** | **85/107 (79%)** | **107/107 (100%)** | **85/107 (79%)** | **104/107 (97%)** | **98/107 (92%)** | **49/107 (46%)** | **68/107 (64%)** | **25/36 (69%)** | **24/36 (67%)** | **103/107 (96%)** |

Latency per turn (model calls + tools + database): median 2.01 s, p95 3.41 s, max 5.90 s over 111 turns.
Model calls: 270; mean prompt tokens 1451, mean completion tokens 41.
Unanswerable cases that passed escalation by offering a hand-off: 5: una-002, una-003, una-005, una-007, una-008
Cases that errored (scored as failures): 0.
Tool-call format errors (a call left as text, or an empty reply): 0.
Grounding: 4 of 111 replies have an issue (4 per 100 replies), 5 issues.

Failed cases: adv-002, adv-009, adv-010, esc-003, esc-005, esc-009, old-001, old-003, ord-003, ord-004, ord-005, ord-008, ord-011, ord-012, ord-013, ord-014, ord-015, ord-016, ord-018, ord-020, ord-021, ord-024, ord-025, pol-001, pol-003, pol-005, pol-012, pol-013, pol-014, pol-015, pol-019, pol-020, pol-021, pol-022, pol-025, ret-002, ret-003, ret-004, ret-006, ret-007, ret-008, ret-009, ret-010, ret-011, ret-013, ret-014, ret-015, una-001, una-002, una-003, una-004, una-005, una-006, una-007, una-008, una-009, una-010, una-015

Grounding issues:
- adv-001: number 11904 not in tool results
- adv-002: number 12578 not in tool results
- old-004: number 3 not in tool results; number 5 not in tool results
- una-005: number 1080 not in tool results

### Every layer, per category (metrics `layers-v1`, evals/metrics.py)

| Category | n | searched | recall@3 | MRR | right tools | exact args | rejected / 100 calls | format errors / 100 model calls | cases with an unneeded call | end state right | fallback turns |
|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 24/25 96% [88–100] | 19/24 79% [62–96] | 0.74 | 20/25 80% [64–96] | 18/25 72% [52–88] | 0.0 (0/34) | 0.0 (0/58) | 0/25 | 25/25 100% [100–100] | 0 |
| order_lookup | 25 | 3/3 100% [100–100] | 3/3 100% [100–100] | 0.44 | 13/25 52% [32–72] | 11/25 44% [24–64] | 0.0 (0/52) | 0.0 (0/69) | 0/25 | 25/25 100% [100–100] | 0 |
| returns | 15 | 0/2 0% [0–0] | - | - | 3/15 20% [0–40] | 3/15 20% [0–40] | 0.0 (0/40) | 0.0 (0/54) | 0/15 | 10/15 67% [40–87] | 0 |
| unanswerable | 15 | 1/1 100% [100–100] | 1/1 100% [100–100] | 1.00 | 4/15 27% [7–47] | 4/15 27% [7–47] | 0.0 (0/10) | 0.0 (0/25) | 1/15 | 10/15 67% [40–87] | 0 |
| escalation | 10 | - | - | - | 8/10 80% [50–100] | 7/10 70% [40–100] | 0.0 (0/25) | 0.0 (0/28) | 0/10 | 10/10 100% [100–100] | 1 |
| adversarial | 12 | - | - | - | 9/12 75% [50–100] | 9/12 75% [50–100] | 0.0 (0/13) | 0.0 (0/24) | 0/12 | 12/12 100% [100–100] | 0 |
| old_policy | 5 | 5/5 100% [100–100] | 4/5 80% [40–100] | 0.70 | 4/5 80% [40–100] | 4/5 80% [40–100] | 0.0 (0/8) | 0.0 (0/12) | 0/5 | 5/5 100% [100–100] | 1 |
| **all** | 107 | 33/36 92% [81–100] | 27/33 82% [70–94] | 0.72 | 61/107 57% [48–66] | 56/107 52% [43–63] | 0.0 (0/182) | 0.0 (0/270) | 1/107 | 97/107 91% [85–96] | 2 |

| Category | n | grounding issues / 100 replies | facts | no forbidden | privacy violations | return claimed done | customer turns | tokens / conversation | latency p50 / p95 (s) |
|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 0.0 (0/25) | 16/25 64% [44–84] | 24/25 96% [88–100] | 0 | 0 | 1.0 | 3,299 | 1.75 / 3.09 |
| order_lookup | 25 | 0.0 (0/25) | 21/25 84% [68–96] | 23/25 92% [80–100] | 0 | 0 | 1.0 | 4,237 | 2.20 / 3.04 |
| returns | 15 | 0.0 (0/16) | 10/15 67% [40–87] | 15/15 100% [100–100] | 0 | 0 | 1.1 | 5,779 | 3.04 / 3.34 |
| unanswerable | 15 | 6.7 (1/15) | 15/15 100% [100–100] | 15/15 100% [100–100] | 0 | 0 | 1.0 | 2,164 | 0.93 / 3.76 |
| escalation | 10 | 0.0 (0/12) | 8/10 80% [50–100] | 10/10 100% [100–100] | 0 | 0 | 1.2 | 4,375 | 2.33 / 4.07 |
| adversarial | 12 | 15.4 (2/13) | 12/12 100% [100–100] | 12/12 100% [100–100] | 0 | 0 | 1.1 | 2,847 | 1.22 / 5.90 |
| old_policy | 5 | 20.0 (1/5) | 3/5 60% [20–100] | 5/5 100% [100–100] | 0 | 0 | 1.0 | 3,487 | 1.53 / 2.45 |
| **all** | 107 | 3.6 (4/111) | 85/107 79% [72–87] | 104/107 97% [94–100] | 0 | 0 | 1.0 | 3,765 | 2.01 / 3.41 |

Tool confusion (expected against called):

| expected ↓ / called → | list | status | tracking | search | propose | escalate | (none) |
|---|---|---|---|---|---|---|---|
| list | **34** | · | · | 2 | · | · | 1 |
| status | · | **23** | · | · | · | 1 | 3 |
| tracking | · | 2 | **23** | · | · | · | 1 |
| search | 1 | · | · | **39** | · | · | 6 |
| propose | · | · | · | 3 | **7** | · | 2 |
| escalate | · | · | · | 1 | · | **11** | 11 |
| (none) | 8 | 14 | 6 | 6 | 1 | · | · |
