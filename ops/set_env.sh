#!/usr/bin/env bash
# Change the deployed backend's settings and time how long until the change is live.
#
#   ops/set_env.sh CANARY_SHARE=0                                   # rollback: every new conversation to production
#   ops/set_env.sh CANARY_MODEL=nova-next CANARY_VERSION=sft2b-v1-fp8 CANARY_SHARE=0.10
#
# Each argument is NAME=value and is merged into the Cloud Run service's environment (other variables are kept).
# Cloud Run starts a new revision with the new settings and moves all traffic to it; conversations already open
# on the old revision end with it, and every new one reads the new settings (api/app.py pick_route).
#
# The time printed is from the command to /health reporting the new canary share, which is what "the rollback is
# done" means from a visitor's side.
#
#   SERVICE (default nova-backend)  REGION (default us-east4)  PROJECT (default nova-evals)
#   BACKEND_URL (default: read from the service)
set -euo pipefail
[ $# -ge 1 ] || { sed -n '2,6p' "$0"; exit 2; }
SERVICE=${SERVICE:-nova-backend}
REGION=${REGION:-us-east4}
PROJECT=${PROJECT:-nova-evals}
for kv in "$@"; do
  [[ "$kv" == *=* ]] || { echo "not NAME=value: $kv" >&2; exit 2; }
  [[ "$kv" != *,* ]] || { echo "a value may not contain a comma: $kv" >&2; exit 2; }
done
URL=${BACKEND_URL:-$(gcloud run services describe "$SERVICE" --region "$REGION" --project "$PROJECT" \
                       --format 'value(status.url)')}
want=""
for kv in "$@"; do [[ "$kv" == CANARY_SHARE=* ]] && want=${kv#CANARY_SHARE=}; done

start=$(date +%s)
gcloud run services update "$SERVICE" --region "$REGION" --project "$PROJECT" --quiet \
  --update-env-vars "$(IFS=,; echo "$*")" 2>&1 | tail -2
if [ -n "$want" ]; then
  until curl -s "$URL/health" | python3 -c "import json,sys; sys.exit(0 if abs(json.load(sys.stdin)['canary']['share'] - float('$want')) < 1e-9 else 1)" 2>/dev/null; do
    sleep 1
  done
fi
echo "live after $(( $(date +%s) - start )) s: $*"
