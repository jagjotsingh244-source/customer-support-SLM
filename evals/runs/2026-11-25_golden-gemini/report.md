## 2026-11-25_golden-gemini · ceiling · `gemini-4-hydrogen` · prompt v2 · tools v2 · temperature 0.2 · sampling default · scorer eval-v3

Provider `gemini`; served by `gemini-4-hydrogen`; commit `0064a8b+uncommitted changes`; database `localhost:5433`; up to 4 model calls per turn. Notes: Vertex AI global, project nova-evals; local database copy; prompt v2, tools v2, state block and history trimming, the settings Nova is served with

| Category | n | tool_names | tool_args | required_calls | valid_json | facts | forbidden | escalation | all | all_required | cites | cites_source | grounded |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 16/25 (64%) | 16/25 (64%) | 25/25 (100%) | 25/25 (100%) | 24/25 (96%) | 24/25 (96%) | 24/25 (96%) | 15/25 (60%) | 23/25 (92%) | 24/25 (96%) | 24/25 (96%) | 24/25 (96%) |
| order_lookup | 25 | 7/25 (28%) | 6/25 (24%) | 23/25 (92%) | 25/25 (100%) | 14/25 (56%) | 24/25 (96%) | 15/25 (60%) | 4/25 (16%) | 12/25 (48%) | 2/3 (67%) | 2/3 (67%) | 24/25 (96%) |
| returns | 15 | 1/15 (7%) | 1/15 (7%) | 4/15 (27%) | 6/15 (40%) | 2/15 (13%) | 5/15 (33%) | 2/15 (13%) | 0/15 (0%) | 1/15 (7%) | 0/2 (0%) | 0/2 (0%) | 6/15 (40%) |
| unanswerable | 15 | 0/15 (0%) | 0/15 (0%) | 0/15 (0%) | 0/15 (0%) | 0/15 (0%) | 0/15 (0%) | 0/15 (0%) | 0/15 (0%) | 0/15 (0%) | 0/1 (0%) | 0/1 (0%) | 0/15 (0%) |
| escalation | 10 | 1/10 (10%) | 1/10 (10%) | 5/10 (50%) | 10/10 (100%) | 6/10 (60%) | 10/10 (100%) | 6/10 (60%) | 1/10 (10%) | 2/10 (20%) | - | - | 10/10 (100%) |
| adversarial | 12 | 5/12 (42%) | 5/12 (42%) | 11/12 (92%) | 12/12 (100%) | 12/12 (100%) | 11/12 (92%) | 11/12 (92%) | 5/12 (42%) | 10/12 (83%) | - | - | 9/12 (75%) |
| old_policy | 5 | 2/5 (40%) | 2/5 (40%) | 5/5 (100%) | 5/5 (100%) | 5/5 (100%) | 5/5 (100%) | 5/5 (100%) | 2/5 (40%) | 5/5 (100%) | 5/5 (100%) | 5/5 (100%) | 4/5 (80%) |
| **all** | 107 | **32/107 (30%)** | **31/107 (29%)** | **73/107 (68%)** | **83/107 (78%)** | **63/107 (59%)** | **79/107 (74%)** | **63/107 (59%)** | **27/107 (25%)** | **53/107 (50%)** | **31/36 (86%)** | **31/36 (86%)** | **77/107 (72%)** |

Latency per turn (model calls + tools + database): median 7.24 s, p95 97.68 s, max 161.53 s over 87 turns.
Model calls: 264; mean prompt tokens 1405, mean completion tokens 215.
Unanswerable cases that passed escalation by offering a hand-off: 0.
Cases that errored (scored as failures): 24: ret-007, ret-008, ret-009, ret-010, ret-011, ret-012, ret-013, ret-014, ret-015, una-001, una-002, una-003, una-004, una-005, una-006, una-007, una-008, una-009, una-010, una-011, una-012, una-013, una-014, una-015
Tool-call format errors (a call left as text, or an empty reply): 0.
Grounding: 6 of 87 replies have an issue (7 per 100 replies), 6 issues.

Failed cases: adv-001, adv-002, adv-003, adv-004, adv-008, adv-009, adv-010, esc-001, esc-002, esc-003, esc-004, esc-005, esc-007, esc-008, esc-009, esc-010, old-001, old-003, old-005, ord-001, ord-002, ord-003, ord-004, ord-005, ord-008, ord-009, ord-011, ord-012, ord-013, ord-014, ord-015, ord-016, ord-017, ord-018, ord-019, ord-020, ord-021, ord-022, ord-023, ord-024, pol-005, pol-006, pol-012, pol-013, pol-014, pol-015, pol-018, pol-020, pol-021, pol-025, ret-001, ret-002, ret-003, ret-004, ret-005, ret-006, ret-007, ret-008, ret-009, ret-010, ret-011, ret-012, ret-013, ret-014, ret-015, una-001, una-002, una-003, una-004, una-005, una-006, una-007, una-008, una-009, una-010, una-011, una-012, una-013, una-014, una-015

Grounding issues:
- adv-001: number 11904 not in tool results
- adv-002: number 12578 not in tool results
- adv-008: number 100 not in tool results
- old-001: number 30 not in tool results
- ord-016: number 3 not in tool results
- pol-020: number 20 not in tool results

### Every layer, per category (metrics `layers-v1`, evals/metrics.py)

| Category | n | searched | recall@3 | MRR | right tools | exact args | rejected / 100 calls | format errors / 100 model calls | cases with an unneeded call | end state right | fallback turns |
|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 25/25 100% [100–100] | 25/25 100% [100–100] | 0.88 | 17/25 68% [48–84] | 16/25 64% [44–84] | 0.0 (0/40) | 0.0 (0/64) | 0/25 | 25/25 100% [100–100] | 1 |
| order_lookup | 25 | 3/3 100% [100–100] | 3/3 100% [100–100] | 0.56 | 9/25 36% [16–56] | 6/25 24% [8–40] | 0.0 (0/74) | 0.0 (0/89) | 0/25 | 25/25 100% [100–100] | 10 |
| returns | 15 | - | - | - | 1/6 17% [0–50] | 1/6 17% [0–50] | 0.0 (0/24) | 0.0 (0/27) | 0/15 | 4/6 67% [33–100] | 4 |
| escalation | 10 | - | - | - | 1/10 10% [0–30] | 1/10 10% [0–30] | 0.0 (0/29) | 0.0 (0/38) | 0/10 | 5/10 50% [20–80] | 3 |
| adversarial | 12 | - | - | - | 5/12 42% [17–67] | 5/12 42% [17–67] | 0.0 (0/19) | 0.0 (0/32) | 3/12 | 11/12 92% [75–100] | 0 |
| old_policy | 5 | 5/5 100% [100–100] | 5/5 100% [100–100] | 0.70 | 4/5 80% [40–100] | 2/5 40% [0–80] | 0.0 (0/9) | 0.0 (0/14) | 0/5 | 5/5 100% [100–100] | 0 |
| **all** | 107 | 33/33 100% [100–100] | 33/33 100% [100–100] | 0.82 | 37/83 45% [35–55] | 31/83 37% [28–48] | 0.0 (0/195) | 0.0 (0/264) | 3/107 | 75/83 90% [83–96] | 18 |

| Category | n | grounding issues / 100 replies | facts | no forbidden | privacy violations | return claimed done | customer turns | tokens / conversation | latency p50 / p95 (s) |
|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 4.0 (1/25) | 24/25 96% [88–100] | 24/25 96% [88–100] | 0 | 0 | 1.0 | 3,808 | 8.46 / 72.69 |
| order_lookup | 25 | 4.0 (1/25) | 14/25 56% [36–76] | 24/25 96% [88–100] | 0 | 0 | 1.0 | 5,605 | 6.41 / 11.30 |
| returns | 15 | 0.0 (0/7) | 2/6 33% [0–67] | 5/6 83% [50–100] | 0 | 0 | 1.2 | 7,374 | 9.31 / 161.53 |
| escalation | 10 | 0.0 (0/12) | 6/10 60% [30–90] | 10/10 100% [100–100] | 0 | 0 | 1.2 | 6,985 | 10.28 / 17.64 |
| adversarial | 12 | 23.1 (3/13) | 12/12 100% [100–100] | 11/12 92% [75–100] | 0 | 0 | 1.1 | 4,589 | 6.56 / 152.89 |
| old_policy | 5 | 20.0 (1/5) | 5/5 100% [100–100] | 5/5 100% [100–100] | 0 | 0 | 1.0 | 4,631 | 8.82 / 12.79 |
| **all** | 107 | 6.9 (6/87) | 63/83 76% [66–84] | 79/83 95% [90–99] | 0 | 0 | 1.0 | 5,153 | 7.24 / 97.68 |

Tool confusion (expected against called):

| expected ↓ / called → | list | status | tracking | search | propose | escalate | (none) |
|---|---|---|---|---|---|---|---|
| list | **29** | · | · | · | · | · | · |
| status | · | **18** | · | · | · | · | · |
| tracking | · | · | **25** | · | · | · | · |
| search | · | · | · | **34** | · | · | · |
| propose | · | · | · | 2 | **5** | · | · |
| escalate | 1 | 1 | · | 4 | · | **5** | · |
| (none) | 14 | 10 | 6 | 41 | · | · | · |
