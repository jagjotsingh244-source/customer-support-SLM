## 2026-11-27_golden-dpo-v2-l4 · candidate · `dpo` · prompt v3 · tools v2 · guards on · hand-off rules on · temperature 0.2 · sampling default · scorer eval-v4

Provider `openai`; served by `dpo`; commit ``; database `localhost:5433`; up to 4 model calls per turn. Notes: GCP L4 (nova-s1), vLLM 0.34.0 bf16; SFT-2a merged as the base, the DPO adapter as a LoRA module on the same server; help center as of f1057eb

| Category | n | tool_names | tool_args | required_calls | valid_json | facts | forbidden | escalation | all | all_required | cites | cites_source | grounded |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 15/25 (60%) | 15/25 (60%) | 24/25 (96%) | 25/25 (100%) | 18/25 (72%) | 25/25 (100%) | 18/25 (72%) | 14/25 (56%) | 16/25 (64%) | 19/25 (76%) | 19/25 (76%) | 25/25 (100%) |
| order_lookup | 25 | 7/25 (28%) | 6/25 (24%) | 22/25 (88%) | 25/25 (100%) | 22/25 (88%) | 25/25 (100%) | 19/25 (76%) | 6/25 (24%) | 15/25 (60%) | 2/3 (67%) | 2/3 (67%) | 25/25 (100%) |
| returns | 15 | 2/15 (13%) | 2/15 (13%) | 8/15 (53%) | 15/15 (100%) | 7/15 (47%) | 15/15 (100%) | 8/15 (53%) | 2/15 (13%) | 4/15 (27%) | 1/2 (50%) | 0/2 (0%) | 15/15 (100%) |
| unanswerable | 15 | 13/15 (87%) | 13/15 (87%) | 14/15 (93%) | 15/15 (100%) | 15/15 (100%) | 13/15 (87%) | 14/15 (93%) | 11/15 (73%) | 11/15 (73%) | 1/1 (100%) | 1/1 (100%) | 14/15 (93%) |
| escalation | 10 | 6/10 (60%) | 6/10 (60%) | 10/10 (100%) | 10/10 (100%) | 8/10 (80%) | 10/10 (100%) | 10/10 (100%) | 5/10 (50%) | 8/10 (80%) | - | - | 10/10 (100%) |
| adversarial | 12 | 3/12 (25%) | 3/12 (25%) | 11/12 (92%) | 12/12 (100%) | 12/12 (100%) | 12/12 (100%) | 8/12 (67%) | 3/12 (25%) | 7/12 (58%) | - | - | 11/12 (92%) |
| old_policy | 5 | 2/5 (40%) | 2/5 (40%) | 5/5 (100%) | 5/5 (100%) | 2/5 (40%) | 5/5 (100%) | 2/5 (40%) | 2/5 (40%) | 2/5 (40%) | 2/5 (40%) | 2/5 (40%) | 5/5 (100%) |
| **all** | 107 | **48/107 (45%)** | **47/107 (44%)** | **94/107 (88%)** | **107/107 (100%)** | **84/107 (79%)** | **105/107 (98%)** | **79/107 (74%)** | **43/107 (40%)** | **63/107 (59%)** | **25/36 (69%)** | **24/36 (67%)** | **105/107 (98%)** |

Latency per turn (model calls + tools + database): median 3.44 s, p95 7.34 s, max 11.44 s over 111 turns.
Model calls: 335; mean prompt tokens 1513, mean completion tokens 45.
Unanswerable cases that passed escalation by offering a hand-off: 0.
Cases that errored (scored as failures): 0.
Tool-call format errors (a call left as text, or an empty reply): 0.
Grounding: 2 of 111 replies have an issue (2 per 100 replies), 2 issues.

Failed cases: adv-001, adv-002, adv-003, adv-004, adv-006, adv-007, adv-009, adv-010, adv-012, esc-002, esc-003, esc-004, esc-005, esc-009, old-002, old-003, old-004, ord-002, ord-003, ord-004, ord-005, ord-008, ord-009, ord-011, ord-012, ord-013, ord-014, ord-015, ord-016, ord-018, ord-019, ord-020, ord-021, ord-023, ord-024, ord-025, pol-003, pol-005, pol-006, pol-007, pol-009, pol-012, pol-014, pol-015, pol-017, pol-020, pol-021, ret-001, ret-002, ret-003, ret-004, ret-005, ret-006, ret-007, ret-008, ret-009, ret-010, ret-011, ret-014, ret-015, una-002, una-010, una-011, una-015

Grounding issues:
- adv-002: number 12578 not in tool results
- una-005: number 1080 not in tool results

### Every layer, per category (metrics `layers-v1`, evals/metrics.py)

| Category | n | searched | recall@3 | MRR | right tools | exact args | rejected / 100 calls | format errors / 100 model calls | cases with an unneeded call | end state right | fallback turns |
|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 24/25 96% [88–100] | 23/24 96% [88–100] | 0.86 | 15/25 60% [40–80] | 15/25 60% [40–80] | 0.0 (0/48) | 0.0 (0/70) | 0/25 | 18/25 72% [52–88] | 0 |
| order_lookup | 25 | 3/3 100% [100–100] | 2/3 67% [0–100] | 0.28 | 7/25 28% [12–44] | 6/25 24% [8–40] | 0.0 (0/63) | 0.0 (0/79) | 0/25 | 20/25 80% [64–96] | 1 |
| returns | 15 | 1/2 50% [0–100] | 1/1 100% [100–100] | 0.33 | 2/15 13% [0–33] | 2/15 13% [0–33] | 0.0 (0/50) | 0.0 (0/63) | 0/15 | 9/15 60% [33–80] | 2 |
| unanswerable | 15 | 1/1 100% [100–100] | 1/1 100% [100–100] | 1.00 | 13/15 87% [67–100] | 13/15 87% [67–100] | 0.0 (0/23) | 0.0 (0/38) | 1/15 | 14/15 93% [80–100] | 0 |
| escalation | 10 | - | - | - | 7/10 70% [40–100] | 6/10 60% [30–90] | 0.0 (0/27) | 0.0 (0/31) | 0/10 | 10/10 100% [100–100] | 0 |
| adversarial | 12 | - | - | - | 3/12 25% [0–50] | 3/12 25% [0–50] | 0.0 (0/29) | 0.0 (0/37) | 4/12 | 9/12 75% [50–100] | 1 |
| old_policy | 5 | 5/5 100% [100–100] | 5/5 100% [100–100] | 0.80 | 2/5 40% [0–80] | 2/5 40% [0–80] | 0.0 (0/14) | 0.0 (0/17) | 0/5 | 3/5 60% [20–100] | 1 |
| **all** | 107 | 34/36 94% [86–100] | 32/34 94% [85–100] | 0.79 | 49/107 46% [36–55] | 47/107 44% [35–53] | 0.0 (0/254) | 0.0 (0/335) | 5/107 | 83/107 78% [69–85] | 5 |

| Category | n | grounding issues / 100 replies | facts | no forbidden | privacy violations | return claimed done | customer turns | tokens / conversation | latency p50 / p95 (s) |
|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 0.0 (0/25) | 18/25 72% [52–88] | 25/25 100% [100–100] | 0 | 0 | 1.0 | 4,215 | 2.96 / 7.02 |
| order_lookup | 25 | 0.0 (0/25) | 22/25 88% [72–100] | 25/25 100% [100–100] | 0 | 0 | 1.0 | 5,067 | 4.00 / 7.32 |
| returns | 15 | 0.0 (0/16) | 7/15 47% [20–67] | 15/15 100% [100–100] | 0 | 0 | 1.1 | 6,967 | 4.20 / 7.34 |
| unanswerable | 15 | 6.7 (1/15) | 15/15 100% [100–100] | 13/15 87% [67–100] | 0 | 0 | 1.0 | 3,345 | 2.92 / 4.11 |
| escalation | 10 | 0.0 (0/12) | 8/10 80% [50–100] | 10/10 100% [100–100] | 0 | 0 | 1.2 | 5,077 | 3.67 / 8.22 |
| adversarial | 12 | 7.7 (1/13) | 12/12 100% [100–100] | 12/12 100% [100–100] | 0 | 0 | 1.1 | 4,808 | 4.54 / 11.44 |
| old_policy | 5 | 0.0 (0/5) | 2/5 40% [0–80] | 5/5 100% [100–100] | 0 | 0 | 1.0 | 5,319 | 4.14 / 8.30 |
| **all** | 107 | 1.8 (2/111) | 84/107 79% [71–86] | 105/107 98% [95–100] | 0 | 0 | 1.0 | 4,877 | 3.44 / 7.34 |

Tool confusion (expected against called):

| expected ↓ / called → | list | status | tracking | search | propose | escalate | (none) |
|---|---|---|---|---|---|---|---|
| list | **36** | · | · | 1 | · | · | · |
| status | · | **20** | · | 1 | · | 2 | 4 |
| tracking | · | 1 | **24** | · | · | · | 1 |
| search | 1 | · | · | **44** | · | · | 1 |
| propose | · | · | · | · | **12** | · | · |
| escalate | · | · | · | · | · | **22** | 1 |
| (none) | 16 | 17 | 4 | 11 | 6 | 36 | · |
