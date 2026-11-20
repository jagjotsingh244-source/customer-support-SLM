# Lesson 0.4: risk tests on a Kaggle T4

Notebook: `training/notebooks/risk-tests.ipynb`. Run 1: Kaggle, GPU T4 x2, 2026-11-20 (`report-run1.txt`).

| Test | Run 1 |
|---|---|
| 1. Transformers generate on a T4 | PASS |
| 2. Unsloth LoRA: train 50 steps, save, reload, generate | PASS |
| 3. vLLM serves the base model with one parsed tool call | FAIL: engine core did not start |
| 4. vLLM serves the adapter as a LoRA module | FAIL: blocked by test 3 |

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
