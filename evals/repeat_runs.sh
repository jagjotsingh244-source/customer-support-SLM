#!/usr/bin/env bash
# Repeated runs for reliability (pass^3): every system on the golden set and on the simulated customers, three
# times each with the settings Nova is served with (prompt v2, tools v2, state block, temperature 0.2).
#
#   STUDENT=<student url> SIM=<teacher url> bash evals/repeat_runs.sh <date> [systems...]
#
# The four systems run side by side, each against its own copy of the database (nimbus_<system>, created with
# CREATE DATABASE nimbus_<system> TEMPLATE nimbus): the golden runner clears every agent-written row between
# cases, so two systems sharing one database would delete each other's proposals. Within a system the runs go
# one after another. Golden runs that already exist (run 1 of each system) are skipped; every run resumes.
set -euo pipefail
cd "$(dirname "$0")/.."
DATE=$1; shift
SYSTEMS=${*:-base sft1 sft2a sft2b}
: "${STUDENT:?set STUDENT to the student server URL}" "${SIM:?set SIM to the simulator server URL}"
OPENAI_API_KEY=$(grep '^TEACHER_API_KEY=' .env | cut -d= -f2- | tr -d '"'"'")
export OPENAI_API_KEY
NOTES="Modal L4, vLLM 0.34.0, bf16, adapters served as LoRA modules (max rank 16); one server for all four systems; prompt v2, tools v2, state block and history trimming as served; repeated for pass^3"

one_system() {
  local s=$1 model=$1 kind=candidate
  [ "$s" = base ] && model=Qwen/Qwen3.5-2B && kind=floor
  local db=postgresql://nimbus:nimbus@localhost:5433/nimbus_$s
  for r in r2 r3; do
    DB_URL=$db uv run --group rag python evals/run_eval.py --run "${DATE}_golden-$s-$r" --system $kind \
      --provider openai --base-url "$STUDENT/v1" --model "$model" --tools v2 --prompt v2 --state \
      --temperature 0.2 --notes "$NOTES" > /dev/null
    echo "$s golden $r done"
  done
  for r in r1 r2 r3; do
    uv run --group rag python evals/simulate.py --run "${DATE}_sim-$s-$r" --system $kind --base-url "$STUDENT/v1" \
      --model "$model" --sim-url "$SIM" --workers 8 --db-url "$db" --notes "$NOTES" > /dev/null
    echo "$s simulated $r done"
  done
}

for s in $SYSTEMS; do
  one_system "$s" > "evals/runs/.repeat-$s.log" 2>&1 &
done
wait
echo "all done"
