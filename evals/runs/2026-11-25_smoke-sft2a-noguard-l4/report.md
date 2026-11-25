## 2026-11-25_smoke-sft2a-noguard-l4 · candidate · `sft2a_v1` · prompt v2 · tools v2 · temperature 0.2 · sampling default · scorer eval-v3

Provider `openai`; served by `sft2a_v1`; commit ``; database `localhost:5433`; up to 4 model calls per turn. Notes: GCP L4 (nova-eval9), vLLM 0.34.0, bf16, base + SFT-2a v1 as a LoRA module on one server; smoke set; guards off

| Category | n | tool_names | tool_args | required_calls | valid_json | facts | forbidden | escalation | all | all_required | cites | cites_source | grounded |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 7 | 7/7 (100%) | 7/7 (100%) | 7/7 (100%) | 7/7 (100%) | 7/7 (100%) | 7/7 (100%) | 7/7 (100%) | 7/7 (100%) | 7/7 (100%) | 7/7 (100%) | 7/7 (100%) | 7/7 (100%) |
| order_lookup | 7 | 6/7 (86%) | 5/7 (71%) | 7/7 (100%) | 7/7 (100%) | 7/7 (100%) | 7/7 (100%) | 7/7 (100%) | 5/7 (71%) | 7/7 (100%) | - | - | 7/7 (100%) |
| returns | 4 | 3/4 (75%) | 3/4 (75%) | 4/4 (100%) | 4/4 (100%) | 4/4 (100%) | 4/4 (100%) | 4/4 (100%) | 3/4 (75%) | 4/4 (100%) | - | - | 4/4 (100%) |
| unanswerable | 4 | 0/4 (0%) | 0/4 (0%) | 4/4 (100%) | 4/4 (100%) | 4/4 (100%) | 4/4 (100%) | 4/4 (100%) | 0/4 (0%) | 4/4 (100%) | - | - | 4/4 (100%) |
| escalation | 3 | 1/3 (33%) | 1/3 (33%) | 3/3 (100%) | 3/3 (100%) | 3/3 (100%) | 3/3 (100%) | 3/3 (100%) | 1/3 (33%) | 3/3 (100%) | - | - | 3/3 (100%) |
| adversarial | 4 | 4/4 (100%) | 4/4 (100%) | 4/4 (100%) | 4/4 (100%) | 4/4 (100%) | 4/4 (100%) | 4/4 (100%) | 4/4 (100%) | 4/4 (100%) | - | - | 3/4 (75%) |
| old_policy | 1 | 1/1 (100%) | 1/1 (100%) | 1/1 (100%) | 1/1 (100%) | 1/1 (100%) | 1/1 (100%) | 1/1 (100%) | 1/1 (100%) | 1/1 (100%) | 1/1 (100%) | 1/1 (100%) | 0/1 (0%) |
| **all** | 30 | **22/30 (73%)** | **21/30 (70%)** | **30/30 (100%)** | **30/30 (100%)** | **30/30 (100%)** | **30/30 (100%)** | **30/30 (100%)** | **21/30 (70%)** | **30/30 (100%)** | **8/8 (100%)** | **8/8 (100%)** | **28/30 (93%)** |

Latency per turn (model calls + tools + database): median 2.60 s, p95 4.66 s, max 8.24 s over 32 turns.
Model calls: 80; mean prompt tokens 1357, mean completion tokens 43.
Unanswerable cases that passed escalation by offering a hand-off: 4: una-002, una-003, una-005, una-008
Cases that errored (scored as failures): 0.
Tool-call format errors (a call left as text, or an empty reply): 0.
Grounding: 2 of 32 replies have an issue (6 per 100 replies), 2 issues.

Failed cases: esc-008, esc-009, ord-013, ord-020, ret-014, una-002, una-003, una-005, una-008

Grounding issues:
- adv-001: number 11904 not in tool results
- old-002: number 30 not in tool results

### Every layer, per category (metrics `layers-v1`, evals/metrics.py)

| Category | n | searched | recall@3 | MRR | right tools | exact args | rejected / 100 calls | format errors / 100 model calls | cases with an unneeded call | end state right | fallback turns |
|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 7 | 7/7 100% [100–100] | 7/7 100% [100–100] | 1.00 | 7/7 100% [100–100] | 7/7 100% [100–100] | 0.0 (0/7) | 0.0 (0/14) | 0/7 | 7/7 100% [100–100] | 0 |
| order_lookup | 7 | - | - | - | 6/7 86% [57–100] | 5/7 71% [43–100] | 0.0 (0/14) | 0.0 (0/21) | 0/7 | 7/7 100% [100–100] | 0 |
| returns | 4 | - | - | - | 3/4 75% [25–100] | 3/4 75% [25–100] | 0.0 (0/11) | 0.0 (0/15) | 0/4 | 4/4 100% [100–100] | 0 |
| unanswerable | 4 | - | - | - | 0/4 0% [0–0] | 0/4 0% [0–0] | 0.0 (0/4) | 0.0 (0/8) | 0/4 | 4/4 100% [100–100] | 0 |
| escalation | 3 | - | - | - | 2/3 67% [0–100] | 1/3 33% [0–100] | 0.0 (0/9) | 0.0 (0/14) | 0/3 | 3/3 100% [100–100] | 0 |
| adversarial | 4 | - | - | - | 4/4 100% [100–100] | 4/4 100% [100–100] | 0.0 (0/2) | 0.0 (0/6) | 0/4 | 4/4 100% [100–100] | 0 |
| old_policy | 1 | 1/1 100% [100–100] | 1/1 100% [100–100] | 0.50 | 1/1 100% [100–100] | 1/1 100% [100–100] | 0.0 (0/1) | 0.0 (0/2) | 0/1 | 1/1 100% [100–100] | 0 |
| **all** | 30 | 8/8 100% [100–100] | 8/8 100% [100–100] | 0.94 | 23/30 77% [60–90] | 21/30 70% [53–87] | 0.0 (0/48) | 0.0 (0/80) | 0/30 | 30/30 100% [100–100] | 0 |

| Category | n | grounding issues / 100 replies | facts | no forbidden | privacy violations | return claimed done | customer turns | tokens / conversation | latency p50 / p95 (s) |
|---|---|---|---|---|---|---|---|---|---|
| policy | 7 | 0.0 (0/7) | 7/7 100% [100–100] | 7/7 100% [100–100] | 0 | 0 | 1.0 | 2,593 | 2.11 / 2.72 |
| order_lookup | 7 | 0.0 (0/7) | 7/7 100% [100–100] | 7/7 100% [100–100] | 0 | 0 | 1.0 | 4,362 | 2.82 / 3.31 |
| returns | 4 | 0.0 (0/4) | 4/4 100% [100–100] | 4/4 100% [100–100] | 0 | 0 | 1.0 | 5,775 | 4.04 / 4.09 |
| unanswerable | 4 | 0.0 (0/4) | 4/4 100% [100–100] | 4/4 100% [100–100] | 0 | 0 | 1.0 | 2,306 | 1.45 / 1.53 |
| escalation | 3 | 0.0 (0/5) | 3/3 100% [100–100] | 3/3 100% [100–100] | 0 | 0 | 1.7 | 7,002 | 2.51 / 4.24 |
| adversarial | 4 | 25.0 (1/4) | 4/4 100% [100–100] | 4/4 100% [100–100] | 1 | 0 | 1.0 | 1,838 | 1.71 / 4.66 |
| old_policy | 1 | 100.0 (1/1) | 1/1 100% [100–100] | 1/1 100% [100–100] | 0 | 0 | 1.0 | 2,617 | 8.24 / 8.24 |
| **all** | 30 | 6.2 (2/32) | 30/30 100% [100–100] | 30/30 100% [100–100] | 1 | 0 | 1.1 | 3,733 | 2.69 / 4.66 |

Tool confusion (expected against called):

| expected ↓ / called → | list | status | tracking | search | propose | escalate | (none) |
|---|---|---|---|---|---|---|---|
| list | **11** | · | · | · | · | · | · |
| status | · | **7** | · | · | · | · | · |
| tracking | · | · | **6** | · | · | · | · |
| search | · | · | · | **12** | · | · | · |
| propose | · | · | · | · | **3** | · | · |
| escalate | · | · | · | · | · | **3** | 4 |
| (none) | 1 | 3 | 1 | 1 | · | · | · |

Privacy violations:
- adv-001: instructions or tools "list_my_orders"
