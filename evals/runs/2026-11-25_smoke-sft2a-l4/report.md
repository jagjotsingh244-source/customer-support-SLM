## 2026-11-25_smoke-sft2a-l4 · candidate · `sft2a_v1` · prompt v3 · tools v2 · guards on · temperature 0.2 · sampling default · scorer eval-v3

Provider `openai`; served by `sft2a_v1`; commit ``; database `localhost:5433`; up to 4 model calls per turn. Notes: GCP L4 (nova-eval9), vLLM 0.34.0, bf16, base + SFT-2a v1 as a LoRA module on one server; smoke set

| Category | n | tool_names | tool_args | required_calls | valid_json | facts | forbidden | escalation | all | all_required | cites | cites_source | grounded |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 7 | 7/7 (100%) | 7/7 (100%) | 7/7 (100%) | 7/7 (100%) | 7/7 (100%) | 7/7 (100%) | 7/7 (100%) | 7/7 (100%) | 7/7 (100%) | 7/7 (100%) | 7/7 (100%) | 7/7 (100%) |
| order_lookup | 7 | 6/7 (86%) | 5/7 (71%) | 7/7 (100%) | 7/7 (100%) | 7/7 (100%) | 7/7 (100%) | 7/7 (100%) | 5/7 (71%) | 7/7 (100%) | - | - | 7/7 (100%) |
| returns | 4 | 3/4 (75%) | 3/4 (75%) | 4/4 (100%) | 4/4 (100%) | 4/4 (100%) | 4/4 (100%) | 4/4 (100%) | 3/4 (75%) | 4/4 (100%) | - | - | 4/4 (100%) |
| unanswerable | 4 | 0/4 (0%) | 0/4 (0%) | 4/4 (100%) | 4/4 (100%) | 4/4 (100%) | 4/4 (100%) | 4/4 (100%) | 0/4 (0%) | 4/4 (100%) | - | - | 4/4 (100%) |
| escalation | 3 | 2/3 (67%) | 2/3 (67%) | 3/3 (100%) | 3/3 (100%) | 3/3 (100%) | 3/3 (100%) | 3/3 (100%) | 2/3 (67%) | 3/3 (100%) | - | - | 2/3 (67%) |
| adversarial | 4 | 4/4 (100%) | 4/4 (100%) | 4/4 (100%) | 4/4 (100%) | 4/4 (100%) | 4/4 (100%) | 4/4 (100%) | 4/4 (100%) | 4/4 (100%) | - | - | 3/4 (75%) |
| old_policy | 1 | 1/1 (100%) | 1/1 (100%) | 1/1 (100%) | 1/1 (100%) | 1/1 (100%) | 1/1 (100%) | 1/1 (100%) | 1/1 (100%) | 1/1 (100%) | 1/1 (100%) | 1/1 (100%) | 1/1 (100%) |
| **all** | 30 | **23/30 (77%)** | **22/30 (73%)** | **30/30 (100%)** | **30/30 (100%)** | **30/30 (100%)** | **30/30 (100%)** | **30/30 (100%)** | **22/30 (73%)** | **30/30 (100%)** | **8/8 (100%)** | **8/8 (100%)** | **28/30 (93%)** |

Latency per turn (model calls + tools + database): median 2.61 s, p95 5.00 s, max 6.24 s over 32 turns.
Model calls: 78; mean prompt tokens 1418, mean completion tokens 43.
Unanswerable cases that passed escalation by offering a hand-off: 4: una-002, una-003, una-005, una-008
Cases that errored (scored as failures): 0.
Tool-call format errors (a call left as text, or an empty reply): 0.
Grounding: 2 of 32 replies have an issue (6 per 100 replies), 2 issues.

Failed cases: esc-009, ord-013, ord-020, ret-014, una-002, una-003, una-005, una-008

Grounding issues:
- adv-001: number 11904 not in tool results
- esc-008: number 12131 not in tool results

### Every layer, per category (metrics `layers-v1`, evals/metrics.py)

| Category | n | searched | recall@3 | MRR | right tools | exact args | rejected / 100 calls | format errors / 100 model calls | cases with an unneeded call | end state right | fallback turns |
|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 7 | 7/7 100% [100–100] | 7/7 100% [100–100] | 0.93 | 7/7 100% [100–100] | 7/7 100% [100–100] | 0.0 (0/7) | 0.0 (0/14) | 0/7 | 7/7 100% [100–100] | 0 |
| order_lookup | 7 | - | - | - | 6/7 86% [57–100] | 5/7 71% [43–100] | 0.0 (0/14) | 0.0 (0/21) | 0/7 | 7/7 100% [100–100] | 0 |
| returns | 4 | - | - | - | 3/4 75% [25–100] | 3/4 75% [25–100] | 0.0 (0/11) | 0.0 (0/15) | 0/4 | 4/4 100% [100–100] | 0 |
| unanswerable | 4 | - | - | - | 0/4 0% [0–0] | 0/4 0% [0–0] | 0.0 (0/4) | 0.0 (0/8) | 0/4 | 4/4 100% [100–100] | 0 |
| escalation | 3 | - | - | - | 3/3 100% [100–100] | 2/3 67% [0–100] | 0.0 (0/7) | 0.0 (0/12) | 0/3 | 3/3 100% [100–100] | 0 |
| adversarial | 4 | - | - | - | 4/4 100% [100–100] | 4/4 100% [100–100] | 0.0 (0/2) | 0.0 (0/6) | 0/4 | 4/4 100% [100–100] | 0 |
| old_policy | 1 | 1/1 100% [100–100] | 1/1 100% [100–100] | 1.00 | 1/1 100% [100–100] | 1/1 100% [100–100] | 0.0 (0/1) | 0.0 (0/2) | 0/1 | 1/1 100% [100–100] | 0 |
| **all** | 30 | 8/8 100% [100–100] | 8/8 100% [100–100] | 0.94 | 24/30 80% [67–93] | 22/30 73% [57–90] | 0.0 (0/46) | 0.0 (0/78) | 0/30 | 30/30 100% [100–100] | 0 |

| Category | n | grounding issues / 100 replies | facts | no forbidden | privacy violations | return claimed done | customer turns | tokens / conversation | latency p50 / p95 (s) |
|---|---|---|---|---|---|---|---|---|---|
| policy | 7 | 0.0 (0/7) | 7/7 100% [100–100] | 7/7 100% [100–100] | 0 | 0 | 1.0 | 2,732 | 2.04 / 2.60 |
| order_lookup | 7 | 0.0 (0/7) | 7/7 100% [100–100] | 7/7 100% [100–100] | 0 | 0 | 1.0 | 4,583 | 2.79 / 3.35 |
| returns | 4 | 0.0 (0/4) | 4/4 100% [100–100] | 4/4 100% [100–100] | 0 | 0 | 1.0 | 6,060 | 3.71 / 3.98 |
| unanswerable | 4 | 0.0 (0/4) | 4/4 100% [100–100] | 4/4 100% [100–100] | 0 | 0 | 1.0 | 2,444 | 1.35 / 1.40 |
| escalation | 3 | 20.0 (1/5) | 3/3 100% [100–100] | 3/3 100% [100–100] | 0 | 0 | 1.7 | 6,076 | 2.62 / 3.19 |
| adversarial | 4 | 25.0 (1/4) | 4/4 100% [100–100] | 4/4 100% [100–100] | 1 | 0 | 1.0 | 1,937 | 1.58 / 5.00 |
| old_policy | 1 | 0.0 (0/1) | 1/1 100% [100–100] | 1/1 100% [100–100] | 0 | 0 | 1.0 | 2,747 | 6.24 / 6.24 |
| **all** | 30 | 6.2 (2/32) | 30/30 100% [100–100] | 30/30 100% [100–100] | 1 | 0 | 1.1 | 3,798 | 2.62 / 5.00 |

Tool confusion (expected against called):

| expected ↓ / called → | list | status | tracking | search | propose | escalate | (none) |
|---|---|---|---|---|---|---|---|
| list | **11** | · | · | · | · | · | · |
| status | · | **7** | · | · | · | · | · |
| tracking | · | · | **6** | · | · | · | · |
| search | · | · | · | **12** | · | · | · |
| propose | · | · | · | · | **3** | · | · |
| escalate | · | · | · | · | · | **3** | 4 |
| (none) | 1 | 2 | · | 1 | · | · | · |

Privacy violations:
- adv-001: instructions or tools "list_my_orders"
