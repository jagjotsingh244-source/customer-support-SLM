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


## Training data

### 2026-11-22 · Looking at Bitext before training on it
- Did: measured all 26,872 rows in `data_prep/bitext_eda.ipynb` (intent counts, reply tokens, duplicates, placeholders, phrasing flags, reply habits) and wrote five decisions with evidence in `data/DECISIONS.md`. Gemini read a 5-per-intent sample and drafted a note per intent; two notes promised things Nova cannot do and were corrected.
- Surprised me: the counts look perfectly balanced (950 to 1,000 per intent) but 59% of `cancel_order` questions repeat an earlier one. Half the replies carry `{{...}}` slots, 8 per cancel reply on average, and a quarter of customer messages carry them too. 239 refund messages say "dollars" for a store that sells in rupees.
- Next time: count distinct rows, not rows; a flat bar chart hid the biggest imbalance.

### 2026-11-22 · Rewriting the replies, and the rewriter's own habits
- Did: `data_prep/prepare_bitext.py` dedups, triages, fills customer placeholders with seeded NimbusCart values, samples 5,500 rows (rare phrasings at double weight) and has Gemini rewrite every reply content-free, then checks each one. Wrote a meaning judge and tested it on 20 planted pairs before using it.
- Surprised me: the checks passed 99.9% of the first full run, and the run was still not usable: 31% of replies said "I'd be glad", and 21% of calm customers were told they were frustrated. The pass rate measured form; only counting phrases found the habits. Writing the judge's test showed two of my own "good" examples broke the rules. The judge then caught only 3 of my 6 hand rejections: it stops clear invented facts (PayPal) but not vague ones ("we offer a few different options"), which needed a pattern check.
- Next time: after every generation run, count the most common openings, closings and phrases before looking at the pass rate.

### 2026-11-22 · The chat template decides where the loss starts
- Did: rendered examples with Qwen3.5-2B's template, wrote `training/masking.py` and a test (now in CI) that fails if any system or customer token is trained. `data_prep/build_chat_dataset.py` makes the splits, token stats and the dataset card.
- Surprised me: every reply renders after an empty `<think></think>` block that the serving prompt already contains, so the usual marker (`<|im_start|>assistant\n`) would train the model to write that block. Earlier assistant turns render without it, so only the last turn of a conversation has the shape the model generates.
- Next time: render the serving prompt and the training example side by side before choosing any marker.

### 2026-11-23 · Counting the adapter before training it
- Did: `training/lora_budget.py` builds Qwen3.5-2B from its config with no weights, counts LoRA parameters by hand for r = 8, 16, 64, checks them against PEFT, and estimates training memory. Results and the target-module decision are in `DESIGN.md`.
- Surprised me: only 6 of the 24 layers have `q/k/v/o_proj`; the other 18 are linear-attention layers with different names, so the usual target list never touches their attention. The model also carries a 331M-parameter vision tower that `all-linear` would quietly train. And the biggest activation cost is the logits: a 248k vocabulary makes them about 1 GB for one batch of 512 tokens.
- Next time: print the model before choosing target modules; a recipe's names only mean something for the architecture it was written for.

### 2026-11-23 · The first full fine-tune
- Did: trained `sft1-r16-lr2e-4-bitext_v1` (278 steps, 40 min on a T4) with `training/sft.py`, watching validation loss, held-out-intent loss and eight greedy probes every 25 steps. Peak memory 4.94 GB against an estimate of 4.9–5.6 GB; the adapter is 43.7 MB, as counted.
- Surprised me: the probes changed most in the first 25 steps (flat "I will check your order details first" became warm, 30-word replies ending in an offer) and hardly at all after step 200, while loss kept falling slowly. Held-out-intent loss levelled off at 0.83 from step 225. The model also amplified a habit: 5 of 8 probe replies open by restating the customer ("You're wondering where your order is"), a pattern in only 20% of the training replies. And "Hello!" came back with an exclamation mark that no training reply has.
- Next time: count the openings of probe replies at every step, not only at the end; a habit that grows from 20% to 60% shows up in the probes before it shows in any loss.

### 2026-11-23 · Three ranks, one short epoch
- Did: trained r = 8, 16 and 64 (alpha = r) on the same seeded 1,000 rows for 63 steps and compared them with `training/ablation_table.py`; results and the choice are in `training/ABLATIONS.md`. Kept r = 16.
- Surprised me: r = 64 had the lowest loss everywhere, held-out intents included, which looked like a clear win until the curves showed its lead shrinking from 0.46 at step 10 to 0.12 at the end. With alpha = r a bigger rank also takes bigger steps, so a short run rewards speed, not capacity. The full-data r = 16 run beat every 1,000-row run, and all three ranks had the same probe faults.
- Next time: when an ablation changes how fast a model learns as well as what it can learn, compare the curves, not only the last point, or hold the step size fixed.

### 2026-11-23 · What the first fine-tune took away
- Did: judged SFT-1 four ways (loss, style metrics on 200 held-out prompts, a blind side-by-side against the base model, the 100 golden cases with tools) and checked that vLLM serves the adapter word for word like Transformers. Read all 18 golden cases it newly failed. Report: `evals/reports/02_sft_bitext.md`.
- Surprised me: two things. SFT-1 made no tool call in any golden case, not fewer: 83% of training replies end by asking permission to check, and the model learned that as the answer. And it matched the data on every style rule, yet I preferred the base model's replies 23 to 2 in the blind read, because they were half as long and said what they would do. The style metrics measured the rules I wrote, not whether a customer would want the reply.
- Next time: read a blind sample of the training replies themselves before training on them; a preference test on the data is cheaper than one on the model.
