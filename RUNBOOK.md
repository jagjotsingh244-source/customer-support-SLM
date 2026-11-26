# Runbook

How to change Nova safely, one routine per kind of change, each with the check that says it worked. Written for
whoever is on call. Commands are Makefile targets (`make help`) unless shown in full.

## What runs where

| Part | Where | Settings | Look at it |
|---|---|---|---|
| Chat page and backend (`api/app.py`, `ui/index.html`) | Cloud Run `nova-backend`, project `nova-evals`, `us-east4`, public | environment variables on the service (list below) | `/health`; Cloud Run logs |
| Model server (vLLM, the fine-tune in FP8) | Modal app `nova-serve`, one L4, scales to zero after 60 s | `serving/modal_nova.py`; key in Modal secret `nova-serve` | first request after idle takes about 2 minutes |
| Store: orders, help center, vectors, three roles | Neon Postgres | owner URL in `.env` (`NEON_URL`), never in the backend | `make reindex DB_URL=...` checks retrieval |
| Traces | Langfuse Cloud (US), project "My Project" | `LANGFUSE_*` on the backend | the Tracing page; filter by tag, user or time |
| Local stand-in for all of the above | this machine: Docker Postgres, llama.cpp with the GGUF | `.claude/launch.json` | `http://localhost:8080` |

Backend settings that matter: `MODEL_BASE_URL`, `MODEL_NAME` (nova), `MODEL_VERSION` (tag, e.g. sft2a-v1-fp8),
`NOVA_KEY`, `CANARY_MODEL` / `CANARY_BASE_URL` / `CANARY_VERSION` / `CANARY_SHARE`, `NOW_MODE` (frozen for the
demo), `DEMO_RESET=1`, `LANGFUSE_*`, the database role passwords. Change them with `ops/set_env.sh NAME=value`,
which keeps the others and prints how long the change took to go live.

Three rules that hold for every routine:

1. **Names are permanent.** A model, image tag or Modal app name is never reused for something else. A rollback
   then only has to point back at the old name, which still exists.
2. **Staging first.** Every change is tried on the local stand-in (or a canary slice) before it reaches every
   visitor.
3. **Write down the time.** Each routine ends with a check and how long it took, in the PR or the report.

---

## 1. A help-center page changed (`make reindex`)

When the shop changes a policy, edits a page in `kb/`, or Meera fixes a typo. If nobody re-embeds the page, Nova
keeps quoting the old chunk.

1. Edit the page in `kb/`, with its new `effective_date`. Keep the old rule in `kb/_archive/` if customers with
   older orders still fall under it.
2. On the local store: `make reindex`. It reloads the sections, re-chunks and re-embeds, and fails if vector
   recall@3 drops under `MIN_RECALL3` (0.80; it was 0.83). If the chunker changed the set of chunk IDs, it stops and
   prints the difference: a removed ID breaks every citation and eval label that points at it. Accept on purpose with
   `uv run --group rag python rag/index.py --update-ids`, then rerun.
3. Ask Nova about the change locally and check that it quotes the new rule and cites the new chunk.
   `make old-policy BASE_URL=http://localhost:8090/v1` runs the five old-policy golden cases.
4. Open a PR. CI loads the help center from scratch and checks it against the seed.
5. Promote to Neon only after the PR is merged. Load the role passwords from `.env` first, because loading the
   help center re-applies the roles and would otherwise set the local default passwords:
   `set -a; source .env; set +a; make reindex DB_URL="$NEON_URL"`
6. **Check:** one live question about the changed rule, and its trace shows the new chunk id in the
   `retrieval` step.

## 2. Code or prompt changed (pull request, then `make deploy`)

1. Open a PR. CI (`.github/workflows/checks.yml`) runs the clock rule, the help-center rules, the store checks,
   the whole test suite on a fresh store, and the 30-case smoke eval against the model server (at least 27 of 30).
   A red check blocks the merge.
2. Merge, then `make deploy TAG=v<next>` with a tag never used before. Settings are kept.
3. **Check:** `/health` says database ok; one chat on the demo; its trace appears in Langfuse with the expected
   tags.
4. **Undo:** Cloud Run keeps every revision. `gcloud run services update-traffic nova-backend --region us-east4
   --project nova-evals --to-revisions <previous revision>=100` sends everything back at once.

A prompt change changes the model's input, so it also needs a full `make eval` and a `make gate` against
production's runs before it ships, like a new model.

## 3. A new model (canary, then promote or roll back)

1. Train or export under a **new name**: e.g. `nova-sft2b-v1-merged` in the Modal volume `nova-models`
   (upload command in `serving/modal_nova.py`). Never overwrite the folder production reads.
2. Full eval and the gate on the same GPU type as production:
   `make eval MODEL=<name> BASE_URL=...` (three runs), then `make gate CANDIDATE=... CURRENT=...`. A BLOCK stops
   here.
3. Deploy it as its own endpoint:
   `NOVA_APP=nova-next-serve NOVA_MODEL_DIR=nova-sft2b-v1-merged NOVA_SERVED=nova-next uv run --group teacher modal deploy serving/modal_nova.py`
4. Canary: `make canary CANARY_VERSION=sft2b-v1-fp8` plus the new endpoint, i.e.
   `ops/set_env.sh CANARY_MODEL=nova-next CANARY_VERSION=sft2b-v1-fp8 CANARY_BASE_URL=<new endpoint>/v1 CANARY_SHARE=0.10`.
   One new conversation in ten goes to it, and keeps it for the whole conversation.
5. Watch both versions for 48 hours. In Langfuse, filter traces by the tag `adapter:sft2b-v1-fp8` against
   production's tag and compare the per-turn scores (escalated, tool errors, grounding issues, filter hits, thumbs)
   and the latency; read a sample of the canary's traces. With real traffic, build a dashboard that splits these by
   trace version, one line per model (evals/reports/06_serving.md, section 7, lists the panels).
6. **Promote:** set `MODEL_NAME`, `MODEL_VERSION` and `MODEL_BASE_URL` to the new model, then `make rollback` to
   turn the canary off. The old app stays deployed (it costs nothing while idle) until the new one has run a week.
7. **Roll back:** `make rollback` (`CANARY_SHARE=0`). Every new conversation goes to production from the moment
   the new revision is live; conversations already open on the canary finish there.

## 4. Roll back anything, fast

| What went wrong | Command | Measured |
|---|---|---|
| The canary model | `make rollback` | 72 s (a new revision); evals/reports/07_operations.md |
| A backend release | `gcloud run services update-traffic ... --to-revisions <previous>=100` | 9 s if that revision is still warm, 86 s if it scaled to zero |
| A help-center change | revert the PR, then section 1 from step 5 | a few minutes |
| Public access (a runaway bill, abuse) | `gcloud run services remove-iam-policy-binding nova-backend --region us-east4 --project nova-evals --member=allUsers --role=roles/run.invoker` | seconds |

## 5. Rotate the model server's API key (`NOVA_KEY`)

When it may have leaked, or every 90 days.

1. Make a new key: `python3 -c "import secrets; print(secrets.token_urlsafe(32))"` into a file, never into chat.
2. Model server first: `uv run --group teacher modal secret create nova-serve --force --from-dotenv <file>` and
   redeploy `serving/modal_nova.py` (and any canary app).
3. Backend: `ops/set_env.sh NOVA_KEY=<new>` (run from a shell that reads it from the file).
4. `.env` and the GitHub secret `STAGING_NOVA_KEY` (`gh secret set STAGING_NOVA_KEY < file`). Delete the file.
5. **Check:** `serving/server_checks.py auth` gives 401 with the old key and 200 with the new; one chat works.
   Between steps 2 and 3 chats fail with 502: do it outside demo hours.

Langfuse keys: create a new pair in the project settings, `ops/set_env.sh LANGFUSE_PUBLIC_KEY=... LANGFUSE_SECRET_KEY=...`,
update `.env`, check one trace arrives, then delete the old pair in Langfuse.

## 6. Before a demo, and when something looks wrong

- **Before a demo:** open the page about two minutes early: it wakes the model. For a long session, keep one
  container warm (`min_containers=1` in `serving/modal_nova.py`, about $0.89 an hour) and set it back after.
- **Chats fail:** `/health` first (database, model, canary). Then Cloud Run logs (`event: turn_failed` lines carry
  the trace id and error type), then the trace in Langfuse.
- **A visitor reports a wrong answer:** find their turn in Langfuse (time, customer id), read the tool results and
  the retrieval scores, and add the case to the weekly review (`evals/reviews/`).
- **The bill:** Modal and Google Cloud consoles. The Modal app releases its GPU after 60 s idle; the canary app too.
