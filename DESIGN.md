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
