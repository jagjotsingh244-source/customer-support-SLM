# Learning log

One entry per session: what I did, what surprised me, what I'd do differently.

## Foundations: model, GPUs and design

### 2026-11-20 · Deciding where each capability lives
- Did: wrote DESIGN.md, mapping 12 capabilities to prompt / RAG / tool / fine-tune / code, plus budgets with numbers.
- Surprised me: most capabilities need two or three mechanisms. A tool gives the data, but fine-tuning is what makes the model call it.
- Next time: rules that must hold every time go in code. A prompt only works "most of the time".

### 2026-11-20 · A training setup that survives free GPUs
- Did: built the repo layout and the Hub repos, ran Postgres + pgvector in Docker (port 5433, because a system Postgres 18 holds 5432), ran the disconnect drill on Colab and a closed-tab run on Kaggle.
- Surprised me: the drill resumed from step 250, not 100. The tiny model trained faster than I could click, so the newest save was at 250. Added a pause at step 120.
- Next time: keep checkpoints on the Hub, never only on the notebook's own disk; leave no logic in the notebook.

### 2026-11-20 · How a small model produces a reply
- Did: rendered the real chat template, counted tokens (6 draft tools = 656), wrote the greedy loop and matched `generate`, compared sampling (temperature 1.0 made replies vary 106–284 tokens, against 101–129 at 0.2) and thinking on vs off, saved the raw tool-call format.
- Surprised me: the model config's stop token is `<|endoftext|>`, not `<|im_end|>`, so `generate` ran past the end of the turn. Thinking is turned off by an empty `<think></think>` block in the prompt.
- Next time: always decode with special tokens visible when debugging, and check stop tokens on every new serving setup.

### 2026-11-20 · Risk tests on a T4
- Did: ran the four risk tests on Kaggle. Transformers and Unsloth passed first time; vLLM failed, and I fixed it with a run 2 notebook that tried fixes in a set order. Pinned training and serving versions in separate files.
- Surprised me: the cause of the failure was a missing file name (`libcuda.so`), hidden 300 lines above the error the report showed. vLLM was 4.5x faster than Transformers on the same GPU.
- Next time: always read the full log for the first real error, not the last line; keep training and serving in separate environments.


## NimbusCart's data

### 2026-11-21 · The schema is the contract
- Did: wrote 16 customer questions in `db/QUESTIONS.md` (including failed payments), finished `db/schema.sql` (11 tables, 9 enums), wrote one scoped query per question in `db/questions.sql` and tested them against a hand-built world (`db/fixtures.sql`); 10 bad inserts in `db/break.sql` all fail; wrote six state machines in `db/STATES.md`.
- Surprised me: writing the questions first found 11 gaps in the starting schema (refunds for cancelled orders, shipping fee, a delivery address per order, payments...). Writing the SQL found one more (the return reason, for "opened electronics only if faulty"), and writing the state machine found another (a cancelled packed order left its shipment label stuck, so `shipment_status` got `cancelled`). The Docker Postgres runs in UTC, so `::date` gave the wrong day for times between 00:00 and 05:30 IST.
- Next time: every query filters on `customer_id`, even with an order ID; set the session time zone to IST in every tool; keep policy numbers (7 and 15 days) in one place in code.

### 2026-11-21 · One clock and two worlds
- Did: added `config.py` (a frozen `NOW` read through `now()`, plus `partition_for`), `scripts/check_clock.sh` and a CI workflow that fails if any code reads the real clock.
- Surprised me: the hash split gave 17.6% eval, not 20%; that is the price of every customer keeping its side forever. My own hand-built test data broke the rule straight away (customer 1 is eval, I had marked it train).
- Next time: write the guard before the code it protects; the clock check caught a comment I had written myself.

### 2026-11-21 · Seeding the problems, not the average day
- Did: wrote `db/seed.py` (14 order scenarios, one builder each, plus failed payments), `db/checks.sql` (19 invariants) and `db/scenarios.csv`. 3,000 orders, every check passes, two seeds give identical data, and every scenario has at least 7 orders on eval customers.
- Surprised me: all checks passed first time, so I broke five things on purpose to prove they could fail; they caught all five. The two dumps "differed" only by a random token pg_dump writes, not by data. A COD refund needs its own state (awaiting bank details) while the return is still picked up.
- Next time: build every timestamp forward from one clock and assert it is before `NOW`, so a builder that asks for the future crashes instead of writing a bad row.

### 2026-11-21 · Writing the help center for retrieval
- Did: wrote 18 pages in `kb/` (one topic per page, one rule per section, every number in digits), an archived 30-day returns page, a customer-words file for retrieval tests, and `scripts/check_kb.py`, which checks the writing rules and that every promised number matches the constants in `db/seed.py`. Added it to CI.
- Surprised me: the checker passed first time, so I planted five mistakes; it caught all five, including a page that no longer matched the seed's 15-day window. Inside a Python f-string, a regex `{3}` silently becomes `3`. "7 days" means three different things across the pages (electronics window, possible loss, reporting a faulty not-returnable item).
- Next time: write the numbers table before the pages, and make the seed's numbers named constants from the start so the docs can be checked against them.

### 2026-11-21 · The store's gate: real queries on real rows
- Did: wrote `db/verify_queries.py`, which reads the 16 queries from `db/questions.sql` and runs them against every eval order of the matching scenario (24 cases, about 1,100 query runs, plus a scope check on all 521 eval orders). Added a CI job that seeds a fresh Postgres and runs the seed checks, the query gate and the bad-insert tests.
- Surprised me: before running anything, counting order statuses showed the seed had no placed or packed orders, so "Can I cancel?" and "Can I change my address?" had nothing to look up. Added a `not_yet_shipped` scenario (3%) and resolved tickets on old orders. Changing one row's ETA made the gate fail on exactly that order.
- Next time: check that every question has seeded rows behind it as soon as the scenario catalog is written, not at the end.


## Baseline and scorecard

### 2026-11-22 · The cheapest Nova that could work
- Did: loaded the help center into Postgres as 103 searchable sections, moved the eval database to Neon, and wrote prompt v0, six rough tools (customer from the session, read-only connection) and a plain tool-calling loop. Ran one delayed-order conversation on the prompted Qwen3.5-2B (vLLM on a T4) and on Gemini through an adapter, same prompt, tools and loop.
- Surprised me: the 2B found the right order and tool in 6/6 runs but said "which is in 5 days" about a date four days past. Gemini never answered at all: it obeyed "policy facts only from search", the keyword search found nothing for "late delivery delayed shipment", and the 4-call limit ran out. The smarter model lost on that case because it was more careful.
- Next time: test the tools with the strongest model first; a tool that blocks the ceiling blocks everything.

### 2026-11-22 · A golden set that is true
- Did: wrote 100 cases in six categories (policy, order lookups, returns, unanswerable, escalation, adversarial) on eval customers, and `evals/validate.py`, which checks every case against the database and help center: ownership, scenario, real tool results, and every required fact present in a tool result or cited section. Planted mistakes; all caught. CI runs it.
- Surprised me: writing the cases found a real data bug: sealed earbuds were "never returnable" in the data while the help center said "once unsealed". Raw customer wording found the right help-center section only 3 times in 25.
- Next time: ask other people to write messages early; I wrote only 3 compound cases where about 10 were planned.

### 2026-11-22 · The first scorecard
- Did: `evals/run_eval.py` runs, saves, scores and reports per category; froze the scorer as `eval-v1` before seeing the floor's results. Floor 25/100 correct, ceiling 58/100. Read 30 floor failures and counted the types: treats general questions as order questions (7), runs out of calls (7), mishandles returns (4). Kept temperature 0.2 (9/30 against 5/30 for the model card's settings).
- Surprised me: on strict checks the 2B beats Gemini (19 against 14), because Gemini searches 2.9 times per case. Several "failures" were the checks, not the models: negations ("No return has been created yet") and the customer's own words echoed back trip substring checks. A finished Kaggle run lost its files when the draft session restarted.
- Next time: write results somewhere that outlives the session (Drive, or locally) from the first run; read traces before trusting a headline number.
