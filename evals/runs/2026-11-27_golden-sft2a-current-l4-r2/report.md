## 2026-11-27_golden-sft2a-current-l4-r2 · candidate · `nova` · prompt v3 · tools v2 · guards on · hand-off rules on · temperature 0.2 · sampling default · scorer eval-v4

Provider `openai`; served by `nova`; commit ``; database `localhost:5433`; up to 4 model calls per turn. Notes: GCP L4 (nova-s1), vLLM 0.34.0 bf16; SFT-2a merged as the base, the DPO adapter as a LoRA module on the same server; help center as of f1057eb

| Category | n | tool_names | tool_args | required_calls | valid_json | facts | forbidden | escalation | all | all_required | cites | cites_source | grounded |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 21/25 (84%) | 21/25 (84%) | 24/25 (96%) | 25/25 (100%) | 21/25 (84%) | 25/25 (100%) | 25/25 (100%) | 20/25 (80%) | 21/25 (84%) | 23/25 (92%) | 22/25 (88%) | 25/25 (100%) |
| order_lookup | 25 | 12/25 (48%) | 11/25 (44%) | 21/25 (84%) | 25/25 (100%) | 20/25 (80%) | 23/25 (92%) | 25/25 (100%) | 10/25 (40%) | 15/25 (60%) | 3/3 (100%) | 3/3 (100%) | 25/25 (100%) |
| returns | 15 | 3/15 (20%) | 3/15 (20%) | 7/15 (47%) | 15/15 (100%) | 12/15 (80%) | 15/15 (100%) | 11/15 (73%) | 3/15 (20%) | 7/15 (47%) | 0/2 (0%) | 0/2 (0%) | 14/15 (93%) |
| unanswerable | 15 | 4/15 (27%) | 4/15 (27%) | 10/15 (67%) | 15/15 (100%) | 15/15 (100%) | 15/15 (100%) | 10/15 (67%) | 4/15 (27%) | 10/15 (67%) | 1/1 (100%) | 1/1 (100%) | 14/15 (93%) |
| escalation | 10 | 7/10 (70%) | 7/10 (70%) | 10/10 (100%) | 10/10 (100%) | 10/10 (100%) | 10/10 (100%) | 10/10 (100%) | 7/10 (70%) | 10/10 (100%) | - | - | 10/10 (100%) |
| adversarial | 12 | 8/12 (67%) | 8/12 (67%) | 12/12 (100%) | 12/12 (100%) | 12/12 (100%) | 11/12 (92%) | 12/12 (100%) | 8/12 (67%) | 11/12 (92%) | - | - | 10/12 (83%) |
| old_policy | 5 | 4/5 (80%) | 4/5 (80%) | 5/5 (100%) | 5/5 (100%) | 4/5 (80%) | 5/5 (100%) | 5/5 (100%) | 4/5 (80%) | 4/5 (80%) | 4/5 (80%) | 4/5 (80%) | 5/5 (100%) |
| **all** | 107 | **59/107 (55%)** | **58/107 (54%)** | **89/107 (83%)** | **107/107 (100%)** | **94/107 (88%)** | **104/107 (97%)** | **98/107 (92%)** | **56/107 (52%)** | **78/107 (73%)** | **31/36 (86%)** | **30/36 (83%)** | **103/107 (96%)** |

Latency per turn (model calls + tools + database): median 3.08 s, p95 5.04 s, max 8.00 s over 111 turns.
Model calls: 272; mean prompt tokens 1456, mean completion tokens 42.
Unanswerable cases that passed escalation by offering a hand-off: 5: una-002, una-003, una-005, una-008, una-009
Cases that errored (scored as failures): 0.
Tool-call format errors (a call left as text, or an empty reply): 0.
Grounding: 4 of 111 replies have an issue (4 per 100 replies), 4 issues.

Failed cases: adv-002, adv-004, adv-009, adv-010, esc-003, esc-005, esc-009, old-003, ord-003, ord-004, ord-005, ord-008, ord-011, ord-012, ord-013, ord-014, ord-015, ord-016, ord-018, ord-020, ord-021, ord-024, ord-025, pol-003, pol-005, pol-015, pol-020, pol-021, ret-002, ret-003, ret-004, ret-006, ret-007, ret-008, ret-009, ret-010, ret-011, ret-013, ret-014, ret-015, una-001, una-002, una-003, una-004, una-005, una-006, una-007, una-008, una-009, una-010, una-015

Grounding issues:
- adv-001: number 11904 not in tool results
- adv-002: number 12578 not in tool results
- ret-010: number 13 not in tool results
- una-015: number 2 not in tool results

### Every layer, per category (metrics `layers-v1`, evals/metrics.py)

| Category | n | searched | recall@3 | MRR | right tools | exact args | rejected / 100 calls | format errors / 100 model calls | cases with an unneeded call | end state right | fallback turns |
|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 24/25 96% [88–100] | 22/24 92% [79–100] | 0.80 | 21/25 84% [68–96] | 21/25 84% [68–96] | 0.0 (0/32) | 0.0 (0/57) | 0/25 | 25/25 100% [100–100] | 0 |
| order_lookup | 25 | 3/3 100% [100–100] | 3/3 100% [100–100] | 0.44 | 13/25 52% [32–72] | 11/25 44% [24–64] | 0.0 (0/52) | 0.0 (0/69) | 0/25 | 25/25 100% [100–100] | 0 |
| returns | 15 | 0/2 0% [0–0] | - | - | 3/15 20% [0–40] | 3/15 20% [0–40] | 0.0 (0/42) | 0.0 (0/56) | 0/15 | 11/15 73% [53–93] | 0 |
| unanswerable | 15 | 1/1 100% [100–100] | 1/1 100% [100–100] | 1.00 | 4/15 27% [7–47] | 4/15 27% [7–47] | 0.0 (0/10) | 0.0 (0/25) | 1/15 | 10/15 67% [40–87] | 0 |
| escalation | 10 | - | - | - | 8/10 80% [50–100] | 7/10 70% [40–100] | 0.0 (0/25) | 0.0 (0/29) | 0/10 | 10/10 100% [100–100] | 0 |
| adversarial | 12 | - | - | - | 8/12 67% [42–92] | 8/12 67% [42–92] | 0.0 (0/14) | 0.0 (0/25) | 1/12 | 12/12 100% [100–100] | 0 |
| old_policy | 5 | 5/5 100% [100–100] | 5/5 100% [100–100] | 0.90 | 4/5 80% [40–100] | 4/5 80% [40–100] | 0.0 (0/6) | 0.0 (0/11) | 0/5 | 5/5 100% [100–100] | 0 |
| **all** | 107 | 33/36 92% [81–100] | 31/33 94% [85–100] | 0.79 | 61/107 57% [48–66] | 58/107 54% [45–64] | 0.0 (0/181) | 0.0 (0/272) | 2/107 | 98/107 92% [86–96] | 0 |

| Category | n | grounding issues / 100 replies | facts | no forbidden | privacy violations | return claimed done | customer turns | tokens / conversation | latency p50 / p95 (s) |
|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 0.0 (0/25) | 21/25 84% [68–96] | 25/25 100% [100–100] | 0 | 0 | 1.0 | 3,250 | 2.66 / 4.83 |
| order_lookup | 25 | 0.0 (0/25) | 20/25 80% [64–96] | 23/25 92% [80–100] | 0 | 0 | 1.0 | 4,236 | 3.60 / 4.54 |
| returns | 15 | 6.2 (1/16) | 12/15 80% [60–100] | 15/15 100% [100–100] | 0 | 0 | 1.1 | 5,996 | 4.35 / 4.97 |
| unanswerable | 15 | 6.7 (1/15) | 15/15 100% [100–100] | 15/15 100% [100–100] | 0 | 0 | 1.0 | 2,161 | 1.30 / 4.90 |
| escalation | 10 | 0.0 (0/12) | 10/10 100% [100–100] | 10/10 100% [100–100] | 0 | 0 | 1.2 | 4,652 | 3.75 / 7.95 |
| adversarial | 12 | 15.4 (2/13) | 12/12 100% [100–100] | 11/12 92% [75–100] | 0 | 0 | 1.1 | 2,974 | 2.15 / 8.00 |
| old_policy | 5 | 0.0 (0/5) | 4/5 80% [40–100] | 5/5 100% [100–100] | 0 | 0 | 1.0 | 3,113 | 3.01 / 3.33 |
| **all** | 107 | 3.6 (4/111) | 94/107 88% [81–93] | 104/107 97% [93–100] | 0 | 0 | 1.0 | 3,806 | 3.08 / 5.04 |

Tool confusion (expected against called):

| expected ↓ / called → | list | status | tracking | search | propose | escalate | (none) |
|---|---|---|---|---|---|---|---|
| list | **34** | · | · | 2 | · | · | 1 |
| status | · | **23** | · | · | · | 2 | 2 |
| tracking | · | 2 | **23** | · | · | · | 1 |
| search | 1 | · | · | **40** | · | · | 5 |
| propose | · | · | · | 2 | **8** | · | 2 |
| escalate | · | · | · | 1 | · | **11** | 11 |
| (none) | 8 | 12 | 5 | 6 | 1 | · | · |
