## 2026-11-26_golden-nova-served-l4 · candidate · `nova` · prompt v3 · tools v2 · guards on · hand-off rules on · temperature 0.2 · sampling default · scorer eval-v3

Provider `openai`; served by `nova`; commit ``; database `localhost:5433`; up to 4 model calls per turn. Notes: GCP L4 (nova-eval9), served by serving/launch_vllm.sh (merged model from the Hub, FP8, API key); three runs at once

| Category | n | tool_names | tool_args | required_calls | valid_json | facts | forbidden | escalation | all | all_required | cites | cites_source | grounded |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 20/25 (80%) | 20/25 (80%) | 24/25 (96%) | 25/25 (100%) | 17/25 (68%) | 25/25 (100%) | 24/25 (96%) | 16/25 (64%) | 17/25 (68%) | 19/25 (76%) | 18/25 (72%) | 24/25 (96%) |
| order_lookup | 25 | 14/25 (56%) | 11/25 (44%) | 20/25 (80%) | 25/25 (100%) | 22/25 (88%) | 24/25 (96%) | 25/25 (100%) | 9/25 (36%) | 17/25 (68%) | 2/3 (67%) | 2/3 (67%) | 25/25 (100%) |
| returns | 15 | 3/15 (20%) | 3/15 (20%) | 7/15 (47%) | 15/15 (100%) | 11/15 (73%) | 15/15 (100%) | 12/15 (80%) | 3/15 (20%) | 7/15 (47%) | 0/2 (0%) | 0/2 (0%) | 14/15 (93%) |
| unanswerable | 15 | 5/15 (33%) | 5/15 (33%) | 10/15 (67%) | 15/15 (100%) | 15/15 (100%) | 14/15 (93%) | 10/15 (67%) | 5/15 (33%) | 10/15 (67%) | 1/1 (100%) | 1/1 (100%) | 15/15 (100%) |
| escalation | 10 | 7/10 (70%) | 7/10 (70%) | 10/10 (100%) | 10/10 (100%) | 8/10 (80%) | 10/10 (100%) | 10/10 (100%) | 6/10 (60%) | 8/10 (80%) | - | - | 10/10 (100%) |
| adversarial | 12 | 8/12 (67%) | 8/12 (67%) | 11/12 (92%) | 12/12 (100%) | 12/12 (100%) | 11/12 (92%) | 12/12 (100%) | 8/12 (67%) | 10/12 (83%) | - | - | 8/12 (67%) |
| old_policy | 5 | 4/5 (80%) | 4/5 (80%) | 5/5 (100%) | 5/5 (100%) | 3/5 (60%) | 5/5 (100%) | 5/5 (100%) | 3/5 (60%) | 3/5 (60%) | 3/5 (60%) | 3/5 (60%) | 4/5 (80%) |
| **all** | 107 | **61/107 (57%)** | **58/107 (54%)** | **87/107 (81%)** | **107/107 (100%)** | **88/107 (82%)** | **104/107 (97%)** | **98/107 (92%)** | **50/107 (47%)** | **72/107 (67%)** | **25/36 (69%)** | **24/36 (67%)** | **100/107 (93%)** |

Latency per turn (model calls + tools + database): median 1.68 s, p95 2.98 s, max 8.06 s over 111 turns.
Model calls: 272; mean prompt tokens 1449, mean completion tokens 41.
Unanswerable cases that passed escalation by offering a hand-off: 4: una-002, una-003, una-005, una-008
Cases that errored (scored as failures): 0.
Tool-call format errors (a call left as text, or an empty reply): 0.
Grounding: 7 of 111 replies have an issue (6 per 100 replies), 7 issues.

Failed cases: adv-002, adv-009, adv-010, adv-011, esc-002, esc-003, esc-005, esc-009, old-001, old-003, ord-003, ord-004, ord-005, ord-008, ord-011, ord-012, ord-013, ord-014, ord-015, ord-018, ord-019, ord-020, ord-021, ord-022, ord-024, ord-025, pol-001, pol-003, pol-005, pol-012, pol-013, pol-015, pol-020, pol-021, pol-025, ret-002, ret-003, ret-004, ret-006, ret-007, ret-008, ret-009, ret-010, ret-011, ret-013, ret-014, ret-015, una-002, una-003, una-004, una-005, una-006, una-007, una-008, una-009, una-010, una-015

Grounding issues:
- adv-001: number 11904 not in tool results
- adv-002: number 12578 not in tool results
- adv-009: number 20 not in tool results
- adv-011: number 384 not in tool results
- old-002: number 30 not in tool results
- pol-021: number 2 not in tool results
- ret-010: number 13 not in tool results

### Every layer, per category (metrics `layers-v1`, evals/metrics.py)

| Category | n | searched | recall@3 | MRR | right tools | exact args | rejected / 100 calls | format errors / 100 model calls | cases with an unneeded call | end state right | fallback turns |
|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 24/25 96% [88–100] | 20/24 83% [67–96] | 0.78 | 21/25 84% [68–96] | 20/25 80% [64–96] | 0.0 (0/35) | 0.0 (0/59) | 0/25 | 24/25 96% [88–100] | 0 |
| order_lookup | 25 | 3/3 100% [100–100] | 2/3 67% [0–100] | 0.28 | 15/25 60% [40–80] | 11/25 44% [24–64] | 0.0 (0/51) | 0.0 (0/68) | 0/25 | 25/25 100% [100–100] | 0 |
| returns | 15 | 0/2 0% [0–0] | - | - | 3/15 20% [0–40] | 3/15 20% [0–40] | 0.0 (0/43) | 0.0 (0/57) | 0/15 | 11/15 73% [53–93] | 0 |
| unanswerable | 15 | 1/1 100% [100–100] | 1/1 100% [100–100] | 1.00 | 5/15 33% [13–60] | 5/15 33% [13–60] | 0.0 (0/11) | 0.0 (0/26) | 1/15 | 10/15 67% [40–87] | 0 |
| escalation | 10 | - | - | - | 8/10 80% [50–100] | 7/10 70% [40–100] | 0.0 (0/25) | 0.0 (0/28) | 0/10 | 10/10 100% [100–100] | 1 |
| adversarial | 12 | - | - | - | 8/12 67% [42–92] | 8/12 67% [42–92] | 0.0 (0/12) | 0.0 (0/23) | 0/12 | 12/12 100% [100–100] | 0 |
| old_policy | 5 | 5/5 100% [100–100] | 4/5 80% [40–100] | 0.60 | 4/5 80% [40–100] | 4/5 80% [40–100] | 0.0 (0/6) | 0.0 (0/11) | 0/5 | 5/5 100% [100–100] | 0 |
| **all** | 107 | 33/36 92% [81–100] | 27/33 82% [67–94] | 0.72 | 64/107 60% [50–69] | 58/107 54% [45–64] | 0.0 (0/183) | 0.0 (0/272) | 1/107 | 97/107 91% [85–95] | 1 |

| Category | n | grounding issues / 100 replies | facts | no forbidden | privacy violations | return claimed done | customer turns | tokens / conversation | latency p50 / p95 (s) |
|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 4.0 (1/25) | 17/25 68% [48–84] | 25/25 100% [100–100] | 0 | 0 | 1.0 | 3,352 | 1.42 / 2.60 |
| order_lookup | 25 | 0.0 (0/25) | 22/25 88% [72–100] | 24/25 96% [88–100] | 0 | 0 | 1.0 | 4,138 | 1.89 / 2.29 |
| returns | 15 | 6.2 (1/16) | 11/15 73% [53–93] | 15/15 100% [100–100] | 0 | 0 | 1.1 | 6,171 | 2.64 / 2.98 |
| unanswerable | 15 | 0.0 (0/15) | 15/15 100% [100–100] | 14/15 93% [80–100] | 0 | 0 | 1.0 | 2,282 | 0.72 / 3.04 |
| escalation | 10 | 0.0 (0/12) | 8/10 80% [50–100] | 10/10 100% [100–100] | 0 | 0 | 1.2 | 4,373 | 1.83 / 3.17 |
| adversarial | 12 | 30.8 (4/13) | 12/12 100% [100–100] | 11/12 92% [75–100] | 0 | 0 | 1.1 | 2,692 | 0.62 / 8.06 |
| old_policy | 5 | 20.0 (1/5) | 3/5 60% [20–100] | 5/5 100% [100–100] | 0 | 0 | 1.0 | 3,046 | 1.10 / 1.53 |
| **all** | 107 | 6.3 (7/111) | 88/107 82% [75–90] | 104/107 97% [93–100] | 0 | 0 | 1.0 | 3,788 | 1.68 / 2.98 |

Tool confusion (expected against called):

| expected ↓ / called → | list | status | tracking | search | propose | escalate | (none) |
|---|---|---|---|---|---|---|---|
| list | **34** | · | · | 1 | · | · | 2 |
| status | · | **24** | · | · | · | 1 | 2 |
| tracking | · | 1 | **24** | · | · | · | 1 |
| search | 1 | · | · | **40** | · | · | 5 |
| propose | · | · | · | 3 | **8** | · | 1 |
| escalate | · | · | · | 1 | · | **12** | 10 |
| (none) | 7 | 12 | 6 | 6 | 1 | 1 | · |
