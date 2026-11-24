---
library_name: peft
license: apache-2.0
base_model: unsloth/Qwen3.5-2B
tags:
- lora
- tool-use
- customer-support
pipeline_tag: text-generation
---

# sft2a-r16-lr2e-4-traj_v1

SFT-2a: Nova's tool-using support model, trained from the base model. A LoRA adapter for Qwen3.5-2B that plays Nova, the support assistant of a fictional store,
inside an agent loop with six tools (order lookups, tracking, help-center search, return proposals, hand-off to a
person). Starts from the base model (`unsloth/Qwen3.5-2B`), learning rate 2e-4.

## Training data

`123jagjot/nova-sft2-mix-v1` (built by `training/sft2_mix.py`): 9,485 training examples, one per model call, each
the request exactly as Nova serves it (system prompt v2, the conversation state block, trimmed history, the six
tool schemas) with one target: a tool call or a reply. Loss on the target only.

| Source | Examples |
|---|---|
| Steps of conversations that passed every check (`nova-trajectories-v1`) | 4,511 |
| Clean leading steps of conversations failed only by the fact-check judge | 4,772 |
| No-tool chats (greetings, thanks, "are you a bot?", out of scope) | 97 |
| Bitext replies right without a tool | 105 |

Validation: 266 examples from whole held-out conversations.

## Settings

LoRA r 16, alpha 16, dropout 0, the seven attention and MLP projections; 10,911,744 trainable parameters.
One epoch, 593 steps of 16 examples (batch 8 x accumulation 2, grouped by length), cosine schedule, 5% warmup,
AdamW 8-bit, bf16, max length 2,432 tokens. One A100-80GB on Modal, 894 s of training, peak 43.8 GB.

## Results

Validation loss 0.530 -> 0.237 (step 0 is the starting point).

Golden set (107 cases, the full agent loop, temperature 0.2, served by vLLM 0.34.0 as a LoRA module),
correct = every required call, the right facts, nothing forbidden, the right hand-off:

| | Base | SFT-1 | SFT-2a | SFT-2b |
|---|---|---|---|---|
| Correct | 29/107 | 11/107 | **69/107** | 67/107 |

The adapter chosen for serving: tied with SFT-2b overall, better on returns (7/15 against 3/15), and it does not depend on SFT-1.

Synthetic data only; made for a portfolio support assistant for a fictional store. Not for production use.
