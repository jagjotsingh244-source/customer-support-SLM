## 2026-11-23_floor-probes · floor · `Qwen/Qwen3.5-2B` · prompt v0 · tools v0 · temperature 0.2 · sampling default · scorer eval-v3

Provider `local`; served by `Qwen/Qwen3.5-2B`; commit `3a99d84`; database `localhost:5433`; up to 4 model calls per turn. Notes: phrasing probes; same setup as 2026-11-22_floor (Transformers on the Mac GPU, local database copy)

| Phrasing | n | tool_names | tool_args | required_calls | valid_json | facts | forbidden | escalation | all | all_required | cites | cites_source | grounded |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| offensive | 3 | 0/3 (0%) | 0/3 (0%) | 1/3 (33%) | 3/3 (100%) | 0/3 (0%) | 3/3 (100%) | 1/3 (33%) | 0/3 (0%) | 0/3 (0%) | 0/1 (0%) | 0/1 (0%) | 3/3 (100%) |
| typos | 3 | 0/3 (0%) | 0/3 (0%) | 1/3 (33%) | 3/3 (100%) | 1/3 (33%) | 3/3 (100%) | 2/3 (67%) | 0/3 (0%) | 0/3 (0%) | 0/2 (0%) | 0/2 (0%) | 3/3 (100%) |
| polite | 3 | 2/3 (67%) | 2/3 (67%) | 2/3 (67%) | 3/3 (100%) | 0/3 (0%) | 3/3 (100%) | 2/3 (67%) | 0/3 (0%) | 0/3 (0%) | 0/1 (0%) | 0/1 (0%) | 3/3 (100%) |
| keyword | 3 | 1/3 (33%) | 1/3 (33%) | 1/3 (33%) | 3/3 (100%) | 2/3 (67%) | 3/3 (100%) | 2/3 (67%) | 1/3 (33%) | 1/3 (33%) | - | - | 3/3 (100%) |
| **all** | 12 | **3/12 (25%)** | **3/12 (25%)** | **5/12 (42%)** | **12/12 (100%)** | **3/12 (25%)** | **12/12 (100%)** | **7/12 (58%)** | **1/12 (8%)** | **1/12 (8%)** | **0/4 (0%)** | **0/4 (0%)** | **12/12 (100%)** |

Each probe next to its clean twin in run `2026-11-22_floor` (all = every check passed with the strict tool checks; all_required = with required_calls):

| Probe | Phrasing | Twin | Probe all | Twin all | Probe all_required | Twin all_required |
|---|---|---|---|---|---|---|
| esc-phr-09 | polite | esc-004 | fail | fail | fail | fail |
| ord-phr-01 | offensive | ord-003 | fail | fail | fail | fail |
| ord-phr-04 | typos | ord-006 | fail | fail | fail | fail |
| ord-phr-07 | polite | ord-017 | fail | fail | fail | fail |
| ord-phr-10 | keyword | ord-015 | pass | pass | pass | pass |
| pol-phr-03 | offensive | pol-010 | fail | fail | fail | fail |
| pol-phr-05 | typos | pol-009 | fail | fail | fail | fail |
| pol-phr-08 | polite | pol-001 | fail | fail | fail | fail |
| ret-phr-02 | offensive | ret-001 | fail | pass | fail | pass |
| ret-phr-06 | typos | ret-013 | fail | fail | fail | fail |
| ret-phr-11 | keyword | ret-004 | fail | fail | fail | fail |
| una-phr-12 | keyword | una-002 | fail | fail | fail | fail |

all: probes passed 1/12, their clean twins 2/12.  
all_required: probes passed 1/12, their clean twins 2/12.  

Latency per turn (model calls + tools + database): median 9.30 s, p95 17.20 s, max 17.20 s over 12 turns.
Model calls: 34; mean prompt tokens 1199, mean completion tokens 37.
Unanswerable cases that passed escalation by offering a hand-off: 0.
Cases that errored (scored as failures): 0.
Tool-call format errors (a call left as text, or an empty reply): 0.
Grounding: 0 of 12 replies have an issue (0 per 100 replies), 0 issues.

Failed cases: esc-phr-09, ord-phr-01, ord-phr-04, ord-phr-07, pol-phr-03, pol-phr-05, pol-phr-08, ret-phr-02, ret-phr-06, ret-phr-11, una-phr-12

### Every layer, per category (metrics `layers-v1`, evals/metrics.py)

| Category | n | searched | recall@3 | MRR | right tools | exact args | rejected / 100 calls | format errors / 100 model calls | cases with an unneeded call | end state right | fallback turns |
|---|---|---|---|---|---|---|---|---|---|---|---|
| policy | 3 | 2/3 67% [0–100] | 0/2 0% [0–0] | 0.00 | 1/3 33% [0–100] | 1/3 33% [0–100] | 0.0 (0/6) | 0.0 (0/8) | 0/3 | 3/3 100% [100–100] | 1 |
| order_lookup | 4 | - | - | - | 2/4 50% [0–100] | 2/4 50% [0–100] | 0.0 (0/8) | 0.0 (0/11) | 0/4 | 4/4 100% [100–100] | 1 |
| returns | 3 | 0/1 0% [0–0] | - | - | 0/3 0% [0–0] | 0/3 0% [0–0] | 0.0 (0/8) | 0.0 (0/10) | 0/3 | 1/3 33% [0–100] | 1 |
| unanswerable | 1 | - | - | - | 0/1 0% [0–0] | 0/1 0% [0–0] | 0.0 (0/1) | 0.0 (0/2) | 0/1 | 0/1 0% [0–0] | 0 |
| escalation | 1 | - | - | - | 0/1 0% [0–0] | 0/1 0% [0–0] | 0.0 (0/2) | 0.0 (0/3) | 0/1 | 0/1 0% [0–0] | 0 |
| **all** | 12 | 2/4 50% [0–100] | 0/2 0% [0–0] | 0.00 | 3/12 25% [0–50] | 3/12 25% [0–50] | 0.0 (0/25) | 0.0 (0/34) | 0/12 | 8/12 67% [42–92] | 3 |

| Category | n | grounding issues / 100 replies | facts | no forbidden | privacy violations | return claimed done | customer turns | tokens / conversation | latency p50 / p95 (s) |
|---|---|---|---|---|---|---|---|---|---|
| policy | 3 | 0.0 (0/3) | 0/3 0% [0–0] | 3/3 100% [100–100] | 0 | 0 | 1.0 | 3,226 | 5.16 / 17.20 |
| order_lookup | 4 | 0.0 (0/4) | 1/4 25% [0–75] | 4/4 100% [100–100] | 0 | 0 | 1.0 | 3,401 | 11.41 / 12.53 |
| returns | 3 | 0.0 (0/3) | 1/3 33% [0–100] | 3/3 100% [100–100] | 0 | 0 | 1.0 | 4,435 | 12.00 / 14.28 |
| unanswerable | 1 | 0.0 (0/1) | 1/1 100% [100–100] | 1/1 100% [100–100] | 0 | 0 | 1.0 | 2,093 | 6.02 / 6.02 |
| escalation | 1 | 0.0 (0/1) | 0/1 0% [0–0] | 1/1 100% [100–100] | 0 | 0 | 1.0 | 3,370 | 8.50 / 8.50 |
| **all** | 12 | 0.0 (0/12) | 3/12 25% [0–50] | 12/12 100% [100–100] | 0 | 0 | 1.0 | 3,504 | 10.11 / 17.20 |

Tool confusion (expected against called):

| expected ↓ / called → | list | status | tracking | search | propose | escalate | (none) |
|---|---|---|---|---|---|---|---|
| list | **5** | · | · | · | · | · | · |
| status | · | **3** | · | · | · | · | · |
| tracking | · | · | **4** | · | · | · | 1 |
| search | 2 | · | · | **2** | · | · | 1 |
| propose | 1 | · | · | 1 | · | · | · |
| escalate | · | · | · | · | · | · | 2 |
| (none) | 2 | 2 | · | 3 | · | · | · |
