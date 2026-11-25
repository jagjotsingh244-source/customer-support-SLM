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


## Retrieval

### 2026-11-23 · Chunking the help center by section
- Did: `rag/chunks.py` turns every indexed page into one chunk per `##` section, with the path (`Returning electronics › Opened electronics`) on the first line and a Qwen token count; `rag/index.py` loads them into `kb_chunks` and refuses to load if the chunk IDs differ from `rag/chunk_ids.txt`. 103 chunks, 19–120 tokens, median 40; none needed splitting.
- Surprised me: the short end was not one problem but two. Twelve one-line chunks are a single sharp rule ("You can return unopened electronics within 7 days of delivery") and are the best possible unit; merging them would have blurred the rule and broken IDs the golden set cites. Two were pure pointers (`See "Split shipments".`) that would fill a top-3 slot with nothing, so I rewrote them to state the rule and keep the reference.
- Next time: before merging short chunks, ask whether each one holds a rule; length alone does not say whether a chunk is useful.

### 2026-11-23 · Measuring retrieval before any answer
- Did: labelled 60 questions from the pages (golden policy cases, customer phrasings, raw Bitext with typos) plus the 37 search queries the models wrote in the baseline runs, and scored vector, full-text and hybrid search with three embedding models in `evals/retrieval_eval.py`. Report: `evals/reports/02a_rag.md`. Chose bge-small, plain vector search, no query prefix: recall@3 0.83 on customer messages, 0.95 on model queries.
- Surprised me: hybrid search, the usual winner for support, never beat vector search here and lost 10 customer messages to filler words ("give it back" found a section about coming back to a ticket). The help center uses one term per idea and order numbers go to the order tools, so full-text has nothing rare to catch. Six page edits (one a new "we do not offer exchanges" section) moved recall more than a model four times larger, and the query prefix the model card suggests made no difference.
- Next time: score on the queries the tool will actually receive, not only on the customer's words; here the model's keyword queries were a different, easier test, and the one that matches production.

### 2026-11-23 · Grounded answers, and what retrieval cannot fix
- Did: built the new `search_help_center` (vector search, top 3, nothing below a 0.68 cutoff chosen on 22 unanswerable questions), prompt v1 with citations, number and citation checks on every reply (`agent/grounding.py`, scorer `eval-v2`), and five golden cases where the customer quotes the archived policy. Ran the 2B model and SFT-1 on the 30 policy cases on the Mac. Results in `evals/reports/02a_rag.md`.
- Surprised me: when the 2B model searched, the new tool found the right section 8 times in 11 (the old one: once), and it then stated the facts correctly 7 times in 8. But it searched in only 11 of 30 cases, called `list_my_orders` first every time, and never cited. All three invented numbers came from not searching. The grounding check also found that the loop had been sending escaped JSON to the 2B model ("1\u20133 days") since the first baseline, while Gemini got clean structured results. And it missed an invented date, because it checks numbers one at a time.
- Next time: before improving a component, count how often the system actually calls it; a perfect tool the model skips fixes nothing.


## Tools

### 2026-11-23 · What a tool call is, token by token
- Did: rendered one full tool round trip (Nova's prompt, six tools, a `get_tracking` call and its real result) through the chat template with every part marked and counted (`notes/tool-call-anatomy/`), and sent the same request to vLLM on a T4 with and without the tool-call parser. The loop now treats a call left as text, or an empty reply, as a format error that never reaches the customer.
- Surprised me: with the parser on and `tool_choice="none"`, vLLM threw away the model's call and returned a completely empty reply with HTTP 200, a failure no status check would see. Without the parser the call came back as ordinary text in `content`. The render also showed that the tool definitions (780 tokens) come before Nova's own rules, and that a tool result reaches the model as a customer turn with a `<tool_response>` wrapper.
- Next time: check what a component returns when it fails, not only when it works; an empty success is harder to spot than an error.


### 2026-11-23 · Tools that cannot leak or confirm
- Did: `agent/tools_v2.py` with one strict Pydantic model per tool; three database roles with row-level security (`db/roles.sql`); return eligibility as one pure function with unit tests (`agent/returns.py`); `propose_return` writes only a proposal, and a FastAPI endpoint (`api/`) is the only path to a confirmed return. `tests/test_tool_guards.py` checks every guard against the database, and runs in CI. Two new golden cases (scorer `eval-v3`).
- Surprised me: my first cross-customer test passed for the wrong reason: the other customer's order had no returns or refunds, so "zero rows" proved nothing for those tables; it now uses an order with rows in every table and checks the owner sees them first. Pydantic's schemas cost 953 tokens against the old tools' 781 until I stripped what only the validator needs. And the 2B model read the tool note "a Confirm button is shown to the customer" back to the customer word for word; a note telling it what to say worked.
- Next time: before trusting a "nothing leaked" test, check that there was something to leak.

### 2026-11-23 · Errors the model can use, and a fix that made things worse
- Did: `call_tool` in `agent/tools_v2.py` validates every call and answers a bad one with one sentence (what was wrong, what right looks like, what to do next), stops retries after the second failure, and never returns a blank or a stack trace. `tests/test_tool_errors.py` sends 15 malformed calls and sweeps every real order through every tool. Then I re-ran the floor and SFT-1 on the 40 order and return cases with only the tools changed (`evals/reports/02b_tools.md`).
- Surprised me: the floor got worse, 11 to 8 of 40. The baseline traces showed why there was nothing to gain: the model made no argument errors in 101 calls. And one of my own "explicit" sentences, "No return on this order.", read to the model as "returns not allowed" and caused 6 hand-offs; rewording it put proposals up from 4 to 15. The sweep also found a real bug: cancelled orders' voided labels were handed out as tracking numbers.
- Next time: count how often a failure actually happens before building the fix for it, and test every sentence a tool says with the model, because to a 2B model a tool's reply is part of the prompt.

### 2026-11-23 · A context budget, and a state block the model misread
- Did: `agent/state.py` with the state (built from tool results only), `fit()` (drops whole old turns, never splits a call from its result) and a counter that uses the model's tokenizer on the rendered template. Measured every part of the prompt and set the budget to 4,200 + 512 for the reply. `tests/test_state.py` runs a 15-turn chat in CI, and `evals/long_chat.py` runs two with the real model (`evals/reports/02c_context_budget.md`).
- Surprised me: my stand-in model, which I wrote to read the state, got every turn right with it; the real 2B got fewer right with my first state than with no state at all. It trusted the line `Order in focus: 10689` over the customer saying "the webcam order". Labelling every order by its items took it to 14/14, and a second chat written afterwards also scored 14/14. Measuring the block also showed that a status lookup was erasing the tracking number found earlier.
- Next time: a stand-in model proves the plumbing, not the design; run the real model before trusting a layout, and keep one chat back to check the change on.


## Evaluation

### 2026-11-25 · Every layer, every category, three runs each
- Did: a metric catalogue read from saved traces (`evals/metrics.py`: retrieval, tool choice, end state, grounding, privacy, false return claims, tokens, latency), per category with counts and bootstrap intervals; 40 simulated customers on eval-partition orders with expected end states (`evals/build_simulated.py`, `evals/simulate.py`); every system run three times on both sets for pass^3 (`evals/scorecard.py`); all 21 earlier runs re-scored without calling a model. Report: `evals/reports/04a_layers.md`.
- Surprised me: my first pass rule for simulated chats passed SFT-1 on 57%, a model that calls no tools and whose customers gave up half the time, because answering nothing never creates a wrong end state. Requiring the evidence an answer needs (a lookup of that order, the right section retrieved) took it to 8%. The "return claimed done" check I reused from the training filters was mostly false alarms ("No return has been created yet"). And conversations, not scripted cases, are where reliability breaks: SFT-2a passes 78% of simulated chats once but only 60% in all three runs, and in them it hands off too often, the opposite of the golden set's missed hand-offs.
- Next time: before trusting a pass rule, run it on a system known to be useless and check that it fails; and read every hit of a new safety check before counting it.

### 2026-11-25 · A judge that agreed with me on the replies I tuned it on
- Did: 75 labelled replies (grounded and resolved, with a reason each): 25 to write the judge prompt, 25 to test it, and 25 fresh ones labelled before the judge saw them; gpt-oss-120b on Modal as the judge (`evals/judge.py`, `serving/modal_judge.py`), five prompt versions, TPR and TNR on every set. Report: `evals/reports/04b_judge.md`.
- Surprised me: the plain "is this resolved?" prompt passed 11 of 15 failures. Definitions, examples and a checklist took the tune set to TNR 0.90 for grounded, and the held-out sets came back at 0.67 and 0.43. Giving the judge date facts computed by code did not help either: it still accepted "has not been lost" for a parcel with no scan for 8 days, because "there is no indication of loss". It treats no evidence against a claim as evidence for it. The same prompt also moved by one reply between runs.
- Next time: before tuning a judge, ask which of its checks code could do. Most of the misses here (reassurance on a stuck parcel, "not covered" without a search, a hand-off that never happened) are exact rules over the trace. And keep a second held-out set from the start, because the first one is used up the moment it changes the prompt.
