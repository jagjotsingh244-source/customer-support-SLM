#!/usr/bin/env bash
# Load test the deployed backend at 1, 10 and 50 simulated customers, five minutes each, back to back so the
# model stays warm (one cold start, before the first level). Results: serving/load/u{1,10,50}_*.csv.
#
#   BACKEND=https://<backend> BACKEND_TOKEN=$(gcloud auth print-identity-token) bash serving/load_test.sh
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p serving/load
AUTH=()
[ -n "${BACKEND_TOKEN:-}" ] && AUTH=(-H "Authorization: Bearer $BACKEND_TOKEN")
echo "warm-up: $(curl -s -m 900 -X POST "${AUTH[@]}" "$BACKEND/warmup")"
for u in 1 10 50; do
  r=$(( u < 5 ? 1 : u / 5 ))
  echo "=== $u customers, from $(date +%T)"
  uv run --with locust locust -f serving/locustfile.py --host "$BACKEND" --headless -u $u -r $r -t ${DURATION:-5m} \
    --csv serving/load/u$u --only-summary --stop-timeout 30 > serving/load/u$u.log 2>&1 || true
  tail -25 serving/load/u$u.log | grep -E "Aggregated|/chat|turn \(server\)|model \(server\)|/demo-login" || true
done
echo "LOAD DONE $(date +%T)"
