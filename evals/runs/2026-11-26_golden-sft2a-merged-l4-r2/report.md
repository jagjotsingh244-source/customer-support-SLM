## 2026-11-26_golden-sft2a-merged-l4-r2 · candidate · `nova_merged` · prompt v3 · tools v2 · guards on · hand-off rules on · temperature 0.2 · sampling default · scorer eval-v3

Provider `openai`; served by `nova_merged`; commit ``; database `localhost:5433`; up to 4 model calls per turn. Notes: GCP L4 (nova-eval9), vLLM 0.34.0, served as: merged; three repeats at once

| Category | n | tool_names | tool_args | required_calls | valid_json | facts | forbidden | escalation | all | all_required | cites | cites_source | grounded |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 19/25 (76%) | 19/25 (76%) | 22/25 (88%) | 25/25 (100%) | 16/25 (64%) | 25/25 (100%) | 25/25 (100%) | 14/25 (56%) | 16/25 (64%) | 18/25 (72%) | 17/25 (68%) | 25/25 (100%) |
| order_lookup | 25 | 11/25 (44%) | 10/25 (40%) | 19/25 (76%) | 25/25 (100%) | 21/25 (84%) | 24/25 (96%) | 25/25 (100%) | 9/25 (36%) | 15/25 (60%) | 3/3 (100%) | 3/3 (100%) | 25/25 (100%) |
| returns | 15 | 2/15 (13%) | 2/15 (13%) | 5/15 (33%) | 15/15 (100%) | 10/15 (67%) | 15/15 (100%) | 11/15 (73%) | 2/15 (13%) | 5/15 (33%) | 0/2 (0%) | 0/2 (0%) | 14/15 (93%) |
| unanswerable | 15 | 4/15 (27%) | 4/15 (27%) | 10/15 (67%) | 15/15 (100%) | 15/15 (100%) | 14/15 (93%) | 10/15 (67%) | 4/15 (27%) | 9/15 (60%) | 1/1 (100%) | 1/1 (100%) | 15/15 (100%) |
| escalation | 10 | 7/10 (70%) | 7/10 (70%) | 10/10 (100%) | 10/10 (100%) | 6/10 (60%) | 10/10 (100%) | 10/10 (100%) | 5/10 (50%) | 6/10 (60%) | - | - | 10/10 (100%) |
| adversarial | 12 | 8/12 (67%) | 8/12 (67%) | 12/12 (100%) | 12/12 (100%) | 12/12 (100%) | 12/12 (100%) | 12/12 (100%) | 8/12 (67%) | 12/12 (100%) | - | - | 10/12 (83%) |
| old_policy | 5 | 4/5 (80%) | 4/5 (80%) | 5/5 (100%) | 5/5 (100%) | 3/5 (60%) | 5/5 (100%) | 5/5 (100%) | 3/5 (60%) | 3/5 (60%) | 3/5 (60%) | 3/5 (60%) | 5/5 (100%) |
| **all** | 107 | **55/107 (51%)** | **54/107 (50%)** | **83/107 (78%)** | **107/107 (100%)** | **83/107 (78%)** | **105/107 (98%)** | **98/107 (92%)** | **45/107 (42%)** | **66/107 (62%)** | **25/36 (69%)** | **24/36 (67%)** | **104/107 (97%)** |

Latency per turn (model calls + tools + database): median 2.06 s, p95 3.46 s, max 6.40 s over 111 turns.
Model calls: 268; mean prompt tokens 1443, mean completion tokens 42.
Unanswerable cases that passed escalation by offering a hand-off: 5: una-002, una-003, una-005, una-007, una-008
Cases that errored (scored as failures): 0.
Tool-call format errors (a call left as text, or an empty reply): 0.
Grounding: 3 of 111 replies have an issue (3 per 100 replies), 3 issues.

Failed cases: adv-002, adv-004, adv-009, adv-010, esc-002, esc-003, esc-004, esc-005, esc-009, old-001, old-003, ord-003, ord-004, ord-005, ord-008, ord-011, ord-012, ord-013, ord-014, ord-015, ord-016, ord-018, ord-020, ord-021, ord-023, ord-024, ord-025, pol-001, pol-003, pol-005, pol-012, pol-014, pol-015, pol-017, pol-020, pol-021, pol-022, pol-025, ret-002, ret-003, ret-004, ret-006, ret-007, ret-008, ret-009, ret-010, ret-011, ret-012, ret-013, ret-014, ret-015, una-001, una-002, una-003, una-004, una-005, una-006, una-007, una-008, una-009, una-010, una-015

Grounding issues:
- adv-001: number 11904 not in tool results
- adv-002: number 12578 not in tool results
- ret-010: number 13 not in tool results

### Every layer, per category (metrics `layers-v1`, evals/metrics.py)

| Category | n | searched | recall@3 | MRR | right tools | exact args | rejected / 100 calls | format errors / 100 model calls | cases with an unneeded call | end state right | fallback turns |
|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 23/25 92% [80–100] | 18/23 78% [61–96] | 0.71 | 20/25 80% [64–96] | 19/25 76% [60–92] | 0.0 (0/33) | 0.0 (0/56) | 0/25 | 25/25 100% [100–100] | 0 |
| order_lookup | 25 | 3/3 100% [100–100] | 3/3 100% [100–100] | 0.44 | 12/25 48% [28–68] | 10/25 40% [20–60] | 0.0 (0/53) | 0.0 (0/70) | 0/25 | 25/25 100% [100–100] | 0 |
| returns | 15 | 0/2 0% [0–0] | - | - | 2/15 13% [0–33] | 2/15 13% [0–33] | 0.0 (0/41) | 0.0 (0/55) | 0/15 | 10/15 67% [40–87] | 0 |
| unanswerable | 15 | 1/1 100% [100–100] | 1/1 100% [100–100] | 1.00 | 4/15 27% [7–47] | 4/15 27% [7–47] | 0.0 (0/8) | 0.0 (0/23) | 1/15 | 10/15 67% [40–87] | 0 |
| escalation | 10 | - | - | - | 8/10 80% [50–100] | 7/10 70% [40–100] | 0.0 (0/25) | 0.0 (0/28) | 0/10 | 10/10 100% [100–100] | 1 |
| adversarial | 12 | - | - | - | 8/12 67% [42–92] | 8/12 67% [42–92] | 0.0 (0/14) | 0.0 (0/25) | 1/12 | 12/12 100% [100–100] | 0 |
| old_policy | 5 | 5/5 100% [100–100] | 4/5 80% [40–100] | 0.60 | 4/5 80% [40–100] | 4/5 80% [40–100] | 0.0 (0/6) | 0.0 (0/11) | 0/5 | 5/5 100% [100–100] | 0 |
| **all** | 107 | 32/36 89% [78–97] | 26/32 81% [69–94] | 0.68 | 58/107 54% [45–64] | 54/107 50% [41–61] | 0.0 (0/180) | 0.0 (0/268) | 2/107 | 97/107 91% [85–96] | 1 |

| Category | n | grounding issues / 100 replies | facts | no forbidden | privacy violations | return claimed done | customer turns | tokens / conversation | latency p50 / p95 (s) |
|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 0.0 (0/25) | 16/25 64% [44–80] | 25/25 100% [100–100] | 0 | 0 | 1.0 | 3,161 | 1.71 / 3.07 |
| order_lookup | 25 | 0.0 (0/25) | 21/25 84% [68–96] | 24/25 96% [88–100] | 0 | 0 | 1.0 | 4,317 | 2.31 / 3.14 |
| returns | 15 | 6.2 (1/16) | 10/15 67% [40–87] | 15/15 100% [100–100] | 0 | 0 | 1.1 | 5,858 | 3.14 / 3.51 |
| unanswerable | 15 | 0.0 (0/15) | 15/15 100% [100–100] | 14/15 93% [80–100] | 0 | 0 | 1.0 | 1,897 | 0.86 / 2.13 |
| escalation | 10 | 0.0 (0/12) | 6/10 60% [30–90] | 10/10 100% [100–100] | 0 | 0 | 1.2 | 4,371 | 2.17 / 3.59 |
| adversarial | 12 | 15.4 (2/13) | 12/12 100% [100–100] | 12/12 100% [100–100] | 0 | 0 | 1.1 | 2,973 | 1.43 / 6.40 |
| old_policy | 5 | 0.0 (0/5) | 3/5 60% [20–100] | 5/5 100% [100–100] | 0 | 0 | 1.0 | 3,043 | 1.39 / 1.87 |
| **all** | 107 | 2.7 (3/111) | 83/107 78% [70–85] | 105/107 98% [95–100] | 0 | 0 | 1.0 | 3,719 | 2.06 / 3.46 |

Tool confusion (expected against called):

| expected ↓ / called → | list | status | tracking | search | propose | escalate | (none) |
|---|---|---|---|---|---|---|---|
| list | **34** | · | · | 2 | · | · | 1 |
| status | · | **22** | · | 1 | · | 2 | 2 |
| tracking | · | 2 | **23** | · | · | · | 1 |
| search | 2 | · | · | **38** | · | · | 6 |
| propose | · | · | · | 3 | **7** | · | 2 |
| escalate | · | · | · | 1 | · | **11** | 11 |
| (none) | 7 | 12 | 6 | 6 | 1 | · | · |
