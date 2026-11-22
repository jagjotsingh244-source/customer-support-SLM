## 2026-11-23_floor-probes · floor · `Qwen/Qwen3.5-2B` · prompt v0 · temperature 0.2 · sampling default · scorer eval-v1

Provider `local`; served by `Qwen/Qwen3.5-2B`; commit `3a99d84`; database `localhost:5433`; up to 4 model calls per turn. Notes: phrasing probes; same setup as 2026-11-22_floor (Transformers on the Mac GPU, local database copy)

| Phrasing | n | tool_names | tool_args | required_calls | valid_json | facts | forbidden | escalation | all | all_required |
|---|---|---|---|---|---|---|---|---|---|---|
| offensive | 3 | 0/3 (0%) | 0/3 (0%) | 1/3 (33%) | 3/3 (100%) | 0/3 (0%) | 3/3 (100%) | 1/3 (33%) | 0/3 (0%) | 0/3 (0%) |
| typos | 3 | 0/3 (0%) | 0/3 (0%) | 1/3 (33%) | 3/3 (100%) | 1/3 (33%) | 3/3 (100%) | 2/3 (67%) | 0/3 (0%) | 0/3 (0%) |
| polite | 3 | 2/3 (67%) | 2/3 (67%) | 2/3 (67%) | 3/3 (100%) | 0/3 (0%) | 3/3 (100%) | 2/3 (67%) | 0/3 (0%) | 0/3 (0%) |
| keyword | 3 | 1/3 (33%) | 1/3 (33%) | 1/3 (33%) | 3/3 (100%) | 2/3 (67%) | 3/3 (100%) | 2/3 (67%) | 1/3 (33%) | 1/3 (33%) |
| **all** | 12 | **3/12 (25%)** | **3/12 (25%)** | **5/12 (42%)** | **12/12 (100%)** | **3/12 (25%)** | **12/12 (100%)** | **7/12 (58%)** | **1/12 (8%)** | **1/12 (8%)** |

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

Failed cases: esc-phr-09, ord-phr-01, ord-phr-04, ord-phr-07, pol-phr-03, pol-phr-05, pol-phr-08, ret-phr-02, ret-phr-06, ret-phr-11, una-phr-12
