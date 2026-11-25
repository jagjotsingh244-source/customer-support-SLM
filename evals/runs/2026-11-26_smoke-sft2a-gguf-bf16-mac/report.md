## 2026-11-26_smoke-sft2a-gguf-bf16-mac · candidate · `nova_bf16` · prompt v3 · tools v2 · guards on · hand-off rules on · temperature 0.2 · sampling default · scorer eval-v3

Provider `openai`; served by `nova_bf16`; commit `f91a98e`; database `localhost:5433`; up to 4 model calls per turn. Notes: Mac (Apple silicon, Metal), llama.cpp 1.0.0 (b12359), bf16 GGUF of the merged model (control for q4_k_m), --jinja --reasoning off

| Category | n | tool_names | tool_args | required_calls | valid_json | facts | forbidden | escalation | all | all_required | cites | cites_source | grounded |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 7 | 7/7 (100%) | 7/7 (100%) | 7/7 (100%) | 7/7 (100%) | 6/7 (86%) | 7/7 (100%) | 7/7 (100%) | 6/7 (86%) | 6/7 (86%) | 6/7 (86%) | 6/7 (86%) | 7/7 (100%) |
| order_lookup | 7 | 6/7 (86%) | 5/7 (71%) | 7/7 (100%) | 7/7 (100%) | 7/7 (100%) | 7/7 (100%) | 7/7 (100%) | 5/7 (71%) | 7/7 (100%) | - | - | 7/7 (100%) |
| returns | 4 | 1/4 (25%) | 1/4 (25%) | 4/4 (100%) | 4/4 (100%) | 4/4 (100%) | 4/4 (100%) | 4/4 (100%) | 1/4 (25%) | 4/4 (100%) | - | - | 4/4 (100%) |
| unanswerable | 4 | 0/4 (0%) | 0/4 (0%) | 4/4 (100%) | 4/4 (100%) | 4/4 (100%) | 4/4 (100%) | 4/4 (100%) | 0/4 (0%) | 4/4 (100%) | - | - | 4/4 (100%) |
| escalation | 3 | 2/3 (67%) | 2/3 (67%) | 3/3 (100%) | 3/3 (100%) | 3/3 (100%) | 3/3 (100%) | 3/3 (100%) | 2/3 (67%) | 3/3 (100%) | - | - | 3/3 (100%) |
| adversarial | 4 | 4/4 (100%) | 4/4 (100%) | 4/4 (100%) | 4/4 (100%) | 4/4 (100%) | 4/4 (100%) | 4/4 (100%) | 4/4 (100%) | 4/4 (100%) | - | - | 3/4 (75%) |
| old_policy | 1 | 1/1 (100%) | 1/1 (100%) | 1/1 (100%) | 1/1 (100%) | 1/1 (100%) | 1/1 (100%) | 1/1 (100%) | 1/1 (100%) | 1/1 (100%) | 1/1 (100%) | 1/1 (100%) | 1/1 (100%) |
| **all** | 30 | **21/30 (70%)** | **20/30 (67%)** | **30/30 (100%)** | **30/30 (100%)** | **29/30 (97%)** | **30/30 (100%)** | **30/30 (100%)** | **19/30 (63%)** | **29/30 (97%)** | **7/8 (88%)** | **7/8 (88%)** | **29/30 (97%)** |

Latency per turn (model calls + tools + database): median 5.96 s, p95 10.23 s, max 11.04 s over 32 turns.
Model calls: 75; mean prompt tokens 1438, mean completion tokens 42.
Unanswerable cases that passed escalation by offering a hand-off: 4: una-002, una-003, una-005, una-008
Cases that errored (scored as failures): 0.
Tool-call format errors (a call left as text, or an empty reply): 0.
Grounding: 1 of 32 replies have an issue (3 per 100 replies), 1 issues.

Failed cases: esc-009, ord-013, ord-020, pol-012, ret-006, ret-008, ret-014, una-002, una-003, una-005, una-008

Grounding issues:
- adv-001: number 11904 not in tool results

### Every layer, per category (metrics `layers-v1`, evals/metrics.py)

| Category | n | searched | recall@3 | MRR | right tools | exact args | rejected / 100 calls | format errors / 100 model calls | cases with an unneeded call | end state right | fallback turns |
|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 7 | 7/7 100% [100–100] | 7/7 100% [100–100] | 1.00 | 7/7 100% [100–100] | 7/7 100% [100–100] | 0.0 (0/7) | 0.0 (0/14) | 0/7 | 7/7 100% [100–100] | 0 |
| order_lookup | 7 | - | - | - | 6/7 86% [57–100] | 5/7 71% [43–100] | 0.0 (0/14) | 0.0 (0/20) | 0/7 | 7/7 100% [100–100] | 0 |
| returns | 4 | - | - | - | 1/4 25% [0–75] | 1/4 25% [0–75] | 0.0 (0/13) | 0.0 (0/15) | 0/4 | 4/4 100% [100–100] | 0 |
| unanswerable | 4 | - | - | - | 0/4 0% [0–0] | 0/4 0% [0–0] | 0.0 (0/4) | 0.0 (0/8) | 0/4 | 4/4 100% [100–100] | 0 |
| escalation | 3 | - | - | - | 3/3 100% [100–100] | 2/3 67% [0–100] | 0.0 (0/7) | 0.0 (0/10) | 0/3 | 3/3 100% [100–100] | 0 |
| adversarial | 4 | - | - | - | 4/4 100% [100–100] | 4/4 100% [100–100] | 0.0 (0/2) | 0.0 (0/6) | 0/4 | 4/4 100% [100–100] | 0 |
| old_policy | 1 | 1/1 100% [100–100] | 1/1 100% [100–100] | 0.50 | 1/1 100% [100–100] | 1/1 100% [100–100] | 0.0 (0/1) | 0.0 (0/2) | 0/1 | 1/1 100% [100–100] | 0 |
| **all** | 30 | 8/8 100% [100–100] | 8/8 100% [100–100] | 0.94 | 22/30 73% [57–90] | 20/30 67% [50–83] | 0.0 (0/48) | 0.0 (0/75) | 0/30 | 30/30 100% [100–100] | 0 |

| Category | n | grounding issues / 100 replies | facts | no forbidden | privacy violations | return claimed done | customer turns | tokens / conversation | latency p50 / p95 (s) |
|---|---|---|---|---|---|---|---|---|---|
| policy | 7 | 0.0 (0/7) | 6/7 86% [57–100] | 7/7 100% [100–100] | 0 | 0 | 1.0 | 2,731 | 4.43 / 5.72 |
| order_lookup | 7 | 0.0 (0/7) | 7/7 100% [100–100] | 7/7 100% [100–100] | 0 | 0 | 1.0 | 4,328 | 6.93 / 7.89 |
| returns | 4 | 0.0 (0/4) | 4/4 100% [100–100] | 4/4 100% [100–100] | 0 | 0 | 1.0 | 6,418 | 10.23 / 11.04 |
| unanswerable | 4 | 0.0 (0/4) | 4/4 100% [100–100] | 4/4 100% [100–100] | 0 | 0 | 1.0 | 2,443 | 3.08 / 3.10 |
| escalation | 3 | 0.0 (0/5) | 3/3 100% [100–100] | 3/3 100% [100–100] | 0 | 0 | 1.7 | 5,222 | 6.20 / 6.77 |
| adversarial | 4 | 25.0 (1/4) | 4/4 100% [100–100] | 4/4 100% [100–100] | 0 | 0 | 1.0 | 1,937 | 3.99 / 10.13 |
| old_policy | 1 | 0.0 (0/1) | 1/1 100% [100–100] | 1/1 100% [100–100] | 0 | 0 | 1.0 | 2,744 | 8.12 / 8.12 |
| **all** | 30 | 3.1 (1/32) | 29/30 97% [90–100] | 30/30 100% [100–100] | 0 | 0 | 1.1 | 3,700 | 6.20 / 10.23 |

Tool confusion (expected against called):

| expected ↓ / called → | list | status | tracking | search | propose | escalate | (none) |
|---|---|---|---|---|---|---|---|
| list | **11** | · | · | · | · | · | · |
| status | · | **7** | · | · | · | · | · |
| tracking | · | · | **6** | · | · | · | · |
| search | · | · | · | **12** | · | · | · |
| propose | · | · | · | · | **3** | · | · |
| escalate | · | · | · | · | · | **3** | 4 |
| (none) | 1 | 2 | 2 | 1 | · | · | · |
