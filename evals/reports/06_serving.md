# Serving Nova: the model server, the deployment, cold starts, load and cost

Nova runs as three separately deployed parts, each configured only by environment variables:

| Part | Where | Why there |
|---|---|---|
| Model server: vLLM 0.34.0, the merged fine-tune in FP8, `serving/launch_vllm.sh` | Modal, one L4, **scale to zero** (`serving/modal_nova.py`) | The GPU is the expensive part and is needed only while someone is chatting |
| Backend: FastAPI, the agent loop, tools, guardrails, the confirm route (`api/app.py`, `Dockerfile`) | Google Cloud Run, `us-east4`, 2 vCPU / 4 GiB, scales to zero, public since 2026-11-26 (the demo; it was private until then) | Always reachable, little CPU, billed per request |
| Store: orders, help center, pgvector, three roles with row-level security | Neon (managed Postgres 16), US East | Persists through every restart; nothing lives on a GPU machine's disk |

**Result.** The served model scores what the notebook-era runs scored: golden pass@1 67% [59–75] through the
launch script, against 64% [56–73] in the comparison runs. The API key is enforced, and prefix caching cuts
time to first token from 73 to 42 ms. Deployed, Nova answered 2,091 turns across the three load levels with no
errors. At 50 simulated customers that is 6,720 conversations an hour, so **$0.16 (about ₹14) per 1,000
conversations**, from Modal's and Cloud Run's per-second prices and the measured throughput.

Two things miss their mark, and both are written down below rather than hidden. **Latency:** the deployed p95
per turn is 4.2 s at one customer and 8.7 s at 50, against a 3 s budget. **Cold start:** the endpoint first took 4 to
15 minutes to wake. Keeping Triton's and Inductor's kernel caches in the volume brought one measured cold start
down to 116 s, still about twice the one-minute mark. The rest is in "What would fix it".

## 1. The model server (`serving/launch_vllm.sh`)

One script holds every vLLM flag, with a line on why each is there. It is used both on the rented GPU and
inside the Modal container. It refuses to start without `NOVA_KEY`, and it can switch prefix caching off
(`PREFIX_CACHING=0`) for the measurement below. `serving/check_server.sh` ran these checks on a GCP L4
(nova-eval9), with the merged model pulled from the private Hub repo:

| Check | Result |
|---|---|
| Golden set ×3 against the server, shipping configuration (prompt v3, state, guards, hand-off rules) | **67%** [59–75]; comparison runs of 2026-11-25 64% [56–73]; format runs (FP8) 69% [61–77]. Same within the intervals |
| API key (`serving/server_checks.py auth`) | no key 401, wrong key 401, right key 200 |
| Time to first token, 20 different first-turn requests (median 1,169 prompt tokens), one at a time | **42 ms** with prefix caching, **73 ms** without (medians; max 44 / 77 ms). Hit rate in the log about 75% |
| 20 requests at once (real agent requests with tools) | all 20 usable (tool calls parsed, none left as text), 0.85 s for the whole burst, slowest 0.85 s |
| Cache and queue warnings | none: at most 3 requests running during the golden runs, nothing waiting. No `max_num_seqs` warning, so the default 64 stays |
| Memory | weights 2.4 GiB; KV cache 17.1 GiB = 967k tokens, 118 conversations of 8,192 tokens at once |

Why prefix caching matters for Nova in particular: Qwen's template puts the tool schemas first (about 780
tokens), and every request carries the same ones. The system prompt names the signed-in customer, which ends
the shared part, so moving the name to the end of the system prompt would make more of every prompt reusable.
That would change the model's input, so it waits for the next prompt version.

Per-category golden results:

| Run | Order tasks | Policy | Old policy | Returns | Escalation | Unanswerable | Adversarial | **All** | Grounding issues / 100 replies | p50 / p95 per turn |
|---|---|---|---|---|---|---|---|---|---|---|
| Served by the launch script (FP8, key) ×3 | 71 | 65 | 60 | 47 | 73 | 62 | 92 | **67** | 3.9 | 1.67 / 2.93 s |
| FP8, format comparison ×3 | 72 | 69 | 67 | 47 | 77 | 60 | 94 | **69** | 3.0 | 1.57 / 2.73 s |
| SFT-2a v1, comparison runs ×3 (prompt v2, no guards) | 64 | 75 | 60 | 44 | 47 | 62 | 89 | **64** | 5.4 | 2.37 / 4.54 s |

vLLM logs one deprecation warning: `--quantization fp8` is to be renamed `fp8_per_tensor`, the same method. The
flag stays as measured until vLLM is upgraded.

## 2. The deployment

- **Store.** The Neon database already held the seeded store. Its contents were checked against the local one
  table by table, by row count and a checksum over every row (help-center chunks included): identical, so
  nothing was reloaded. The backend connects as the three limited roles. The owner's password is not in the
  backend's settings, only the host and database name.
- **Backend image** (`Dockerfile`): Python 3.12, the locked `api` and `rag` dependencies with torch's CPU build
  (the backend only embeds short queries), and the embedding model and tokenizer baked in, so a cold start
  downloads nothing. Settings come only from the environment at deploy time (`DATABASE_URL`, `MODEL_BASE_URL`,
  `NOVA_KEY`, the role passwords, `NOW_MODE=real`). Built by Cloud Build, about 2 minutes.
- **Routes**: `/demo-login` (eval-partition customers only, sets a session cookie), `/chat` (one turn through the
  same loop, tools, guards and hand-off rules the golden set measures), `/health` (database, and whether the
  model is awake, without failing when it is asleep), `/warmup` (wakes the model and waits until it answers: the
  "Waking Nova up..." button calls it), and the existing confirm route, now reading the customer from the session.
- **Model endpoint** (`serving/modal_nova.py`): `launch_vllm.sh` in a Modal container on one L4, with up to 64
  requests at once, a single container, and the GPU released after 60 s without a request. The weights come from a
  Modal volume uploaded from this machine, so no Hub token goes to Modal. A single 4.4 GB upload failed halfway,
  so the weights went as five 1 GB shards, checked tensor by tensor against the original.

**Found in deployment: a scale-to-zero database drops idle connections.** The first sign-in after a quiet spell
failed with `AdminShutdown`: Neon suspends its compute after a few idle minutes and closes every connection. The
backend's pool now pings a connection pair that has been idle for more than a minute before using it, and
replaces any pair that failed during a turn (`tests/test_api_sessions.py` closes them all and signs in again).

**Kept private until the demo.** Until 2026-11-26 the backend accepted only requests with a Google identity token, so an unattended URL could not
run up GPU time. It was opened for the demo with
`gcloud run services add-iam-policy-binding nova-backend --region us-east4 --member=allUsers --role=roles/run.invoker`
(`remove-iam-policy-binding` with the same arguments closes it). Open, anyone with the link can wake the GPU; the
spend is bounded by one container and by the Modal credit, after which the model stops answering.

## 3. Cold starts

Measured through the deployed backend (`serving/cold_start.py`): wait until Modal reports no running container,
call `/warmup`, then send one chat turn.

| Run | Wake-up (`/warmup`) | First chat turn after it | Notes |
|---|---|---|---|
| First boot ever | about 7 min | timed out (300 s client limit) | vLLM's compile cache was empty |
| 1 | 420 s | 2.7 s | |
| 2 | over 600 s (`/warmup` gave up at 10 min) | 282 s more | the turn waited for the same start to finish |
| 3 | 232 s | 2.9 s | |
| Before the load test (new image) | 599 s | — | the image had just been rebuilt |
| **After the cache fix** | **116 s** | 2.2 s | vLLM's engine start 39 s instead of 130–149 s |

Where the time goes, from the container's own log (runs 1–3):

| Step | Time |
|---|---|
| From the request to the container's process starting (finding an L4, loading the image) | 1 to 7 minutes, the largest and most variable part |
| Loading the weights (5 shards from the volume) and quantizing to FP8 | 7–8 s |
| vLLM's engine start: compiling the model graph, Triton kernels for the linear-attention layers, KV cache, CUDA graphs | 130–149 s |
| Server up to first answer | under 5 s |

vLLM's own compile cache was in the volume from the start. Triton's and Inductor's caches were not, so every
cold start rebuilt the kernels. With both in the volume too (one run, after the load test had filled them), the
engine start fell from 130–149 s to **39 s** and the whole cold start to **116 s**: about 16 s to get a container,
45 s of process start-up and imports, 8 s of weights, 39 s of engine start. That is one measurement; the
scheduling wait varies the most (16 s here, minutes before).

**What would fix it**, in order of effect:
1. Keep one container warm during a demo window (`min_containers=1` for an hour costs about $0.89). The
   `/warmup` button already does this on demand, and the UI should press it when the page opens.
2. A smaller image (vLLM without unused extras) and Modal's memory snapshots, which restore a started process
   instead of booting it.
3. `--enforce-eager` skips compiling and CUDA graphs, so start-up is faster but every token is slower.
   Measure it before choosing, as with every serving change.

The scheduling wait (finding a free L4) is outside the app; allowing a second card type would shorten it. The
L40S also supports FP8.

## 4. Load test

`serving/load_test.sh`: locust from this machine (`serving/locustfile.py`), back to back so the model stays warm.
Simulated customers sign in as eval-partition accounts and have 3-message conversations of golden-set
messages, with 2–6 s between messages. Every reply also reports its own server-side time, so the network between
this machine (India) and the backend (US East) is kept apart.

| Customers at once | Turns in 5 min | Conversations in 5 min | Errors | Server turn p50 / p95 | Model share p50 / p95 | Seen by the client p50 / p95 |
|---|---|---|---|---|---|---|
| 1 | 39 | 13 | 0 | 2.4 / 4.2 s | 1.9 / 3.3 s | 2.8 / 4.5 s |
| 10 | 429 | 148 | 0 | 2.3 / 4.5 s | 2.1 / 3.9 s | 2.7 / 4.9 s |
| 50 | 1,623 | 560 | 0 | 4.5 / 8.7 s | 3.9 / 7.5 s | 4.8 / 9.0 s |

The GPU, from vLLM's log over each level (`serving/load/vllm_engine_stats.log`):

| Customers | Prompt tokens/s | Generated tokens/s | Sequences running (mean / max) | Waiting (max) | KV cache used (max) | Prefix cache hits |
|---|---|---|---|---|---|---|
| 1 | 193 | 13 | 0.2 / 1 | 0 | 0.4% | 64% |
| 10 | 1,639 | 128 | 2.4 / 10 | 0 | 2.1% | 68% |
| 50 | 6,445 | 477 | 15.9 / 23 | 1 | 5.4% | 67% |

**Where the time goes.** At 50 customers nothing queues: vLLM never had more than one request waiting, and the
KV cache stayed under 6%. The GPU decoded 477 tokens/s, a third of what the same card did at 32 conversations in
the decode benchmark (1,615). The growth in model time comes from batching. About 6,400 prompt tokens a second
are prefilled next to the decoding, each turn makes 2–3 model calls (each one a round trip to Modal), and every
sequence slows down as the batch grows. The backend and database add about 0.5 s per turn at every level
(server turn minus model share).

**Against the 3 s p95 budget.** On the rented GPU, with the database and agent on the same machine, p95 was
2.9 s. Deployed, it is 4.2 s at one customer. The difference is the hops: backend to Modal on every model
call, and backend to Neon on every tool call, across providers. Ways to get it back: fewer model calls per turn
(the hand-off rules already save some), the customer's name at the end of the system prompt (a longer shared
prefix), and the backend in the same region as the GPU. Measure each one against this table.

## 5. Cost per 1,000 conversations

Measured throughput times per-second prices, which replaces the earlier estimates ($5 in `DESIGN.md`, $0.21 in
`evals/reports/04_comparison.md`):

- Model: Modal L4 at $0.000222/s ($0.80/h), plus the container's CPU and memory. Modal's bill for these runs put
  those at 11% of the GPU, so **$0.89/h** while awake. $0 while scaled to zero.
- Backend: Cloud Run, 2 vCPU and 4 GiB while serving requests, at the list price for `us-east4`, about
  **$0.21/h** while busy. $0 when idle.
- Database: Neon's free tier, $0.

| Load | Conversations an hour | Cost an hour | **Per 1,000 conversations** |
|---|---|---|---|
| 1 customer at a time | 156 | $1.10 | $7.05 (₹620) |
| 10 at once | 1,776 | $1.10 | $0.62 (₹55) |
| 50 at once | 6,720 | $1.10 | **$0.16 (₹14)** |

The price per conversation falls with load because the GPU costs the same an hour whether it serves one person
or fifty. At 50 it was still far from full, so a busier hour would be cheaper still. At 50 customers, though,
latency is far over budget. A demo with a handful of visitors pays about the one-customer row while the model is
awake, plus each cold start (5–10 minutes of GPU, $0.07–0.15) and nothing while it sleeps.

All of section 2–4 cost about $0.60 of Modal credit and under ₹20 of Cloud Run and Cloud Build; the GPU checks in
section 1 used about 11 minutes of the GCP L4 (about ₹16).

## 6. The chat page and streamed events

A turn takes several seconds: list the orders, read the tracking, then write. A blank box for that long reads as
broken. So `POST /chat/stream` sends **events**, as server-sent events, and the page (`ui/index.html`, one file
served by the backend at `/`) shows each one as it arrives:

| Event | Sent when | The page shows |
|---|---|---|
| `status` | a tool call starts (the model's or one the hand-off rules force) | "Checking your orders…", "Checking the tracking for order 12466…" (only a number is ever put into the line) |
| `status` with `waking` | the model endpoint has been idle past its scale-down window and does not answer | "Waking Nova up…" |
| `reply` | the reply has passed the grounding check and the output filter | the message |
| `confirm_card` | `propose_return` found the item returnable | the item, order and refund estimate, and a Confirm button that sends **only the proposal id** to `/returns/{id}/confirm`, which re-reads and re-checks everything |
| `handoff` | a ticket was opened | the ticket number, and when a person will reply (from the store's clock and the support hours) |
| `done` | the turn is over | input enabled again, thumbs up/down sent to `/feedback` with the turn's trace id |
| `error` | the turn failed (model unreachable) | a plain message; the conversation is put back as it was and the text returns to the box |

**The reply is never streamed token by token.** The output filter (links, a prompt echo, an action claim no tool
backs, personal data, tool names) reads the finished reply. Tokens on screen before it runs could not be taken
back, so the reply is held until the loop returns, and the status lines fill the wait. The page never calls the
model: every request goes to the backend, which holds the session, tools and checks. `/chat` runs the same
events and answers once, in JSON, for the load test and scripts.

**What the hold costs.** Streamed, the first words would appear about one time to first token after the final
model call starts. Buffered, they appear when that call has finished and the checks have run. So the hold is at
most the final call's latency plus the checks. `serving/stream_check.py` signs in as each demo customer, sends
their suggested message through the stream and times what arrives (10 turns, `serving/stream/mac.json`):

| Where | First status line, p50 / p95 | Reply, p50 / p95 | Hold (upper bound), p50 / p95 | Checks |
|---|---|---|---|---|
| Mac: the bf16 GGUF in llama.cpp, local store | 1.7 / 2.1 s | 7.3 / 10.6 s | 3.4 / 4.2 s | under 5 ms |
| Deployed: Modal L4 (FP8) + Cloud Run + Neon, timed from this machine in India | 0.9 / 4.5 s | 2.9 / 5.1 s | 0.8 / 1.2 s | about 1 ms (one 116 ms outlier on the first turn) |

Every turn, on both, showed a status line before its reply. Deployed, the first one arrives in under a second
and the reply at 2.9 s (p50), so a visitor sees Nova working about 2 s before the answer. The checks cost almost
nothing (about 1 ms); the hold is the time the model takes to write the reply: **at most 0.8 s at p50 and 1.2 s
at p95** on the L4, which the status lines cover. Measured on 2026-11-26 right after a cold start
(`serving/stream/deployed.json`); the 4.5 s first-event p95 is the first turn, which also warmed the backend.
Nothing here needed the progressive filtering (streaming with a hold-back window) that a slow hold would call
for.

**The public demo** opens on a contact list: five scenario customers first, then all 88 eval-partition customers with search (city and latest order shown; `demo_customer_list()` in `db/demo.sql` returns only those three fields). The other 412 customers are the training partition: chatting as them would flatter the model. A cold start shows "Nova is waking up. Sorry, the GPU sleeps when nobody's chatting (student budget). About 2 minutes." with a timer; the live one took about 100 s.

**Five demo customers**, each chosen to show one part of Nova (`DEMO_PERSONAS` in `api/app.py`; the picker shows
each with a message to try; `DEMO_CUSTOMERS` can narrow sign-in to a list):

| Customer | Scenario | What Nova does on the Mac |
|---|---|---|
| 57 | A parcel on its way | Lists the orders, reads the tracking, gives carrier, last scan and estimate |
| 116 | Returning something | Checks the order, proposes the return: Confirm card, ₹699 estimate |
| 137 | A parcel that never came | Reads the tracking (no scan for weeks), opens a ticket: hand-off card |
| 176 | A late order | Gives the old estimate and the last scan |
| 372 | A return window that has closed | **Opens a ticket instead of saying the window has closed** (below; the same deployed) |

**Found while testing, fixed: demo visitors shared one store.** After one visitor pressed Confirm, the next one
signed in as the same customer heard "your return is already confirmed". With `DEMO_RESET=1`, signing in first
calls `demo_reset()` (`db/demo.sql`), which deletes the returns and tickets the tools made for that one
customer. It runs with the owner's rights but only touches tool-made rows (ids from 900001) of an eval-partition
customer, and only the confirm role may call it (`tests/test_api_stream.py` checks all three), so the backend
still never holds the owner's password. Two visitors signed in as the same customer at once would still share
it; for a demo that is acceptable.

**Found while testing, not fixed: customer 372.** Asked "Can I return the induction cooktop I bought in October?",
Nova searched the returns policy but never looked at the delivery date, and handed off instead of saying the
15-day window had closed (both runs). It is a model behaviour, not a page bug, so it goes to the first weekly
review of traces as a candidate golden case.

## 7. Traces

A request log says a turn took 4 s and returned 200. It cannot say which order Nova looked up, what the tool
returned, or whether a check fired, so a bug report from a visitor could not be reproduced. Now every chat turn
on the demo is one **trace** in Langfuse Cloud (US region, free plan), sent by `api/tracing.py`:

    turn (the customer's message, Nova's reply, the cards the page showed)
      input_check            flags on the message
      model_call ×n          sizes, tokens, what the model asked for (never the prompt itself)
      tool:<name> ×n         arguments, a compact result, errors
        retrieval            help-center query, section ids and scores, whether the cutoff kept any
      rule:<name>            a hand-off or tracking check the code rules made on their own
      reply_checks           output-filter hits, grounding issues

Each trace is tagged with the model version, prompt version, help-center index version (`kb:104-dcbb2bdc`, a
fingerprint of every chunk) and clock mode, so comparing a new model with the current one is a filter. Each turn
also gets five scores (escalated, tool errors, grounding issues, filter hits, input flags), and a thumbs click
becomes a sixth score on the same trace, by its id. Everything is redacted before it leaves (PRIVACY.md);
`tests/test_tracing.py` checks the nesting, tags, scores and redaction with an in-memory exporter. Without the
keys nothing is sent, so tests and evals are unchanged.

**No dashboard yet, on purpose.** A demo with a handful of visitors would chart almost nothing, so the
dashboard was built once, checked, and removed. With real traffic it is the next step, and it needs no new code:
the tags and scores above are what it would chart. Four panels would cover a live system: hand-off and thumbs-up
rates per day with one line per model version (which is how a canary is compared with production), tool errors and
grounding issues per 100 replies, output-filter hits and flagged messages per day (a spike means an attack or a
bug), and p50 / p95 latency per step. Until then, a single trace answers "what happened in this conversation".

**First trace, first finding.** The first test turn (customer 372, "Can I return the induction cooktop I bought in
October?") shows why Nova hands off there: the help-center search found the right section, `returns-general#
return-window`, but scored it 0.631, under the 0.68 cutoff, so Nova had no policy to quote and passed the customer
to a person. The request log could never have shown that.

The weekly review of traces (thumbs-down and random turns, each failure tagged and routed to a fix) starts once
the demo has real visitors.

## Reproduce

    NOVA_KEY=... HF_TOKEN=... DATE=2026-11-26 bash serving/check_server.sh              # on the GPU machine
    gcloud builds submit --region us-east4 --tag us-east4-docker.pkg.dev/<project>/nova/backend:v2 .
    gcloud run deploy nova-backend --region us-east4 --image ... --env-vars-file <env.yaml> --cpu 2 --memory 4Gi \
        --min-instances 0 --max-instances 1 --session-affinity --timeout 900 --no-allow-unauthenticated
    uv run --group teacher modal deploy serving/modal_nova.py
    BACKEND_TOKEN=$(gcloud auth print-identity-token) uv run --group teacher python serving/cold_start.py --backend ... --runs 3
    BACKEND=... BACKEND_TOKEN=... bash serving/load_test.sh
    llama-server -m outputs/gguf/nova-sft2a-v1-bf16.gguf --jinja --reasoning off -c 8192 -ngl 99 --port 8090   # the Mac
    MODEL_BASE_URL=http://localhost:8090/v1 COOKIE_SECURE=0 DEMO_RESET=1 uv run --group api --group rag uvicorn api.app:app --port 8080
    uv run --group dev python serving/stream_check.py --base-url http://localhost:8080 --repeats 2 --out serving/stream/mac.json
