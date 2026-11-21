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
