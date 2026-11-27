## 2026-11-27_golden-dpo-v2-l4-r3 · candidate · `dpo` · prompt v3 · tools v2 · guards on · hand-off rules on · temperature 0.2 · sampling default · scorer eval-v4

Provider `openai`; served by `dpo`; commit ``; database `localhost:5433`; up to 4 model calls per turn. Notes: GCP L4 (nova-s1), vLLM 0.34.0 bf16; SFT-2a merged as the base, the DPO adapter as a LoRA module on the same server; help center as of f1057eb

| Category | n | tool_names | tool_args | required_calls | valid_json | facts | forbidden | escalation | all | all_required | cites | cites_source | grounded |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 14/25 (56%) | 14/25 (56%) | 24/25 (96%) | 25/25 (100%) | 18/25 (72%) | 25/25 (100%) | 17/25 (68%) | 14/25 (56%) | 15/25 (60%) | 20/25 (80%) | 18/25 (72%) | 25/25 (100%) |
| order_lookup | 25 | 6/25 (24%) | 5/25 (20%) | 22/25 (88%) | 25/25 (100%) | 23/25 (92%) | 25/25 (100%) | 19/25 (76%) | 5/25 (20%) | 15/25 (60%) | 3/3 (100%) | 3/3 (100%) | 25/25 (100%) |
| returns | 15 | 4/15 (27%) | 4/15 (27%) | 8/15 (53%) | 15/15 (100%) | 10/15 (67%) | 15/15 (100%) | 9/15 (60%) | 4/15 (27%) | 7/15 (47%) | 1/2 (50%) | 0/2 (0%) | 15/15 (100%) |
| unanswerable | 15 | 12/15 (80%) | 12/15 (80%) | 14/15 (93%) | 15/15 (100%) | 15/15 (100%) | 15/15 (100%) | 14/15 (93%) | 12/15 (80%) | 13/15 (87%) | 1/1 (100%) | 1/1 (100%) | 15/15 (100%) |
| escalation | 10 | 7/10 (70%) | 7/10 (70%) | 10/10 (100%) | 10/10 (100%) | 10/10 (100%) | 10/10 (100%) | 10/10 (100%) | 7/10 (70%) | 10/10 (100%) | - | - | 10/10 (100%) |
| adversarial | 12 | 3/12 (25%) | 3/12 (25%) | 12/12 (100%) | 12/12 (100%) | 12/12 (100%) | 12/12 (100%) | 6/12 (50%) | 3/12 (25%) | 6/12 (50%) | - | - | 11/12 (92%) |
| old_policy | 5 | 2/5 (40%) | 2/5 (40%) | 5/5 (100%) | 5/5 (100%) | 2/5 (40%) | 5/5 (100%) | 2/5 (40%) | 2/5 (40%) | 2/5 (40%) | 2/5 (40%) | 2/5 (40%) | 5/5 (100%) |
| **all** | 107 | **48/107 (45%)** | **47/107 (44%)** | **95/107 (89%)** | **107/107 (100%)** | **90/107 (84%)** | **107/107 (100%)** | **77/107 (72%)** | **47/107 (44%)** | **68/107 (64%)** | **27/36 (75%)** | **24/36 (67%)** | **106/107 (99%)** |

Latency per turn (model calls + tools + database): median 3.49 s, p95 7.57 s, max 11.85 s over 111 turns.
Model calls: 334; mean prompt tokens 1509, mean completion tokens 45.
Unanswerable cases that passed escalation by offering a hand-off: 1: una-006
Cases that errored (scored as failures): 0.
Tool-call format errors (a call left as text, or an empty reply): 0.
Grounding: 1 of 111 replies have an issue (1 per 100 replies), 1 issues.

Failed cases: adv-001, adv-002, adv-003, adv-004, adv-006, adv-007, adv-009, adv-010, adv-012, esc-003, esc-005, esc-009, old-002, old-003, old-004, ord-001, ord-002, ord-003, ord-004, ord-005, ord-008, ord-009, ord-011, ord-012, ord-013, ord-014, ord-015, ord-016, ord-018, ord-019, ord-020, ord-021, ord-023, ord-024, ord-025, pol-003, pol-005, pol-006, pol-007, pol-009, pol-012, pol-014, pol-015, pol-020, pol-021, pol-024, ret-001, ret-002, ret-003, ret-004, ret-006, ret-007, ret-008, ret-009, ret-011, ret-014, ret-015, una-006, una-010, una-015

Grounding issues:
- adv-002: number 12578 not in tool results

### Every layer, per category (metrics `layers-v1`, evals/metrics.py)

| Category | n | searched | recall@3 | MRR | right tools | exact args | rejected / 100 calls | format errors / 100 model calls | cases with an unneeded call | end state right | fallback turns |
|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 24/25 96% [88–100] | 22/24 92% [79–100] | 0.85 | 14/25 56% [36–76] | 14/25 56% [36–76] | 0.0 (0/49) | 0.0 (0/71) | 0/25 | 18/25 72% [52–88] | 1 |
| order_lookup | 25 | 3/3 100% [100–100] | 3/3 100% [100–100] | 0.44 | 6/25 24% [8–40] | 5/25 20% [4–36] | 0.0 (0/62) | 0.0 (0/79) | 0/25 | 19/25 76% [60–92] | 0 |
| returns | 15 | 1/2 50% [0–100] | 0/1 0% [0–0] | 0.00 | 4/15 27% [7–47] | 4/15 27% [7–47] | 0.0 (0/44) | 0.0 (0/58) | 0/15 | 9/15 60% [33–80] | 1 |
| unanswerable | 15 | 1/1 100% [100–100] | 1/1 100% [100–100] | 1.00 | 12/15 80% [60–100] | 12/15 80% [60–100] | 0.0 (0/22) | 0.0 (0/37) | 1/15 | 14/15 93% [80–100] | 0 |
| escalation | 10 | - | - | - | 7/10 70% [40–100] | 7/10 70% [40–100] | 0.0 (0/26) | 0.0 (0/30) | 0/10 | 10/10 100% [100–100] | 0 |
| adversarial | 12 | - | - | - | 3/12 25% [0–50] | 3/12 25% [0–50] | 0.0 (0/33) | 0.0 (0/41) | 4/12 | 6/12 50% [25–75] | 1 |
| old_policy | 5 | 5/5 100% [100–100] | 5/5 100% [100–100] | 0.80 | 2/5 40% [0–80] | 2/5 40% [0–80] | 0.0 (0/16) | 0.0 (0/18) | 0/5 | 3/5 60% [20–100] | 1 |
| **all** | 107 | 34/36 94% [86–100] | 31/34 91% [82–100] | 0.78 | 48/107 45% [35–54] | 47/107 44% [34–53] | 0.0 (0/252) | 0.0 (0/334) | 5/107 | 79/107 74% [65–81] | 4 |

| Category | n | grounding issues / 100 replies | facts | no forbidden | privacy violations | return claimed done | customer turns | tokens / conversation | latency p50 / p95 (s) |
|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 0.0 (0/25) | 18/25 72% [52–88] | 25/25 100% [100–100] | 0 | 0 | 1.0 | 4,272 | 3.17 / 7.15 |
| order_lookup | 25 | 0.0 (0/25) | 23/25 92% [80–100] | 25/25 100% [100–100] | 0 | 0 | 1.0 | 5,080 | 3.70 / 7.57 |
| returns | 15 | 0.0 (0/16) | 10/15 67% [40–87] | 15/15 100% [100–100] | 0 | 0 | 1.1 | 6,184 | 3.56 / 7.03 |
| unanswerable | 15 | 0.0 (0/15) | 15/15 100% [100–100] | 15/15 100% [100–100] | 0 | 0 | 1.0 | 3,244 | 2.87 / 4.32 |
| escalation | 10 | 0.0 (0/12) | 10/10 100% [100–100] | 10/10 100% [100–100] | 0 | 0 | 1.2 | 4,900 | 4.24 / 8.21 |
| adversarial | 12 | 7.7 (1/13) | 12/12 100% [100–100] | 12/12 100% [100–100] | 0 | 0 | 1.1 | 5,516 | 5.05 / 11.85 |
| old_policy | 5 | 0.0 (0/5) | 2/5 40% [0–80] | 5/5 100% [100–100] | 0 | 0 | 1.0 | 5,725 | 3.96 / 8.94 |
| **all** | 107 | 0.9 (1/111) | 90/107 84% [77–91] | 107/107 100% [100–100] | 0 | 0 | 1.0 | 4,851 | 3.49 / 7.57 |

Tool confusion (expected against called):

| expected ↓ / called → | list | status | tracking | search | propose | escalate | (none) |
|---|---|---|---|---|---|---|---|
| list | **34** | · | · | 3 | · | · | · |
| status | · | **20** | · | · | 1 | 3 | 3 |
| tracking | · | 1 | **24** | · | · | · | 1 |
| search | 1 | · | · | **44** | · | · | 1 |
| propose | · | · | · | · | **10** | · | 2 |
| escalate | · | · | · | · | · | **21** | 2 |
| (none) | 17 | 16 | 4 | 11 | 5 | 37 | · |
