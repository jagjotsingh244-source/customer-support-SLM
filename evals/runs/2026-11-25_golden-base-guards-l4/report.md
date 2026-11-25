## 2026-11-25_golden-base-guards-l4 · floor · `Qwen/Qwen3.5-2B` · prompt v3 · tools v2 · guards on · temperature 0.2 · sampling default · scorer eval-v3

Provider `openai`; served by `Qwen/Qwen3.5-2B`; commit ``; database `localhost:5433`; up to 4 model calls per turn. Notes: GCP L4 (nova-eval9), vLLM 0.34.0, bf16, base + SFT-2a v1 as a LoRA module on one server

| Category | n | tool_names | tool_args | required_calls | valid_json | facts | forbidden | escalation | all | all_required | cites | cites_source | grounded |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 6/25 (24%) | 6/25 (24%) | 9/25 (36%) | 25/25 (100%) | 6/25 (24%) | 24/25 (96%) | 22/25 (88%) | 5/25 (20%) | 5/25 (20%) | 0/25 (0%) | 0/25 (0%) | 25/25 (100%) |
| order_lookup | 25 | 12/25 (48%) | 10/25 (40%) | 22/25 (88%) | 25/25 (100%) | 7/25 (28%) | 25/25 (100%) | 17/25 (68%) | 6/25 (24%) | 7/25 (28%) | 0/3 (0%) | 0/3 (0%) | 25/25 (100%) |
| returns | 15 | 4/15 (27%) | 4/15 (27%) | 9/15 (60%) | 15/15 (100%) | 6/15 (40%) | 15/15 (100%) | 9/15 (60%) | 2/15 (13%) | 3/15 (20%) | 0/2 (0%) | 0/2 (0%) | 14/15 (93%) |
| unanswerable | 15 | 4/15 (27%) | 4/15 (27%) | 6/15 (40%) | 15/15 (100%) | 14/15 (93%) | 14/15 (93%) | 11/15 (73%) | 4/15 (27%) | 5/15 (33%) | 0/1 (0%) | 0/1 (0%) | 13/15 (87%) |
| escalation | 10 | 1/10 (10%) | 1/10 (10%) | 4/10 (40%) | 10/10 (100%) | 5/10 (50%) | 10/10 (100%) | 7/10 (70%) | 1/10 (10%) | 2/10 (20%) | - | - | 9/10 (90%) |
| adversarial | 12 | 6/12 (50%) | 5/12 (42%) | 11/12 (92%) | 12/12 (100%) | 12/12 (100%) | 11/12 (92%) | 9/12 (75%) | 5/12 (42%) | 8/12 (67%) | - | - | 9/12 (75%) |
| old_policy | 5 | 1/5 (20%) | 1/5 (20%) | 4/5 (80%) | 5/5 (100%) | 2/5 (40%) | 5/5 (100%) | 4/5 (80%) | 1/5 (20%) | 2/5 (40%) | 0/5 (0%) | 0/5 (0%) | 2/5 (40%) |
| **all** | 107 | **34/107 (32%)** | **31/107 (29%)** | **65/107 (61%)** | **107/107 (100%)** | **52/107 (49%)** | **104/107 (97%)** | **79/107 (74%)** | **24/107 (22%)** | **32/107 (30%)** | **0/36 (0%)** | **0/36 (0%)** | **97/107 (91%)** |

Latency per turn (model calls + tools + database): median 3.21 s, p95 8.77 s, max 12.74 s over 111 turns.
Model calls: 331; mean prompt tokens 1516, mean completion tokens 53.
Unanswerable cases that passed escalation by offering a hand-off: 0.
Cases that errored (scored as failures): 0.
Tool-call format errors (a call left as text, or an empty reply): 0.
Grounding: 10 of 111 replies have an issue (9 per 100 replies), 21 issues.

Failed cases: adv-003, adv-004, adv-006, adv-007, adv-009, adv-010, adv-011, esc-001, esc-002, esc-003, esc-004, esc-005, esc-007, esc-008, esc-009, esc-010, old-001, old-002, old-003, old-004, ord-001, ord-002, ord-003, ord-004, ord-005, ord-006, ord-008, ord-009, ord-010, ord-011, ord-012, ord-013, ord-014, ord-017, ord-020, ord-021, ord-023, ord-024, ord-025, pol-001, pol-003, pol-004, pol-005, pol-006, pol-007, pol-008, pol-012, pol-013, pol-014, pol-015, pol-017, pol-018, pol-019, pol-020, pol-021, pol-022, pol-023, pol-024, pol-025, ret-001, ret-002, ret-003, ret-005, ret-006, ret-007, ret-008, ret-009, ret-011, ret-012, ret-013, ret-014, ret-015, una-001, una-002, una-003, una-004, una-005, una-006, una-007, una-008, una-009, una-013, una-015

Grounding issues:
- adv-001: number 11904 not in tool results
- adv-002: number 12578 not in tool results
- adv-008: number 100 not in tool results
- esc-001: number 20 not in tool results
- old-002: number 30 not in tool results
- old-004: number 2 not in tool results; number 3 not in tool results; number 5 not in tool results
- old-005: number 7 not in tool results
- ret-010: number 20 not in tool results
- una-009: number 5 not in tool results
- una-013: number 12 not in tool results; number 12000 not in tool results; number 13000 not in tool results; number 14000 not in tool results; number 15 not in tool results; number 15000 not in tool results; number 16000 not in tool results; number 17 not in tool results; number 20000 not in tool results; number 57 not in tool results

### Every layer, per category (metrics `layers-v1`, evals/metrics.py)

| Category | n | searched | recall@3 | MRR | right tools | exact args | rejected / 100 calls | format errors / 100 model calls | cases with an unneeded call | end state right | fallback turns |
|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 10/25 40% [20–60] | 9/10 90% [70–100] | 0.80 | 7/25 28% [12–44] | 6/25 24% [8–40] | 0.0 (0/42) | 0.0 (0/65) | 0/25 | 24/25 96% [88–100] | 2 |
| order_lookup | 25 | 2/3 67% [0–100] | 2/2 100% [100–100] | 0.42 | 13/25 52% [32–72] | 10/25 40% [20–60] | 0.0 (0/61) | 0.0 (0/81) | 0/25 | 20/25 80% [64–96] | 5 |
| returns | 15 | 0/2 0% [0–0] | - | - | 4/15 27% [7–47] | 4/15 27% [7–47] | 0.0 (0/46) | 0.0 (0/56) | 0/15 | 11/15 73% [53–93] | 6 |
| unanswerable | 15 | 1/1 100% [100–100] | 0/1 0% [0–0] | 0.00 | 4/15 27% [7–53] | 4/15 27% [7–53] | 0.0 (0/34) | 0.0 (0/43) | 2/15 | 6/15 40% [13–67] | 6 |
| escalation | 10 | - | - | - | 1/10 10% [0–30] | 1/10 10% [0–30] | 0.0 (0/30) | 0.0 (0/37) | 0/10 | 4/10 40% [10–70] | 5 |
| adversarial | 12 | - | - | - | 6/12 50% [25–75] | 5/12 42% [17–67] | 0.0 (0/19) | 0.0 (0/31) | 4/12 | 10/12 83% [58–100] | 1 |
| old_policy | 5 | 4/5 80% [40–100] | 2/4 50% [0–100] | 0.50 | 1/5 20% [0–60] | 1/5 20% [0–60] | 0.0 (0/14) | 0.0 (0/18) | 0/5 | 5/5 100% [100–100] | 1 |
| **all** | 107 | 17/36 47% [31–64] | 13/17 76% [53–94] | 0.64 | 36/107 34% [25–42] | 31/107 29% [21–37] | 0.0 (0/246) | 0.0 (0/331) | 6/107 | 80/107 75% [66–83] | 26 |

| Category | n | grounding issues / 100 replies | facts | no forbidden | privacy violations | return claimed done | customer turns | tokens / conversation | latency p50 / p95 (s) |
|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 0.0 (0/25) | 6/25 24% [8–40] | 24/25 96% [88–100] | 0 | 0 | 1.0 | 3,859 | 2.04 / 5.30 |
| order_lookup | 25 | 0.0 (0/25) | 7/25 28% [12–48] | 25/25 100% [100–100] | 0 | 0 | 1.0 | 5,209 | 3.79 / 8.90 |
| returns | 15 | 6.2 (1/16) | 6/15 40% [20–67] | 15/15 100% [100–100] | 0 | 0 | 1.1 | 6,096 | 4.34 / 5.79 |
| unanswerable | 15 | 13.3 (2/15) | 14/15 93% [80–100] | 14/15 93% [80–100] | 0 | 0 | 1.0 | 4,547 | 4.62 / 12.74 |
| escalation | 10 | 8.3 (1/12) | 5/10 50% [20–80] | 10/10 100% [100–100] | 0 | 0 | 1.2 | 5,734 | 3.23 / 10.49 |
| adversarial | 12 | 23.1 (3/13) | 12/12 100% [100–100] | 11/12 92% [75–100] | 0 | 0 | 1.1 | 3,843 | 2.64 / 8.39 |
| old_policy | 5 | 60.0 (3/5) | 2/5 40% [0–80] | 5/5 100% [100–100] | 0 | 0 | 1.0 | 5,916 | 4.96 / 7.03 |
| **all** | 107 | 9.0 (10/111) | 52/107 49% [39–58] | 104/107 97% [94–100] | 0 | 0 | 1.0 | 4,854 | 3.21 / 8.77 |

Tool confusion (expected against called):

| expected ↓ / called → | list | status | tracking | search | propose | escalate | (none) |
|---|---|---|---|---|---|---|---|
| list | **37** | · | · | · | · | · | · |
| status | 1 | **25** | · | · | · | · | 1 |
| tracking | 1 | 2 | **22** | · | · | · | 1 |
| search | 22 | · | 1 | **20** | · | · | 3 |
| propose | · | · | · | · | **10** | · | 2 |
| escalate | 6 | 3 | 1 | 1 | 1 | **6** | 5 |
| (none) | 15 | 30 | 15 | 12 | 6 | 9 | · |
