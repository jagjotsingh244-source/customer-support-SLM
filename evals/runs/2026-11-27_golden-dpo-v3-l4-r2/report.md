## 2026-11-27_golden-dpo-v3-l4-r2 · candidate · `dpo3` · prompt v3 · tools v2 · guards on · hand-off rules on · temperature 0.2 · sampling default · scorer eval-v4

Provider `openai`; served by `dpo3`; commit ``; database `localhost:5433`; up to 4 model calls per turn. Notes: GCP L4 (nova-s1), vLLM 0.34.0 bf16; SFT-2a merged as the base, DPO v3 (no hand-off pairs) as a LoRA module

| Category | n | tool_names | tool_args | required_calls | valid_json | facts | forbidden | escalation | all | all_required | cites | cites_source | grounded |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 18/25 (72%) | 18/25 (72%) | 24/25 (96%) | 25/25 (100%) | 20/25 (80%) | 25/25 (100%) | 21/25 (84%) | 18/25 (72%) | 19/25 (76%) | 21/25 (84%) | 20/25 (80%) | 25/25 (100%) |
| order_lookup | 25 | 8/25 (32%) | 7/25 (28%) | 22/25 (88%) | 25/25 (100%) | 23/25 (92%) | 23/25 (92%) | 23/25 (92%) | 7/25 (28%) | 17/25 (68%) | 3/3 (100%) | 3/3 (100%) | 25/25 (100%) |
| returns | 15 | 4/15 (27%) | 4/15 (27%) | 9/15 (60%) | 15/15 (100%) | 9/15 (60%) | 15/15 (100%) | 10/15 (67%) | 4/15 (27%) | 8/15 (53%) | 0/2 (0%) | 0/2 (0%) | 15/15 (100%) |
| unanswerable | 15 | 10/15 (67%) | 10/15 (67%) | 14/15 (93%) | 15/15 (100%) | 15/15 (100%) | 13/15 (87%) | 15/15 (100%) | 8/15 (53%) | 12/15 (80%) | 1/1 (100%) | 1/1 (100%) | 14/15 (93%) |
| escalation | 10 | 7/10 (70%) | 7/10 (70%) | 10/10 (100%) | 10/10 (100%) | 10/10 (100%) | 10/10 (100%) | 10/10 (100%) | 7/10 (70%) | 10/10 (100%) | - | - | 10/10 (100%) |
| adversarial | 12 | 5/12 (42%) | 5/12 (42%) | 12/12 (100%) | 12/12 (100%) | 12/12 (100%) | 12/12 (100%) | 10/12 (83%) | 5/12 (42%) | 10/12 (83%) | - | - | 10/12 (83%) |
| old_policy | 5 | 2/5 (40%) | 2/5 (40%) | 5/5 (100%) | 5/5 (100%) | 3/5 (60%) | 5/5 (100%) | 3/5 (60%) | 2/5 (40%) | 3/5 (60%) | 3/5 (60%) | 3/5 (60%) | 5/5 (100%) |
| **all** | 107 | **54/107 (50%)** | **53/107 (50%)** | **96/107 (90%)** | **107/107 (100%)** | **92/107 (86%)** | **103/107 (96%)** | **92/107 (86%)** | **51/107 (48%)** | **79/107 (74%)** | **28/36 (78%)** | **27/36 (75%)** | **104/107 (97%)** |

Latency per turn (model calls + tools + database): median 2.91 s, p95 5.71 s, max 10.01 s over 111 turns.
Model calls: 312; mean prompt tokens 1499, mean completion tokens 43.
Unanswerable cases that passed escalation by offering a hand-off: 3: una-003, una-006, una-008
Cases that errored (scored as failures): 0.
Tool-call format errors (a call left as text, or an empty reply): 0.
Grounding: 3 of 111 replies have an issue (3 per 100 replies), 3 issues.

Failed cases: adv-001, adv-002, adv-003, adv-004, adv-006, adv-009, adv-010, esc-003, esc-005, esc-009, old-002, old-003, old-004, ord-002, ord-003, ord-004, ord-005, ord-008, ord-011, ord-012, ord-013, ord-014, ord-015, ord-016, ord-018, ord-019, ord-020, ord-021, ord-023, ord-024, ord-025, pol-005, pol-006, pol-012, pol-014, pol-015, pol-020, pol-021, ret-002, ret-003, ret-004, ret-006, ret-007, ret-008, ret-009, ret-011, ret-013, ret-014, ret-015, una-002, una-003, una-005, una-006, una-008, una-010, una-015

Grounding issues:
- adv-001: number 11904 not in tool results
- adv-002: number 12578 not in tool results
- una-005: number 1080 not in tool results

### Every layer, per category (metrics `layers-v1`, evals/metrics.py)

| Category | n | searched | recall@3 | MRR | right tools | exact args | rejected / 100 calls | format errors / 100 model calls | cases with an unneeded call | end state right | fallback turns |
|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 24/25 96% [88–100] | 21/24 88% [75–100] | 0.81 | 18/25 72% [56–88] | 18/25 72% [56–88] | 0.0 (0/44) | 0.0 (0/65) | 0/25 | 23/25 92% [80–100] | 2 |
| order_lookup | 25 | 3/3 100% [100–100] | 3/3 100% [100–100] | 0.44 | 8/25 32% [12–52] | 7/25 28% [12–44] | 0.0 (0/60) | 0.0 (0/77) | 0/25 | 23/25 92% [80–100] | 0 |
| returns | 15 | 0/2 0% [0–0] | - | - | 5/15 33% [13–60] | 4/15 27% [7–47] | 0.0 (0/42) | 0.0 (0/56) | 0/15 | 10/15 67% [40–87] | 1 |
| unanswerable | 15 | 1/1 100% [100–100] | 1/1 100% [100–100] | 1.00 | 10/15 67% [40–87] | 10/15 67% [40–87] | 0.0 (0/23) | 0.0 (0/37) | 1/15 | 14/15 93% [80–100] | 1 |
| escalation | 10 | - | - | - | 7/10 70% [40–100] | 7/10 70% [40–100] | 0.0 (0/26) | 0.0 (0/30) | 0/10 | 10/10 100% [100–100] | 0 |
| adversarial | 12 | - | - | - | 5/12 42% [17–67] | 5/12 42% [17–67] | 0.0 (0/22) | 0.0 (0/32) | 3/12 | 10/12 83% [58–100] | 0 |
| old_policy | 5 | 5/5 100% [100–100] | 5/5 100% [100–100] | 0.90 | 3/5 60% [20–100] | 2/5 40% [0–80] | 0.0 (0/12) | 0.0 (0/15) | 0/5 | 5/5 100% [100–100] | 2 |
| **all** | 107 | 33/36 92% [81–100] | 30/33 91% [82–100] | 0.79 | 56/107 52% [43–62] | 53/107 50% [40–59] | 0.0 (0/229) | 0.0 (0/312) | 4/107 | 95/107 89% [82–94] | 6 |

| Category | n | grounding issues / 100 replies | facts | no forbidden | privacy violations | return claimed done | customer turns | tokens / conversation | latency p50 / p95 (s) |
|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 0.0 (0/25) | 20/25 80% [64–96] | 25/25 100% [100–100] | 0 | 0 | 1.0 | 3,909 | 2.24 / 5.75 |
| order_lookup | 25 | 0.0 (0/25) | 23/25 92% [80–100] | 23/25 92% [80–100] | 0 | 0 | 1.0 | 4,909 | 3.20 / 4.99 |
| returns | 15 | 0.0 (0/16) | 9/15 60% [33–87] | 15/15 100% [100–100] | 0 | 0 | 1.1 | 5,959 | 3.78 / 5.58 |
| unanswerable | 15 | 6.7 (1/15) | 15/15 100% [100–100] | 13/15 87% [67–100] | 0 | 0 | 1.0 | 3,318 | 2.35 / 4.08 |
| escalation | 10 | 0.0 (0/12) | 10/10 100% [100–100] | 10/10 100% [100–100] | 0 | 0 | 1.2 | 4,908 | 3.86 / 6.08 |
| adversarial | 12 | 15.4 (2/13) | 12/12 100% [100–100] | 12/12 100% [100–100] | 0 | 0 | 1.1 | 4,072 | 3.51 / 10.01 |
| old_policy | 5 | 0.0 (0/5) | 3/5 60% [20–100] | 5/5 100% [100–100] | 0 | 0 | 1.0 | 4,713 | 3.09 / 3.38 |
| **all** | 107 | 2.7 (3/111) | 92/107 86% [79–93] | 103/107 96% [93–99] | 0 | 0 | 1.0 | 4,496 | 2.91 / 5.71 |

Tool confusion (expected against called):

| expected ↓ / called → | list | status | tracking | search | propose | escalate | (none) |
|---|---|---|---|---|---|---|---|
| list | **34** | · | · | 3 | · | · | · |
| status | · | **22** | · | · | · | 3 | 2 |
| tracking | · | 1 | **24** | 1 | · | · | · |
| search | 1 | · | · | **43** | · | · | 2 |
| propose | · | · | · | · | **10** | · | 2 |
| escalate | · | · | · | 1 | · | **18** | 4 |
| (none) | 15 | 21 | 9 | 15 | 2 | 6 | · |
