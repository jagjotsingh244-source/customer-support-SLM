# Lesson 0.4: risk tests on a Kaggle T4

Run 1: `training/notebooks/risk-tests.ipynb` (`report-run1.txt`). Run 2, vLLM only, with run 1's adapter attached:
`training/notebooks/risk-tests-vllm.ipynb` (`report-run2.txt`). Both on Kaggle, GPU T4 x2, 2026-11-20.

| Test | Run 1 | Run 2 |
|---|---|---|
| 1. Transformers generate on a T4 | PASS | |
| 2. Unsloth LoRA: train 50 steps, save, reload, generate | PASS | |
| 3. vLLM serves the base model with one parsed tool call | FAIL: engine core did not start | PASS after the libcuda fix |
| 4. vLLM serves the adapter as a LoRA module | FAIL: blocked by test 3 | PASS |

**Result: all four pass, no fallback taken.** Pins: `requirements-gpu.txt` (training) and
`requirements-serve.txt` (vLLM); T4 fix: `serving/t4_libcuda_fix.sh`.

## Findings

1. **Transformers on a T4 is slow: 11 tokens/s** (145 tokens in 13.2 s), slower than the Mac's
   about 21 tokens/s. Gated DeltaNet runs on slow reference kernels without `flash-linear-attention`
   and `causal-conv1d`. At this speed one reply takes about 13 s against a 3 s p95 budget, so
   Transformers is fine for training and offline evals but cannot be the serving engine.
   That makes the vLLM tests (3–4) matter.
2. **The T4 gives the same tool call as the Mac:** `get_order_status(order_id=4417)`, 31 tokens,
   ending with `<|im_end|>` once the stop-token fix is used.
3. **The Unsloth LoRA loop works end to end on Qwen3.5-2B:** loss 1.60 → 0.58 in 50 steps (165 s on 200
   rows); the saved adapter reloads and changes the output.
4. **Bitext replies contain template placeholders** such as `{{Online Company Portal Info}}` and
   `{{Online Order Interaction}}`. After only 50 steps the adapter already copies them into replies.
   Module 3 must replace or drop every `{{...}}` slot before training, and the evals should fail any
   reply that contains `{{`.
5. **Pin the training and serving environments separately.** Training used torch 2.11.0 (Kaggle's
   image); vLLM 0.34.0 installed its own torch 2.14.0 in a separate venv. Mixing them in one environment
   would have broken one or the other.
6. **A failing test needs its root cause in the report.** Run 1 kept only the last 2,500 characters of
   the vLLM log, which held vLLM's summary error, not the cause. The full log is in the run's Output.
7. **Why vLLM did not start (from `vllm-base.log`):** vLLM loaded the model, then ran a dummy forward pass
   to measure memory. Qwen3.5's gated norm calls FlashInfer's `gemma_rmsnorm`, which FlashInfer compiles on
   first use for the GPU's architecture (sm75 for a T4). Compiling worked; linking failed with
   `/usr/bin/ld: cannot find -lcuda`, because Kaggle's image has the driver (only as `libcuda.so.<version>`) but no
   `libcuda.so` file and no CUDA stubs folder. The other T4 messages in the log were not fatal: FlashAttention 2
   needs compute capability 8.0+ and FlashInfer sampling needs more than 7.5, so vLLM fell back for both.
   Lesson: newer serving stacks assume Ampere-or-newer GPUs; on a T4, expect kernels to be built on the spot
   and fallbacks to be used.
8. **Run 2 (`training/notebooks/risk-tests-vllm.ipynb`)** tries the fixes in order and stops at the first that
   serves: (A) link `libcuda.so` to the driver and add it to `LIBRARY_PATH`; (B) A + `--enforce-eager`;
   (C) A + FlashInfer removed; (D) A + vLLM 0.17.x. It stops starting new attempts after 60 minutes.
   **Attempt A worked first time (11 of the 60 minutes).** The driver was at
   `/usr/local/nvidia/lib64/libcuda.so.580.178.04`, not registered with `ldconfig`, and the CUDA stubs folder
   was empty. Every later notebook that starts vLLM on Kaggle runs `source serving/t4_libcuda_fix.sh` first.
9. **vLLM is about 4.5x faster than Transformers on the same T4:** 128 tokens in 2.6 s (50 tok/s) against
   11 tok/s. The tool-call request took 4.0 s, but it was the first request after start-up (cold); Module 10
   measures warm p95 latency against the 3 s budget.
10. **vLLM's `qwen3_coder` parser turns the XML-style call into OpenAI JSON:** `get_order_status`
    with arguments `{"order_id": 4417}`, an integer as the schema asks, and `content` is `None`. The agent loop
    in Module 6 reads `message.tool_calls`; it never parses `<tool_call>` text itself.
11. **Start-up is slow the first time:** 650 s for the first start (model download, FlashInfer kernel build,
    CUDA graph capture), 190 s for the second start with LoRA once the kernel was built. Cold starts matter
    when choosing a host in Module 10.
12. **The adapter serves next to the base:** one vLLM process answers both `Qwen/Qwen3.5-2B` and `nova-test`,
    and the adapter's reply matches what Unsloth produced in run 1 (same Bitext style and `{{...}}` slots).
13. **Sampling through vLLM, with the model card's `presence_penalty=2.0`** (5 runs, all stopped on their own):
    temperature 0.2 gave 115–131 tokens; the model card settings gave 92–234 tokens. The penalty narrowed the
    spread a little (Lesson 0.3, without it: 106–284), but the card settings still vary about 2.5x. Support stays at
    the low-temperature end.
