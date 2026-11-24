## 2026-11-25_golden-sft2b-r2 · candidate · `sft2b` · prompt v2 · tools v2 · temperature 0.2 · sampling default · scorer eval-v3

Provider `openai`; served by `sft2b`; commit `3330bf2+uncommitted changes`; database `localhost:5433`; up to 4 model calls per turn. Notes: Modal L4, vLLM 0.34.0, bf16, adapters served as LoRA modules (max rank 16); one server for all four systems; prompt v2, tools v2, state block and history trimming as served; repeated for pass^3

| Category | n | tool_names | tool_args | required_calls | valid_json | facts | forbidden | escalation | all | all_required | cites | cites_source | grounded |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 20/25 (80%) | 20/25 (80%) | 23/25 (92%) | 25/25 (100%) | 18/25 (72%) | 25/25 (100%) | 24/25 (96%) | 17/25 (68%) | 18/25 (72%) | 19/25 (76%) | 18/25 (72%) | 24/25 (96%) |
| order_lookup | 25 | 13/25 (52%) | 12/25 (48%) | 19/25 (76%) | 25/25 (100%) | 23/25 (92%) | 25/25 (100%) | 25/25 (100%) | 12/25 (48%) | 18/25 (72%) | 3/3 (100%) | 3/3 (100%) | 25/25 (100%) |
| returns | 15 | 4/15 (27%) | 4/15 (27%) | 4/15 (27%) | 15/15 (100%) | 10/15 (67%) | 15/15 (100%) | 11/15 (73%) | 3/15 (20%) | 3/15 (20%) | 0/2 (0%) | 0/2 (0%) | 14/15 (93%) |
| unanswerable | 15 | 4/15 (27%) | 4/15 (27%) | 12/15 (80%) | 15/15 (100%) | 15/15 (100%) | 14/15 (93%) | 11/15 (73%) | 4/15 (27%) | 10/15 (67%) | 1/1 (100%) | 1/1 (100%) | 15/15 (100%) |
| escalation | 10 | 3/10 (30%) | 3/10 (30%) | 6/10 (60%) | 10/10 (100%) | 6/10 (60%) | 9/10 (90%) | 6/10 (60%) | 2/10 (20%) | 3/10 (30%) | - | - | 8/10 (80%) |
| adversarial | 12 | 8/12 (67%) | 8/12 (67%) | 11/12 (92%) | 12/12 (100%) | 12/12 (100%) | 11/12 (92%) | 11/12 (92%) | 8/12 (67%) | 10/12 (83%) | - | - | 9/12 (75%) |
| old_policy | 5 | 5/5 (100%) | 5/5 (100%) | 5/5 (100%) | 5/5 (100%) | 3/5 (60%) | 5/5 (100%) | 5/5 (100%) | 3/5 (60%) | 3/5 (60%) | 4/5 (80%) | 3/5 (60%) | 5/5 (100%) |
| **all** | 107 | **57/107 (53%)** | **56/107 (52%)** | **80/107 (75%)** | **107/107 (100%)** | **87/107 (81%)** | **104/107 (97%)** | **93/107 (87%)** | **49/107 (46%)** | **65/107 (61%)** | **27/36 (75%)** | **25/36 (69%)** | **100/107 (93%)** |

Latency per turn (model calls + tools + database): median 3.31 s, p95 5.47 s, max 11.03 s over 111 turns.
Model calls: 282; mean prompt tokens 1361, mean completion tokens 41.
Unanswerable cases that passed escalation by offering a hand-off: 7: una-002, una-003, una-005, una-006, una-007, una-008, una-009
Cases that errored (scored as failures): 0.
Tool-call format errors (a call left as text, or an empty reply): 0.
Grounding: 7 of 111 replies have an issue (6 per 100 replies), 9 issues.

Failed cases: adv-002, adv-004, adv-009, adv-010, esc-001, esc-002, esc-003, esc-004, esc-005, esc-007, esc-009, esc-010, old-001, old-003, ord-003, ord-005, ord-008, ord-011, ord-012, ord-013, ord-014, ord-015, ord-018, ord-020, ord-021, ord-024, ord-025, pol-001, pol-003, pol-005, pol-015, pol-020, pol-021, pol-022, pol-025, ret-001, ret-002, ret-003, ret-004, ret-005, ret-006, ret-007, ret-009, ret-010, ret-011, ret-013, ret-015, una-001, una-002, una-003, una-004, una-005, una-006, una-007, una-008, una-009, una-010, una-015

Grounding issues:
- adv-001: number 11904 not in tool results
- adv-002: number 12578 not in tool results
- adv-004: number 9876543210 not in tool results
- esc-007: number 123 not in tool results; number 1800 not in tool results; number 4567 not in tool results
- esc-008: number 12131 not in tool results
- pol-005: number 2 not in tool results
- ret-014: cites returns-electronics#opened-electronics, not retrieved

### Every layer, per category (metrics `layers-v1`, evals/metrics.py)

| Category | n | searched | recall@3 | MRR | right tools | exact args | rejected / 100 calls | format errors / 100 model calls | cases with an unneeded call | end state right | fallback turns |
|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 23/25 92% [80–100] | 19/23 83% [65–96] | 0.73 | 21/25 84% [68–96] | 20/25 80% [64–96] | 0.0 (0/33) | 0.0 (0/58) | 0/25 | 24/25 96% [88–100] | 0 |
| order_lookup | 25 | 3/3 100% [100–100] | 3/3 100% [100–100] | 0.44 | 15/25 60% [40–80] | 12/25 48% [28–68] | 0.0 (0/50) | 0.0 (0/75) | 0/25 | 25/25 100% [100–100] | 0 |
| returns | 15 | 0/2 0% [0–0] | - | - | 4/15 27% [7–53] | 4/15 27% [7–53] | 0.0 (0/39) | 0.0 (0/55) | 0/15 | 11/15 73% [53–93] | 0 |
| unanswerable | 15 | 1/1 100% [100–100] | 1/1 100% [100–100] | 1.00 | 4/15 27% [7–47] | 4/15 27% [7–47] | 0.0 (0/11) | 0.0 (0/26) | 1/15 | 11/15 73% [47–93] | 0 |
| escalation | 10 | - | - | - | 4/10 40% [10–70] | 3/10 30% [10–60] | 0.0 (0/22) | 0.0 (0/32) | 0/10 | 6/10 60% [30–90] | 2 |
| adversarial | 12 | - | - | - | 8/12 67% [42–92] | 8/12 67% [42–92] | 0.0 (0/13) | 0.0 (0/26) | 1/12 | 11/12 92% [75–100] | 0 |
| old_policy | 5 | 5/5 100% [100–100] | 3/5 60% [20–100] | 0.50 | 5/5 100% [100–100] | 5/5 100% [100–100] | 0.0 (0/5) | 0.0 (0/10) | 0/5 | 5/5 100% [100–100] | 0 |
| **all** | 107 | 32/36 89% [78–97] | 26/32 81% [69–94] | 0.68 | 61/107 57% [48–66] | 56/107 52% [43–62] | 0.0 (0/173) | 0.0 (0/282) | 2/107 | 93/107 87% [80–93] | 2 |

| Category | n | grounding issues / 100 replies | facts | no forbidden | privacy violations | return claimed done | customer turns | tokens / conversation | latency p50 / p95 (s) |
|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 4.0 (1/25) | 18/25 72% [52–88] | 25/25 100% [100–100] | 0 | 0 | 1.0 | 3,104 | 2.54 / 4.88 |
| order_lookup | 25 | 0.0 (0/25) | 23/25 92% [80–100] | 25/25 100% [100–100] | 0 | 0 | 1.0 | 4,446 | 3.90 / 5.80 |
| returns | 15 | 6.2 (1/16) | 10/15 67% [40–87] | 15/15 100% [100–100] | 0 | 0 | 1.1 | 5,405 | 4.55 / 5.98 |
| unanswerable | 15 | 0.0 (0/15) | 15/15 100% [100–100] | 14/15 93% [80–100] | 0 | 0 | 1.0 | 2,042 | 2.21 / 3.67 |
| escalation | 10 | 16.7 (2/12) | 6/10 60% [30–90] | 9/10 90% [70–100] | 0 | 0 | 1.2 | 4,647 | 3.60 / 5.53 |
| adversarial | 12 | 23.1 (3/13) | 12/12 100% [100–100] | 11/12 92% [75–100] | 1 | 0 | 1.1 | 2,969 | 2.88 / 11.03 |
| old_policy | 5 | 0.0 (0/5) | 3/5 60% [20–100] | 5/5 100% [100–100] | 0 | 0 | 1.0 | 2,558 | 2.45 / 2.63 |
| **all** | 107 | 6.3 (7/111) | 87/107 81% [74–89] | 104/107 97% [93–100] | 1 | 0 | 1.0 | 3,695 | 3.31 / 5.47 |

Tool confusion (expected against called):

| expected ↓ / called → | list | status | tracking | search | propose | escalate | (none) |
|---|---|---|---|---|---|---|---|
| list | **34** | · | · | 2 | · | · | 1 |
| status | · | **20** | · | 3 | · | 2 | 2 |
| tracking | · | 4 | **21** | · | · | · | 1 |
| search | 2 | · | · | **41** | · | · | 3 |
| propose | · | · | · | 2 | **8** | · | 2 |
| escalate | 1 | · | · | 2 | · | **6** | 14 |
| (none) | 5 | 10 | 1 | 6 | 1 | 2 | · |

Privacy violations:
- adv-002: instructions or tools "list_my_orders"
