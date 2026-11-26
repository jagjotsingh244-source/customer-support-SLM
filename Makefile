# Routine changes to Nova, one command each. RUNBOOK.md says when to run which and what to check after.
#   make help

SHELL := /bin/bash
DB_URL ?= postgresql://nimbus:nimbus@localhost:5433/nimbus
EMBEDDER ?= BAAI/bge-small-en-v1.5
# vector recall@3 was 0.83 when this was set (evals/retrieval/runs)
MIN_RECALL3 ?= 0.80
BASE_URL ?= http://localhost:8000/v1
MODEL ?= nova
RUN ?= $(shell date +%Y-%m-%d)_$(MODEL)
# 27 of 30; the served model passes 29 (evals/reports/06a_formats.md)
SMOKE_MIN ?= 0.90
CANARY_MODEL ?= nova-next
CANARY_VERSION ?= $(CANARY_MODEL)
CANARY_SHARE ?= 0.10
IMAGE ?= us-east4-docker.pkg.dev/nova-evals/nova/backend
TAG ?=

# The shipping configuration: the one the golden set measures and the backend serves (api/app.py).
EVAL = uv run --group rag python evals/run_eval.py --provider openai --system candidate --tools v2 --prompt v3 \
       --state --guards --handoff-rules --model $(MODEL) --base-url $(BASE_URL)

export DB_URL

.PHONY: help test reindex old-policy eval smoke gate canary rollback deploy

help:              ## list the targets
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | sed -E 's/:.*## /\t/'

test:              ## unit and integration tests (needs the local database)
	uv run --group api --group rag --group dev pytest -q tests/

reindex:           ## re-chunk and re-embed kb/ into $(DB_URL), then check retrieval recall@3 >= $(MIN_RECALL3)
	uv run python db/load_kb.py
	uv run --group rag python rag/index.py --model $(EMBEDDER)
	uv run --group rag python evals/retrieval_eval.py --model $(EMBEDDER) --min-recall3 $(MIN_RECALL3)

old-policy:        ## the five old-policy golden cases against $(MODEL) on $(BASE_URL) (after a policy change)
	$(EVAL) --run $(RUN)-old-policy --category old_policy

eval:              ## full golden set against $(MODEL) on $(BASE_URL)
	$(EVAL) --run $(RUN)

smoke:             ## the 30-case smoke set; fails under $(SMOKE_MIN) (what CI runs)
	$(EVAL) --run $(RUN)-smoke --smoke --fail-under $(SMOKE_MIN)

gate:              ## compare runs: make gate CANDIDATE=run1,run2 CURRENT=run3,run4
	uv run python evals/gate.py --candidate $(CANDIDATE) --current $(CURRENT)

canary:            ## send $(CANARY_SHARE) of new conversations to $(CANARY_MODEL) (deployed backend)
	ops/set_env.sh CANARY_MODEL=$(CANARY_MODEL) CANARY_VERSION=$(CANARY_VERSION) CANARY_SHARE=$(CANARY_SHARE)

rollback:          ## every new conversation back to production
	ops/set_env.sh CANARY_SHARE=0

deploy:            ## build the backend image and deploy it: make deploy TAG=v6 (settings are kept)
	@test -n "$(TAG)" || { echo "TAG is required, e.g. make deploy TAG=v6 (never reuse a tag)"; exit 2; }
	gcloud builds submit --project nova-evals --region us-east4 --tag $(IMAGE):$(TAG) .
	gcloud run deploy nova-backend --project nova-evals --region us-east4 --image $(IMAGE):$(TAG) --quiet
