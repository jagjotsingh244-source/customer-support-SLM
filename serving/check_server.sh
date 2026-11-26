#!/usr/bin/env bash
# Serve Nova with serving/launch_vllm.sh and check the server: the golden set three times (one run through
# the capture proxy, to collect real requests), the API key, time to first token with prefix caching on and
# off, and 20 requests at once. Results go to serving/server/.
#
#   NOVA_KEY=... HF_TOKEN=... DATE=2026-11-26 bash serving/check_server.sh
set -uo pipefail
cd "$(dirname "$0")/.."
OUT=${OUT:-serving/server}
mkdir -p "$OUT"
export DB_URL=${DB_URL:-postgresql://nimbus:nimbus@localhost:5433/nimbus}
R=(uv run --group rag python evals/run_eval.py --provider openai --system candidate --tools v2 --prompt v3
   --state --guards --handoff-rules --model nova)
NOTE="GCP L4 (nova-eval9), served by serving/launch_vllm.sh (merged model from the Hub, FP8, API key)"

start() {   # $1 = log name; extra env is passed through
  bash serving/launch_vllm.sh > "$OUT/vllm-$1.log" 2>&1 &
  SERVER=$!
  until curl -s -H "Authorization: Bearer $NOVA_KEY" localhost:8000/v1/models | grep -q '"nova"'; do
    kill -0 $SERVER 2>/dev/null || { echo "server died"; tail -30 "$OUT/vllm-$1.log"; exit 1; }
    sleep 5
  done
}
stop() { kill $SERVER; wait $SERVER 2>/dev/null; sleep 5; }

echo "=== serve, prefix caching on $(date +%T)"
start on
.venv/bin/python serving/server_checks.py auth --out "$OUT/auth.json"
rm -f "$OUT/requests.jsonl"
.venv/bin/python serving/template_check.py capture --port 8001 --out "$OUT/requests.jsonl" &
PROXY=$!
sleep 2
pids=()
for r in "" -r2 -r3; do
  db=nimbus; url=http://localhost:8000/v1
  if [ -n "$r" ]; then
    db=nimbus_${r#-}
    PGPASSWORD=nimbus dropdb -h localhost -p 5433 -U nimbus --if-exists "$db"
    PGPASSWORD=nimbus createdb -h localhost -p 5433 -U nimbus -T nimbus "$db"
  else
    url=http://localhost:8001/v1                      # run 1 goes through the proxy: real requests for below
  fi
  DB_URL=${DB_URL%/*}/$db "${R[@]}" --run "${DATE}_golden-nova-served-l4$r" --base-url $url \
    --notes "$NOTE; three runs at once" > "$OUT/golden$r.log" 2>&1 &
  pids+=($!)
done
wait "${pids[@]}"
kill $PROXY
for r in "" -r2 -r3; do grep -m1 "^| \*\*all" "evals/runs/${DATE}_golden-nova-served-l4$r/report.md" | cut -c1-60; done
.venv/bin/python serving/server_checks.py ttft --requests "$OUT/requests.jsonl" --out "$OUT/ttft-caching-on.json"
.venv/bin/python serving/server_checks.py burst --requests "$OUT/requests.jsonl" -n 20 --out "$OUT/burst-20.json"
grep -E "prefix|Prefix|max_num_seqs|preempt|Preempt|cache blocks|WARNING" "$OUT/vllm-on.log" | grep -v "POST\|GET" \
  | tail -40 > "$OUT/vllm-on-warnings.txt"
grep -E "Model loading took|Available KV cache|GPU KV cache size|Maximum concurrency|Mamba cache mode" \
  "$OUT/vllm-on.log" > "$OUT/memory.txt"
stop

echo "=== serve, prefix caching off $(date +%T)"
PREFIX_CACHING=0 start off
.venv/bin/python serving/server_checks.py ttft --requests "$OUT/requests.jsonl" --out "$OUT/ttft-caching-off.json"
stop
echo "CHECKS DONE $(date +%T)"
