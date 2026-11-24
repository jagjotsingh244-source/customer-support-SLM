## 2026-11-23_sft1-policy-v1 · candidate · `Qwen/Qwen3.5-2B` · prompt v1 · tools v1 · temperature 0.2 · sampling default · scorer eval-v3

Provider `local`; served by `Qwen/Qwen3.5-2B`; commit `c924ae1+uncommitted changes`; database `localhost:5433`; up to 4 model calls per turn. Notes: Apple M4 (MPS), Transformers 5.23.0, fp16, in-process; adapter merged; help-center retrieval tools and citation prompt

| Category | n | tool_names | tool_args | required_calls | valid_json | facts | forbidden | escalation | all | all_required | cites | cites_source | grounded |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 0/25 (0%) | 0/25 (0%) | 0/25 (0%) | 25/25 (100%) | 1/25 (4%) | 25/25 (100%) | 25/25 (100%) | 0/25 (0%) | 0/25 (0%) | 0/25 (0%) | 0/25 (0%) | 25/25 (100%) |
| old_policy | 5 | 0/5 (0%) | 0/5 (0%) | 0/5 (0%) | 5/5 (100%) | 0/5 (0%) | 4/5 (80%) | 5/5 (100%) | 0/5 (0%) | 0/5 (0%) | 0/5 (0%) | 0/5 (0%) | 4/5 (80%) |
| **all** | 30 | **0/30 (0%)** | **0/30 (0%)** | **0/30 (0%)** | **30/30 (100%)** | **1/30 (3%)** | **29/30 (97%)** | **30/30 (100%)** | **0/30 (0%)** | **0/30 (0%)** | **0/30 (0%)** | **0/30 (0%)** | **29/30 (97%)** |

Latency per turn (model calls + tools + database): median 3.62 s, p95 4.40 s, max 4.44 s over 30 turns.
Model calls: 30; mean prompt tokens 1023, mean completion tokens 41.
Unanswerable cases that passed escalation by offering a hand-off: 0.
Cases that errored (scored as failures): 0.
Tool-call format errors (a call left as text, or an empty reply): 0.
Grounding: 1 of 30 replies have an issue (3 per 100 replies), 1 issues.

Failed cases: old-001, old-002, old-003, old-004, old-005, pol-001, pol-002, pol-003, pol-004, pol-005, pol-006, pol-007, pol-008, pol-009, pol-010, pol-011, pol-012, pol-013, pol-014, pol-015, pol-016, pol-017, pol-018, pol-019, pol-020, pol-021, pol-022, pol-023, pol-024, pol-025

Grounding issues:
- old-002: number 30 not in tool results

### Every layer, per category (metrics `layers-v1`, evals/metrics.py)

| Category | n | searched | recall@3 | MRR | right tools | exact args | rejected / 100 calls | format errors / 100 model calls | cases with an unneeded call | end state right | fallback turns |
|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 0/25 0% [0–0] | - | - | 0/25 0% [0–0] | 0/25 0% [0–0] | - | 0.0 (0/25) | 0/25 | 25/25 100% [100–100] | 0 |
| old_policy | 5 | 0/5 0% [0–0] | - | - | 0/5 0% [0–0] | 0/5 0% [0–0] | - | 0.0 (0/5) | 0/5 | 5/5 100% [100–100] | 0 |
| **all** | 30 | 0/30 0% [0–0] | - | - | 0/30 0% [0–0] | 0/30 0% [0–0] | - | 0.0 (0/30) | 0/30 | 30/30 100% [100–100] | 0 |

| Category | n | grounding issues / 100 replies | facts | no forbidden | privacy violations | return claimed done | customer turns | tokens / conversation | latency p50 / p95 (s) |
|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 0.0 (0/25) | 1/25 4% [0–12] | 25/25 100% [100–100] | 0 | 0 | 1.0 | 1,061 | 3.62 / 4.14 |
| old_policy | 5 | 20.0 (1/5) | 0/5 0% [0–0] | 4/5 80% [40–100] | 0 | 0 | 1.0 | 1,077 | 3.61 / 4.40 |
| **all** | 30 | 3.3 (1/30) | 1/30 3% [0–10] | 29/30 97% [90–100] | 0 | 0 | 1.0 | 1,064 | 3.62 / 4.40 |

Tool confusion (expected against called):

| expected ↓ / called → | list | status | tracking | search | propose | escalate | (none) |
|---|---|---|---|---|---|---|---|
| list | · | · | · | · | · | · | · |
| status | · | · | · | · | · | · | · |
| tracking | · | · | · | · | · | · | · |
| search | · | · | · | · | · | · | 31 |
| propose | · | · | · | · | · | · | · |
| escalate | · | · | · | · | · | · | · |
| (none) | · | · | · | · | · | · | · |
