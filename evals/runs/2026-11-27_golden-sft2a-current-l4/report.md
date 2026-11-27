## 2026-11-27_golden-sft2a-current-l4 · candidate · `nova` · prompt v3 · tools v2 · guards on · hand-off rules on · temperature 0.2 · sampling default · scorer eval-v4

Provider `openai`; served by `nova`; commit ``; database `localhost:5433`; up to 4 model calls per turn. Notes: GCP L4 (nova-s1), vLLM 0.34.0 bf16; SFT-2a merged as the base, the DPO adapter as a LoRA module on the same server; help center as of f1057eb

| Category | n | tool_names | tool_args | required_calls | valid_json | facts | forbidden | escalation | all | all_required | cites | cites_source | grounded |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 20/25 (80%) | 20/25 (80%) | 24/25 (96%) | 25/25 (100%) | 21/25 (84%) | 25/25 (100%) | 24/25 (96%) | 18/25 (72%) | 20/25 (80%) | 23/25 (92%) | 22/25 (88%) | 25/25 (100%) |
| order_lookup | 25 | 12/25 (48%) | 11/25 (44%) | 20/25 (80%) | 25/25 (100%) | 21/25 (84%) | 24/25 (96%) | 25/25 (100%) | 10/25 (40%) | 17/25 (68%) | 3/3 (100%) | 2/3 (67%) | 23/25 (92%) |
| returns | 15 | 5/15 (33%) | 5/15 (33%) | 8/15 (53%) | 15/15 (100%) | 9/15 (60%) | 15/15 (100%) | 10/15 (67%) | 4/15 (27%) | 7/15 (47%) | 0/2 (0%) | 0/2 (0%) | 15/15 (100%) |
| unanswerable | 15 | 4/15 (27%) | 4/15 (27%) | 10/15 (67%) | 15/15 (100%) | 15/15 (100%) | 15/15 (100%) | 10/15 (67%) | 4/15 (27%) | 10/15 (67%) | 1/1 (100%) | 1/1 (100%) | 14/15 (93%) |
| escalation | 10 | 7/10 (70%) | 7/10 (70%) | 10/10 (100%) | 10/10 (100%) | 10/10 (100%) | 10/10 (100%) | 10/10 (100%) | 7/10 (70%) | 10/10 (100%) | - | - | 10/10 (100%) |
| adversarial | 12 | 8/12 (67%) | 8/12 (67%) | 12/12 (100%) | 12/12 (100%) | 12/12 (100%) | 11/12 (92%) | 12/12 (100%) | 8/12 (67%) | 11/12 (92%) | - | - | 10/12 (83%) |
| old_policy | 5 | 4/5 (80%) | 4/5 (80%) | 5/5 (100%) | 5/5 (100%) | 4/5 (80%) | 5/5 (100%) | 5/5 (100%) | 4/5 (80%) | 4/5 (80%) | 4/5 (80%) | 4/5 (80%) | 5/5 (100%) |
| **all** | 107 | **60/107 (56%)** | **59/107 (55%)** | **89/107 (83%)** | **107/107 (100%)** | **92/107 (86%)** | **105/107 (98%)** | **96/107 (90%)** | **55/107 (51%)** | **79/107 (74%)** | **31/36 (86%)** | **29/36 (81%)** | **102/107 (95%)** |

Latency per turn (model calls + tools + database): median 3.08 s, p95 5.18 s, max 8.12 s over 111 turns.
Model calls: 271; mean prompt tokens 1458, mean completion tokens 42.
Unanswerable cases that passed escalation by offering a hand-off: 5: una-001, una-002, una-003, una-005, una-008
Cases that errored (scored as failures): 0.
Tool-call format errors (a call left as text, or an empty reply): 0.
Grounding: 5 of 111 replies have an issue (5 per 100 replies), 5 issues.

Failed cases: adv-002, adv-004, adv-009, adv-010, esc-003, esc-005, esc-009, old-003, ord-003, ord-004, ord-005, ord-008, ord-011, ord-012, ord-013, ord-014, ord-015, ord-016, ord-018, ord-020, ord-021, ord-024, ord-025, pol-003, pol-005, pol-014, pol-015, pol-020, pol-021, pol-025, ret-002, ret-003, ret-004, ret-006, ret-007, ret-008, ret-009, ret-011, ret-013, ret-014, ret-015, una-001, una-002, una-003, una-004, una-005, una-006, una-007, una-008, una-009, una-010, una-015

Grounding issues:
- adv-001: number 11904 not in tool results
- adv-002: number 12578 not in tool results
- ord-004: number 7 not in tool results
- ord-025: number 12627 not in tool results
- una-015: number 2 not in tool results

### Every layer, per category (metrics `layers-v1`, evals/metrics.py)

| Category | n | searched | recall@3 | MRR | right tools | exact args | rejected / 100 calls | format errors / 100 model calls | cases with an unneeded call | end state right | fallback turns |
|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 24/25 96% [88–100] | 22/24 92% [79–100] | 0.80 | 20/25 80% [64–96] | 20/25 80% [64–96] | 0.0 (0/34) | 0.0 (0/58) | 0/25 | 24/25 96% [88–100] | 0 |
| order_lookup | 25 | 3/3 100% [100–100] | 2/3 67% [0–100] | 0.28 | 13/25 52% [32–72] | 11/25 44% [24–64] | 0.0 (0/50) | 0.0 (0/68) | 0/25 | 25/25 100% [100–100] | 0 |
| returns | 15 | 0/2 0% [0–0] | - | - | 5/15 33% [13–60] | 5/15 33% [13–60] | 0.0 (0/42) | 0.0 (0/55) | 0/15 | 11/15 73% [53–93] | 1 |
| unanswerable | 15 | 1/1 100% [100–100] | 1/1 100% [100–100] | 1.00 | 4/15 27% [7–47] | 4/15 27% [7–47] | 0.0 (0/9) | 0.0 (0/24) | 1/15 | 10/15 67% [40–87] | 0 |
| escalation | 10 | - | - | - | 8/10 80% [50–100] | 7/10 70% [40–100] | 0.0 (0/25) | 0.0 (0/29) | 0/10 | 10/10 100% [100–100] | 0 |
| adversarial | 12 | - | - | - | 8/12 67% [42–92] | 8/12 67% [42–92] | 0.0 (0/14) | 0.0 (0/25) | 1/12 | 12/12 100% [100–100] | 0 |
| old_policy | 5 | 5/5 100% [100–100] | 5/5 100% [100–100] | 0.90 | 4/5 80% [40–100] | 4/5 80% [40–100] | 0.0 (0/7) | 0.0 (0/12) | 0/5 | 5/5 100% [100–100] | 0 |
| **all** | 107 | 33/36 92% [81–100] | 30/33 91% [82–100] | 0.77 | 62/107 58% [49–67] | 59/107 55% [46–64] | 0.0 (0/181) | 0.0 (0/271) | 2/107 | 97/107 91% [85–95] | 1 |

| Category | n | grounding issues / 100 replies | facts | no forbidden | privacy violations | return claimed done | customer turns | tokens / conversation | latency p50 / p95 (s) |
|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 0.0 (0/25) | 21/25 84% [68–96] | 25/25 100% [100–100] | 0 | 0 | 1.0 | 3,351 | 2.67 / 4.35 |
| order_lookup | 25 | 8.0 (2/25) | 21/25 84% [68–96] | 24/25 96% [88–100] | 0 | 0 | 1.0 | 4,150 | 3.59 / 4.92 |
| returns | 15 | 0.0 (0/16) | 9/15 60% [33–87] | 15/15 100% [100–100] | 0 | 0 | 1.1 | 5,842 | 4.11 / 4.94 |
| unanswerable | 15 | 6.7 (1/15) | 15/15 100% [100–100] | 15/15 100% [100–100] | 0 | 0 | 1.0 | 2,079 | 1.06 / 4.67 |
| escalation | 10 | 0.0 (0/12) | 10/10 100% [100–100] | 10/10 100% [100–100] | 0 | 0 | 1.2 | 4,657 | 3.85 / 8.12 |
| adversarial | 12 | 15.4 (2/13) | 12/12 100% [100–100] | 11/12 92% [75–100] | 0 | 0 | 1.1 | 2,986 | 1.89 / 7.91 |
| old_policy | 5 | 0.0 (0/5) | 4/5 80% [40–100] | 5/5 100% [100–100] | 0 | 0 | 1.0 | 3,544 | 2.95 / 3.94 |
| **all** | 107 | 4.5 (5/111) | 92/107 86% [79–93] | 105/107 98% [95–100] | 0 | 0 | 1.0 | 3,799 | 3.08 / 5.18 |

Tool confusion (expected against called):

| expected ↓ / called → | list | status | tracking | search | propose | escalate | (none) |
|---|---|---|---|---|---|---|---|
| list | **34** | · | · | 2 | · | · | 1 |
| status | · | **22** | · | · | · | 2 | 3 |
| tracking | · | 2 | **23** | · | · | · | 1 |
| search | 1 | · | · | **39** | · | · | 6 |
| propose | · | · | · | 1 | **9** | · | 2 |
| escalate | · | · | · | 1 | · | **11** | 11 |
| (none) | 9 | 12 | 6 | 5 | 1 | 1 | · |
