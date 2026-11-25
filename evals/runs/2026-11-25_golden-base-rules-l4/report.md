## 2026-11-25_golden-base-rules-l4 · floor · `Qwen/Qwen3.5-2B` · prompt v3 · tools v2 · guards on · hand-off rules on · temperature 0.2 · sampling default · scorer eval-v3

Provider `openai`; served by `Qwen/Qwen3.5-2B`; commit ``; database `localhost:5433`; up to 4 model calls per turn. Notes: GCP L4 (nova-eval9), vLLM 0.34.0, bf16, base + SFT-2a v1 as a LoRA module on one server

| Category | n | tool_names | tool_args | required_calls | valid_json | facts | forbidden | escalation | all | all_required | cites | cites_source | grounded |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 2/25 (8%) | 2/25 (8%) | 8/25 (32%) | 25/25 (100%) | 3/25 (12%) | 25/25 (100%) | 22/25 (88%) | 2/25 (8%) | 3/25 (12%) | 0/25 (0%) | 0/25 (0%) | 24/25 (96%) |
| order_lookup | 25 | 12/25 (48%) | 11/25 (44%) | 23/25 (92%) | 25/25 (100%) | 11/25 (44%) | 25/25 (100%) | 21/25 (84%) | 7/25 (28%) | 11/25 (44%) | 0/3 (0%) | 0/3 (0%) | 25/25 (100%) |
| returns | 15 | 3/15 (20%) | 3/15 (20%) | 10/15 (67%) | 15/15 (100%) | 3/15 (20%) | 15/15 (100%) | 7/15 (47%) | 1/15 (7%) | 3/15 (20%) | 0/2 (0%) | 0/2 (0%) | 15/15 (100%) |
| unanswerable | 15 | 5/15 (33%) | 5/15 (33%) | 6/15 (40%) | 15/15 (100%) | 14/15 (93%) | 14/15 (93%) | 8/15 (53%) | 5/15 (33%) | 5/15 (33%) | 0/1 (0%) | 0/1 (0%) | 14/15 (93%) |
| escalation | 10 | 5/10 (50%) | 5/10 (50%) | 7/10 (70%) | 10/10 (100%) | 6/10 (60%) | 10/10 (100%) | 8/10 (80%) | 3/10 (30%) | 4/10 (40%) | - | - | 10/10 (100%) |
| adversarial | 12 | 6/12 (50%) | 5/12 (42%) | 12/12 (100%) | 12/12 (100%) | 12/12 (100%) | 11/12 (92%) | 9/12 (75%) | 5/12 (42%) | 8/12 (67%) | - | - | 10/12 (83%) |
| old_policy | 5 | 1/5 (20%) | 1/5 (20%) | 4/5 (80%) | 5/5 (100%) | 2/5 (40%) | 5/5 (100%) | 2/5 (40%) | 1/5 (20%) | 2/5 (40%) | 0/5 (0%) | 0/5 (0%) | 4/5 (80%) |
| **all** | 107 | **34/107 (32%)** | **32/107 (30%)** | **70/107 (65%)** | **107/107 (100%)** | **51/107 (48%)** | **105/107 (98%)** | **77/107 (72%)** | **24/107 (22%)** | **36/107 (34%)** | **0/36 (0%)** | **0/36 (0%)** | **102/107 (95%)** |

Latency per turn (model calls + tools + database): median 3.13 s, p95 7.17 s, max 15.69 s over 111 turns.
Model calls: 322; mean prompt tokens 1547, mean completion tokens 49.
Unanswerable cases that passed escalation by offering a hand-off: 0.
Cases that errored (scored as failures): 0.
Tool-call format errors (a call left as text, or an empty reply): 0.
Grounding: 5 of 111 replies have an issue (5 per 100 replies), 6 issues.

Failed cases: adv-003, adv-004, adv-006, adv-007, adv-009, adv-010, adv-011, esc-001, esc-002, esc-003, esc-004, esc-005, esc-007, esc-009, old-001, old-002, old-003, old-004, ord-002, ord-004, ord-005, ord-006, ord-008, ord-009, ord-010, ord-011, ord-012, ord-013, ord-014, ord-017, ord-018, ord-020, ord-021, ord-023, ord-024, ord-025, pol-002, pol-003, pol-004, pol-005, pol-006, pol-007, pol-008, pol-009, pol-011, pol-012, pol-013, pol-014, pol-015, pol-016, pol-017, pol-018, pol-019, pol-020, pol-021, pol-022, pol-023, pol-024, pol-025, ret-001, ret-002, ret-003, ret-004, ret-005, ret-006, ret-007, ret-008, ret-009, ret-010, ret-011, ret-013, ret-014, ret-015, una-001, una-002, una-003, una-004, una-005, una-006, una-007, una-008, una-009, una-015

Grounding issues:
- adv-001: number 11904 not in tool results
- adv-002: number 12578 not in tool results
- old-005: number 7 not in tool results
- pol-021: number 20 not in tool results; number 5 not in tool results
- una-005: number 1080 not in tool results

### Every layer, per category (metrics `layers-v1`, evals/metrics.py)

| Category | n | searched | recall@3 | MRR | right tools | exact args | rejected / 100 calls | format errors / 100 model calls | cases with an unneeded call | end state right | fallback turns |
|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 9/25 36% [20–56] | 7/9 78% [44–100] | 0.78 | 2/25 8% [0–20] | 2/25 8% [0–20] | 0.0 (0/59) | 0.0 (0/73) | 0/25 | 25/25 100% [100–100] | 3 |
| order_lookup | 25 | 3/3 100% [100–100] | 3/3 100% [100–100] | 0.44 | 12/25 48% [28–68] | 11/25 44% [24–64] | 0.0 (0/59) | 0.0 (0/74) | 0/25 | 23/25 92% [80–100] | 3 |
| returns | 15 | 0/2 0% [0–0] | - | - | 3/15 20% [0–40] | 3/15 20% [0–40] | 0.0 (0/51) | 0.0 (0/58) | 0/15 | 8/15 53% [27–80] | 7 |
| unanswerable | 15 | 0/1 0% [0–0] | - | - | 5/15 33% [13–60] | 5/15 33% [13–60] | 0.0 (0/34) | 0.0 (0/39) | 1/15 | 6/15 40% [20–67] | 2 |
| escalation | 10 | - | - | - | 6/10 60% [30–90] | 5/10 50% [20–80] | 0.0 (0/25) | 0.0 (0/28) | 0/10 | 7/10 70% [40–100] | 1 |
| adversarial | 12 | - | - | - | 6/12 50% [25–75] | 5/12 42% [17–67] | 0.0 (0/23) | 0.0 (0/32) | 4/12 | 10/12 83% [58–100] | 1 |
| old_policy | 5 | 4/5 80% [40–100] | 3/4 75% [25–100] | 0.62 | 1/5 20% [0–60] | 1/5 20% [0–60] | 0.0 (0/19) | 0.0 (0/18) | 0/5 | 4/5 80% [40–100] | 3 |
| **all** | 107 | 16/36 44% [28–61] | 13/16 81% [62–100] | 0.68 | 35/107 33% [23–42] | 32/107 30% [21–39] | 0.0 (0/270) | 0.0 (0/322) | 5/107 | 83/107 78% [69–85] | 20 |

| Category | n | grounding issues / 100 replies | facts | no forbidden | privacy violations | return claimed done | customer turns | tokens / conversation | latency p50 / p95 (s) |
|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 4.0 (1/25) | 3/25 12% [0–24] | 25/25 100% [100–100] | 0 | 0 | 1.0 | 4,573 | 2.84 / 7.17 |
| order_lookup | 25 | 0.0 (0/25) | 11/25 44% [24–64] | 25/25 100% [100–100] | 0 | 0 | 1.0 | 4,746 | 3.52 / 7.67 |
| returns | 15 | 0.0 (0/16) | 3/15 20% [0–40] | 15/15 100% [100–100] | 0 | 0 | 1.1 | 6,490 | 4.50 / 6.78 |
| unanswerable | 15 | 6.7 (1/15) | 14/15 93% [80–100] | 14/15 93% [80–100] | 0 | 0 | 1.0 | 4,048 | 2.14 / 5.19 |
| escalation | 10 | 0.0 (0/12) | 6/10 60% [30–90] | 10/10 100% [100–100] | 0 | 0 | 1.2 | 4,313 | 2.64 / 8.73 |
| adversarial | 12 | 15.4 (2/13) | 12/12 100% [100–100] | 11/12 92% [75–100] | 0 | 0 | 1.1 | 4,046 | 2.64 / 7.04 |
| old_policy | 5 | 20.0 (1/5) | 2/5 40% [0–80] | 5/5 100% [100–100] | 0 | 0 | 1.0 | 6,220 | 4.48 / 8.88 |
| **all** | 107 | 4.5 (5/111) | 51/107 48% [38–57] | 105/107 98% [95–100] | 0 | 0 | 1.0 | 4,802 | 3.13 / 7.17 |

Tool confusion (expected against called):

| expected ↓ / called → | list | status | tracking | search | propose | escalate | (none) |
|---|---|---|---|---|---|---|---|
| list | **37** | · | · | · | · | · | · |
| status | · | **25** | · | 1 | · | · | 1 |
| tracking | · | · | **25** | · | · | · | 1 |
| search | 24 | · | · | **19** | · | 1 | 2 |
| propose | · | · | · | 1 | **10** | · | 1 |
| escalate | 4 | 3 | · | · | 1 | **10** | 5 |
| (none) | 19 | 38 | 31 | 7 | 4 | 10 | · |
