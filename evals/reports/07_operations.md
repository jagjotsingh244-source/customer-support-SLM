# Operations: routine changes, checks before merging, a canary and its rollback

Nova changes in three ways: the help center is edited, the code or prompt changes, or a new model is trained.
Each now has a routine with a check (`RUNBOOK.md`, `Makefile`), and each routine was rehearsed and timed on
2026-11-26.

## Checks before a change reaches main

`.github/workflows/checks.yml` runs five jobs on every push and pull request: the clock rule, the help-center
rules, the store and eval-case checks, the loss-mask test, and a new job that seeds a fresh store, embeds the help
center and runs the whole test suite (387 tests). The same job runs the 30-case smoke eval against the model
server, through the shipping configuration, and fails under 27 of 30, once the server's URL and key are stored as
repository secrets. It is off for now: every run wakes the GPU. `main` requires all five checks before a merge.

**Rehearsed: a pull request that breaks a tool.** The return tool was changed to skip its eligibility check, so an
expired or opened item would get a Confirm card. The first finding came before CI ran: **the full test suite
passed with that bug in place.** No test asked the tool to refuse an item that cannot go back. The missing test
(`tests/test_tool_guards.py::test_propose_refuses_an_item_that_cannot_go_back`, an expired item and an opened
electronic) went into `main`, and the pull request then failed two jobs and was closed unmerged. A check that never
fails proves nothing, which is the point of rehearsing a break.

Also fixed on the way: the clock rule had failed on `main` all day because the trace-retention script read the
real clock. Retention has to follow the calendar even when the shop's clock is frozen, so `config.py` now has a
clearly named `wall_clock_today()` for that one purpose.

## A help-center change (`make reindex`)

Rehearsed on the local store, then reverted: home items' return window shortened from 15 days to 10 (accessories
unchanged), `policy_version` 3.

| Step | Time |
|---|---|
| Edit the page and `make reindex` (reload sections, re-chunk, re-embed 104 chunks, retrieval eval) | 13 s |
| Nova answers with the new rule and cites `returns-general#return-window` | 18 s after the edit |
| Revert and reindex; Nova says 15 days again | 16 s |

Vector recall@3 stayed 0.83 (the gate is 0.80). One model error surfaced: Nova put cushion covers under
"accessories" and quoted their 15-day window. It goes to the weekly review as a golden-case candidate.

## A new model: canary, then rollback

The backend sends a `CANARY_SHARE` of **new** conversations to `CANARY_MODEL` on `CANARY_BASE_URL`, chosen at
sign-in and kept for the whole conversation, and tags every trace with the version that answered. A second model
is its own Modal app (`serving/modal_nova.py` takes the model folder and served name at deploy time), so production
is never touched.

**Rehearsed on this machine** with two real models: production as the 16-bit GGUF and the candidate `nova-next`
as the 4-bit GGUF (cheaper to serve; 27 of 30 smoke cases against 29), half the conversations each:

| Version | Conversations | Reply p50 | Hand-offs | Confirm cards | Expired cooktop (372) |
|---|---|---|---|---|---|
| sft2a-v1-bf16-gguf-mac (production) | 6 | 8.2 s | 2 | 1 | hands off |
| sft2a-v1-q4-gguf-mac (candidate) | 9 | 5.1 s | 2 | 2 | calls the return tool, which says the window has closed |

Fifteen conversations decide nothing (the golden set and the gate do), but the split, the tags and the comparison
work end to end, and the candidate already shows a behaviour difference worth a look.

**Rehearsed on Cloud Run**, with the canary pointed at the production model under a drill tag so visitors saw no
difference. Times are from the command to `/health` reporting the change:

| Action | Time |
|---|---|
| Canary on (`make canary`: a new revision with the canary settings) | 76 s |
| Rollback (`make rollback`: `CANARY_SHARE=0`, a new revision) | 72 s |
| Rollback by revision, target still warm (`update-traffic --to-latest`) | 9 s |
| Rollback by revision, target scaled to zero | 86 s |

So a settings rollback takes about 75 s, almost all of it Cloud Run starting a revision. Pointing traffic back at
a revision that is still warm takes 9 s, and that is the fast path for a bad release caught early. Conversations
already open on the canary finish on it either way; every new one goes to production. The drill settings were
removed afterwards.

## What is left out, and why

- **The smoke eval in CI is off.** It needs the model server's URL and key as repository secrets, and every pull
  request would wake the GPU (about $0.05 per run). Turning it on is two `gh secret set` commands (`RUNBOOK.md`).
- **No separate staging GPU.** "Staging" is the local stand-in (Docker store and llama.cpp) for the help center and
  the code, and a canary slice for models. A second always-ready model server would double the GPU bill of a demo.
- **No operations dashboard yet** (`evals/reports/06_serving.md`, section 7): the per-turn scores and version tags
  are in every trace, ready for one once there is traffic.
