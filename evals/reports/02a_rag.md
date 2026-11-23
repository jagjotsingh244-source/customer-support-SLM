# Retrieval over the help center: which search finds the right chunk

The help center is 104 chunks in `kb_chunks`, one per `##` section (`rag/chunks.py`, loaded by `rag/index.py`).
Before any answer is generated, this report scores retrieval on its own: given a question, does the chunk that
answers it come back in the top 3? Nova reads the top 3, so **recall@3** is the number that decides. MRR (mean of
1 / rank of the first answering chunk, top 10) shows how high it lands.

**In one line:** plain vector search with `BAAI/bge-small-en-v1.5` wins. It finds the answer in the top 3 for
**83% of customer messages** and **95% of the queries the models actually wrote**. Hybrid search never beat it on
recall@3, and on raw customer messages it was worse (68%). Six small page edits raised recall more than a model
four times the size did.

The second half ("Answers with the new tool") runs the golden policy cases through the full agent loop. **When the
2B model searches, the new tool hands it the right section in 8 of 11 cases (the old tool: 1 of 11), and it states
the right facts in 7 of those 8.** But it searches in only 11 of 30 policy cases, never cites, and every
ungrounded number it wrote came from not searching. Retrieval is no longer the bottleneck; the model's tool choice is.

## The labelled sets

Labels were written from the chunk text before any search ran. A question has one or more answer groups. A group
lists every chunk that answers that part of the question on its own, and any one of them counts. The help center
repeats some facts across pages (the cash-on-delivery refund rule is on three), so a group often has two or three
chunks. One question has two parts and needs a chunk from each group.

| File | Questions | Where they come from |
|---|---|---|
| `evals/retrieval/questions.jsonl` | 60 | 25 golden policy cases (their first turn); 20 rewritten in the phrasing of `kb/_customer_words.md`; 15 verbatim Bitext questions with typo (Z) or colloquial (Q) flags, about refunds, cancellations and delivery, order-number placeholders filled |
| `evals/retrieval/model_queries.jsonl` | 37 | The first `search_help_center` query each model wrote for a golden policy case in the baseline runs: 12 from Qwen3.5-2B (it searched in 12 of 25 cases), 25 from Gemini. Labels copied from the matching golden case |
| `evals/retrieval/hinglish_probe.jsonl` | 4 | Unscored probe from `kb/_customer_words.md` |

The second set matters because the tool never sees the customer's message. The model writes the query, and it
writes keywords: "return pickup time", "awaiting bank details refund". The 60 questions are the harder test; the
37 queries are closer to what the tool will receive.

## Methods

All five run in Postgres (`rag/search.py`) against the same table.

| Method | What it does |
|---|---|
| vector | Cosine similarity between query and chunk embeddings (exact scan; no index needed at 104 rows) |
| fulltext_all | Postgres full-text search needing every word (`websearch_to_tsquery`), as the first rough tool did |
| fulltext_any | Full-text ranked by `ts_rank`, matching any word of the question |
| hybrid_all / hybrid_any | Vector and the full-text variant merged with reciprocal rank fusion (k = 60, top 20 of each) |

## Results

Final pages, no query prefix, `BAAI/bge-small-en-v1.5` (rankings in `evals/retrieval/runs/`):

| Method | recall@3, 60 questions | MRR | recall@3, 37 model queries | MRR |
|---|---|---|---|---|
| **vector** | **0.83** | **0.74** | **0.95** | **0.85** |
| fulltext_all | 0.05 | 0.05 | 0.30 | 0.30 |
| fulltext_any | 0.53 | 0.50 | 0.73 | 0.75 |
| hybrid_all | 0.83 | 0.74 | 0.95 | 0.83 |
| hybrid_any | 0.68 | 0.64 | 0.95 | 0.83 |

By segment, vector recall@3: golden 0.92, customer words 0.95, Bitext 0.53; Gemini's queries 0.96, Qwen3.5-2B's 0.92.

**Full-text needing every word almost never matches.** It returns anything for only 3 of 60 customer messages. This is why the
first tool kept returning `[]` in the baseline runs.

**Full-text matching any word matches the filler.** "used the bluetooth speaker once, sound is fine, want to give it
**back**" ranks *Coming back to a resolved ticket* first; "i cant **track** my reimbursement" returns three shipment
tracking chunks. Merged into hybrid, that noise pushes right answers out of the top 3 on 10 messages, and fixes
only 1: "why was i charged **49** extra", where the exact number matters. On keyword queries it is harmless but adds
nothing to recall.

**Why hybrid does not pay here.** Hybrid's strength is exact tokens: order numbers, product names, rare words.
In Nova, order numbers go to the order tools, never to the help center, and the help center names no products. The
pages were written with one term per idea, so there are few rare words for full-text to catch. The hybrid code and
its eval stay, to rerun if the help center gains product names or model numbers.

### Embedding models

Same sets, vector search, no query prefix:

| Model | Parameters | Dims | Query, CPU median | recall@3, 60 questions | MRR | recall@3, 37 queries | MRR |
|---|---|---|---|---|---|---|---|
| **BAAI/bge-small-en-v1.5** | 33M | 384 | 6.2 ms | **0.83** | **0.74** | 0.95 | 0.85 |
| sentence-transformers/all-MiniLM-L6-v2 | 23M | 384 | 3.5 ms | 0.72 | 0.68 | 0.89 | 0.82 |
| BAAI/bge-base-en-v1.5 (size check) | 109M | 768 | 14.5 ms | 0.78 | 0.68 | 0.95 | 0.92 |

Measured on this Mac's CPU, one query at a time after a warm-up. Embedding all 104 chunks takes 0.4 s with
bge-small.

**Choice: bge-small.** It leads on customer messages, ties on model queries, and costs about 6 ms a query. MiniLM is
faster but misses more paraphrases (Bitext 0.40 against 0.53). bge-base ranks model queries better (MRR 0.92) but is
worse on customer messages and 2.3 times slower; at this size of help center the model is not the bottleneck.

**Query prefix: off.** bge's card suggests an instruction before short queries
(`Represent this sentence for searching relevant passages: `) and calls it optional for v1.5. With it, bge-small
scored the same on the 60 questions (0.83) and one query lower on the 37 (0.92). The prefix reorders 33 of the 60
top-3 lists, so it does something; it just does not help here. `Embedder` defaults to no prefix and
`--prefix` reruns the comparison.

With 60 and 37 questions, one question is 1.7 and 2.7 points. Differences of one or two questions are noise.

## Page fixes

Reading every miss of the first run (bge-small with prefix, vector: 0.78 on the questions, 0.86 on the queries)
gave five edits, and a policy decision gave a sixth. The labels for two questions gained a chunk, because the edited chunk now answers them; labels
were judged from the new page text, not from what the search returned.

| Page and section | Edit | Miss it targeted | Fixed? |
|---|---|---|---|
| payment-failures › Money debited but no order | Adds that the money comes back within 5–7 business days | "payment deducted order not placed refund" found this section, but the answer was in the next one | Yes |
| returns-electronics › Earbuds, earphones and trimmers | Adds the faulty-on-arrival rule: report within 7 days, replaced after inspection | "trimmer arrives broken" found this section, which said only "not returnable" | Yes |
| returns-general › Pickup | "We collect" → "We pick up", the help center's own term | "return pickup time" ranked it 5th | Yes |
| cancellations › Before the order ships | Adds "There is no cancellation fee." | "need help checking trhe early exit charge" | No: the typo and "early exit" still miss; the sentence is true and customers ask it |
| shipping-times › Estimated delivery date | Adds "the day the order should arrive" | "when my parcel is gonna arrive" | No: still misses |
| returns-general › Exchanges (new section) | "We do not offer exchanges": return the item and place a new order | "can i exchange this lamp, i dont like the colour": no page mentioned exchanges | Yes: rank 1. Its label is now this chunk alone, since the return chunks never said whether exchanges exist |

Earlier, two sections that held only a pointer (`See "Split shipments".`) were rewritten to state their rule.

After the first five edits, bge-small with prefix went from 0.78 to 0.82 on the questions and 0.86 to 0.92 on the
queries. Switching the prefix off took the queries to 0.95, and the exchanges section took the questions to 0.83.

## Every remaining miss

bge-small, vector, no prefix. "Rank" is where the first answering chunk landed in the top 10.

| Question | Rank | Decision |
|---|---|---|
| why was i charged 49 extra on my order | 5 | **Accept.** An exact number is vector search's known weak spot; the 3 chunks above it are all about the shipping charge, so the reply would still be close. Hybrid fixes this one and breaks ten others |
| how many days to return a bedsheet and how long does upi refund take after that (and both model queries for it) | 1 | **Accept.** Two questions in one; the top 3 cover the refund part only. The model can search twice, as Gemini did |
| my parcel is stuck for days, still not here | 4 | **Accept.** The top 3 are the other delay chunks (delivered-not-received, tracking updates, possible loss) |
| i dont know how i can asj for a rebate · I'm waiting for a restitution oof ₹1200 · check ur money back guarantee · need help checking trhe early exit charge · cance order 10917 · I'm calling ot check when my parcel is gonna arrive · can uhelp me check how soon can i epect the delivery | 6, 7, –, –, –, –, 6 | **Accept.** Verbatim Bitext text where the typo or an odd word hides the key word. The model rewrites these into keywords before searching: none of the 37 model-written queries has a typo, and 95% of them hit |

## What this means for the tool

- The new `search_help_center` uses bge-small vector search over `kb_chunks`, top 3.
- **A score threshold will be hard.** On the 60 questions, the top chunk's similarity is 0.60–0.93 (median 0.78)
  when it answers and 0.64–0.87 (median 0.73) when it does not. The two ranges overlap almost completely. The
  threshold has to come from the unanswerable questions, not from these.
- Embeddings and queries must come from one model: `kb_chunks.embedding_model` records it and `Embedder.check_index`
  refuses a mismatch.

## The cutoff: when the tool returns nothing

Vector search always returns its 3 nearest chunks, even for "can you gift wrap my order". The tool drops every chunk
scoring below a cutoff and says "No help-center page matches. Offer to connect a teammate." when none is left.
`evals/retrieval_threshold.py` chose it on two new sets of questions the help center cannot answer: 10 unanswerable messages
(`evals/retrieval/unanswerable.jsonl`: gift wrap, Dubai, EMI, coupons, price match, loyalty points, store pickup,
restock, time slots, student discount) and the 12 queries the models wrote for unanswerable golden cases
(`unanswerable_model_queries.jsonl`; una-001 left out, since half of it asks about Pune, which is answerable).

How often a retrieved chunk answers the question, by its score (answerable sets, top 3):

| Score | Customer messages | Model queries |
|---|---|---|
| 0.50–0.65 | 5/22 (23%) | – |
| 0.65–0.70 | 13/45 (29%) | 4/14 (29%) |
| 0.70–0.75 | 9/35 (26%) | 10/35 (29%) |
| 0.75–0.80 | 24/46 (52%) | 18/38 (47%) |
| 0.80–1.00 | 24/32 (75%) | 19/24 (79%) |

| Cutoff | recall@3, messages | recall@3, model queries | empty, unanswerable messages | empty, unanswerable queries |
|---|---|---|---|---|
| none | 0.83 | 0.95 | 0/10 | 1/12 |
| 0.64 | 0.80 | 0.95 | 6/10 | 8/12 |
| 0.66 | 0.73 | 0.95 | 7/10 | 11/12 |
| **0.68** | 0.72 | **0.95** | 8/10 | **12/12** |
| 0.70 | 0.62 | 0.89 | 10/10 | 12/12 |

**Cutoff: 0.68** (`agent/tools_v1.py`, `MIN_SCORE`). It is the highest cutoff that keeps every answerable model query
(recall@3 stays 0.95) and empties every unanswerable one; below it, chunks answer the question 29% of the time or
less. It is chosen on the model queries because those are what the tool receives; on raw customer messages the same
cutoff would cost 11 points of recall. **The margin is thin**: the highest unanswerable query ("out of stock restock
availability") scored 0.668. Recheck it whenever the help center, the embedding model or the query style changes.

## The new tool

`agent/tools_v1.py`: the first order tools unchanged, and a new `search_help_center` returning up to 3 sections at or
above the cutoff:

```
{"results": [{"id": "returns-electronics#return-window", "title": "Returning electronics › Return window",
              "text": "You can return unopened electronics within 7 days of delivery.", "effective_date": "2026-10-01"}],
 "note": "Cite results as [kb:<id>]. If none answer the question, say so."}
```

A result costs 256 Qwen tokens at the median and 342 at most; `DESIGN.md`'s budget for retrieved text is now 1,000
(three searches), down from 2,000. Prompt v1 (`agent/prompts.py`) adds one rule to v0: cite every policy fact as
`[kb:<id>]`, and say the help center does not cover it when the search returns nothing.

**Grounding checks** (`agent/grounding.py`) run on every reply in the agent loop and are logged in the trace. A
number in the reply must appear in a tool result Nova was given earlier in the conversation; a citation must be the
id of a section a search returned. The scorer (`eval-v2`) recomputes both from saved messages, so every old run was
rescored too; none of the `eval-v1` metrics changed.

**A bug they found.** The agent loop wrote tool results with `json.dumps` defaults, so the 2B model read
`"1\u20133 business days"` and `"\u20b949"` instead of "1–3 business days" and "₹49" in every run before this one.
Gemini receives tool results as parsed JSON and never saw the escapes, so part of the baseline gap between the two
was formatting. The loop now writes plain text (`ensure_ascii=False`).

**The archive never reaches the index.** `kb/_archive/` is skipped by path, and the chunker now also refuses any page
whose front matter has `superseded_by`, so an archived page copied back into `kb/` stops the load.

## Answers with the new tool

The 25 golden policy cases plus 5 new **old-policy** cases (`evals/golden/old_policy.jsonl`): the customer quotes a
rule from the archived page (30 days for everything, opened items in their box, pickup in 3–5 days, refund within 7
days of pickup), and Nova must give and cite the current one. All runs: Qwen3.5-2B in-process on an Apple M4,
temperature 0.2, scorer `eval-v2`.

| Run | Tools · prompt | facts | cites | cites the right source | Replies with a grounding issue, per 100 |
|---|---|---|---|---|---|
| `2026-11-23_floor-policy-v0` | v0 · v0 | 1/30 (3%) | 0/30 | 0/30 | 7 (2 of 30) |
| `2026-11-23_floor-policy-v1` | **v1 · v1** | **7/30 (23%)** | 0/30 | 0/30 | 7 (2 of 30) |
| `2026-11-23_sft1-policy-v1` | v1 · v1 | 1/30 (3%) | 0/30 | 0/30 | 3 (1 of 30) |

Old-policy cases alone: the 2B model gave the current rule in 0/5 with the first tools and **3/5** with the new ones
("No, that's not correct. Electronics have a 7-day return window, not 30 days."). No case passes `all`: the strict
tool checks fail on extra order lookups, and the model never cites. The ship gate also asks for these five to pass
on the ceiling model; that run could not happen, because Vertex AI refused every request on 2026-11-23 (an account
review, not a request error). It stays open.

### Where the facts were lost

| | First tools | New tools |
|---|---|---|
| Cases where the 2B model searched | 11 of 30 | 11 of 30 |
| ... and a search returned an expected section | 1 | **8** |
| ... and the reply had the right facts | 1 | **7** (7 of the 8 that retrieved it) |
| Searches that came back empty | 9 cases | 0 |
| First call was `list_my_orders` | 25 of 30 | 30 of 30 |
| Ran out of model calls (fixed hand-off reply) | 13 | 9 |

With the first tool, retrieval was the wall: nine searches returned nothing because every word had to match. With
the new tool the model reads what it gets: 7 of 8. What is left is the model: it calls `list_my_orders` first on
every policy question (prompt rule: "if the customer has not said which order, call list_my_orders"), searches in
barely a third of cases, often spends its 4 calls on order lookups and hands off, and never writes a citation despite
the new rule. SFT-1 makes no tool call at all, so better retrieval cannot reach it (1/30, the same as before).

The 3 misses among searched cases: "refund policy" (old-005) and "extra charge order payment" (pol-015) are queries
too vague to point anywhere; "return policy headphones" (pol-003) found the earbuds section instead of opened
electronics. pol-025 retrieved the right section and then ran out of calls.

### Every grounding violation

| Run · case | Reply (excerpt) | Issue | Cause |
|---|---|---|---|
| v1 · pol-010 | "A UPI refund typically takes 7-10 business days to process." | 7, 10 not in any tool result | **Model**: never searched; invented the internet's usual number (the help center says 1–3) |
| v0 · pol-018, v1 · pol-018 | "Delivery to Ludhiana typically takes 1-2 days once it reaches the hub" / "3-5 days once shipped" | 1, 2 / 3 not in any tool result | **Model**: answered from the tracking tool, never searched (the help center says 4–7 days) |
| v0 · pol-015 | "Which order was charged with the extra 49 INR?" | 49 | **Check**: repeats the customer's own number. Counted on purpose: the customer's words are not evidence |
| SFT-1 · old-002 | "...whether electronics can still be returned within 30 days of delivery. I can check the policy..." | 30 | **Check**: repeats the customer's claim while offering to look it up |

None came from retrieval or the cutoff. Three are true hallucinations, all after not searching, the failure retrieval is
meant to prevent: a remembered number instead of the current one.

**A gap in the number check.** In pol-002 (v1) the model wrote "Your return window ends on October 7, 2026", a date
no tool returned. It passed, because 7 and 2026 each appear somewhere in the tool
results. Numbers are matched one at a time; dates need to be matched whole. That belongs in the guardrails.

### What this means

- Retrieval does its job when called: the right section in 8 of 11, nothing for questions the help center cannot
  answer.
- The next gains are in behaviour, which the order tools and the second fine-tune address: search first for policy
  questions instead of listing orders, cite what was retrieved, and never state a policy number without a search.
  The three hallucinations above are the training signal.
- The prompt's order-first rule is a likely cause of the wasted `list_my_orders` calls; worth testing a prompt that
  scopes it to order questions.

## Reproduce

```
uv run --group rag python rag/index.py --model BAAI/bge-small-en-v1.5
uv run --group rag python evals/retrieval_eval.py --model BAAI/bge-small-en-v1.5
uv run --group rag python evals/retrieval_eval.py --model BAAI/bge-small-en-v1.5 --file evals/retrieval/model_queries.jsonl --misses vector
uv run --group rag python evals/retrieval_threshold.py
uv run --group local-model --group rag python evals/run_eval.py --run 2026-11-23_floor-policy-v1 --system floor \
    --provider local --model Qwen/Qwen3.5-2B --tools v1 --prompt v1 --category policy old_policy
```
