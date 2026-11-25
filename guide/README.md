# Guide

Readable write-ups of how Nova was designed and why: the decisions, the evidence behind them,
and the questions they answer. The source of truth stays in `DESIGN.md` and `notes/`; these PDFs
explain it end to end.

| PDF | Covers |
|---|---|
| [foundations.pdf](foundations.pdf) | Where each capability lives, the budgets, the model choice, training on free GPUs, how the model produces a reply, the GPU risk tests and the vLLM fix, and likely interview questions with answers |
| [store-and-data.pdf](store-and-data.pdf) | The store Nova works in: the schema designed from customer questions, state machines, the frozen clock and train/eval split, the scenario seed, the help center written for retrieval, the five layers of checks, bugs found, and likely interview questions with answers |
| [baseline-and-scorecard.pdf](baseline-and-scorecard.pdf) | Measuring Nova before improving it: the agent loop, tools and prompt v0, the Neon database, the help center as searchable sections, floor (Qwen3.5-2B) against ceiling (Gemini) on one loop, the 100 golden cases and their validator, the frozen scorer, the results, 30 failures read and counted, sampling and latency, what went wrong, and likely interview questions with answers |
| [training-data.pdf](training-data.pdf) | Teaching Nova how to sound: reading Bitext before training on it, five decisions with evidence, triage of all 27 intents, placeholders (the customer's filled, Nova's never), sampling that protects rare phrasings, the rewrite and the rewriting model's own habits, three layers of checks (rules, a tested judge, a hand review), the chat template and the loss mask, splits and sequence length, the phrasing probes, what went wrong including the cost, and likely interview questions with answers |
| [fine-tuning.pdf](fine-tuning.pdf) | The first fine-tune: why LoRA (the memory wall), counting the adapter by hand on a hybrid architecture, memory estimated then measured, the training setup and what every run records, the first run and its probes, the rank ablation and how not to misread it, four checks (loss, style, a blind read, the golden set with tools) and the export check, why tool use collapsed, what changes for the next fine-tune, what went wrong, and likely interview questions with answers |
| [help-center-retrieval.pdf](help-center-retrieval.pdf) | Retrieval over the help center: chunking one rule per section, pgvector in Postgres, measuring recall@3 on customer messages and on the queries the models write, why plain vector search beat hybrid, choosing the embedding model, fixing pages instead of the model, the 0.68 cutoff for "nothing matches", the new tool and citation prompt, grounding checks on every reply, archived policies, the end-to-end results, what went wrong, and likely interview questions with answers |
| [tool-layer.pdf](tool-layer.pdf) | The tool layer: what a tool call is at token level and what the parser does with it, a threat model of four layers, typed arguments with Pydantic, database roles and row-level security, returns the model can only propose and the customer confirms, errors written for the model, results with no blanks, what hardening fixed without training (and what it made worse), a context budget enforced in code, the state block and the layout the model misread, history trimming, what went wrong, and likely interview questions with answers |
| [synthetic-conversations.pdf](synthetic-conversations.pdf) | Making training data for a tool-using agent: trajectory distillation (a 27B teacher playing Nova inside the real agent loop, every fact from the real tools), choosing the teacher, context distillation, simulated customers and the realism check, the pilot, fifteen checks and how the judges were tested, keep rates and the coverage grid, one training example per model call and the loss mask, SFT-2a against SFT-2b, results on the golden set and the failures left, the second round (the "shortly" repair, fill runs, a coding agent as the teacher) and why it did not beat the first, the release gate, what went wrong, cost, and likely interview questions with answers |

Each PDF is built from the HTML file of the same name in `src/`. After editing it, rebuild with:

```bash
./guide/build.sh
```

(This needs Google Chrome; set `CHROME` to another Chrome or Chromium binary if it is not in `/Applications`.)
