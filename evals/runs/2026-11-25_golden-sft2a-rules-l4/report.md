## 2026-11-25_golden-sft2a-rules-l4 · candidate · `sft2a_v1` · prompt v3 · tools v2 · guards on · hand-off rules on · temperature 0.2 · sampling default · scorer eval-v3

Provider `openai`; served by `sft2a_v1`; commit ``; database `localhost:5433`; up to 4 model calls per turn. Notes: GCP L4 (nova-eval9), vLLM 0.34.0, bf16, base + SFT-2a v1 as a LoRA module on one server

| Category | n | tool_names | tool_args | required_calls | valid_json | facts | forbidden | escalation | all | all_required | cites | cites_source | grounded |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 19/25 (76%) | 19/25 (76%) | 23/25 (92%) | 25/25 (100%) | 16/25 (64%) | 25/25 (100%) | 25/25 (100%) | 15/25 (60%) | 16/25 (64%) | 17/25 (68%) | 17/25 (68%) | 25/25 (100%) |
| order_lookup | 25 | 12/25 (48%) | 11/25 (44%) | 19/25 (76%) | 25/25 (100%) | 22/25 (88%) | 24/25 (96%) | 25/25 (100%) | 11/25 (44%) | 16/25 (64%) | 3/3 (100%) | 3/3 (100%) | 25/25 (100%) |
| returns | 15 | 4/15 (27%) | 4/15 (27%) | 8/15 (53%) | 15/15 (100%) | 11/15 (73%) | 15/15 (100%) | 12/15 (80%) | 4/15 (27%) | 8/15 (53%) | 0/2 (0%) | 0/2 (0%) | 15/15 (100%) |
| unanswerable | 15 | 4/15 (27%) | 4/15 (27%) | 9/15 (60%) | 15/15 (100%) | 15/15 (100%) | 15/15 (100%) | 9/15 (60%) | 4/15 (27%) | 9/15 (60%) | 1/1 (100%) | 1/1 (100%) | 14/15 (93%) |
| escalation | 10 | 7/10 (70%) | 7/10 (70%) | 10/10 (100%) | 10/10 (100%) | 7/10 (70%) | 10/10 (100%) | 10/10 (100%) | 6/10 (60%) | 7/10 (70%) | - | - | 10/10 (100%) |
| adversarial | 12 | 9/12 (75%) | 9/12 (75%) | 11/12 (92%) | 12/12 (100%) | 12/12 (100%) | 12/12 (100%) | 12/12 (100%) | 9/12 (75%) | 11/12 (92%) | - | - | 9/12 (75%) |
| old_policy | 5 | 4/5 (80%) | 4/5 (80%) | 5/5 (100%) | 5/5 (100%) | 3/5 (60%) | 5/5 (100%) | 5/5 (100%) | 3/5 (60%) | 3/5 (60%) | 3/5 (60%) | 3/5 (60%) | 4/5 (80%) |
| **all** | 107 | **59/107 (55%)** | **58/107 (54%)** | **85/107 (79%)** | **107/107 (100%)** | **86/107 (80%)** | **106/107 (99%)** | **98/107 (92%)** | **52/107 (49%)** | **70/107 (65%)** | **24/36 (67%)** | **24/36 (67%)** | **102/107 (95%)** |

Latency per turn (model calls + tools + database): median 2.46 s, p95 4.47 s, max 8.79 s over 111 turns.
Model calls: 266; mean prompt tokens 1447, mean completion tokens 41.
Unanswerable cases that passed escalation by offering a hand-off: 4: una-002, una-003, una-005, una-008
Cases that errored (scored as failures): 0.
Tool-call format errors (a call left as text, or an empty reply): 0.
Grounding: 5 of 111 replies have an issue (5 per 100 replies), 6 issues.

Failed cases: adv-002, adv-009, adv-010, esc-002, esc-003, esc-005, esc-009, old-001, old-003, ord-003, ord-005, ord-008, ord-011, ord-012, ord-013, ord-014, ord-015, ord-016, ord-018, ord-020, ord-021, ord-024, ord-025, pol-001, pol-003, pol-005, pol-012, pol-014, pol-015, pol-020, pol-021, pol-022, pol-025, ret-002, ret-003, ret-004, ret-006, ret-007, ret-008, ret-009, ret-011, ret-013, ret-014, ret-015, una-001, una-002, una-003, una-004, una-005, una-006, una-007, una-008, una-009, una-010, una-015

Grounding issues:
- adv-001: number 11904 not in tool results
- adv-002: number 12578 not in tool results
- adv-006: number 11281 not in tool results
- old-004: number 3 not in tool results; number 5 not in tool results
- una-005: number 1080 not in tool results

### Every layer, per category (metrics `layers-v1`, evals/metrics.py)

| Category | n | searched | recall@3 | MRR | right tools | exact args | rejected / 100 calls | format errors / 100 model calls | cases with an unneeded call | end state right | fallback turns |
|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 24/25 96% [88–100] | 18/24 75% [54–92] | 0.68 | 20/25 80% [64–96] | 19/25 76% [60–92] | 0.0 (0/33) | 0.0 (0/57) | 0/25 | 25/25 100% [100–100] | 0 |
| order_lookup | 25 | 3/3 100% [100–100] | 3/3 100% [100–100] | 0.44 | 13/25 52% [32–72] | 11/25 44% [24–64] | 0.0 (0/52) | 0.0 (0/69) | 0/25 | 25/25 100% [100–100] | 0 |
| returns | 15 | 0/2 0% [0–0] | - | - | 4/15 27% [7–47] | 4/15 27% [7–47] | 0.0 (0/41) | 0.0 (0/55) | 0/15 | 11/15 73% [53–93] | 0 |
| unanswerable | 15 | 1/1 100% [100–100] | 1/1 100% [100–100] | 1.00 | 4/15 27% [7–47] | 4/15 27% [7–47] | 0.0 (0/9) | 0.0 (0/24) | 1/15 | 9/15 60% [33–80] | 0 |
| escalation | 10 | - | - | - | 8/10 80% [50–100] | 7/10 70% [40–100] | 0.0 (0/25) | 0.0 (0/28) | 0/10 | 10/10 100% [100–100] | 1 |
| adversarial | 12 | - | - | - | 9/12 75% [50–100] | 9/12 75% [50–100] | 0.0 (0/11) | 0.0 (0/22) | 0/12 | 12/12 100% [100–100] | 0 |
| old_policy | 5 | 5/5 100% [100–100] | 4/5 80% [40–100] | 0.60 | 4/5 80% [40–100] | 4/5 80% [40–100] | 0.0 (0/6) | 0.0 (0/11) | 0/5 | 5/5 100% [100–100] | 0 |
| **all** | 107 | 33/36 92% [81–100] | 26/33 79% [64–91] | 0.66 | 62/107 58% [49–67] | 58/107 54% [45–64] | 0.0 (0/177) | 0.0 (0/266) | 1/107 | 97/107 91% [85–96] | 1 |

| Category | n | grounding issues / 100 replies | facts | no forbidden | privacy violations | return claimed done | customer turns | tokens / conversation | latency p50 / p95 (s) |
|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 0.0 (0/25) | 16/25 64% [44–84] | 25/25 100% [100–100] | 0 | 0 | 1.0 | 3,229 | 2.20 / 4.18 |
| order_lookup | 25 | 0.0 (0/25) | 22/25 88% [72–100] | 24/25 96% [88–100] | 0 | 0 | 1.0 | 4,236 | 2.97 / 3.97 |
| returns | 15 | 0.0 (0/16) | 11/15 73% [53–93] | 15/15 100% [100–100] | 0 | 0 | 1.1 | 5,876 | 4.08 / 4.75 |
| unanswerable | 15 | 6.7 (1/15) | 15/15 100% [100–100] | 15/15 100% [100–100] | 0 | 0 | 1.0 | 2,081 | 1.17 / 4.18 |
| escalation | 10 | 0.0 (0/12) | 7/10 70% [40–100] | 10/10 100% [100–100] | 0 | 0 | 1.2 | 4,369 | 2.88 / 5.26 |
| adversarial | 12 | 23.1 (3/13) | 12/12 100% [100–100] | 12/12 100% [100–100] | 0 | 0 | 1.1 | 2,582 | 1.13 / 8.79 |
| old_policy | 5 | 20.0 (1/5) | 3/5 60% [20–100] | 5/5 100% [100–100] | 0 | 0 | 1.0 | 3,048 | 1.90 / 2.40 |
| **all** | 107 | 4.5 (5/111) | 86/107 80% [73–88] | 106/107 99% [97–100] | 0 | 0 | 1.0 | 3,700 | 2.46 / 4.47 |

Tool confusion (expected against called):

| expected ↓ / called → | list | status | tracking | search | propose | escalate | (none) |
|---|---|---|---|---|---|---|---|
| list | **34** | · | · | 2 | · | · | 1 |
| status | · | **22** | · | · | · | 1 | 4 |
| tracking | · | 2 | **23** | · | · | · | 1 |
| search | 1 | · | · | **38** | · | · | 7 |
| propose | · | · | · | 1 | **9** | · | 2 |
| escalate | · | · | · | 1 | · | **11** | 11 |
| (none) | 8 | 12 | 6 | 6 | · | · | · |
