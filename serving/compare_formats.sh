#!/usr/bin/env bash
# The three ways to serve the fine-tune, measured the same way on one L4 (vLLM 0.34.0):
#   adapter  base Qwen3.5-2B + the LoRA adapter as a named module
#   merged   the adapter merged into the base, 16-bit (serving/export_formats.py)
#   fp8      the merged model quantized to FP8 when vLLM loads it (--quantization fp8; weights and activations)
# For each: the golden set three times in the shipping configuration (prompt v3, state, guards, hand-off rules),
# generation speed (serving/decode_speed.py) and memory (from the vLLM startup log). On the adapter and merged
# servers, the template check (serving/template_check.py) as well.
#
#   ADAPTER=outputs/sft2a-r16-lr2e-4-traj_v1 MERGED=/data/nova-sft2a-v1-merged DATE=2026-11-26 \
#       bash serving/compare_formats.sh adapter merged fp8      # PARALLEL=1: the three golden repeats at once
set -uo pipefail
cd "$(dirname "$0")/.."
VLLM=${VLLM:-$HOME/vllm-env/bin/vllm}
OUT=${OUT:-serving/formats}
mkdir -p "$OUT"
export DB_URL=${DB_URL:-postgresql://nimbus:nimbus@localhost:5433/nimbus}
COMMON=(--port 8000 --max-model-len 8192 --language-model-only --enable-auto-tool-choice
        --tool-call-parser qwen3_coder --gpu-memory-utilization 0.9)
R=(uv run --group rag python evals/run_eval.py --provider openai --system candidate --tools v2 --prompt v3
   --state --guards --handoff-rules)

serve() {   # format -> starts the server in the background, waits until it answers
  local f=$1
  case $f in
    adapter) args=(Qwen/Qwen3.5-2B --dtype bfloat16 --enable-lora --max-lora-rank 16 --max-loras 1
                   --lora-modules "nova_$f=$ADAPTER");;
    merged)  args=("$MERGED" --dtype bfloat16 --served-model-name "nova_$f");;
    fp8)     args=("$MERGED" --dtype bfloat16 --quantization fp8 --served-model-name "nova_$f");;
  esac
  "$VLLM" serve "${args[@]}" "${COMMON[@]}" > "$OUT/vllm-$f.log" 2>&1 &
  SERVER=$!
  until curl -s localhost:8000/v1/models | grep -q "nova_$f"; do
    kill -0 $SERVER 2>/dev/null || { echo "server $f died"; tail -30 "$OUT/vllm-$f.log"; return 1; }
    sleep 5
  done
  nvidia-smi --query-gpu=memory.used --format=csv,noheader > "$OUT/nvidia-smi-$f.txt"
  grep -E "Model loading took|Available KV cache|GPU KV cache size|Maximum concurrency|prefix caching" \
    "$OUT/vllm-$f.log" > "$OUT/memory-$f.txt"
}

for f in "$@"; do
  echo "=== $f $(date +%T)"
  serve "$f" || continue
  NOTE="GCP L4 (nova-eval9), vLLM 0.34.0, served as: $f"
  if [ "$f" != fp8 ]; then
    # Capture real agent requests through the proxy, then compare training and server renderings.
    rm -f "$OUT/requests-$f.jsonl"
    .venv/bin/python serving/template_check.py capture --port 8001 --out "$OUT/requests-$f.jsonl" &
    PROXY=$!
    sleep 2
    "${R[@]}" --run "${DATE}_template-capture-$f" --base-url http://localhost:8001/v1 --model "nova_$f" \
      --ids adv-010 esc-009 ret-002 ord-001 ord-002 ret-001 pol-001 esc-001 una-001 adv-001 \
      --notes "$NOTE; requests captured for the template check" > "$OUT/capture-$f.log" 2>&1
    kill $PROXY
    uv run python serving/template_check.py compare --requests "$OUT/requests-$f.jsonl" \
      --tokenizer "$ADAPTER" --tokenizer Qwen/Qwen3.5-2B --out "$OUT/template-check-$f.json" \
      | tee "$OUT/template-check-$f.txt"
  fi
  # PARALLEL=1 runs the three repeats at once, each on its own copy of the store (the runner resets the agent's
  # writes in the database it is given). Pass rates do not depend on it; per-turn latency in those runs does,
  # so speed comes from decode_speed.py below, measured the same way for every format.
  pids=()
  for r in "" -r2 -r3; do
    db=nimbus
    if [ "${PARALLEL:-0}" = 1 ] && [ -n "$r" ]; then
      db=nimbus_${r#-}
      PGPASSWORD=nimbus dropdb -h localhost -p 5433 -U nimbus --if-exists "$db"
      PGPASSWORD=nimbus createdb -h localhost -p 5433 -U nimbus -T nimbus "$db"
    fi
    DB_URL=${DB_URL%/*}/$db "${R[@]}" --run "${DATE}_golden-sft2a-$f-l4$r" --base-url http://localhost:8000/v1 \
      --model "nova_$f" --notes "$NOTE${PARALLEL:+; three repeats at once}" > "$OUT/golden-$f$r.log" 2>&1 &
    pids+=($!)
    [ "${PARALLEL:-0}" = 1 ] || wait $!
  done
  wait "${pids[@]}"
  for r in "" -r2 -r3; do tail -3 "$OUT/golden-$f$r.log"; done
  uv run python serving/decode_speed.py --base-url http://localhost:8000/v1 --model "nova_$f" \
    --requests "$OUT/requests-adapter.jsonl" --out "$OUT/speed-$f.json" > "$OUT/speed-$f.log" 2>&1
  tail -1 "$OUT/speed-$f.log"
  kill $SERVER; wait $SERVER 2>/dev/null
  sleep 5
done
echo "FORMATS DONE $(date +%T)"
