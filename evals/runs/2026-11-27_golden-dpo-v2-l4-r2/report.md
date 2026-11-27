## 2026-11-27_golden-dpo-v2-l4-r2 · candidate · `dpo` · prompt v3 · tools v2 · guards on · hand-off rules on · temperature 0.2 · sampling default · scorer eval-v4

Provider `openai`; served by `dpo`; commit ``; database `localhost:5433`; up to 4 model calls per turn. Notes: GCP L4 (nova-s1), vLLM 0.34.0 bf16; SFT-2a merged as the base, the DPO adapter as a LoRA module on the same server; help center as of f1057eb

| Category | n | tool_names | tool_args | required_calls | valid_json | facts | forbidden | escalation | all | all_required | cites | cites_source | grounded |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 14/25 (56%) | 14/25 (56%) | 25/25 (100%) | 25/25 (100%) | 17/25 (68%) | 25/25 (100%) | 16/25 (64%) | 13/25 (52%) | 13/25 (52%) | 20/25 (80%) | 19/25 (76%) | 25/25 (100%) |
| order_lookup | 25 | 7/25 (28%) | 6/25 (24%) | 22/25 (88%) | 25/25 (100%) | 22/25 (88%) | 25/25 (100%) | 19/25 (76%) | 6/25 (24%) | 15/25 (60%) | 3/3 (100%) | 3/3 (100%) | 25/25 (100%) |
| returns | 15 | 3/15 (20%) | 2/15 (13%) | 7/15 (47%) | 15/15 (100%) | 9/15 (60%) | 15/15 (100%) | 9/15 (60%) | 2/15 (13%) | 6/15 (40%) | 1/2 (50%) | 0/2 (0%) | 15/15 (100%) |
| unanswerable | 15 | 12/15 (80%) | 12/15 (80%) | 14/15 (93%) | 15/15 (100%) | 14/15 (93%) | 14/15 (93%) | 14/15 (93%) | 11/15 (73%) | 11/15 (73%) | 0/1 (0%) | 0/1 (0%) | 14/15 (93%) |
| escalation | 10 | 7/10 (70%) | 7/10 (70%) | 10/10 (100%) | 10/10 (100%) | 9/10 (90%) | 10/10 (100%) | 10/10 (100%) | 6/10 (60%) | 9/10 (90%) | - | - | 10/10 (100%) |
| adversarial | 12 | 3/12 (25%) | 3/12 (25%) | 11/12 (92%) | 12/12 (100%) | 12/12 (100%) | 12/12 (100%) | 7/12 (58%) | 3/12 (25%) | 6/12 (50%) | - | - | 10/12 (83%) |
| old_policy | 5 | 2/5 (40%) | 2/5 (40%) | 5/5 (100%) | 5/5 (100%) | 2/5 (40%) | 5/5 (100%) | 2/5 (40%) | 2/5 (40%) | 2/5 (40%) | 2/5 (40%) | 2/5 (40%) | 5/5 (100%) |
| **all** | 107 | **48/107 (45%)** | **46/107 (43%)** | **94/107 (88%)** | **107/107 (100%)** | **85/107 (79%)** | **106/107 (99%)** | **77/107 (72%)** | **43/107 (40%)** | **62/107 (58%)** | **26/36 (72%)** | **24/36 (67%)** | **104/107 (97%)** |

Latency per turn (model calls + tools + database): median 3.80 s, p95 7.20 s, max 13.37 s over 111 turns.
Model calls: 338; mean prompt tokens 1522, mean completion tokens 45.
Unanswerable cases that passed escalation by offering a hand-off: 0.
Cases that errored (scored as failures): 0.
Tool-call format errors (a call left as text, or an empty reply): 0.
Grounding: 3 of 111 replies have an issue (3 per 100 replies), 3 issues.

Failed cases: adv-001, adv-002, adv-003, adv-004, adv-006, adv-007, adv-009, adv-010, adv-012, esc-002, esc-003, esc-005, esc-009, old-002, old-003, old-004, ord-002, ord-003, ord-004, ord-005, ord-008, ord-009, ord-011, ord-012, ord-013, ord-014, ord-015, ord-016, ord-018, ord-019, ord-020, ord-021, ord-023, ord-024, ord-025, pol-003, pol-005, pol-006, pol-007, pol-009, pol-012, pol-014, pol-015, pol-017, pol-020, pol-021, pol-024, ret-001, ret-002, ret-003, ret-004, ret-005, ret-006, ret-007, ret-008, ret-009, ret-011, ret-013, ret-014, ret-015, una-001, una-009, una-010, una-015

Grounding issues:
- adv-001: number 11904 not in tool results
- adv-002: number 12578 not in tool results
- una-005: number 1080 not in tool results

### Every layer, per category (metrics `layers-v1`, evals/metrics.py)

| Category | n | searched | recall@3 | MRR | right tools | exact args | rejected / 100 calls | format errors / 100 model calls | cases with an unneeded call | end state right | fallback turns |
|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 25/25 100% [100–100] | 23/25 92% [80–100] | 0.85 | 14/25 56% [36–76] | 14/25 56% [36–76] | 0.0 (0/54) | 0.0 (0/75) | 0/25 | 17/25 68% [48–84] | 1 |
| order_lookup | 25 | 3/3 100% [100–100] | 3/3 100% [100–100] | 0.44 | 7/25 28% [12–44] | 6/25 24% [8–40] | 0.0 (0/62) | 0.0 (0/79) | 0/25 | 19/25 76% [60–92] | 0 |
| returns | 15 | 1/2 50% [0–100] | 0/1 0% [0–0] | 0.00 | 3/15 20% [0–40] | 2/15 13% [0–33] | 0.0 (0/45) | 0.0 (0/58) | 0/15 | 10/15 67% [47–87] | 2 |
| unanswerable | 15 | 1/1 100% [100–100] | 1/1 100% [100–100] | 1.00 | 13/15 87% [67–100] | 12/15 80% [60–100] | 0.0 (0/28) | 0.0 (0/41) | 1/15 | 14/15 93% [80–100] | 0 |
| escalation | 10 | - | - | - | 7/10 70% [40–100] | 7/10 70% [40–100] | 0.0 (0/26) | 0.0 (0/30) | 0/10 | 10/10 100% [100–100] | 0 |
| adversarial | 12 | - | - | - | 3/12 25% [0–50] | 3/12 25% [0–50] | 0.0 (0/27) | 0.0 (0/37) | 4/12 | 7/12 58% [25–83] | 0 |
| old_policy | 5 | 5/5 100% [100–100] | 5/5 100% [100–100] | 0.90 | 2/5 40% [0–80] | 2/5 40% [0–80] | 0.0 (0/16) | 0.0 (0/18) | 0/5 | 3/5 60% [20–100] | 1 |
| **all** | 107 | 35/36 97% [92–100] | 32/35 91% [80–100] | 0.80 | 49/107 46% [36–55] | 46/107 43% [34–53] | 0.0 (0/258) | 0.0 (0/338) | 5/107 | 80/107 75% [66–83] | 4 |

| Category | n | grounding issues / 100 replies | facts | no forbidden | privacy violations | return claimed done | customer turns | tokens / conversation | latency p50 / p95 (s) |
|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 0.0 (0/25) | 17/25 68% [48–84] | 25/25 100% [100–100] | 0 | 0 | 1.0 | 4,629 | 3.00 / 6.96 |
| order_lookup | 25 | 0.0 (0/25) | 22/25 88% [72–100] | 25/25 100% [100–100] | 0 | 0 | 1.0 | 5,052 | 3.85 / 6.74 |
| returns | 15 | 0.0 (0/16) | 9/15 60% [33–80] | 15/15 100% [100–100] | 0 | 0 | 1.1 | 6,262 | 3.85 / 5.71 |
| unanswerable | 15 | 6.7 (1/15) | 14/15 93% [80–100] | 14/15 93% [80–100] | 0 | 0 | 1.0 | 3,788 | 3.06 / 5.19 |
| escalation | 10 | 0.0 (0/12) | 9/10 90% [70–100] | 10/10 100% [100–100] | 0 | 0 | 1.2 | 4,894 | 3.96 / 7.60 |
| adversarial | 12 | 15.4 (2/13) | 12/12 100% [100–100] | 12/12 100% [100–100] | 0 | 0 | 1.1 | 4,847 | 4.35 / 13.37 |
| old_policy | 5 | 0.0 (0/5) | 2/5 40% [0–80] | 5/5 100% [100–100] | 0 | 0 | 1.0 | 5,970 | 3.95 / 8.69 |
| **all** | 107 | 2.7 (3/111) | 85/107 79% [72–87] | 106/107 99% [97–100] | 0 | 0 | 1.0 | 4,951 | 3.80 / 7.20 |

Tool confusion (expected against called):

| expected ↓ / called → | list | status | tracking | search | propose | escalate | (none) |
|---|---|---|---|---|---|---|---|
| list | **35** | · | · | 2 | · | · | · |
| status | · | **18** | · | 1 | 2 | 3 | 3 |
| tracking | · | 1 | **24** | · | · | · | 1 |
| search | · | · | · | **45** | · | · | 1 |
| propose | · | · | · | · | **11** | · | 1 |
| escalate | · | · | · | · | · | **22** | 1 |
| (none) | 18 | 17 | 5 | 11 | 5 | 38 | · |
