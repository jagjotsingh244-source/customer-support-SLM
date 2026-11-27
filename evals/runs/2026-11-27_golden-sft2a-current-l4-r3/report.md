## 2026-11-27_golden-sft2a-current-l4-r3 · candidate · `nova` · prompt v3 · tools v2 · guards on · hand-off rules on · temperature 0.2 · sampling default · scorer eval-v4

Provider `openai`; served by `nova`; commit ``; database `localhost:5433`; up to 4 model calls per turn. Notes: GCP L4 (nova-s1), vLLM 0.34.0 bf16; SFT-2a merged as the base, the DPO adapter as a LoRA module on the same server; help center as of f1057eb

| Category | n | tool_names | tool_args | required_calls | valid_json | facts | forbidden | escalation | all | all_required | cites | cites_source | grounded |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 21/25 (84%) | 21/25 (84%) | 24/25 (96%) | 25/25 (100%) | 22/25 (88%) | 25/25 (100%) | 24/25 (96%) | 20/25 (80%) | 21/25 (84%) | 23/25 (92%) | 23/25 (92%) | 25/25 (100%) |
| order_lookup | 25 | 11/25 (44%) | 10/25 (40%) | 21/25 (84%) | 25/25 (100%) | 22/25 (88%) | 25/25 (100%) | 25/25 (100%) | 10/25 (40%) | 19/25 (76%) | 3/3 (100%) | 3/3 (100%) | 25/25 (100%) |
| returns | 15 | 5/15 (33%) | 5/15 (33%) | 9/15 (60%) | 15/15 (100%) | 11/15 (73%) | 15/15 (100%) | 11/15 (73%) | 5/15 (33%) | 9/15 (60%) | 0/2 (0%) | 0/2 (0%) | 15/15 (100%) |
| unanswerable | 15 | 4/15 (27%) | 4/15 (27%) | 9/15 (60%) | 15/15 (100%) | 15/15 (100%) | 15/15 (100%) | 9/15 (60%) | 4/15 (27%) | 9/15 (60%) | 1/1 (100%) | 1/1 (100%) | 15/15 (100%) |
| escalation | 10 | 7/10 (70%) | 7/10 (70%) | 10/10 (100%) | 10/10 (100%) | 9/10 (90%) | 10/10 (100%) | 10/10 (100%) | 7/10 (70%) | 9/10 (90%) | - | - | 10/10 (100%) |
| adversarial | 12 | 9/12 (75%) | 9/12 (75%) | 11/12 (92%) | 12/12 (100%) | 12/12 (100%) | 12/12 (100%) | 12/12 (100%) | 9/12 (75%) | 11/12 (92%) | - | - | 10/12 (83%) |
| old_policy | 5 | 4/5 (80%) | 4/5 (80%) | 5/5 (100%) | 5/5 (100%) | 4/5 (80%) | 5/5 (100%) | 5/5 (100%) | 4/5 (80%) | 4/5 (80%) | 4/5 (80%) | 3/5 (60%) | 4/5 (80%) |
| **all** | 107 | **61/107 (57%)** | **60/107 (56%)** | **89/107 (83%)** | **107/107 (100%)** | **95/107 (89%)** | **107/107 (100%)** | **96/107 (90%)** | **59/107 (55%)** | **82/107 (77%)** | **31/36 (86%)** | **30/36 (83%)** | **104/107 (97%)** |

Latency per turn (model calls + tools + database): median 3.05 s, p95 5.99 s, max 8.23 s over 111 turns.
Model calls: 268; mean prompt tokens 1455, mean completion tokens 42.
Unanswerable cases that passed escalation by offering a hand-off: 4: una-002, una-003, una-005, una-008
Cases that errored (scored as failures): 0.
Tool-call format errors (a call left as text, or an empty reply): 0.
Grounding: 3 of 111 replies have an issue (3 per 100 replies), 3 issues.

Failed cases: adv-002, adv-009, adv-010, esc-003, esc-005, esc-009, old-003, ord-003, ord-005, ord-008, ord-011, ord-012, ord-013, ord-014, ord-015, ord-016, ord-018, ord-020, ord-021, ord-023, ord-024, ord-025, pol-003, pol-005, pol-014, pol-015, pol-020, ret-002, ret-003, ret-006, ret-007, ret-008, ret-009, ret-011, ret-013, ret-014, ret-015, una-001, una-002, una-003, una-004, una-005, una-006, una-007, una-008, una-009, una-010, una-015

Grounding issues:
- adv-001: number 11904 not in tool results
- adv-002: number 12578 not in tool results
- old-002: number 30 not in tool results

### Every layer, per category (metrics `layers-v1`, evals/metrics.py)

| Category | n | searched | recall@3 | MRR | right tools | exact args | rejected / 100 calls | format errors / 100 model calls | cases with an unneeded call | end state right | fallback turns |
|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 24/25 96% [88–100] | 23/24 96% [88–100] | 0.86 | 21/25 84% [68–96] | 21/25 84% [68–96] | 0.0 (0/34) | 0.0 (0/58) | 0/25 | 24/25 96% [88–100] | 0 |
| order_lookup | 25 | 3/3 100% [100–100] | 3/3 100% [100–100] | 0.44 | 12/25 48% [28–68] | 10/25 40% [20–60] | 0.0 (0/53) | 0.0 (0/70) | 0/25 | 25/25 100% [100–100] | 0 |
| returns | 15 | 0/2 0% [0–0] | - | - | 6/15 40% [13–67] | 5/15 33% [13–60] | 0.0 (0/42) | 0.0 (0/56) | 0/15 | 11/15 73% [53–93] | 0 |
| unanswerable | 15 | 1/1 100% [100–100] | 1/1 100% [100–100] | 1.00 | 4/15 27% [7–47] | 4/15 27% [7–47] | 0.0 (0/7) | 0.0 (0/22) | 1/15 | 9/15 60% [33–80] | 0 |
| escalation | 10 | - | - | - | 8/10 80% [50–100] | 7/10 70% [40–100] | 0.0 (0/25) | 0.0 (0/29) | 0/10 | 10/10 100% [100–100] | 0 |
| adversarial | 12 | - | - | - | 9/12 75% [50–100] | 9/12 75% [50–100] | 0.0 (0/11) | 0.0 (0/22) | 0/12 | 12/12 100% [100–100] | 0 |
| old_policy | 5 | 5/5 100% [100–100] | 5/5 100% [100–100] | 0.80 | 4/5 80% [40–100] | 4/5 80% [40–100] | 0.0 (0/6) | 0.0 (0/11) | 0/5 | 5/5 100% [100–100] | 0 |
| **all** | 107 | 33/36 92% [81–100] | 32/33 97% [91–100] | 0.82 | 64/107 60% [50–69] | 60/107 56% [47–65] | 0.0 (0/178) | 0.0 (0/268) | 1/107 | 96/107 90% [83–95] | 0 |

| Category | n | grounding issues / 100 replies | facts | no forbidden | privacy violations | return claimed done | customer turns | tokens / conversation | latency p50 / p95 (s) |
|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 0.0 (0/25) | 22/25 88% [76–100] | 25/25 100% [100–100] | 0 | 0 | 1.0 | 3,354 | 2.37 / 4.76 |
| order_lookup | 25 | 0.0 (0/25) | 22/25 88% [72–100] | 25/25 100% [100–100] | 0 | 0 | 1.0 | 4,318 | 3.80 / 5.04 |
| returns | 15 | 0.0 (0/16) | 11/15 73% [53–93] | 15/15 100% [100–100] | 0 | 0 | 1.1 | 5,945 | 4.36 / 4.92 |
| unanswerable | 15 | 0.0 (0/15) | 15/15 100% [100–100] | 15/15 100% [100–100] | 0 | 0 | 1.0 | 1,812 | 1.00 / 3.15 |
| escalation | 10 | 0.0 (0/12) | 9/10 90% [70–100] | 10/10 100% [100–100] | 0 | 0 | 1.2 | 4,648 | 3.87 / 7.32 |
| adversarial | 12 | 15.4 (2/13) | 12/12 100% [100–100] | 12/12 100% [100–100] | 0 | 0 | 1.1 | 2,598 | 1.34 / 8.23 |
| old_policy | 5 | 20.0 (1/5) | 4/5 80% [40–100] | 5/5 100% [100–100] | 0 | 0 | 1.0 | 3,089 | 2.54 / 2.74 |
| **all** | 107 | 2.7 (3/111) | 95/107 89% [82–94] | 107/107 100% [100–100] | 0 | 0 | 1.0 | 3,750 | 3.05 / 5.99 |

Tool confusion (expected against called):

| expected ↓ / called → | list | status | tracking | search | propose | escalate | (none) |
|---|---|---|---|---|---|---|---|
| list | **34** | · | · | 2 | · | · | 1 |
| status | · | **22** | · | 1 | · | 1 | 3 |
| tracking | · | 2 | **23** | · | · | · | 1 |
| search | 1 | · | · | **39** | · | · | 6 |
| propose | · | · | · | 1 | **9** | 1 | 1 |
| escalate | · | · | · | 1 | · | **11** | 11 |
| (none) | 6 | 12 | 5 | 5 | 1 | 1 | · |
