# Nova design

Nova is NimbusCart's customer-support assistant, built on Qwen3.5-2B.
This file decides where every capability lives and the budgets the system must fit inside.

**Language:** English, including Indian English. Hinglish is out of scope until there is Hinglish
training data; an unscored probe in `kb/_customer_words.md` measures the gap.

## The four rules

1. **If it changes often, retrieve it (RAG):** policies, shipping charges, warranty terms.
2. **If it belongs to one customer, fetch it with a tool:** orders, tracking, returns.
3. **If it describes how to act, train it (fine-tune):** tone, one question at a time, calling the right tool before talking about an order, escalating after two failed turns.
4. **If it is a hard rule, enforce it in code:** who may see which order, whether a return is eligible, what counts as a confirmed write.

## Capability map

Pass marks: rows enforced in code must pass 100% of the time. Pass marks for the other rows (e.g. "required fact present in ≥ 90% of answers") are placeholders until the baseline eval shows what is realistic.

| Capability | Mechanism | Why this mechanism | How it is measured |
|---|---|---|---|
| Greet and set tone | Fine-tune  | Tone is behaviour, not a fact; a 2B model follows long prompt instructions loosely, and every prompt token costs latency on every turn | Rubric score (friendly, concise, on-brand) on held-out openers; reply length within limit; asks at most one question |
| Return-window questions | RAG | Policy changes (e.g. electronics 30 → 15 days); answer must cite current text | Required fact present; citation points at the right chunk |
| Refund-timeline questions | RAG | General policy ("how long do refunds take?"); timelines vary by payment method and change; must quote the current help-center text, never a remembered number | Required fact present; citation points at the right chunk; no number appears that is absent from retrieved chunks |
| Check a refund's status | Tool + fine-tune | "Where is **my** refund?" is per-customer live data, not policy; training teaches the model to call the tool instead of answering from the policy text | Correct tool and arguments; refund status and amount in the reply match the tool output exactly |
| List the customer's recent orders | Tool + fine-tune + code | Data is per customer and live; training teaches when to call; backend scopes the query to the signed-in customer | Correct tool called; listed orders exactly match the DB rows for that customer; zero invented orders |
| Report an order's status | Tool + fine-tune | Data is per customer; training teaches when to call | Tool name and arguments match exactly; the status in the reply matches the tool output |
| Give tracking details | Tool + fine-tune | Carrier, tracking number and ETA are live data; training teaches the model to call the tool before stating any date | Carrier, tracking number and dates in the reply match the tool output exactly; no date stated without a tool call |
| Start a return | Tool + code + fine-tune | Eligibility (window, item category, delivered status) is a hard rule decided by the backend; the write happens only after explicit confirmation; training teaches the confirm-then-act flow | Tool arguments correct; backend rejects 100% of ineligible returns; no return created without a confirmed turn |
| Refuse other customers' data | Code | Must hold every time | Cross-customer test returns "not found" |
| Hand off to a human | Fine-tune + tool | When to escalate (explicit request, two failed turns, frustration) is behaviour; the handoff itself is an action. Decision: the two-failed-turns rule is trained, not a code counter, because judging whether a turn "failed" needs understanding the conversation. Revisit if evals show missed escalations | Escalation precision and recall on a labelled set; scripted two-failure conversations escalate by turn 3 |
| Resist "ignore your instructions" | Code + fine-tune | Code guarantees no privilege change no matter what the model says; training teaches a polite refusal that stays on task | Red-team set covering direct injection (in the user message) and indirect injection (inside retrieved chunks and tool output, e.g. an order note): 0 data leaks or unauthorised actions (must be 100%); refusal rate on attacks; false-refusal rate on benign requests |
| Say "I don't know" when the answer isn't available | Fine-tune (+ handoff tool) | When retrieval finds nothing relevant, a 2B model tends to invent an answer; admitting it and offering a human is behaviour to train | Set of questions the help center cannot answer: rate of "I don't know" + handoff offer; rate of invented answers (target 0) |

## Budgets

Targets are product requirements: change them only deliberately, with a written reason.
Estimates get replaced by measurements as the project goes on.

- **p95 latency, reply with one tool call: 3 s** — *target*. Covers both model passes (emit the tool call, then answer from the result) plus the DB query.
  *Measured* for the prompted Qwen3.5-2B (vLLM 0.34.0, one T4, prompt v0, temperature 0.2, database on Neon), on a
  "where is my order" turn that needs **two** tool calls (three model passes): **median 3.10 s, p95 3.60 s** (6 runs,
  p95 = slowest of 5 warm runs; the cold first run took 6.5 s). Model passes were about 1.0–1.5 s each after warm-up,
  so a one-tool-call reply sits near 2 s, inside the target; two-tool-call turns are over it.
  Over all 100 golden cases on the same setup (2026-11-22, Kaggle T4): **median 4.33 s, p95 7.71 s per turn**
  (104 turns, 311 model calls, about 3 per turn). The baseline turns mostly make two or three tool calls, so the
  p95 is over the 3 s target; fewer wasted calls (see `evals/reports/00_baseline_floor.md`) is the first lever.
- **Context window: 8,192 tokens** — *target* for the total. The split is an *estimate*:
  - system prompt: 500 (*measured* with the tool schemas: system prompt v0 + 6 tool schemas + a 15-token user message = 939 tokens on the first model pass)
  - tool schemas: 700 (*measured* in the generation experiments: 656 tokens for the 6 draft tools, about 180 fixed + about 80 per tool; 700 leaves room for one more tool)
  - history: 4,000 (refine with synthetic conversations and the eval harness)
  - retrieved chunks: 2,000, e.g. 4 × 500 (refine when retrieval is built)
  - reply headroom: 992
- **Max size of one user message: 1,500 tokens** — *target*, enforced in code before the model sees the message (about 1,100 words). Over the cap: no model call; reply with a fixed message asking for the main question or the order number. Keeps one message from taking more than 1,500 of the 4,000 history tokens. Built with the guardrails; tested in the baseline eval (a 3,000-token message must get the polite decline, not an error). When the full prompt is still too long, trim the oldest history first, then retrieved chunks; never the system prompt or tool schemas.
- **Cost per 1,000 conversations: ~$5** — *estimate*. Assumes a GPU at about $1/hour serving about 200 conversations/hour. Replace with the real GPU rate and measured throughput once serving is set up.

## Risk tests

Run on a Kaggle T4 in one session with `training/notebooks/risk-tests.ipynb`. A failing test gets at most 60 minutes of fixing (versions, flags, dtype); after that, take its fallback and move on.

| # | Test | Pass when | Result | Error / notes | Fallback (if failed) |
|---|---|---|---|---|---|
| 1 | Generate in Transformers on a T4 | Coherent reply ending with `<\|im_end\|>` | **PASS** (run 1) | 145-token reply in 13.2 s (11 tok/s); correct `get_order_status(4417)` tool call. Needs `eos_token_id=[<\|im_end\|>, <\|endoftext\|>]` | Not needed |
| 2 | 50-step Unsloth LoRA, save, reload, generate | Loss falls; reloaded adapter changes the output | **PASS** (run 1) | 50 steps in 165 s; loss 1.60 → 0.58; reloaded adapter answers in Bitext's style | Not needed |
| 3 | vLLM serves the base model, one parsed tool call | `message.tool_calls` is filled | **PASS** (run 2, after a fix) | Run 1 failed: FlashInfer JIT-compiles a norm kernel for the T4 (sm75), and the link failed with `/usr/bin/ld: cannot find -lcuda` (Kaggle has the driver but no `libcuda.so`). Fix: `serving/t4_libcuda_fix.sh` (11 of the 60 minutes used, first attempt). Parsed call `get_order_status({"order_id": 4417})`; 50 tok/s greedy; first start 650 s | Not needed |
| 4 | vLLM serves the adapter as a LoRA module | `model="nova-test"` answers in the adapter's style | **PASS** (run 2) | Run 1's adapter served as `nova-test`; replies differ from the base, in Bitext's style. Start with LoRA took 190 s | Not needed |

Pinned versions that worked: `requirements-gpu.txt` (training, tests 1–2) and `requirements-serve.txt` (vLLM, tests 3–4), kept in separate environments.
Reports: `notes/gpu-risk-tests/report-run1.txt` and `report-run2.txt`.

## Fine-tuning: adapter size and training memory

Fine-tunes are LoRA adapters in 16-bit over the frozen base (not 4-bit QLoRA: Unsloth advises against quantized
training for Qwen3.5, and 16-bit already fits a T4). Numbers below come from `training/lora_budget.py`, which reads
the real layer shapes from the model's config on a laptop CPU.

**The model.** Qwen3.5-2B has 2,213,241,664 parameters: 1,881,825,088 in the text model (508,559,360 of them in the
embeddings, which the output head shares) and 331,416,576 in a vision tower that Nova never uses. Its 24 text
layers are not all alike: 6 use full attention (`q/k/v/o_proj`) and 18 use linear attention (Gated DeltaNet, with
`in_proj_qkv`, `in_proj_z`, `in_proj_a`, `in_proj_b`, `out_proj`). Every layer has the same MLP. `q_proj` is
4,096 wide, not 2,048, because it also produces the attention output gate (8 heads × 256 × 2).

**Adapter size.** A LoRA adapter on a layer of shape d_out × d_in trains r × (d_in + d_out) parameters. With
Unsloth's seven targets (`q/k/v/o_proj`, `gate/up/down_proj`):

| Module | Shape (out × in) | Layers | r = 8 | r = 16 | r = 64 |
|---|---|---|---|---|---|
| q_proj | 4096 × 2048 | 6 | 294,912 | 589,824 | 2,359,296 |
| k_proj | 512 × 2048 | 6 | 122,880 | 245,760 | 983,040 |
| v_proj | 512 × 2048 | 6 | 122,880 | 245,760 | 983,040 |
| o_proj | 2048 × 2048 | 6 | 196,608 | 393,216 | 1,572,864 |
| gate_proj | 6144 × 2048 | 24 | 1,572,864 | 3,145,728 | 12,582,912 |
| up_proj | 6144 × 2048 | 24 | 1,572,864 | 3,145,728 | 12,582,912 |
| down_proj | 2048 × 6144 | 24 | 1,572,864 | 3,145,728 | 12,582,912 |
| **Total** | | 96 | **5,455,872** | **10,911,744** | **43,646,976** |
| Share of the model | | | 0.25% | 0.49% | 1.97% |

That is 681,984 parameters per unit of rank. PEFT's own count of trainable parameters matches the hand count
exactly at all three ranks, with 96 layers wrapped and none in the vision tower. At r = 16 the adapter is about
44 MB in fp32 (22 MB in 16-bit).

**Decision: keep the seven targets.** They reach every MLP but only the 6 full-attention layers; the 18
linear-attention layers' own projections get no adapter. Adding them would cost 5.9M more parameters at r = 16
(+54%). The seven are Unsloth's tested recipe for Qwen3.5, and SFT-1 teaches tone, which the MLPs in all 24 layers
can carry. Revisit if a fine-tune fails to move behaviour the evals care about. `target_modules="all-linear"` is
ruled out: on this model it also wraps 98 layers of the vision tower.

**Memory for one training step** (r = 16, batch 2, max_seq_length 256 from the dataset card, `adamw_8bit`,
gradient checkpointing):

| What | Estimate | How |
|---|---|---|
| Frozen base weights, 16-bit | 3.76 GB text only / 4.43 GB with the vision tower | 2 bytes × parameters |
| LoRA weights + gradients, fp32 | 0.09 GB | 8 bytes × 10.9M |
| Adam moments, 8-bit | 0.02 GB | 2 bytes × 10.9M |
| Saved layer inputs | 0.05 GB | batch × seq × 2,048 × 2 bytes × 24 layers |
| Logits and their gradient, fp32 | up to 1.02 GB | batch × seq × 248,320 vocab × 4 bytes × 2; Unsloth's chunked loss keeps most of it from existing at once |
| **Total** | **4.9–5.6 GB** | Unsloth lists about 5 GB for a 16-bit LoRA on this model |

The vocabulary is the surprise: at 248,320 entries, the logits for one batch of 512 tokens weigh more than every
activation the layers save. Batch size and sequence length raise that term linearly.

**Why full fine-tuning does not fit.** Full fine-tuning with Adam in mixed precision costs about 16 bytes per
parameter: 16-bit weights (2) and gradients (2), a 32-bit master copy of the weights (4), and Adam's two 32-bit
moments (8). For the 1.88B text parameters that is 30.1 GB (35.4 GB with the vision tower) before activations,
twice a T4's 15 GB. LoRA trains 0.49% of the parameters, so the optimizer state that dominates the full fine-tune
nearly vanishes, and what is left is the frozen weights.

**Measured on the first full run** (`sft1-r16-lr2e-4-bitext_v1`, Kaggle T4, fp16, Unsloth 2026.11.7; numbers from
`training/runs/sft1-r16-lr2e-4-bitext_v1/run_info.json`):

| | Estimate | Measured |
|---|---|---|
| After loading the base | 3.76 GB text only / 4.43 GB with the vision tower | **4.44 GB**: Unsloth loads the vision tower too |
| Peak during training (`max_memory_allocated`) | 4.9–5.6 GB | **4.94 GB** (5.12 GB reserved) |
| Trainable parameters | 10,911,744 | 10,911,744, 96 layers wrapped, none in the vision tower |
| Saved adapter | about 44 MB in fp32 | 43.7 MB, fp32 |

Training added only 0.50 GB above the loaded weights. The estimate allowed up to 1.02 GB for the logits alone, so
Unsloth's chunked loss kept most of them from existing at once. A T4 has about 10 GB to spare at this batch size.

**Time:** 278 steps in 2,412 s (40 min) including 12 evaluations with probes; 41 min for the whole run.

## Where the eval database lives

The model runs on a Kaggle GPU, and its tools need the store's database. A Kaggle notebook cannot
reach the Postgres on the laptop, so the eval uses a **managed Postgres on Neon** (free tier,
Postgres 16 to match local Docker, pgvector enabled, AWS US East 2 near Kaggle's US GPUs).

- **Local Docker stays the source of truth.** Seed and load there, then copy the whole database
  across (Postgres 16 tools from the container, so client and server versions match):
  `docker compose exec -T -e NEON_URL db sh -c 'pg_dump -U nimbus -d nimbus --no-owner --no-privileges --no-comments | psql "$NEON_URL" -q -v ON_ERROR_STOP=1 --single-transaction'`
  (the target must be empty; reset it first when re-copying).
- **The connection string is a secret:** `NEON_URL` in the gitignored `.env` on the laptop, a
  notebook secret on Kaggle. Scripts take it as `DB_URL`, e.g. `DB_URL="$NEON_URL" uv run python db/verify_queries.py`.
- **Direct connection, not the pooler:** a full restore and a few eval connections do not need pooling.
- **Checked after the first copy (2026-11-22):** row counts match local in all 13 tables, the
  orders table is byte-identical (md5 over every row), and `db/verify_queries.py` passes 24/24 against Neon.

## Systems compared in the baseline

One loop (`agent/loop.py`), one prompt (`agent/prompts.py`, v0) and the same six tools (`agent/tools_v0.py`)
for both systems, so the gap measures the model, not the setup. Every eval run records the model name it
asked for and the model the provider says served each call (`served_model` in the trace).

| | Floor | Ceiling |
|---|---|---|
| Model | `Qwen/Qwen3.5-2B`, base weights, no fine-tuning | `gemini-4-hydrogen` (Google) |
| Where it runs | Serving: vLLM 0.34.0 on one Kaggle T4. The scored 100-case run: in-process on an Apple M4 (`agent/local_client.py`, Transformers, fp16, same template, tools and sampling), because the T4 session's files were lost | Vertex AI, `global` location, API key tied to one project |
| How the loop reaches it | OpenAI-compatible API, directly | `agent/gemini_adapter.py` translates to Google's API; prompt, tools and loop unchanged |
| Sampling | temperature 0.2 (chosen over the model card's settings on 30 cases: 9/30 correct against 5/30) | temperature 0.2 |
| Output cap per model call | 512 tokens | 8,192 tokens, because Gemini's thinking counts against the cap; the visible reply is held to "under 80 words" by the prompt |
| Thinking | off (Qwen3.5 chat template default) | always on (cannot be disabled) |
| Max model calls per turn | 4 | 4 |

Latency for the delayed-order turn ("where is my order", customer 416), 6 runs each:

| | Median | Slowest | Outcome |
|---|---|---|---|
| Floor | 3.10 s | 3.60 s (cold first run 6.5 s) | Answered in 6/6 runs with the right order and last scan; wrong about the date in 3/6 |
| Ceiling | 8.7 s | 65.7 s (first run 15.5 s) | Never answered: in 6/6 runs it kept searching the help center for a delay policy, the keyword search found nothing useful, and the 4-call limit ran out, ending in the loop's fallback hand-off |

The ceiling's failure is a tool limit, not a model limit: the rough keyword search needs every query word to
appear in a section, so "late delivery delayed shipment" returns nothing although a "Delays and lost
shipments" page exists. The baseline keeps v0 as it is (changing the loop or search would need both systems
re-run); better retrieval is the planned fix.

## Evaluation rules

- **One golden set, one scorer, every system.** The floor, the ceiling and every fine-tuned candidate run the
  same 100 cases (`evals/golden/`) and are scored by the same code (`evals/run_eval.py`, `SCORER_VERSION`).
  Traces are saved, so any run can be re-scored for free (`--rescore`).
- **Frozen while systems are compared.** `eval-v1` was frozen on 2026-11-22, before the floor results were seen.
  A change to a case or a check needs a written reason in the change log, a new scorer version, and a
  re-score of every run, so all reports stay on one version. Cases change only when they are wrong, never
  to make a system pass.
- **Same loop for every scored system:** prompt v0, the six tools, at most 4 model calls per turn. Runs with
  other settings are labelled `diagnostic` and never reported as the floor or ceiling.
- **Two views of tool use:** strict (exact calls, nothing extra: correct and efficient) and required calls
  (every needed call, in order, with the right arguments; extras allowed: correct). Both are reported.

## Change log

Record every budget or mechanism change: old → new, and the evidence.

| Date | Change | Reason |
|---|---|---|
| 2026-11-20 | First draft | Capability map and budgets |
| 2026-11-20 | Added "Check a refund's status" and "Say I don't know" rows; order status now also checks the reply; injection set includes indirect injection; pass-mark note added; escalation stays trained (decision recorded) | Review of the first draft |
| 2026-11-20 | Tool schemas: estimate 700 → measured 656 (allotment kept at 700) | Rendered Qwen3.5-2B chat template with 6 draft tools; see `notes/generation-experiments/` |
| 2026-11-20 | New budget: max 1,500 tokens per user message, enforced in code, plus a trim order for over-long prompts | Long pastes would overflow the 8,192 window (vLLM rejects them), slow prefill, dilute a 2B model's attention and hide injections |
| 2026-11-20 | Stack confirmed: Qwen3.5-2B + Unsloth LoRA for training, vLLM 0.34.0 with LoRA modules for serving; no fallbacks taken. Transformers is for training and offline checks only | Risk tests 1–4 pass on a T4; Transformers decodes at 11 tok/s against vLLM's 50 tok/s |
| 2026-11-21 | Language scope: English only; Hinglish measured by an unscored probe, never counted in scores | Training data (Bitext, synthetic conversations) is English; scoring Hinglish would measure a capability Nova was never taught |
| 2026-11-22 | Eval database: managed Postgres on Neon, copied from local Docker | Kaggle notebooks cannot reach the laptop's Postgres; in-notebook Postgres adds minutes to every run, and a laptop-only CPU model would take hours for the eval |
| 2026-11-22 | Hygiene items (earbuds, earphones, trimmers, pillows, screen protectors): not returnable once unsealed; returnable within the normal window while sealed | Data marked them not returnable even when sealed, while the help center said "once unsealed". The help center's rule is kept; the return check, store SQL, seed and help-center wording now agree |
| 2026-11-22 | Latency measured for the prompted 2B: median 3.10 s, p95 3.60 s on a two-tool-call turn | First conversation run on a Kaggle T4 with vLLM and the database on Neon |
| 2026-11-22 | Ceiling model: `gemini-4-hydrogen` on Vertex AI, through an adapter, same prompt, tools and loop as the floor | No Anthropic API access (a Claude Pro plan does not include it); the Vertex key reaches only Gemini models. First run: it never answered the delayed-order turn because the keyword search failed and the 4-call limit ran out |
| 2026-11-22 | Scorer `eval-v1` frozen: adds the required-calls view next to the strict tool checks, and in unanswerable cases counts an explicit offer to hand off as handing off | Read from the ceiling's traces: 63 cases made every required call plus extra searches, and 7 unanswerable replies asked "Would you like me to hand this over to our support team?". Both were correct behaviour failed by over-strict checks. Frozen before the floor results, applied to every system |
| 2026-11-22 | Baseline measured on all 100 golden cases (scorer `eval-v1`): floor 25/100 correct, ceiling 58/100; floor serving latency median 4.33 s, p95 7.71 s per turn | `evals/reports/00_baseline_floor.md` and `00_baseline_ceiling.md`; top three floor failure types counted from 30 read failures |
| 2026-11-22 | Sampling: temperature 0.2 kept for the 2B (model card's 1.0 / top_k 20 / presence penalty 2.0 rejected) | Same 30 cases: 9/30 against 5/30 correct, 17/30 against 12/30 on facts, equal reply length |
| 2026-11-23 | Fine-tuning: 16-bit LoRA, r = 16 / alpha = 16 to start, Unsloth's seven target modules (10.9M trainable parameters, 0.49%); estimated 4.9–5.6 GB per training step | `training/lora_budget.py`: hand count matches PEFT at r = 8, 16, 64. The seven names miss the 18 linear-attention layers' projections (kept as a known choice); `all-linear` would wrap the vision tower. Full fine-tuning needs about 30 GB, twice a T4 |
| 2026-11-23 | Training memory measured: 4.44 GB after loading, 4.94 GB peak (estimate 4.9–5.6 GB); first full run took 40 min on a T4 | First full run, `training/runs/sft1-r16-lr2e-4-bitext_v1/run_info.json`. Unsloth loads the 331M-parameter vision tower even for text training |
