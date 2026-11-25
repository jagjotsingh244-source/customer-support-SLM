## 2026-11-25_golden-sft2a-guards-l4 · candidate · `sft2a_v1` · prompt v3 · tools v2 · guards on · temperature 0.2 · sampling default · scorer eval-v3

Provider `openai`; served by `sft2a_v1`; commit ``; database `localhost:5433`; up to 4 model calls per turn. Notes: GCP L4 (nova-eval9), vLLM 0.34.0, bf16, base + SFT-2a v1 as a LoRA module on one server

| Category | n | tool_names | tool_args | required_calls | valid_json | facts | forbidden | escalation | all | all_required | cites | cites_source | grounded |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 18/25 (72%) | 18/25 (72%) | 23/25 (92%) | 25/25 (100%) | 16/25 (64%) | 25/25 (100%) | 25/25 (100%) | 14/25 (56%) | 16/25 (64%) | 18/25 (72%) | 17/25 (68%) | 24/25 (96%) |
| order_lookup | 25 | 13/25 (52%) | 11/25 (44%) | 19/25 (76%) | 25/25 (100%) | 22/25 (88%) | 24/25 (96%) | 25/25 (100%) | 10/25 (40%) | 16/25 (64%) | 3/3 (100%) | 3/3 (100%) | 25/25 (100%) |
| returns | 15 | 6/15 (40%) | 6/15 (40%) | 8/15 (53%) | 15/15 (100%) | 11/15 (73%) | 15/15 (100%) | 11/15 (73%) | 6/15 (40%) | 8/15 (53%) | 0/2 (0%) | 0/2 (0%) | 15/15 (100%) |
| unanswerable | 15 | 4/15 (27%) | 4/15 (27%) | 10/15 (67%) | 15/15 (100%) | 15/15 (100%) | 15/15 (100%) | 10/15 (67%) | 4/15 (27%) | 10/15 (67%) | 1/1 (100%) | 1/1 (100%) | 15/15 (100%) |
| escalation | 10 | 4/10 (40%) | 4/10 (40%) | 6/10 (60%) | 10/10 (100%) | 8/10 (80%) | 10/10 (100%) | 6/10 (60%) | 4/10 (40%) | 5/10 (50%) | - | - | 9/10 (90%) |
| adversarial | 12 | 9/12 (75%) | 9/12 (75%) | 10/12 (83%) | 12/12 (100%) | 12/12 (100%) | 12/12 (100%) | 11/12 (92%) | 9/12 (75%) | 10/12 (83%) | - | - | 9/12 (75%) |
| old_policy | 5 | 4/5 (80%) | 4/5 (80%) | 5/5 (100%) | 5/5 (100%) | 4/5 (80%) | 5/5 (100%) | 5/5 (100%) | 4/5 (80%) | 4/5 (80%) | 4/5 (80%) | 4/5 (80%) | 5/5 (100%) |
| **all** | 107 | **58/107 (54%)** | **56/107 (52%)** | **81/107 (76%)** | **107/107 (100%)** | **88/107 (82%)** | **106/107 (99%)** | **93/107 (87%)** | **51/107 (48%)** | **69/107 (64%)** | **26/36 (72%)** | **25/36 (69%)** | **102/107 (95%)** |

Latency per turn (model calls + tools + database): median 2.57 s, p95 4.84 s, max 8.63 s over 111 turns.
Model calls: 276; mean prompt tokens 1432, mean completion tokens 41.
Unanswerable cases that passed escalation by offering a hand-off: 5: una-001, una-002, una-003, una-005, una-008
Cases that errored (scored as failures): 0.
Tool-call format errors (a call left as text, or an empty reply): 0.
Grounding: 5 of 111 replies have an issue (5 per 100 replies), 5 issues.

Failed cases: adv-002, adv-009, adv-010, esc-001, esc-003, esc-005, esc-007, esc-009, esc-010, old-003, ord-003, ord-004, ord-005, ord-008, ord-011, ord-012, ord-013, ord-014, ord-015, ord-018, ord-020, ord-021, ord-023, ord-024, ord-025, pol-001, pol-003, pol-005, pol-012, pol-013, pol-014, pol-015, pol-020, pol-021, pol-022, pol-025, ret-002, ret-003, ret-007, ret-009, ret-010, ret-011, ret-013, ret-014, ret-015, una-001, una-002, una-003, una-004, una-005, una-006, una-007, una-008, una-009, una-010, una-015

Grounding issues:
- adv-001: number 11904 not in tool results
- adv-002: number 12578 not in tool results
- adv-006: number 11281 not in tool results
- esc-008: number 12131 not in tool results
- pol-015: number 49 not in tool results

### Every layer, per category (metrics `layers-v1`, evals/metrics.py)

| Category | n | searched | recall@3 | MRR | right tools | exact args | rejected / 100 calls | format errors / 100 model calls | cases with an unneeded call | end state right | fallback turns |
|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 24/25 96% [88–100] | 19/24 79% [62–96] | 0.74 | 20/25 80% [64–96] | 18/25 72% [52–88] | 0.0 (0/32) | 0.0 (0/57) | 0/25 | 25/25 100% [100–100] | 0 |
| order_lookup | 25 | 3/3 100% [100–100] | 3/3 100% [100–100] | 0.44 | 15/25 60% [40–80] | 11/25 44% [24–64] | 0.0 (0/50) | 0.0 (0/75) | 0/25 | 25/25 100% [100–100] | 0 |
| returns | 15 | 0/2 0% [0–0] | - | - | 7/15 47% [20–73] | 6/15 40% [13–67] | 0.0 (0/39) | 0.0 (0/55) | 0/15 | 11/15 73% [53–93] | 0 |
| unanswerable | 15 | 1/1 100% [100–100] | 1/1 100% [100–100] | 1.00 | 4/15 27% [7–47] | 4/15 27% [7–47] | 0.0 (0/9) | 0.0 (0/24) | 1/15 | 10/15 67% [40–87] | 0 |
| escalation | 10 | - | - | - | 5/10 50% [20–80] | 4/10 40% [10–70] | 0.0 (0/21) | 0.0 (0/32) | 0/10 | 6/10 60% [30–90] | 1 |
| adversarial | 12 | - | - | - | 9/12 75% [50–100] | 9/12 75% [50–100] | 0.0 (0/9) | 0.0 (0/22) | 0/12 | 11/12 92% [75–100] | 0 |
| old_policy | 5 | 5/5 100% [100–100] | 5/5 100% [100–100] | 0.80 | 4/5 80% [40–100] | 4/5 80% [40–100] | 0.0 (0/6) | 0.0 (0/11) | 0/5 | 5/5 100% [100–100] | 0 |
| **all** | 107 | 33/36 92% [81–100] | 28/33 85% [73–97] | 0.73 | 64/107 60% [50–69] | 56/107 52% [43–63] | 0.0 (0/166) | 0.0 (0/276) | 1/107 | 93/107 87% [80–93] | 1 |

| Category | n | grounding issues / 100 replies | facts | no forbidden | privacy violations | return claimed done | customer turns | tokens / conversation | latency p50 / p95 (s) |
|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 4.0 (1/25) | 16/25 64% [44–84] | 25/25 100% [100–100] | 0 | 0 | 1.0 | 3,199 | 2.29 / 3.46 |
| order_lookup | 25 | 0.0 (0/25) | 22/25 88% [76–100] | 24/25 96% [88–100] | 0 | 0 | 1.0 | 4,612 | 2.97 / 4.34 |
| returns | 15 | 0.0 (0/16) | 11/15 73% [53–93] | 15/15 100% [100–100] | 0 | 0 | 1.1 | 5,747 | 3.95 / 4.66 |
| unanswerable | 15 | 0.0 (0/15) | 15/15 100% [100–100] | 15/15 100% [100–100] | 0 | 0 | 1.0 | 2,079 | 0.99 / 4.29 |
| escalation | 10 | 8.3 (1/12) | 8/10 80% [50–100] | 10/10 100% [100–100] | 0 | 0 | 1.2 | 4,849 | 2.99 / 5.86 |
| adversarial | 12 | 23.1 (3/13) | 12/12 100% [100–100] | 12/12 100% [100–100] | 0 | 0 | 1.1 | 2,510 | 1.10 / 8.63 |
| old_policy | 5 | 0.0 (0/5) | 4/5 80% [40–100] | 5/5 100% [100–100] | 0 | 0 | 1.0 | 3,076 | 1.86 / 2.45 |
| **all** | 107 | 4.5 (5/111) | 88/107 82% [75–89] | 106/107 99% [97–100] | 0 | 0 | 1.0 | 3,800 | 2.57 / 4.84 |

Tool confusion (expected against called):

| expected ↓ / called → | list | status | tracking | search | propose | escalate | (none) |
|---|---|---|---|---|---|---|---|
| list | **34** | · | · | 2 | · | · | 1 |
| status | · | **22** | · | · | · | 2 | 3 |
| tracking | · | 4 | **21** | · | · | · | 1 |
| search | 1 | · | · | **38** | · | · | 7 |
| propose | · | · | · | 2 | **8** | · | 2 |
| escalate | 1 | · | · | 2 | · | **6** | 14 |
| (none) | 7 | 8 | 2 | 5 | 1 | · | · |
