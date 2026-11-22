# Baseline: the ceiling (Gemini with the same prompt, tools and loop)

Run `evals/runs/2026-11-22_ceiling` · `gemini-4-hydrogen` on Vertex AI (served model confirmed on every call) ·
prompt v0 · the same six rough tools · temperature 0.2 · at most 4 model calls per turn · scorer `eval-v1` ·
100 golden cases. Reached through `agent/gemini_adapter.py`, which translates the loop's messages and leaves the
prompt, tool schemas and loop unchanged.

**Correct on 58/100**, against **25/100 for the floor** (`00_baseline_floor.md`). The ceiling shows how far this
design can go with a much stronger model; the gap is the room training and better tools have to close.

## Floor against ceiling (correct = `all_required`)

| Category | Floor (Qwen3.5-2B) | Ceiling (Gemini) | Gap |
|---|---|---|---|
| policy | 2/25 (8%) | 17/25 (68%) | 60 points |
| order_lookup | 9/25 (36%) | 13/25 (52%) | 16 points |
| returns | 2/15 (13%) | 4/15 (27%) | 13 points |
| unanswerable | 5/15 (33%) | 12/15 (80%) | 47 points |
| escalation | 1/10 (10%) | 2/10 (20%) | 10 points |
| adversarial | 6/10 (60%) | 10/10 (100%) | 40 points |
| **all** | **25/100** | **58/100** | **33 points** |

On the strict checks (correct **and** efficient: exactly the expected calls), the floor scores higher, 19/100
against 14/100: the ceiling makes extra lookups and searches on almost every case.

## Scorecard

| Category | n | tool_names | tool_args | required_calls | valid_json | facts | forbidden | escalation | all | all_required |
|---|---|---|---|---|---|---|---|---|---|---|
| policy | 25 | 5/25 (20%) | 5/25 (20%) | 25/25 (100%) | 25/25 (100%) | 17/25 (68%) | 25/25 (100%) | 17/25 (68%) | 5/25 (20%) | 17/25 (68%) |
| order_lookup | 25 | 2/25 (8%) | 1/25 (4%) | 23/25 (92%) | 25/25 (100%) | 14/25 (56%) | 25/25 (100%) | 15/25 (60%) | 1/25 (4%) | 13/25 (52%) |
| returns | 15 | 0/15 (0%) | 0/15 (0%) | 11/15 (73%) | 15/15 (100%) | 5/15 (33%) | 13/15 (87%) | 10/15 (67%) | 0/15 (0%) | 4/15 (27%) |
| unanswerable | 15 | 5/15 (33%) | 5/15 (33%) | 13/15 (87%) | 15/15 (100%) | 14/15 (93%) | 14/15 (93%) | 14/15 (93%) | 4/15 (27%) | 12/15 (80%) |
| escalation | 10 | 2/10 (20%) | 2/10 (20%) | 4/10 (40%) | 10/10 (100%) | 5/10 (50%) | 10/10 (100%) | 8/10 (80%) | 2/10 (20%) | 2/10 (20%) |
| adversarial | 10 | 2/10 (20%) | 2/10 (20%) | 10/10 (100%) | 10/10 (100%) | 10/10 (100%) | 10/10 (100%) | 10/10 (100%) | 2/10 (20%) | 10/10 (100%) |
| **all** | 100 | **16/100 (16%)** | **15/100 (15%)** | **86/100 (86%)** | **100/100 (100%)** | **65/100 (65%)** | **97/100 (97%)** | **74/100 (74%)** | **14/100 (14%)** | **58/100 (58%)** |

Latency per turn: median 5.94 s, p95 12.05 s (Vertex AI from a laptop in India, retries on rate limits included).
332 model calls; about 445,000 input and 70,000 output tokens (thinking included).

## What limits the ceiling

**1. The rough search tool, through the 4-call limit.** The prompt allows policy facts only from help-center
search results, and Gemini follows that strictly: 285 searches (2.9 per case), 40% of them empty because every query
word must match. In **31 of 100 cases** it used all 4 model calls and the loop handed off with
*"Let me connect you with a teammate."*

A diagnostic re-run of those 31 cases with 8 calls per turn (`2026-11-22_ceiling-8calls`, labelled diagnostic,
never scored as the ceiling) raised them from **1/31 to 13/31 correct** and from 2/31 to 23/31 on facts, at a median
14.4 s per turn and 5.3 searches per case. So the call limit cost the ceiling about 12 of 100 cases; better retrieval
should recover much of that within the limit.

**2. It prefers to solve things itself over handing off.** In escalation cases it often explained instead of
handing off (2/10 correct): for "delivered but not received" it repeated the help center's advice to check with
neighbours, and for "what's the customer care number" it said the support team can be reached here without handing
off. In unanswerable cases it offered a hand-off rather than doing it (7 of 15 passed through the offer rule).

**3. Checks that cannot read negation.** Four replies in the diagnostic failed forbidden phrases by negating them:
*"**No** return has been created yet"*, *"I **don't** have policy details on whether we deliver to Dubai"*.
A deterministic substring check cannot see the "no"; an LLM judge can. Counted as scorer false positives, not
model errors; `eval-v1` stays frozen.

## What went right

- **Adversarial: 10/10.** No leak, no rule change, no fake-admin refund.
- **Required calls: 86/100**, against 54/100 for the floor: it almost always looks up what it needs.
- **Policy facts: 17/25**, against 2/25 for the floor, because it rewrites customer words into searchable terms
  and retries.

## Why Gemini and not Claude

The plan was a Claude model through Anthropic's API, which needs API credits; a Claude Pro subscription does not
include API access. The available Vertex AI key reaches only Gemini models, so the ceiling is `gemini-4-hydrogen`.
Any later comparison should name the ceiling as this model, not "a frontier model" in general.
