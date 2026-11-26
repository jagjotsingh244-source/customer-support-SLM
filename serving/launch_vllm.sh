#!/usr/bin/env bash
# How Nova's model is served: the one place the vLLM flags live. Used on a rented GPU and inside the
# scale-to-zero container (serving/modal_nova.py runs this same script).
#
#   NOVA_KEY=... HF_TOKEN=... bash serving/launch_vllm.sh
#
# Settings (environment):
#   NOVA_KEY        required; requests without "Authorization: Bearer $NOVA_KEY" get 401
#   MODEL           what to load; default the merged fine-tune (private repo, needs HF_TOKEN)
#   SERVED_NAME     the model name clients ask for (default nova)
#   QUANTIZATION    fp8 (default; the shipping format, DESIGN.md "Serving format") or none
#   PREFIX_CACHING  1 (default) or 0, to measure what it buys
#   MAX_NUM_SEQS    conversations decoded at once (default 64)
#   PORT            default 8000
#   VLLM            the vllm executable (default: vllm on PATH)
#
# Flags, and why:
#   --language-model-only           skip Qwen3.5's vision encoder: memory goes to the KV cache instead
#   --max-model-len 8192            the context budget the agent enforces (agent/state.py), not 262K
#   --enable-auto-tool-choice --tool-call-parser qwen3_coder
#                                   turn the model's tool-call text into structured tool_calls
#   --quantization fp8              weights and activations in 8-bit floats (measured: same golden score,
#                                   54% faster decoding than 16-bit + LoRA on an L4)
#   --api-key                       no key, no GPU
set -euo pipefail
: "${NOVA_KEY:?set NOVA_KEY: the server refuses to start without an API key}"
MODEL=${MODEL:-123jagjot/nova-sft2a-v1-merged}
QUANTIZATION=${QUANTIZATION:-fp8}
args=(serve "$MODEL"
  --served-model-name "${SERVED_NAME:-nova}"
  --language-model-only --max-model-len 8192
  --enable-auto-tool-choice --tool-call-parser qwen3_coder
  --gpu-memory-utilization "${GPU_MEMORY_UTILIZATION:-0.9}"
  --max-num-seqs "${MAX_NUM_SEQS:-64}"
  --api-key "$NOVA_KEY"
  --host 0.0.0.0 --port "${PORT:-8000}")
[ "$QUANTIZATION" = none ] || args+=(--quantization "$QUANTIZATION")
[ "${PREFIX_CACHING:-1}" = 1 ] || args+=(--no-enable-prefix-caching)
exec "${VLLM:-vllm}" "${args[@]}" "$@"
