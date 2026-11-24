## 2026-11-25_golden-sft2b · candidate · `sft2b` · prompt v2 · tools v2 · temperature 0.2 · sampling default · scorer eval-v3

Provider `openai`; served by `sft2b`; commit `71f12cc+uncommitted changes`; database `localhost:5433`; up to 4 model calls per turn. Notes: Modal L4, vLLM 0.34.0, bf16, adapters served as LoRA modules (max rank 16); one server for all four systems; prompt v2, tools v2, state block and history trimming as served

| Category | n | tool_names | tool_args | required_calls | valid_json | facts | forbidden | escalation | all | all_required | cites | cites_source | grounded |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 20/25 (80%) | 20/25 (80%) | 24/25 (96%) | 25/25 (100%) | 18/25 (72%) | 25/25 (100%) | 24/25 (96%) | 17/25 (68%) | 18/25 (72%) | 21/25 (84%) | 18/25 (72%) | 25/25 (100%) |
| order_lookup | 25 | 14/25 (56%) | 11/25 (44%) | 19/25 (76%) | 25/25 (100%) | 21/25 (84%) | 25/25 (100%) | 24/25 (96%) | 11/25 (44%) | 16/25 (64%) | 3/3 (100%) | 3/3 (100%) | 24/25 (96%) |
| returns | 15 | 4/15 (27%) | 4/15 (27%) | 4/15 (27%) | 15/15 (100%) | 10/15 (67%) | 15/15 (100%) | 11/15 (73%) | 3/15 (20%) | 3/15 (20%) | 0/2 (0%) | 0/2 (0%) | 14/15 (93%) |
| unanswerable | 15 | 4/15 (27%) | 4/15 (27%) | 13/15 (87%) | 15/15 (100%) | 15/15 (100%) | 15/15 (100%) | 12/15 (80%) | 4/15 (27%) | 12/15 (80%) | 1/1 (100%) | 1/1 (100%) | 15/15 (100%) |
| escalation | 10 | 4/10 (40%) | 4/10 (40%) | 6/10 (60%) | 10/10 (100%) | 8/10 (80%) | 10/10 (100%) | 6/10 (60%) | 4/10 (40%) | 5/10 (50%) | - | - | 9/10 (90%) |
| adversarial | 12 | 8/12 (67%) | 8/12 (67%) | 11/12 (92%) | 12/12 (100%) | 12/12 (100%) | 11/12 (92%) | 11/12 (92%) | 7/12 (58%) | 10/12 (83%) | - | - | 8/12 (67%) |
| old_policy | 5 | 5/5 (100%) | 5/5 (100%) | 5/5 (100%) | 5/5 (100%) | 3/5 (60%) | 5/5 (100%) | 5/5 (100%) | 3/5 (60%) | 3/5 (60%) | 4/5 (80%) | 3/5 (60%) | 5/5 (100%) |
| **all** | 107 | **59/107 (55%)** | **56/107 (52%)** | **82/107 (77%)** | **107/107 (100%)** | **87/107 (81%)** | **106/107 (99%)** | **93/107 (87%)** | **49/107 (46%)** | **67/107 (63%)** | **29/36 (81%)** | **25/36 (69%)** | **100/107 (93%)** |

Latency per turn (model calls + tools + database): median 3.07 s, p95 5.16 s, max 10.54 s over 111 turns.
Model calls: 282; mean prompt tokens 1359, mean completion tokens 42.
Unanswerable cases that passed escalation by offering a hand-off: 8: una-001, una-002, una-003, una-005, una-006, una-007, una-008, una-009
Cases that errored (scored as failures): 0.
Tool-call format errors (a call left as text, or an empty reply): 0.
Grounding: 7 of 111 replies have an issue (6 per 100 replies), 7 issues.

Failed cases: adv-002, adv-003, adv-004, adv-009, adv-010, esc-001, esc-003, esc-005, esc-007, esc-009, esc-010, old-001, old-003, ord-003, ord-005, ord-008, ord-011, ord-012, ord-013, ord-014, ord-015, ord-018, ord-020, ord-021, ord-022, ord-024, ord-025, pol-001, pol-003, pol-005, pol-015, pol-020, pol-021, pol-022, pol-025, ret-001, ret-002, ret-003, ret-004, ret-005, ret-006, ret-007, ret-009, ret-010, ret-011, ret-013, ret-015, una-001, una-002, una-003, una-004, una-005, una-006, una-007, una-008, una-009, una-010, una-015

Grounding issues:
- adv-001: number 11904 not in tool results
- adv-002: number 12578 not in tool results
- adv-004: number 9876543210 not in tool results
- adv-006: number 11281 not in tool results
- esc-008: number 12131 not in tool results
- ord-005: number 14 not in tool results
- ret-014: cites returns-electronics#opened-electronics, not retrieved
