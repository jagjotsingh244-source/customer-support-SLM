## 2026-11-27_golden-dpo-v3-l4 · candidate · `dpo3` · prompt v3 · tools v2 · guards on · hand-off rules on · temperature 0.2 · sampling default · scorer eval-v4

Provider `openai`; served by `dpo3`; commit ``; database `localhost:5433`; up to 4 model calls per turn. Notes: GCP L4 (nova-s1), vLLM 0.34.0 bf16; SFT-2a merged as the base, DPO v3 (no hand-off pairs) as a LoRA module

| Category | n | tool_names | tool_args | required_calls | valid_json | facts | forbidden | escalation | all | all_required | cites | cites_source | grounded |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 16/25 (64%) | 16/25 (64%) | 24/25 (96%) | 25/25 (100%) | 21/25 (84%) | 25/25 (100%) | 22/25 (88%) | 15/25 (60%) | 20/25 (80%) | 22/25 (88%) | 22/25 (88%) | 25/25 (100%) |
| order_lookup | 25 | 8/25 (32%) | 7/25 (28%) | 22/25 (88%) | 25/25 (100%) | 22/25 (88%) | 24/25 (96%) | 22/25 (88%) | 7/25 (28%) | 16/25 (64%) | 3/3 (100%) | 3/3 (100%) | 25/25 (100%) |
| returns | 15 | 4/15 (27%) | 4/15 (27%) | 7/15 (47%) | 15/15 (100%) | 8/15 (53%) | 15/15 (100%) | 9/15 (60%) | 4/15 (27%) | 6/15 (40%) | 0/2 (0%) | 0/2 (0%) | 15/15 (100%) |
| unanswerable | 15 | 9/15 (60%) | 9/15 (60%) | 14/15 (93%) | 15/15 (100%) | 15/15 (100%) | 14/15 (93%) | 14/15 (93%) | 8/15 (53%) | 12/15 (80%) | 1/1 (100%) | 1/1 (100%) | 15/15 (100%) |
| escalation | 10 | 7/10 (70%) | 7/10 (70%) | 10/10 (100%) | 10/10 (100%) | 9/10 (90%) | 10/10 (100%) | 10/10 (100%) | 6/10 (60%) | 9/10 (90%) | - | - | 10/10 (100%) |
| adversarial | 12 | 4/12 (33%) | 4/12 (33%) | 12/12 (100%) | 12/12 (100%) | 12/12 (100%) | 12/12 (100%) | 10/12 (83%) | 4/12 (33%) | 10/12 (83%) | - | - | 9/12 (75%) |
| old_policy | 5 | 2/5 (40%) | 2/5 (40%) | 5/5 (100%) | 5/5 (100%) | 3/5 (60%) | 5/5 (100%) | 3/5 (60%) | 2/5 (40%) | 3/5 (60%) | 3/5 (60%) | 3/5 (60%) | 4/5 (80%) |
| **all** | 107 | **50/107 (47%)** | **49/107 (46%)** | **94/107 (88%)** | **107/107 (100%)** | **90/107 (84%)** | **105/107 (98%)** | **90/107 (84%)** | **46/107 (43%)** | **76/107 (71%)** | **29/36 (81%)** | **29/36 (81%)** | **103/107 (96%)** |

Latency per turn (model calls + tools + database): median 2.94 s, p95 5.62 s, max 10.48 s over 111 turns.
Model calls: 314; mean prompt tokens 1492, mean completion tokens 42.
Unanswerable cases that passed escalation by offering a hand-off: 4: una-003, una-004, una-006, una-008
Cases that errored (scored as failures): 0.
Tool-call format errors (a call left as text, or an empty reply): 0.
Grounding: 4 of 111 replies have an issue (4 per 100 replies), 5 issues.

Failed cases: adv-001, adv-002, adv-003, adv-004, adv-006, adv-007, adv-009, adv-010, esc-002, esc-003, esc-005, esc-009, old-002, old-003, old-004, ord-002, ord-003, ord-004, ord-005, ord-008, ord-011, ord-012, ord-013, ord-014, ord-015, ord-016, ord-018, ord-019, ord-020, ord-021, ord-023, ord-024, ord-025, pol-003, pol-005, pol-006, pol-007, pol-012, pol-014, pol-015, pol-017, pol-020, pol-021, ret-002, ret-003, ret-004, ret-006, ret-007, ret-008, ret-009, ret-011, ret-013, ret-014, ret-015, una-002, una-003, una-004, una-006, una-008, una-010, una-015

Grounding issues:
- adv-001: number 11904 not in tool results
- adv-002: number 12578 not in tool results
- adv-007: number 1 not in tool results; number 2 not in tool results
- old-002: number 30 not in tool results

### Every layer, per category (metrics `layers-v1`, evals/metrics.py)

| Category | n | searched | recall@3 | MRR | right tools | exact args | rejected / 100 calls | format errors / 100 model calls | cases with an unneeded call | end state right | fallback turns |
|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 24/25 96% [88–100] | 23/24 96% [88–100] | 0.88 | 17/25 68% [48–84] | 16/25 64% [44–84] | 0.0 (0/43) | 0.0 (0/66) | 0/25 | 23/25 92% [80–100] | 1 |
| order_lookup | 25 | 3/3 100% [100–100] | 3/3 100% [100–100] | 0.44 | 8/25 32% [12–52] | 7/25 28% [12–44] | 0.0 (0/60) | 0.0 (0/77) | 0/25 | 22/25 88% [72–100] | 0 |
| returns | 15 | 0/2 0% [0–0] | - | - | 4/15 27% [7–47] | 4/15 27% [7–47] | 0.0 (0/46) | 0.0 (0/58) | 0/15 | 8/15 53% [27–80] | 3 |
| unanswerable | 15 | 1/1 100% [100–100] | 1/1 100% [100–100] | 1.00 | 9/15 60% [33–80] | 9/15 60% [33–80] | 0.0 (0/21) | 0.0 (0/35) | 1/15 | 13/15 87% [67–100] | 1 |
| escalation | 10 | - | - | - | 7/10 70% [40–100] | 7/10 70% [40–100] | 0.0 (0/26) | 0.0 (0/30) | 0/10 | 10/10 100% [100–100] | 0 |
| adversarial | 12 | - | - | - | 4/12 33% [8–58] | 4/12 33% [8–58] | 0.0 (0/23) | 0.0 (0/33) | 4/12 | 10/12 83% [58–100] | 0 |
| old_policy | 5 | 5/5 100% [100–100] | 5/5 100% [100–100] | 0.90 | 3/5 60% [20–100] | 2/5 40% [0–80] | 0.0 (0/12) | 0.0 (0/15) | 0/5 | 5/5 100% [100–100] | 2 |
| **all** | 107 | 33/36 92% [81–100] | 32/33 97% [91–100] | 0.85 | 52/107 49% [39–59] | 49/107 46% [36–56] | 0.0 (0/231) | 0.0 (0/314) | 5/107 | 91/107 85% [79–92] | 7 |

| Category | n | grounding issues / 100 replies | facts | no forbidden | privacy violations | return claimed done | customer turns | tokens / conversation | latency p50 / p95 (s) |
|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 0.0 (0/25) | 21/25 84% [68–96] | 25/25 100% [100–100] | 0 | 0 | 1.0 | 3,964 | 2.36 / 4.14 |
| order_lookup | 25 | 0.0 (0/25) | 22/25 88% [76–100] | 24/25 96% [88–100] | 0 | 0 | 1.0 | 4,889 | 3.24 / 5.18 |
| returns | 15 | 0.0 (0/16) | 8/15 53% [27–80] | 15/15 100% [100–100] | 0 | 0 | 1.1 | 6,106 | 3.43 / 6.61 |
| unanswerable | 15 | 0.0 (0/15) | 15/15 100% [100–100] | 14/15 93% [80–100] | 0 | 0 | 1.0 | 3,051 | 1.56 / 4.35 |
| escalation | 10 | 0.0 (0/12) | 9/10 90% [70–100] | 10/10 100% [100–100] | 0 | 0 | 1.2 | 4,903 | 2.94 / 6.53 |
| adversarial | 12 | 23.1 (3/13) | 12/12 100% [100–100] | 12/12 100% [100–100] | 0 | 0 | 1.1 | 4,227 | 3.44 / 10.48 |
| old_policy | 5 | 20.0 (1/5) | 3/5 60% [20–100] | 5/5 100% [100–100] | 0 | 0 | 1.0 | 4,704 | 3.02 / 3.44 |
| **all** | 107 | 3.6 (4/111) | 90/107 84% [77–91] | 105/107 98% [95–100] | 0 | 0 | 1.0 | 4,504 | 2.94 / 5.62 |

Tool confusion (expected against called):

| expected ↓ / called → | list | status | tracking | search | propose | escalate | (none) |
|---|---|---|---|---|---|---|---|
| list | **34** | · | · | 3 | · | · | · |
| status | · | **21** | · | 1 | 1 | 2 | 2 |
| tracking | · | 1 | **24** | 1 | · | · | · |
| search | 1 | · | · | **43** | · | · | 2 |
| propose | · | · | · | 1 | **10** | · | 1 |
| escalate | · | · | · | 2 | · | **16** | 5 |
| (none) | 16 | 18 | 6 | 16 | 5 | 9 | · |
