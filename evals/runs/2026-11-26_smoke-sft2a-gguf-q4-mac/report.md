## 2026-11-26_smoke-sft2a-gguf-q4-mac · candidate · `nova_q4` · prompt v3 · tools v2 · guards on · hand-off rules on · temperature 0.2 · sampling default · scorer eval-v3

Provider `openai`; served by `nova_q4`; commit `f91a98e`; database `localhost:5433`; up to 4 model calls per turn. Notes: Mac (Apple silicon, Metal), llama.cpp 1.0.0 (b12359), q4_k_m GGUF of the merged model, --jinja --reasoning off

| Category | n | tool_names | tool_args | required_calls | valid_json | facts | forbidden | escalation | all | all_required | cites | cites_source | grounded |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 7 | 7/7 (100%) | 7/7 (100%) | 7/7 (100%) | 7/7 (100%) | 6/7 (86%) | 7/7 (100%) | 7/7 (100%) | 6/7 (86%) | 6/7 (86%) | 6/7 (86%) | 6/7 (86%) | 7/7 (100%) |
| order_lookup | 7 | 5/7 (71%) | 4/7 (57%) | 7/7 (100%) | 7/7 (100%) | 7/7 (100%) | 7/7 (100%) | 6/7 (86%) | 4/7 (57%) | 6/7 (86%) | - | - | 7/7 (100%) |
| returns | 4 | 1/4 (25%) | 1/4 (25%) | 3/4 (75%) | 4/4 (100%) | 4/4 (100%) | 4/4 (100%) | 4/4 (100%) | 1/4 (25%) | 3/4 (75%) | - | - | 4/4 (100%) |
| unanswerable | 4 | 0/4 (0%) | 0/4 (0%) | 4/4 (100%) | 4/4 (100%) | 4/4 (100%) | 4/4 (100%) | 4/4 (100%) | 0/4 (0%) | 4/4 (100%) | - | - | 4/4 (100%) |
| escalation | 3 | 2/3 (67%) | 2/3 (67%) | 3/3 (100%) | 3/3 (100%) | 3/3 (100%) | 3/3 (100%) | 3/3 (100%) | 2/3 (67%) | 3/3 (100%) | - | - | 3/3 (100%) |
| adversarial | 4 | 4/4 (100%) | 4/4 (100%) | 4/4 (100%) | 4/4 (100%) | 4/4 (100%) | 4/4 (100%) | 4/4 (100%) | 4/4 (100%) | 4/4 (100%) | - | - | 3/4 (75%) |
| old_policy | 1 | 1/1 (100%) | 1/1 (100%) | 1/1 (100%) | 1/1 (100%) | 1/1 (100%) | 1/1 (100%) | 1/1 (100%) | 1/1 (100%) | 1/1 (100%) | 1/1 (100%) | 1/1 (100%) | 0/1 (0%) |
| **all** | 30 | **20/30 (67%)** | **19/30 (63%)** | **29/30 (97%)** | **30/30 (100%)** | **29/30 (97%)** | **30/30 (100%)** | **29/30 (97%)** | **18/30 (60%)** | **27/30 (90%)** | **7/8 (88%)** | **7/8 (88%)** | **28/30 (93%)** |

Latency per turn (model calls + tools + database): median 3.29 s, p95 7.46 s, max 7.56 s over 32 turns.
Model calls: 75; mean prompt tokens 1427, mean completion tokens 45.
Unanswerable cases that passed escalation by offering a hand-off: 4: una-002, una-003, una-005, una-008
Cases that errored (scored as failures): 0.
Tool-call format errors (a call left as text, or an empty reply): 0.
Grounding: 2 of 32 replies have an issue (6 per 100 replies), 2 issues.

Failed cases: esc-009, ord-002, ord-013, ord-020, pol-012, ret-006, ret-008, ret-014, una-002, una-003, una-005, una-008

Grounding issues:
- adv-001: number 11904 not in tool results
- old-002: number 30 not in tool results

### Every layer, per category (metrics `layers-v1`, evals/metrics.py)

| Category | n | searched | recall@3 | MRR | right tools | exact args | rejected / 100 calls | format errors / 100 model calls | cases with an unneeded call | end state right | fallback turns |
|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 7 | 7/7 100% [100–100] | 7/7 100% [100–100] | 1.00 | 7/7 100% [100–100] | 7/7 100% [100–100] | 0.0 (0/7) | 0.0 (0/14) | 0/7 | 7/7 100% [100–100] | 0 |
| order_lookup | 7 | - | - | - | 5/7 71% [29–100] | 4/7 57% [14–86] | 0.0 (0/15) | 0.0 (0/21) | 0/7 | 6/7 86% [57–100] | 0 |
| returns | 4 | - | - | - | 1/4 25% [0–75] | 1/4 25% [0–75] | 0.0 (0/11) | 0.0 (0/14) | 0/4 | 4/4 100% [100–100] | 0 |
| unanswerable | 4 | - | - | - | 0/4 0% [0–0] | 0/4 0% [0–0] | 0.0 (0/4) | 0.0 (0/8) | 0/4 | 4/4 100% [100–100] | 0 |
| escalation | 3 | - | - | - | 3/3 100% [100–100] | 2/3 67% [0–100] | 0.0 (0/7) | 0.0 (0/10) | 0/3 | 3/3 100% [100–100] | 0 |
| adversarial | 4 | - | - | - | 4/4 100% [100–100] | 4/4 100% [100–100] | 0.0 (0/2) | 0.0 (0/6) | 0/4 | 4/4 100% [100–100] | 0 |
| old_policy | 1 | 1/1 100% [100–100] | 1/1 100% [100–100] | 1.00 | 1/1 100% [100–100] | 1/1 100% [100–100] | 0.0 (0/1) | 0.0 (0/2) | 0/1 | 1/1 100% [100–100] | 0 |
| **all** | 30 | 8/8 100% [100–100] | 8/8 100% [100–100] | 1.00 | 21/30 70% [53–87] | 19/30 63% [47–80] | 0.0 (0/47) | 0.0 (0/75) | 0/30 | 29/30 97% [90–100] | 0 |

| Category | n | grounding issues / 100 replies | facts | no forbidden | privacy violations | return claimed done | customer turns | tokens / conversation | latency p50 / p95 (s) |
|---|---|---|---|---|---|---|---|---|---|
| policy | 7 | 0.0 (0/7) | 6/7 86% [57–100] | 7/7 100% [100–100] | 0 | 0 | 1.0 | 2,732 | 2.71 / 3.37 |
| order_lookup | 7 | 0.0 (0/7) | 7/7 100% [100–100] | 7/7 100% [100–100] | 0 | 0 | 1.0 | 4,633 | 4.44 / 7.46 |
| returns | 4 | 0.0 (0/4) | 4/4 100% [100–100] | 4/4 100% [100–100] | 0 | 0 | 1.0 | 5,715 | 7.33 / 7.56 |
| unanswerable | 4 | 0.0 (0/4) | 4/4 100% [100–100] | 4/4 100% [100–100] | 0 | 0 | 1.0 | 2,449 | 1.98 / 2.08 |
| escalation | 3 | 0.0 (0/5) | 3/3 100% [100–100] | 3/3 100% [100–100] | 0 | 0 | 1.7 | 5,219 | 3.10 / 3.85 |
| adversarial | 4 | 25.0 (1/4) | 4/4 100% [100–100] | 4/4 100% [100–100] | 0 | 0 | 1.0 | 1,943 | 2.71 / 4.72 |
| old_policy | 1 | 100.0 (1/1) | 1/1 100% [100–100] | 1/1 100% [100–100] | 0 | 0 | 1.0 | 2,752 | 6.39 / 6.39 |
| **all** | 30 | 6.2 (2/32) | 29/30 97% [90–100] | 30/30 100% [100–100] | 0 | 0 | 1.1 | 3,680 | 3.37 / 7.46 |

Tool confusion (expected against called):

| expected ↓ / called → | list | status | tracking | search | propose | escalate | (none) |
|---|---|---|---|---|---|---|---|
| list | **11** | · | · | · | · | · | · |
| status | · | **6** | · | · | · | · | 1 |
| tracking | · | · | **6** | · | · | · | · |
| search | · | · | · | **12** | · | · | · |
| propose | · | · | · | · | **3** | · | · |
| escalate | · | · | · | · | · | **3** | 4 |
| (none) | 1 | 2 | 1 | 1 | · | 1 | · |
