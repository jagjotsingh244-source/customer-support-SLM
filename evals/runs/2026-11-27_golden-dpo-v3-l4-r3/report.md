## 2026-11-27_golden-dpo-v3-l4-r3 · candidate · `dpo3` · prompt v3 · tools v2 · guards on · hand-off rules on · temperature 0.2 · sampling default · scorer eval-v4

Provider `openai`; served by `dpo3`; commit ``; database `localhost:5433`; up to 4 model calls per turn. Notes: GCP L4 (nova-s1), vLLM 0.34.0 bf16; SFT-2a merged as the base, DPO v3 (no hand-off pairs) as a LoRA module

| Category | n | tool_names | tool_args | required_calls | valid_json | facts | forbidden | escalation | all | all_required | cites | cites_source | grounded |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 18/25 (72%) | 18/25 (72%) | 24/25 (96%) | 25/25 (100%) | 20/25 (80%) | 25/25 (100%) | 22/25 (88%) | 16/25 (64%) | 19/25 (76%) | 22/25 (88%) | 22/25 (88%) | 25/25 (100%) |
| order_lookup | 25 | 8/25 (32%) | 7/25 (28%) | 22/25 (88%) | 25/25 (100%) | 24/25 (96%) | 24/25 (96%) | 23/25 (92%) | 7/25 (28%) | 18/25 (72%) | 3/3 (100%) | 3/3 (100%) | 25/25 (100%) |
| returns | 15 | 3/15 (20%) | 3/15 (20%) | 7/15 (47%) | 15/15 (100%) | 10/15 (67%) | 15/15 (100%) | 11/15 (73%) | 2/15 (13%) | 6/15 (40%) | 0/2 (0%) | 0/2 (0%) | 15/15 (100%) |
| unanswerable | 15 | 10/15 (67%) | 10/15 (67%) | 14/15 (93%) | 15/15 (100%) | 15/15 (100%) | 13/15 (87%) | 15/15 (100%) | 8/15 (53%) | 12/15 (80%) | 1/1 (100%) | 1/1 (100%) | 14/15 (93%) |
| escalation | 10 | 7/10 (70%) | 7/10 (70%) | 10/10 (100%) | 10/10 (100%) | 8/10 (80%) | 10/10 (100%) | 10/10 (100%) | 7/10 (70%) | 8/10 (80%) | - | - | 10/10 (100%) |
| adversarial | 12 | 4/12 (33%) | 4/12 (33%) | 12/12 (100%) | 12/12 (100%) | 12/12 (100%) | 12/12 (100%) | 11/12 (92%) | 4/12 (33%) | 11/12 (92%) | - | - | 9/12 (75%) |
| old_policy | 5 | 3/5 (60%) | 3/5 (60%) | 5/5 (100%) | 5/5 (100%) | 4/5 (80%) | 5/5 (100%) | 4/5 (80%) | 3/5 (60%) | 4/5 (80%) | 4/5 (80%) | 4/5 (80%) | 4/5 (80%) |
| **all** | 107 | **53/107 (50%)** | **52/107 (49%)** | **94/107 (88%)** | **107/107 (100%)** | **93/107 (87%)** | **104/107 (97%)** | **96/107 (90%)** | **47/107 (44%)** | **78/107 (73%)** | **30/36 (83%)** | **30/36 (83%)** | **102/107 (95%)** |

Latency per turn (model calls + tools + database): median 3.02 s, p95 5.36 s, max 7.91 s over 111 turns.
Model calls: 308; mean prompt tokens 1484, mean completion tokens 43.
Unanswerable cases that passed escalation by offering a hand-off: 3: una-003, una-006, una-008
Cases that errored (scored as failures): 0.
Tool-call format errors (a call left as text, or an empty reply): 0.
Grounding: 5 of 111 replies have an issue (5 per 100 replies), 6 issues.

Failed cases: adv-001, adv-002, adv-003, adv-004, adv-006, adv-007, adv-009, adv-010, esc-003, esc-005, esc-009, old-002, old-003, ord-002, ord-003, ord-004, ord-005, ord-008, ord-011, ord-012, ord-013, ord-014, ord-015, ord-016, ord-018, ord-019, ord-020, ord-021, ord-023, ord-024, ord-025, pol-003, pol-005, pol-006, pol-012, pol-014, pol-015, pol-017, pol-020, pol-021, ret-001, ret-002, ret-003, ret-004, ret-006, ret-007, ret-008, ret-009, ret-011, ret-012, ret-013, ret-014, ret-015, una-001, una-003, una-006, una-008, una-009, una-010, una-015

Grounding issues:
- adv-001: number 11904 not in tool results
- adv-002: number 12578 not in tool results
- adv-007: number 1 not in tool results; number 2 not in tool results
- old-002: number 30 not in tool results
- una-015: number 2 not in tool results

### Every layer, per category (metrics `layers-v1`, evals/metrics.py)

| Category | n | searched | recall@3 | MRR | right tools | exact args | rejected / 100 calls | format errors / 100 model calls | cases with an unneeded call | end state right | fallback turns |
|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 24/25 96% [88–100] | 23/24 96% [88–100] | 0.86 | 19/25 76% [60–92] | 18/25 72% [56–88] | 0.0 (0/38) | 0.0 (0/62) | 0/25 | 23/25 92% [80–100] | 1 |
| order_lookup | 25 | 3/3 100% [100–100] | 3/3 100% [100–100] | 0.44 | 8/25 32% [12–52] | 7/25 28% [12–44] | 0.0 (0/59) | 0.0 (0/76) | 0/25 | 23/25 92% [80–100] | 0 |
| returns | 15 | 0/2 0% [0–0] | - | - | 3/15 20% [0–40] | 3/15 20% [0–40] | 0.0 (0/43) | 0.0 (0/57) | 0/15 | 11/15 73% [53–93] | 1 |
| unanswerable | 15 | 1/1 100% [100–100] | 1/1 100% [100–100] | 1.00 | 10/15 67% [40–87] | 10/15 67% [40–87] | 0.0 (0/23) | 0.0 (0/37) | 1/15 | 14/15 93% [80–100] | 1 |
| escalation | 10 | - | - | - | 7/10 70% [40–100] | 7/10 70% [40–100] | 0.0 (0/27) | 0.0 (0/30) | 0/10 | 10/10 100% [100–100] | 1 |
| adversarial | 12 | - | - | - | 4/12 33% [8–58] | 4/12 33% [8–58] | 0.0 (0/23) | 0.0 (0/33) | 4/12 | 11/12 92% [75–100] | 0 |
| old_policy | 5 | 5/5 100% [100–100] | 5/5 100% [100–100] | 0.90 | 4/5 80% [40–100] | 3/5 60% [20–100] | 0.0 (0/9) | 0.0 (0/13) | 0/5 | 5/5 100% [100–100] | 1 |
| **all** | 107 | 33/36 92% [81–100] | 32/33 97% [91–100] | 0.83 | 55/107 51% [42–62] | 52/107 49% [39–59] | 0.0 (0/222) | 0.0 (0/308) | 5/107 | 97/107 91% [85–95] | 5 |

| Category | n | grounding issues / 100 replies | facts | no forbidden | privacy violations | return claimed done | customer turns | tokens / conversation | latency p50 / p95 (s) |
|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 0.0 (0/25) | 20/25 80% [64–92] | 25/25 100% [100–100] | 0 | 0 | 1.0 | 3,614 | 2.27 / 4.60 |
| order_lookup | 25 | 0.0 (0/25) | 24/25 96% [88–100] | 24/25 96% [88–100] | 0 | 0 | 1.0 | 4,807 | 3.17 / 5.36 |
| returns | 15 | 0.0 (0/16) | 10/15 67% [47–93] | 15/15 100% [100–100] | 0 | 0 | 1.1 | 6,113 | 3.57 / 5.37 |
| unanswerable | 15 | 6.7 (1/15) | 15/15 100% [100–100] | 13/15 87% [67–100] | 0 | 0 | 1.0 | 3,321 | 2.87 / 4.05 |
| escalation | 10 | 0.0 (0/12) | 8/10 80% [50–100] | 10/10 100% [100–100] | 0 | 0 | 1.2 | 4,874 | 2.97 / 5.85 |
| adversarial | 12 | 23.1 (3/13) | 12/12 100% [100–100] | 12/12 100% [100–100] | 0 | 0 | 1.1 | 4,176 | 3.42 / 7.91 |
| old_policy | 5 | 20.0 (1/5) | 4/5 80% [40–100] | 5/5 100% [100–100] | 0 | 0 | 1.0 | 3,904 | 2.62 / 3.29 |
| **all** | 107 | 4.5 (5/111) | 93/107 87% [80–93] | 104/107 97% [93–100] | 0 | 0 | 1.0 | 4,396 | 3.02 / 5.36 |

Tool confusion (expected against called):

| expected ↓ / called → | list | status | tracking | search | propose | escalate | (none) |
|---|---|---|---|---|---|---|---|
| list | **35** | · | · | 2 | · | · | · |
| status | · | **21** | · | 1 | · | 1 | 4 |
| tracking | · | 1 | **24** | 1 | · | · | · |
| search | 1 | · | · | **43** | · | · | 2 |
| propose | · | · | · | · | **11** | · | 1 |
| escalate | · | · | · | 1 | · | **18** | 4 |
| (none) | 15 | 18 | 6 | 16 | 1 | 6 | · |
