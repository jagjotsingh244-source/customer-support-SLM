# Retrieval over the help center: which search finds the right chunk

The help center is 104 chunks in `kb_chunks`, one per `##` section (`rag/chunks.py`, loaded by `rag/index.py`).
Before any answer is generated, this report scores retrieval on its own: given a question, does the chunk that
answers it come back in the top 3? Nova reads the top 3, so **recall@3** is the number that decides. MRR (mean of
1 / rank of the first answering chunk, top 10) shows how high it lands.

**In one line:** plain vector search with `BAAI/bge-small-en-v1.5` wins. It finds the answer in the top 3 for
**83% of customer messages** and **95% of the queries the models actually wrote**. Hybrid search never beat it on
recall@3, and on raw customer messages it was worse (68%). Six small page edits raised recall more than a model
four times the size did.

Retrieval for the answer metrics (facts, citations, grounding violations per 100 replies for the floor model and
SFT-1) comes with the new `search_help_center`; that section is added below when it runs.

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

## Reproduce

```
uv run --group rag python rag/index.py --model BAAI/bge-small-en-v1.5
uv run --group rag python evals/retrieval_eval.py --model BAAI/bge-small-en-v1.5
uv run --group rag python evals/retrieval_eval.py --model BAAI/bge-small-en-v1.5 --file evals/retrieval/model_queries.jsonl --misses vector
```
