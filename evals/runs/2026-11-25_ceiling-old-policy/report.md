## 2026-11-25_ceiling-old-policy · ceiling · `gemini-4-hydrogen` · prompt v1 · tools v1 · temperature 0.2 · sampling default · scorer eval-v3

Provider `gemini`; served by `gemini-4-hydrogen`; commit `2d81805+uncommitted changes`; database `localhost:5433`; up to 4 model calls per turn. Notes: Vertex AI global, project nova-evals (the first project's key was blocked during a policy review); local database copy; help-center retrieval tools and citation prompt

| Category | n | tool_names | tool_args | required_calls | valid_json | facts | forbidden | escalation | all | all_required | cites | cites_source | grounded |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| old_policy | 5 | 2/5 (40%) | 2/5 (40%) | 5/5 (100%) | 5/5 (100%) | 5/5 (100%) | 5/5 (100%) | 5/5 (100%) | 2/5 (40%) | 5/5 (100%) | 5/5 (100%) | 5/5 (100%) | 4/5 (80%) |
| **all** | 5 | **2/5 (40%)** | **2/5 (40%)** | **5/5 (100%)** | **5/5 (100%)** | **5/5 (100%)** | **5/5 (100%)** | **5/5 (100%)** | **2/5 (40%)** | **5/5 (100%)** | **5/5 (100%)** | **5/5 (100%)** | **4/5 (80%)** |

Latency per turn (model calls + tools + database): median 9.89 s, p95 18.52 s, max 18.52 s over 5 turns.
Model calls: 13; mean prompt tokens 1192, mean completion tokens 267.
Unanswerable cases that passed escalation by offering a hand-off: 0.
Cases that errored (scored as failures): 0.
Tool-call format errors (a call left as text, or an empty reply): 0.
Grounding: 1 of 5 replies have an issue (20 per 100 replies), 1 issues.

Failed cases: old-001, old-003, old-005

Grounding issues:
- old-001: number 30 not in tool results

### Every layer, per category (metrics `layers-v1`, evals/metrics.py)

| Category | n | searched | recall@3 | MRR | right tools | exact args | rejected / 100 calls | format errors / 100 model calls | cases with an unneeded call | end state right | fallback turns |
|---|---|---|---|---|---|---|---|---|---|---|---|
| old_policy | 5 | 5/5 100% [100–100] | 5/5 100% [100–100] | 0.80 | 4/5 80% [40–100] | 2/5 40% [0–80] | 0.0 (0/9) | 0.0 (0/13) | 0/5 | 5/5 100% [100–100] | 0 |
| **all** | 5 | 5/5 100% [100–100] | 5/5 100% [100–100] | 0.80 | 4/5 80% [40–100] | 2/5 40% [0–80] | 0.0 (0/9) | 0.0 (0/13) | 0/5 | 5/5 100% [100–100] | 0 |

| Category | n | grounding issues / 100 replies | facts | no forbidden | privacy violations | return claimed done | customer turns | tokens / conversation | latency p50 / p95 (s) |
|---|---|---|---|---|---|---|---|---|---|
| old_policy | 5 | 20.0 (1/5) | 5/5 100% [100–100] | 5/5 100% [100–100] | 0 | 0 | 1.0 | 3,795 | 9.89 / 18.52 |
| **all** | 5 | 20.0 (1/5) | 5/5 100% [100–100] | 5/5 100% [100–100] | 0 | 0 | 1.0 | 3,795 | 9.89 / 18.52 |

Tool confusion (expected against called):

| expected ↓ / called → | list | status | tracking | search | propose | escalate | (none) |
|---|---|---|---|---|---|---|---|
| list | · | · | · | · | · | · | · |
| status | · | · | · | · | · | · | · |
| tracking | · | · | · | · | · | · | · |
| search | · | · | · | **5** | · | · | · |
| propose | · | · | · | · | · | · | · |
| escalate | · | · | · | · | · | · | · |
| (none) | 2 | · | · | 2 | · | · | · |
