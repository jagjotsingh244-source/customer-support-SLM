## 2026-11-26_template-capture-adapter · candidate · `nova_adapter` · prompt v3 · tools v2 · guards on · hand-off rules on · temperature 0.2 · sampling default · scorer eval-v3

Provider `openai`; served by `nova_adapter`; commit ``; database `localhost:5433`; up to 4 model calls per turn. Notes: GCP L4 (nova-eval9), vLLM 0.34.0, served as: adapter; requests captured for the template check

| Category | n | tool_names | tool_args | required_calls | valid_json | facts | forbidden | escalation | all | all_required | cites | cites_source | grounded |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 1 | 1/1 (100%) | 1/1 (100%) | 1/1 (100%) | 1/1 (100%) | 0/1 (0%) | 1/1 (100%) | 1/1 (100%) | 0/1 (0%) | 0/1 (0%) | 0/1 (0%) | 0/1 (0%) | 1/1 (100%) |
| order_lookup | 2 | 2/2 (100%) | 2/2 (100%) | 2/2 (100%) | 2/2 (100%) | 2/2 (100%) | 2/2 (100%) | 2/2 (100%) | 2/2 (100%) | 2/2 (100%) | - | - | 2/2 (100%) |
| returns | 2 | 1/2 (50%) | 1/2 (50%) | 1/2 (50%) | 2/2 (100%) | 2/2 (100%) | 2/2 (100%) | 2/2 (100%) | 1/2 (50%) | 1/2 (50%) | - | - | 2/2 (100%) |
| unanswerable | 1 | 0/1 (0%) | 0/1 (0%) | 0/1 (0%) | 1/1 (100%) | 1/1 (100%) | 1/1 (100%) | 0/1 (0%) | 0/1 (0%) | 0/1 (0%) | 1/1 (100%) | 1/1 (100%) | 1/1 (100%) |
| escalation | 2 | 1/2 (50%) | 1/2 (50%) | 2/2 (100%) | 2/2 (100%) | 2/2 (100%) | 2/2 (100%) | 2/2 (100%) | 1/2 (50%) | 2/2 (100%) | - | - | 2/2 (100%) |
| adversarial | 2 | 1/2 (50%) | 1/2 (50%) | 2/2 (100%) | 2/2 (100%) | 2/2 (100%) | 2/2 (100%) | 2/2 (100%) | 1/2 (50%) | 2/2 (100%) | - | - | 1/2 (50%) |
| **all** | 10 | **6/10 (60%)** | **6/10 (60%)** | **8/10 (80%)** | **10/10 (100%)** | **9/10 (90%)** | **10/10 (100%)** | **9/10 (90%)** | **5/10 (50%)** | **7/10 (70%)** | **1/2 (50%)** | **1/2 (50%)** | **9/10 (90%)** |

Latency per turn (model calls + tools + database): median 2.73 s, p95 7.69 s, max 7.69 s over 14 turns.
Model calls: 39; mean prompt tokens 1504, mean completion tokens 44.
Unanswerable cases that passed escalation by offering a hand-off: 0.
Cases that errored (scored as failures): 0.
Tool-call format errors (a call left as text, or an empty reply): 0.
Grounding: 1 of 14 replies have an issue (7 per 100 replies), 1 issues.

Failed cases: adv-010, esc-009, pol-001, ret-002, una-001

Grounding issues:
- adv-001: number 11904 not in tool results

### Every layer, per category (metrics `layers-v1`, evals/metrics.py)

| Category | n | searched | recall@3 | MRR | right tools | exact args | rejected / 100 calls | format errors / 100 model calls | cases with an unneeded call | end state right | fallback turns |
|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 1 | 1/1 100% [100–100] | 0/1 0% [0–0] | 0.00 | 1/1 100% [100–100] | 1/1 100% [100–100] | 0.0 (0/1) | 0.0 (0/2) | 0/1 | 1/1 100% [100–100] | 0 |
| order_lookup | 2 | - | - | - | 2/2 100% [100–100] | 2/2 100% [100–100] | 0.0 (0/4) | 0.0 (0/6) | 0/2 | 2/2 100% [100–100] | 0 |
| returns | 2 | - | - | - | 1/2 50% [0–100] | 1/2 50% [0–100] | 0.0 (0/7) | 0.0 (0/10) | 0/2 | 2/2 100% [100–100] | 0 |
| unanswerable | 1 | 1/1 100% [100–100] | 1/1 100% [100–100] | 1.00 | 0/1 0% [0–0] | 0/1 0% [0–0] | 0.0 (0/2) | 0.0 (0/3) | 0/1 | 0/1 0% [0–0] | 0 |
| escalation | 2 | - | - | - | 2/2 100% [100–100] | 1/2 50% [0–100] | 0.0 (0/8) | 0.0 (0/11) | 0/2 | 2/2 100% [100–100] | 0 |
| adversarial | 2 | - | - | - | 1/2 50% [0–100] | 1/2 50% [0–100] | 0.0 (0/6) | 0.0 (0/7) | 0/2 | 2/2 100% [100–100] | 0 |
| **all** | 10 | 2/2 100% [100–100] | 1/2 50% [0–100] | 0.50 | 7/10 70% [40–100] | 6/10 60% [30–90] | 0.0 (0/28) | 0.0 (0/39) | 0/10 | 9/10 90% [70–100] | 0 |

| Category | n | grounding issues / 100 replies | facts | no forbidden | privacy violations | return claimed done | customer turns | tokens / conversation | latency p50 / p95 (s) |
|---|---|---|---|---|---|---|---|---|---|
| policy | 1 | 0.0 (0/1) | 0/1 0% [0–0] | 1/1 100% [100–100] | 0 | 0 | 1.0 | 2,452 | 7.69 / 7.69 |
| order_lookup | 2 | 0.0 (0/2) | 2/2 100% [100–100] | 2/2 100% [100–100] | 0 | 0 | 1.0 | 4,470 | 2.91 / 2.91 |
| returns | 2 | 0.0 (0/3) | 2/2 100% [100–100] | 2/2 100% [100–100] | 0 | 0 | 1.5 | 8,078 | 3.51 / 3.55 |
| unanswerable | 1 | 0.0 (0/1) | 1/1 100% [100–100] | 1/1 100% [100–100] | 0 | 0 | 1.0 | 4,227 | 1.99 / 1.99 |
| escalation | 2 | 0.0 (0/4) | 2/2 100% [100–100] | 2/2 100% [100–100] | 0 | 0 | 2.0 | 8,886 | 2.52 / 2.96 |
| adversarial | 2 | 33.3 (1/3) | 2/2 100% [100–100] | 2/2 100% [100–100] | 0 | 0 | 1.5 | 5,408 | 3.24 / 3.38 |
| **all** | 10 | 7.1 (1/14) | 9/10 90% [70–100] | 10/10 100% [100–100] | 0 | 0 | 1.4 | 6,036 | 2.91 / 7.69 |

Tool confusion (expected against called):

| expected ↓ / called → | list | status | tracking | search | propose | escalate | (none) |
|---|---|---|---|---|---|---|---|
| list | **7** | · | · | · | · | · | · |
| status | · | **3** | · | · | · | · | · |
| tracking | · | · | **5** | · | · | · | · |
| search | · | · | · | **3** | · | · | · |
| propose | · | · | · | · | **2** | · | · |
| escalate | · | · | · | · | · | **3** | 1 |
| (none) | 2 | 2 | · | 1 | · | · | · |
