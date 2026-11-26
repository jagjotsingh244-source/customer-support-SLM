# Serving formats: adapter, merged 16-bit, FP8 and a 4-bit GGUF

Exporting a fine-tune changes the model, so each way of shipping it was measured like a new model: the same
golden set, the same agent configuration, the same GPU. The model is the second fine-tune, SFT-2a v1
(`123jagjot/sft2a-r16-lr2e-4-traj_v1`), which ships behind the guard layer.

**Result.** No format costs measurable quality. On the golden set (107 cases, three runs each) the adapter scores
66%, the merged model 64% and FP8 69%, and the 95% intervals overlap almost completely. The template check passed:
the server builds the same prompt, token for token, that training rendered. FP8 is the fastest: 54% more tokens
per second for one conversation than the adapter, 34% more at 32 at once, and a third less time to the first token.
It is also the only format under the 3 s p95 latency budget in these runs. The 4-bit GGUF runs on a Mac and passes
27 of the 30 smoke cases, against 29 for the same file in bf16 on the same Mac and for every vLLM format; it needs llama.cpp's `--reasoning off` flag, or the
model thinks before every answer, which the training data never did.

**Decision** (`DESIGN.md`, change log 2026-11-26): FP8 ships. The adapter repo stays the source of truth. Each
release is merged and served with `--quantization fp8`.

## What was exported

| Format | Where | Size | How it is made |
|---|---|---|---|
| Base + LoRA adapter | `123jagjot/sft2a-r16-lr2e-4-traj_v1` (private) | 44 MB | Training output; holds the tokenizer and the chat template it was trained with |
| Merged, 16-bit | `123jagjot/nova-sft2a-v1-merged` (private) | 4.4 GB | `serving/export_formats.py merge`: the adapter merged into `Qwen/Qwen3.5-2B` (the base vLLM serves it on), tokenizer and template files copied from the adapter |
| FP8 | made at load time from the merged model | 2.4 GB on the GPU | `vllm serve <merged> --quantization fp8` (weights and activations in 8-bit floating point; the L4 is an Ada-generation card with FP8 support) |
| GGUF q4_k_m | `123jagjot/nova-sft2a-v1-gguf` (private) | 1.3 GB | llama.cpp `convert_hf_to_gguf.py` (bf16) then `llama-quantize q4_k_m`, llama.cpp commit 5917b39 |

**The merge was checked before it was saved** (`merge_check.json` in the merged repo). Of 618 tensors, 96 changed:
exactly the adapter's targets (the q/k/v/o projections of the 6 attention layers and the three MLP projections
of all 24 layers). No other tensor moved by a single bit. On three prompts, the merged model's next-token logits
differ from base + adapter (unmerged, in PEFT) by at most 0.22, which is bf16 rounding, and the top token is the
same on all three.

## Template check: training and serving build the same prompt

`serving/template_check.py` put a pass-through proxy in front of vLLM, ran ten golden cases through the agent
(three of them multi-turn), and kept every request the agent sent. Ten requests were picked to cover the four
shapes a request can have: first turn or later turn, with the customer's message or a tool result last. Each was
rendered two ways:

- **training**: `agent/chat_template.py` then the tokenizer's `apply_chat_template(..., add_generation_prompt=True)`,
  as `training/masking.py` does;
- **server**: vLLM's `/tokenize` endpoint, which runs the same chat preprocessing as `/v1/chat/completions`. The
  `prompt_tokens` vLLM reported for the real request was a third check on the length.

| Server | Requests | Prompt lengths | Training tokenizer (the adapter's) | Base model's tokenizer |
|---|---|---|---|---|
| Base + adapter | 10 | 1,158–2,274 tokens | 10/10 identical | 10/10 identical |
| Merged | 10 | 1,158–2,274 tokens | 10/10 identical | 10/10 identical |

End of turn: `<|im_end|>` (id 248046) is the tokenizer's end-of-sequence token on both sides; both configs add
`<|endoftext|>` (248044) as a stop token. Across the 9 golden runs, no model call ended on the token limit.

The template files are **not** byte-identical: the adapter carries Unsloth's copy of Qwen's template, which adds
a `developer` role, merges two leading system messages and drops some error checks. None of that touches a
request Nova sends (one system message, then user, assistant and tool messages), which is why the tokens match.
The merged model ships with the training copy anyway, so the file that served is the file that trained.

## Golden set, three runs per format

Same configuration for all nine runs: prompt v3, tools v2, conversation state, guards and hand-off rules on,
temperature 0.2, one GCP L4 (`g2-standard-8`), vLLM 0.34.0, `--max-model-len 8192 --gpu-memory-utilization 0.9`.
Scorer `eval-v3`, `all_required`; intervals are 95% bootstrap over cases (`evals/compare_systems.py`).

| Format | Order tasks | Policy | Old policy | Returns | Escalation | Unanswerable | Adversarial | **All** | Grounding issues / 100 replies | Privacy violations |
|---|---|---|---|---|---|---|---|---|---|---|
| Base + adapter | 61 | 65 | 73 | 40 | 73 | 67 | 97 | **66** [58–74] | 3.6 | 0 |
| Merged 16-bit | 60 | 67 | 67 | 44 | 70 | 60 | 94 | **64** [56–73] | 2.7 | 0 |
| FP8 | 72 | 69 | 67 | 47 | 77 | 60 | 94 | **69** [61–77] | 3.0 | 0 |

The spread between formats (5 points) is smaller than the interval of any one of them (about 16 points), so this
says "no measurable loss", not "FP8 is better". Per-case results are in the runs
`evals/runs/2026-11-26_golden-sft2a-{adapter,merged,fp8}-l4{,-r2,-r3}`. The adapter scored 66% here and 64% in
the comparison runs of 2026-11-25 on the same kind of GPU. That is the same within noise, so serving through
this setup reproduces the earlier numbers.

## Memory and speed

Memory comes from the vLLM startup log (`serving/formats/memory-*.txt`). Speed comes from
`serving/decode_speed.py`: a real agent request (1,161 prompt tokens: system prompt, state and tool schemas)
with 256 output tokens forced, greedy, median of three rounds, the same for every format.

| Format | Weights on the GPU | KV cache | Conversations of 8,192 tokens that fit at once | Time to first token | Tokens/s, 1 conversation | Tokens/s, 8 at once | Tokens/s, 32 at once |
|---|---|---|---|---|---|---|---|
| Base + adapter | 3.62 GiB | 15.5 GiB (840k tokens) | 102 | 0.62 s | 55.5 | 400 | 1,202 |
| Merged 16-bit | 3.56 GiB | 15.5 GiB (868k tokens) | 106 | 0.55 s | 62.8 | 440 | 1,292 |
| FP8 | 2.40 GiB | 16.6 GiB (938k tokens) | 115 | 0.41 s | **85.7** | **599** | **1,615** |

Per-turn latency in the golden runs (model calls, tools and the database):

| Format | p50 | p95 | p95, turns with one tool call | How the three runs ran |
|---|---|---|---|---|
| Base + adapter | 2.13 s | 3.65 s | 3.14 s | one after another |
| Merged 16-bit | 2.04 s | 3.47 s | 2.75 s | all three at once, each on its own copy of the store |
| FP8 | 1.57 s | 2.73 s | 2.18 s | all three at once |

The merged and FP8 runs shared the GPU three ways, which can only make them slower, so the order holds. The
budget in `DESIGN.md` is 3 s at p95 for a reply with one tool call; at the median, every format is inside it.

Memory is not Nova's limit: even the adapter fits about 100 full-length conversations in the cache on a 24 GB
card. What FP8 buys is speed. A 2B model's decoding is limited by how fast the weights can be read from GPU
memory, and FP8 halves the bytes per weight. The adapter pays a little for LoRA: the extra matrix products on
every layer, and a slot reserved for adapter weights.

## The 4-bit GGUF, on a Mac

GGUF is for running Nova without a GPU server (llama.cpp, Ollama), not for production serving. It was run on an
Apple-silicon Mac with Homebrew's llama.cpp 1.0.0 and the 30-case smoke set (`evals/smoke.json`), on the
local copy of the store, once in q4_k_m and once in bf16 as a control (runs `2026-11-26_smoke-sft2a-gguf-{q4,bf16}-mac`):

    llama-server -m nova-sft2a-v1-q4_k_m.gguf --jinja --reasoning off -c 8192 -ngl 99 --port 8090

**The export bug this format had.** With llama.cpp's default (`--reasoning auto`), the model wrote a paragraph of
reasoning before every answer (83 output tokens for a simple order lookup instead of 32). The chat template
thinks only when `enable_thinking` is set to true. vLLM leaves it unset, as training did, so the prompt ends with
an empty `<think></think>` block. llama.cpp's `auto` sets it to true, so the model is asked to think, which it
was never trained to do. `--reasoning off` gives back the training prompt exactly (checked with llama-server's
`/apply-template`). Nothing errored either way; the output was just different. This is the failure the template
check exists for.

| Served as | Smoke cases passed | Failed cases | Model calls ending on the token limit | Format errors |
|---|---|---|---|---|
| vLLM on the L4, base + adapter (×3) | 28, 29, 29 of 30 | pol-012 every run; ret-006 once | 0 | 0 |
| vLLM, merged (×3) | 29, 29, 29 | pol-012 | 0 | 0 |
| vLLM, FP8 (×3) | 29, 29, 28 | pol-012; una-005 once | 0 | 0 |
| llama.cpp on the Mac, q4_k_m (×1) | **27** | pol-012, ord-002, ret-006 | 0 | 0 |
| llama.cpp on the Mac, bf16 GGUF (×1, control) | **29** | pol-012 | 0 | 0 |

The bf16 GGUF is the control: same Mac, same llama.cpp, same flags, only the 4-bit step removed. It scores what
vLLM scores, so llama.cpp and the conversion cost nothing. The two cases q4_k_m loses (ord-002, an order lookup,
and ret-006, a return) are the price of 4 bits. That is one run of 30 cases, so it is a direction, not a
measurement: a 7-point drop on the smoke set, consistent with Unsloth's warning that Qwen3.5 loses more than usual
to quantization. On the Mac, q4_k_m decodes at about 57 tokens/s against 26 for bf16 (median per call, Apple
silicon, Metal); p95 per turn 7.5 s against 10.2 s.

## Cost

Exports and runs: about 34 minutes of one L4 VM (₹50 of credit). Cost per 1,000 conversations is measured on
the deployment, under load: $0.16 at 50 customers at once (`evals/reports/06_serving.md`).

## Reproduce

    # on the GPU machine, after the adapter is in outputs/
    python serving/export_formats.py merge --adapter outputs/sft2a-r16-lr2e-4-traj_v1 --out /data/nova-sft2a-v1-merged
    ADAPTER=outputs/sft2a-r16-lr2e-4-traj_v1 MERGED=/data/nova-sft2a-v1-merged DATE=2026-11-26 \
        bash serving/compare_formats.sh adapter                    # one run after another
    ADAPTER=... MERGED=... DATE=2026-11-26 PARALLEL=1 bash serving/compare_formats.sh merged fp8
    uv run python evals/compare_systems.py --golden adapter=2026-11-26_golden-sft2a-adapter-l4,... merged=... fp8=...

Logs, the captured requests, memory lines and speed results are in `serving/formats/`.
