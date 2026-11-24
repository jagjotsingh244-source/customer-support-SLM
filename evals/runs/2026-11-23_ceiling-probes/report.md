## 2026-11-23_ceiling-probes · ceiling · `gemini-4-hydrogen` · prompt v0 · tools v0 · temperature 0.2 · sampling default · scorer eval-v3

Provider `gemini`; served by `gemini-4-hydrogen`; commit `3a99d84`; database `localhost:5433`; up to 4 model calls per turn. Notes: phrasing probes; same setup as 2026-11-22_ceiling (Vertex AI global, local database copy)

| Phrasing | n | tool_names | tool_args | required_calls | valid_json | facts | forbidden | escalation | all | all_required | cites | cites_source | grounded |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| offensive | 3 | 0/3 (0%) | 0/3 (0%) | 3/3 (100%) | 3/3 (100%) | 1/3 (33%) | 2/3 (67%) | 2/3 (67%) | 0/3 (0%) | 1/3 (33%) | 0/1 (0%) | 0/1 (0%) | 3/3 (100%) |
| typos | 3 | 1/3 (33%) | 0/3 (0%) | 3/3 (100%) | 3/3 (100%) | 2/3 (67%) | 3/3 (100%) | 3/3 (100%) | 0/3 (0%) | 2/3 (67%) | 0/2 (0%) | 0/2 (0%) | 3/3 (100%) |
| polite | 3 | 0/3 (0%) | 0/3 (0%) | 2/3 (67%) | 3/3 (100%) | 1/3 (33%) | 3/3 (100%) | 2/3 (67%) | 0/3 (0%) | 1/3 (33%) | 0/1 (0%) | 0/1 (0%) | 3/3 (100%) |
| keyword | 3 | 0/3 (0%) | 0/3 (0%) | 2/3 (67%) | 3/3 (100%) | 3/3 (100%) | 3/3 (100%) | 2/3 (67%) | 0/3 (0%) | 2/3 (67%) | - | - | 3/3 (100%) |
| **all** | 12 | **1/12 (8%)** | **0/12 (0%)** | **10/12 (83%)** | **12/12 (100%)** | **7/12 (58%)** | **11/12 (92%)** | **9/12 (75%)** | **0/12 (0%)** | **6/12 (50%)** | **0/4 (0%)** | **0/4 (0%)** | **12/12 (100%)** |

Each probe next to its clean twin in run `2026-11-22_ceiling` (all = every check passed with the strict tool checks; all_required = with required_calls):

| Probe | Phrasing | Twin | Probe all | Twin all | Probe all_required | Twin all_required |
|---|---|---|---|---|---|---|
| esc-phr-09 | polite | esc-004 | fail | fail | fail | fail |
| ord-phr-01 | offensive | ord-003 | fail | fail | fail | fail |
| ord-phr-04 | typos | ord-006 | fail | fail | pass | pass |
| ord-phr-07 | polite | ord-017 | fail | fail | pass | pass |
| ord-phr-10 | keyword | ord-015 | fail | fail | pass | pass |
| pol-phr-03 | offensive | pol-010 | fail | pass | pass | pass |
| pol-phr-05 | typos | pol-009 | fail | fail | pass | fail |
| pol-phr-08 | polite | pol-001 | fail | fail | fail | fail |
| ret-phr-02 | offensive | ret-001 | fail | fail | fail | fail |
| ret-phr-06 | typos | ret-013 | fail | fail | fail | fail |
| ret-phr-11 | keyword | ret-004 | fail | fail | pass | fail |
| una-phr-12 | keyword | una-002 | fail | fail | fail | pass |

all: probes passed 0/12, their clean twins 1/12.  
all_required: probes passed 6/12, their clean twins 5/12.  

Latency per turn (model calls + tools + database): median 7.97 s, p95 37.15 s, max 37.15 s over 12 turns.
Model calls: 40; mean prompt tokens 1259, mean completion tokens 200.
Unanswerable cases that passed escalation by offering a hand-off: 0.
Cases that errored (scored as failures): 0.
Tool-call format errors (a call left as text, or an empty reply): 0.
Grounding: 0 of 12 replies have an issue (0 per 100 replies), 0 issues.

Failed cases: esc-phr-09, ord-phr-01, ord-phr-04, ord-phr-07, ord-phr-10, pol-phr-03, pol-phr-05, pol-phr-08, ret-phr-02, ret-phr-06, ret-phr-11, una-phr-12

### Every layer, per category (metrics `layers-v1`, evals/metrics.py)

| Category | n | searched | recall@3 | MRR | right tools | exact args | rejected / 100 calls | format errors / 100 model calls | cases with an unneeded call | end state right | fallback turns |
|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 3 | 3/3 100% [100–100] | 3/3 100% [100–100] | 0.83 | 2/3 67% [0–100] | 0/3 0% [0–0] | 0.0 (0/11) | 0.0 (0/10) | 0/3 | 3/3 100% [100–100] | 1 |
| order_lookup | 4 | - | - | - | 1/4 25% [0–75] | 0/4 0% [0–0] | 0.0 (0/15) | 0.0 (0/12) | 0/4 | 4/4 100% [100–100] | 1 |
| returns | 3 | 1/1 100% [100–100] | 0/1 0% [0–0] | 0.00 | 1/3 33% [0–100] | 0/3 0% [0–0] | 0.0 (0/15) | 0.0 (0/11) | 0/3 | 1/3 33% [0–100] | 0 |
| unanswerable | 1 | - | - | - | 0/1 0% [0–0] | 0/1 0% [0–0] | 0.0 (0/3) | 0.0 (0/3) | 0/1 | 0/1 0% [0–0] | 0 |
| escalation | 1 | - | - | - | 0/1 0% [0–0] | 0/1 0% [0–0] | 0.0 (0/11) | 0.0 (0/4) | 0/1 | 0/1 0% [0–0] | 1 |
| **all** | 12 | 4/4 100% [100–100] | 3/4 75% [25–100] | 0.62 | 4/12 33% [8–58] | 0/12 0% [0–0] | 0.0 (0/55) | 0.0 (0/40) | 0/12 | 8/12 67% [42–92] | 3 |

| Category | n | grounding issues / 100 replies | facts | no forbidden | privacy violations | return claimed done | customer turns | tokens / conversation | latency p50 / p95 (s) |
|---|---|---|---|---|---|---|---|---|---|
| policy | 3 | 0.0 (0/3) | 2/3 67% [0–100] | 3/3 100% [100–100] | 0 | 0 | 1.0 | 4,795 | 7.80 / 15.88 |
| order_lookup | 4 | 0.0 (0/4) | 3/4 75% [25–100] | 4/4 100% [100–100] | 0 | 0 | 1.0 | 3,936 | 8.14 / 13.05 |
| returns | 3 | 0.0 (0/3) | 1/3 33% [0–100] | 2/3 67% [0–100] | 0 | 0 | 1.0 | 6,109 | 10.83 / 10.94 |
| unanswerable | 1 | 0.0 (0/1) | 1/1 100% [100–100] | 1/1 100% [100–100] | 0 | 0 | 1.0 | 3,618 | 6.57 / 6.57 |
| escalation | 1 | 0.0 (0/1) | 0/1 0% [0–0] | 1/1 100% [100–100] | 0 | 0 | 1.0 | 6,306 | 37.15 / 37.15 |
| **all** | 12 | 0.0 (0/12) | 7/12 58% [33–83] | 11/12 92% [75–100] | 0 | 0 | 1.0 | 4,865 | 8.14 / 37.15 |

Tool confusion (expected against called):

| expected ↓ / called → | list | status | tracking | search | propose | escalate | (none) |
|---|---|---|---|---|---|---|---|
| list | **5** | · | · | · | · | · | · |
| status | · | **3** | · | · | · | · | · |
| tracking | · | · | **5** | · | · | · | · |
| search | · | · | · | **5** | · | · | · |
| propose | · | · | · | · | **2** | · | · |
| escalate | 1 | · | · | 1 | · | · | · |
| (none) | 1 | 4 | 2 | 26 | · | · | · |
