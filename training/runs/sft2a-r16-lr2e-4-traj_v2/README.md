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

# sft2a-r16-lr2e-4-traj_v2

SFT-2a retrained on the second version of the synthetic conversations. A LoRA adapter for Qwen3.5-2B that plays
Nova, the support assistant of a fictional store, inside an agent loop with six tools (order lookups, tracking,
help-center search, return proposals, hand-off to a person). Same recipe as `sft2a-r16-lr2e-4-traj_v1`; only the
data changed. **Not the adapter Nova serves:** it did not beat v1 (results below).

## Training data

`123jagjot/nova-sft2-mix-v2` (built by `training/sft2_mix.py --version v2`): 10,446 training examples, one per
model call, each the request exactly as Nova serves it (system prompt v2, the state block, trimmed history, the
six tool schemas) with one target: a tool call (5,949) or a reply (4,497). Loss on the target only.

| Source | Examples |
|---|---|
| Steps of conversations that passed every check (`nova-trajectories-v2`, 1,267 conversations) | 6,115 |
| Clean leading steps of conversations failed only by the fact-check judge | 4,129 |
| No-tool chats (greetings, thanks, "are you a bot?", out of scope) | 97 |
| Bitext replies right without a tool | 105 |

What changed from v1: hand-off replies had their promised times ("a teammate will reply shortly") removed in
code and were judged again, fill runs targeted the thin scenario x persona cells, and 7 conversations were
written by a coding agent and judged by hand (`notes/trajectory-filters/`). 58 examples over the length limit
were dropped. Validation: 359 examples from whole held-out conversations (not the same set as v1's, so the two
losses are not directly comparable).

## Settings

LoRA r 16, alpha 16, dropout 0, the seven attention and MLP projections; 10,911,744 trainable parameters.
One epoch, 653 steps of 16 examples (batch 4 x accumulation 4, grouped by length), cosine schedule, 5% warmup,
AdamW 8-bit, bf16, max length 2,432 tokens, Unsloth gradient checkpointing. One NVIDIA L4 (24 GB) on a Google
Compute Engine VM, 5,049 s of training, peak 5.9 GB allocated.

## Results

Validation loss 0.514 -> 0.217. Probes (five fixed requests, every 100 steps): 5/5 from step 100.

Both adapters on one vLLM 0.34.0 server on the L4 (LoRA modules), temperature 0.2, scorer `eval-v3`;
correct = every required call, the right facts, nothing forbidden, the right hand-off:

| | v1 | v2 |
|---|---|---|
| Golden set, 107 cases x 3 runs (pass@1) | **64%** (69/107) | 61% (65/107) |
| Fresh set, 50 cases written after the golden set | **66%** (33/50) | 60% (30/50) |
| Grounding issues per 100 replies (golden) | 5.4 | 6.3 |

The gaps are inside the 95% intervals, but both case sets point the same way. Most of v2's extra misses take the
right steps and leave a fact out of the reply (a delivery date, a refund amount). The release gate
(`evals/gate.py`) blocks it.

Synthetic data only; made for a portfolio support assistant for a fictional store. Not for production use.
