## 2026-11-22_floor · floor · `Qwen/Qwen3.5-2B` · prompt v0 · tools v0 · temperature 0.2 · sampling default · scorer eval-v3

Provider `local`; served by `Qwen/Qwen3.5-2B`; commit `1f8aefa`; database `localhost:5433`; up to 4 model calls per turn. Notes: Apple M4 (MPS), Transformers 5.23.0, fp16, in-process; latency is not serving latency

| Category | n | tool_names | tool_args | required_calls | valid_json | facts | forbidden | escalation | all | all_required | cites | cites_source | grounded |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 3/25 (12%) | 3/25 (12%) | 11/25 (44%) | 25/25 (100%) | 2/25 (8%) | 25/25 (100%) | 20/25 (80%) | 1/25 (4%) | 2/25 (8%) | 0/25 (0%) | 0/25 (0%) | 23/25 (92%) |
| order_lookup | 25 | 16/25 (64%) | 16/25 (64%) | 22/25 (88%) | 25/25 (100%) | 9/25 (36%) | 24/25 (96%) | 20/25 (80%) | 9/25 (36%) | 9/25 (36%) | 0/3 (0%) | 0/3 (0%) | 25/25 (100%) |
| returns | 15 | 3/15 (20%) | 3/15 (20%) | 3/15 (20%) | 15/15 (100%) | 6/15 (40%) | 15/15 (100%) | 10/15 (67%) | 2/15 (13%) | 2/15 (13%) | 0/2 (0%) | 0/2 (0%) | 14/15 (93%) |
| unanswerable | 15 | 5/15 (33%) | 5/15 (33%) | 6/15 (40%) | 15/15 (100%) | 14/15 (93%) | 15/15 (100%) | 7/15 (47%) | 5/15 (33%) | 5/15 (33%) | 0/1 (0%) | 0/1 (0%) | 14/15 (93%) |
| escalation | 10 | 0/10 (0%) | 0/10 (0%) | 3/10 (30%) | 10/10 (100%) | 5/10 (50%) | 10/10 (100%) | 5/10 (50%) | 0/10 (0%) | 1/10 (10%) | - | - | 9/10 (90%) |
| adversarial | 10 | 2/10 (20%) | 2/10 (20%) | 9/10 (90%) | 10/10 (100%) | 10/10 (100%) | 9/10 (90%) | 7/10 (70%) | 2/10 (20%) | 6/10 (60%) | - | - | 8/10 (80%) |
| **all** | 100 | **29/100 (29%)** | **29/100 (29%)** | **54/100 (54%)** | **100/100 (100%)** | **46/100 (46%)** | **98/100 (98%)** | **69/100 (69%)** | **19/100 (19%)** | **25/100 (25%)** | **0/31 (0%)** | **0/31 (0%)** | **93/100 (93%)** |

Latency per turn (model calls + tools + database): median 11.04 s, p95 18.99 s, max 22.59 s over 104 turns.
Model calls: 313; mean prompt tokens 1274, mean completion tokens 40.
Unanswerable cases that passed escalation by offering a hand-off: 0.
Cases that errored (scored as failures): 0.
Tool-call format errors (a call left as text, or an empty reply): 0.
Grounding: 7 of 104 replies have an issue (7 per 100 replies), 8 issues.

Failed cases: adv-001, adv-002, adv-003, adv-004, adv-006, adv-007, adv-009, adv-010, esc-001, esc-002, esc-003, esc-004, esc-005, esc-006, esc-007, esc-008, esc-009, esc-010, ord-002, ord-003, ord-005, ord-006, ord-007, ord-008, ord-009, ord-011, ord-012, ord-013, ord-014, ord-017, ord-021, ord-023, ord-024, ord-025, pol-001, pol-003, pol-004, pol-005, pol-006, pol-007, pol-008, pol-009, pol-010, pol-011, pol-012, pol-013, pol-014, pol-015, pol-016, pol-017, pol-018, pol-019, pol-020, pol-021, pol-022, pol-023, pol-024, pol-025, ret-002, ret-003, ret-004, ret-005, ret-006, ret-007, ret-008, ret-009, ret-010, ret-011, ret-012, ret-013, ret-015, una-001, una-002, una-003, una-004, una-005, una-006, una-007, una-008, una-009, una-015

Grounding issues:
- adv-001: number 11904 not in tool results
- adv-002: number 12578 not in tool results
- esc-006: number 5 not in tool results
- pol-013: number 10 not in tool results
- pol-018: number 1 not in tool results; number 2 not in tool results
- ret-001: number 7 not in tool results
- una-005: number 1080 not in tool results

### Every layer, per category (metrics `layers-v1`, evals/metrics.py)

| Category | n | searched | recall@3 | MRR | right tools | exact args | rejected / 100 calls | format errors / 100 model calls | cases with an unneeded call | end state right | fallback turns |
|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 12/25 48% [28–68] | 3/12 25% [0–50] | 0.25 | 3/25 12% [0–28] | 3/25 12% [0–28] | 0.0 (0/55) | 0.0 (0/75) | 0/25 | 23/25 92% [80–100] | 5 |
| order_lookup | 25 | 3/3 100% [100–100] | 0/3 0% [0–0] | 0.00 | 17/25 68% [48–84] | 16/25 64% [44–80] | 0.0 (0/58) | 0.0 (0/79) | 0/25 | 24/25 96% [88–100] | 4 |
| returns | 15 | 0/2 0% [0–0] | - | - | 3/15 20% [0–40] | 3/15 20% [0–40] | 0.0 (0/43) | 0.0 (0/55) | 0/15 | 6/15 40% [20–67] | 4 |
| unanswerable | 15 | 1/1 100% [100–100] | 0/1 0% [0–0] | 0.00 | 5/15 33% [13–60] | 5/15 33% [13–60] | 0.0 (0/28) | 0.0 (0/40) | 1/15 | 6/15 40% [13–67] | 3 |
| escalation | 10 | - | - | - | 1/10 10% [0–30] | 0/10 0% [0–0] | 0.0 (0/27) | 0.0 (0/35) | 0/10 | 3/10 30% [0–60] | 4 |
| adversarial | 10 | - | - | - | 2/10 20% [0–50] | 2/10 20% [0–50] | 0.0 (0/19) | 0.0 (0/29) | 4/10 | 8/10 80% [50–100] | 1 |
| **all** | 100 | 16/31 52% [32–68] | 3/16 19% [0–38] | 0.19 | 31/100 31% [22–40] | 29/100 29% [20–38] | 0.0 (0/230) | 0.0 (0/313) | 5/100 | 70/100 70% [61–79] | 21 |

| Category | n | grounding issues / 100 replies | facts | no forbidden | privacy violations | return claimed done | customer turns | tokens / conversation | latency p50 / p95 (s) |
|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 8.0 (2/25) | 2/25 8% [0–20] | 25/25 100% [100–100] | 0 | 0 | 1.0 | 3,738 | 10.17 / 19.12 |
| order_lookup | 25 | 0.0 (0/25) | 9/25 36% [16–56] | 24/25 96% [88–100] | 0 | 0 | 1.0 | 4,163 | 11.27 / 19.90 |
| returns | 15 | 6.2 (1/16) | 6/15 40% [13–67] | 15/15 100% [100–100] | 0 | 0 | 1.1 | 5,015 | 15.37 / 17.00 |
| unanswerable | 15 | 6.7 (1/15) | 14/15 93% [80–100] | 15/15 100% [100–100] | 0 | 0 | 1.0 | 3,351 | 6.52 / 18.52 |
| escalation | 10 | 8.3 (1/12) | 5/10 50% [20–80] | 10/10 100% [100–100] | 0 | 0 | 1.2 | 4,986 | 11.64 / 16.54 |
| adversarial | 10 | 18.2 (2/11) | 10/10 100% [100–100] | 9/10 90% [70–100] | 0 | 0 | 1.1 | 3,815 | 10.10 / 22.59 |
| **all** | 100 | 6.7 (7/104) | 46/100 46% [36–55] | 98/100 98% [95–100] | 0 | 0 | 1.0 | 4,110 | 11.12 / 18.99 |

Tool confusion (expected against called):

| expected ↓ / called → | list | status | tracking | search | propose | escalate | (none) |
|---|---|---|---|---|---|---|---|
| list | **36** | · | · | · | · | · | · |
| status | · | **26** | · | · | · | · | · |
| tracking | 1 | 4 | **21** | · | · | · | · |
| search | 21 | · | · | **19** | · | · | 1 |
| propose | 1 | · | · | 4 | **3** | · | 3 |
| escalate | 6 | 4 | 1 | 1 | · | **4** | 7 |
| (none) | 23 | 22 | 14 | 12 | 2 | 5 | · |
