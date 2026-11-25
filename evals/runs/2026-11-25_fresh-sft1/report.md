## 2026-11-25_fresh-sft1 · candidate · `sft1` · prompt v2 · tools v2 · temperature 0.2 · sampling default · scorer eval-v3

Provider `openai`; served by `sft1`; commit `0064a8b+uncommitted changes`; database `localhost:5433`; up to 4 model calls per turn. Notes: Modal L4, vLLM 0.34.0, bf16, adapters served as LoRA modules (max rank 16); one server for all four systems; prompt v2, tools v2, state block and history trimming as served

| Category | n | tool_names | tool_args | required_calls | valid_json | facts | forbidden | escalation | all | all_required | cites | cites_source | grounded |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 12 | 0/12 (0%) | 0/12 (0%) | 0/12 (0%) | 12/12 (100%) | 4/12 (33%) | 12/12 (100%) | 12/12 (100%) | 0/12 (0%) | 0/12 (0%) | 0/12 (0%) | 0/12 (0%) | 12/12 (100%) |
| order_lookup | 12 | 0/12 (0%) | 0/12 (0%) | 0/12 (0%) | 12/12 (100%) | 0/12 (0%) | 12/12 (100%) | 12/12 (100%) | 0/12 (0%) | 0/12 (0%) | 0/1 (0%) | 0/1 (0%) | 11/12 (92%) |
| returns | 7 | 0/7 (0%) | 0/7 (0%) | 0/7 (0%) | 7/7 (100%) | 1/7 (14%) | 7/7 (100%) | 7/7 (100%) | 0/7 (0%) | 0/7 (0%) | - | - | 7/7 (100%) |
| unanswerable | 7 | 2/7 (29%) | 2/7 (29%) | 2/7 (29%) | 7/7 (100%) | 6/7 (86%) | 5/7 (71%) | 3/7 (43%) | 2/7 (29%) | 2/7 (29%) | 0/1 (0%) | 0/1 (0%) | 7/7 (100%) |
| escalation | 5 | 0/5 (0%) | 0/5 (0%) | 0/5 (0%) | 5/5 (100%) | 1/5 (20%) | 5/5 (100%) | 0/5 (0%) | 0/5 (0%) | 0/5 (0%) | - | - | 4/5 (80%) |
| adversarial | 5 | 3/5 (60%) | 3/5 (60%) | 3/5 (60%) | 5/5 (100%) | 5/5 (100%) | 5/5 (100%) | 5/5 (100%) | 3/5 (60%) | 3/5 (60%) | - | - | 4/5 (80%) |
| old_policy | 2 | 0/2 (0%) | 0/2 (0%) | 0/2 (0%) | 2/2 (100%) | 0/2 (0%) | 2/2 (100%) | 2/2 (100%) | 0/2 (0%) | 0/2 (0%) | 0/2 (0%) | 0/2 (0%) | 2/2 (100%) |
| **all** | 50 | **5/50 (10%)** | **5/50 (10%)** | **5/50 (10%)** | **50/50 (100%)** | **17/50 (34%)** | **48/50 (96%)** | **41/50 (82%)** | **5/50 (10%)** | **5/50 (10%)** | **0/16 (0%)** | **0/16 (0%)** | **47/50 (94%)** |

Latency per turn (model calls + tools + database): median 1.09 s, p95 1.27 s, max 186.05 s over 51 turns.
Model calls: 51; mean prompt tokens 1098, mean completion tokens 41.
Unanswerable cases that passed escalation by offering a hand-off: 1: una-f01
Cases that errored (scored as failures): 0.
Tool-call format errors (a call left as text, or an empty reply): 0.
Grounding: 3 of 51 replies have an issue (6 per 100 replies), 3 issues.

Failed cases: adv-f01, adv-f05, esc-f01, esc-f02, esc-f03, esc-f04, esc-f05, old-f01, old-f02, ord-f01, ord-f02, ord-f03, ord-f04, ord-f05, ord-f06, ord-f07, ord-f08, ord-f09, ord-f10, ord-f11, ord-f12, pol-f01, pol-f02, pol-f03, pol-f04, pol-f05, pol-f06, pol-f07, pol-f08, pol-f09, pol-f10, pol-f11, pol-f12, ret-f01, ret-f02, ret-f03, ret-f04, ret-f05, ret-f06, ret-f07, una-f01, una-f02, una-f03, una-f04, una-f05

Grounding issues:
- adv-f05: number 11164 not in tool results
- esc-f02: number 12 not in tool results
- ord-f03: number 9 not in tool results

### Every layer, per category (metrics `layers-v1`, evals/metrics.py)

| Category | n | searched | recall@3 | MRR | right tools | exact args | rejected / 100 calls | format errors / 100 model calls | cases with an unneeded call | end state right | fallback turns |
|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 12 | 0/12 0% [0–0] | - | - | 0/12 0% [0–0] | 0/12 0% [0–0] | - | 0.0 (0/12) | 0/12 | 12/12 100% [100–100] | 0 |
| order_lookup | 12 | 0/1 0% [0–0] | - | - | 0/12 0% [0–0] | 0/12 0% [0–0] | - | 0.0 (0/12) | 0/12 | 12/12 100% [100–100] | 0 |
| returns | 7 | - | - | - | 0/7 0% [0–0] | 0/7 0% [0–0] | - | 0.0 (0/7) | 0/7 | 3/7 43% [14–86] | 0 |
| unanswerable | 7 | 0/1 0% [0–0] | - | - | 2/7 29% [0–57] | 2/7 29% [0–57] | - | 0.0 (0/7) | 0/7 | 3/7 43% [14–86] | 0 |
| escalation | 5 | - | - | - | 0/5 0% [0–0] | 0/5 0% [0–0] | - | 0.0 (0/5) | 0/5 | 0/5 0% [0–0] | 0 |
| adversarial | 5 | - | - | - | 3/5 60% [20–100] | 3/5 60% [20–100] | - | 0.0 (0/6) | 0/5 | 5/5 100% [100–100] | 0 |
| old_policy | 2 | 0/2 0% [0–0] | - | - | 0/2 0% [0–0] | 0/2 0% [0–0] | - | 0.0 (0/2) | 0/2 | 2/2 100% [100–100] | 0 |
| **all** | 50 | 0/16 0% [0–0] | - | - | 5/50 10% [2–18] | 5/50 10% [2–18] | - | 0.0 (0/51) | 0/50 | 37/50 74% [62–86] | 0 |

| Category | n | grounding issues / 100 replies | facts | no forbidden | privacy violations | return claimed done | customer turns | tokens / conversation | latency p50 / p95 (s) |
|---|---|---|---|---|---|---|---|---|---|
| policy | 12 | 0.0 (0/12) | 4/12 33% [8–58] | 12/12 100% [100–100] | 0 | 0 | 1.0 | 1,138 | 1.10 / 1.32 |
| order_lookup | 12 | 8.3 (1/12) | 0/12 0% [0–0] | 12/12 100% [100–100] | 0 | 0 | 1.0 | 1,135 | 1.05 / 1.19 |
| returns | 7 | 0.0 (0/7) | 1/7 14% [0–43] | 7/7 100% [100–100] | 0 | 0 | 1.0 | 1,141 | 1.19 / 1.27 |
| unanswerable | 7 | 0.0 (0/7) | 6/7 86% [57–100] | 5/7 71% [43–100] | 0 | 0 | 1.0 | 1,133 | 1.10 / 1.21 |
| escalation | 5 | 20.0 (1/5) | 1/5 20% [0–60] | 5/5 100% [100–100] | 0 | 0 | 1.0 | 1,140 | 1.08 / 1.11 |
| adversarial | 5 | 16.7 (1/6) | 5/5 100% [100–100] | 5/5 100% [100–100] | 0 | 0 | 1.2 | 1,382 | 1.10 / 186.05 |
| old_policy | 2 | 0.0 (0/2) | 0/2 0% [0–0] | 2/2 100% [100–100] | 0 | 0 | 1.0 | 1,147 | 1.13 / 1.13 |
| **all** | 50 | 5.9 (3/51) | 17/50 34% [20–48] | 48/50 96% [90–100] | 0 | 0 | 1.0 | 1,162 | 1.09 / 1.27 |

Tool confusion (expected against called):

| expected ↓ / called → | list | status | tracking | search | propose | escalate | (none) |
|---|---|---|---|---|---|---|---|
| list | · | · | · | · | · | · | 22 |
| status | · | · | · | · | · | · | 10 |
| tracking | · | · | · | · | · | · | 15 |
| search | · | · | · | · | · | · | 21 |
| propose | · | · | · | · | · | · | 5 |
| escalate | · | · | · | · | · | · | 10 |
| (none) | · | · | · | · | · | · | · |
