# An LLM judge, measured against hand labels, and not ready

Code checks facts, tools, end states and privacy. Two things it cannot check are left to a model:
**grounded** (every claim in a reply is backed by what Nova's tools returned) and **resolved** (the reply dealt
with what the customer asked, or handed off correctly). This report builds that judge the careful way: labels
first, one narrow yes/no question per criterion, evidence in the prompt, tuning on one set and measuring on
another.

**In one line:** tuned on 25 labelled replies, gpt-oss-120b agrees well there (grounded TPR 0.93 / TNR 0.90). On
replies it never saw, it **catches only 43–67% of grounding failures and 55–62% of resolve failures**, against a
target of 80%. So it was **not used** to score the four systems. Most of what it misses can be checked by code
instead.

## What was built

| File | What it does |
|---|---|
| `evals/judge_units.py` | Cuts any saved run into judgeable replies: the customer's message, the chat before it, the reply, and the evidence Nova had (every tool call and result so far, today's date, the customer's name); `date_facts` works out every estimated date, scan and delivery relative to today |
| `evals/judge_labels.py` | The labels (`evals/judge/labels.jsonl`), the review sheets (`label_sheet.md`, `label_sheet_fresh.md`), the split, and the written criteria |
| `evals/judge.py` | The judge: five prompt versions, one call per criterion, `agree` (TPR and TNR against labels) and `run` (every reply of a run) |
| `serving/modal_judge.py` | gpt-oss-120b on one H100 with vLLM, the same way the teacher and student are served |
| `evals/judge/agreement/` | Every verdict with the judge's reasoning, per prompt version and label set |

**Why gpt-oss-120b.** The judge must not be the model that wrote the training data (Qwen3.5-27B), or it would
favour the style it taught. gpt-oss is another family, with open weights (Apache-2.0), so anyone can re-run these
verdicts. Temperature 0, reasoning effort medium.

## The labels

75 replies from all four systems, golden and simulated, single-turn and later turns of long chats:

| Set | Replies | Grounded FAIL | Resolved FAIL | Used for |
|---|---|---|---|---|
| tune | 25 | 10 | 15 | writing the prompt |
| test | 25 | 9 | 16 | measuring v3, once |
| fresh | 25 | 7 | 11 | measuring v5, once (added after v3 missed the bar; different cases, labelled before the judge saw them) |

The 50 tune and test replies were split at random within each combination of verdicts (seed 3407).

**Who labelled.** Each verdict was drafted with one sentence of reasoning, then reviewed in the sheets by the
project's author, whose edits were final. Both sheets came back with **no verdict changed**. So the judge was
measured against verdicts its author accepted, not against verdicts the author wrote blind. The difference
matters: a reviewer tends to agree with a plausible draft.

**Criteria drift** (Shankar et al.). Tuning made two rules explicit that the first labels had applied loosely:
"the help center does not cover this" only counts after a search that found nothing, and a parcel with no scan
for about a week may be lost. The fresh set applies both. One test label breaks the first rule: SFT-1 offered a
teammate for an EMI question without searching, and is labelled resolved PASS. It was left as it was, because
changing a test label after seeing the judge's verdict would be tuning on the test set.

## The prompts

| Version | Change | Why |
|---|---|---|
| v1 | The plain prompts: one criterion each, with the evidence | Starting point, written before reading any label |
| v2 | Definitions of a claim, rules (tool results only, not Nova's own hand-off summary; dates against today; a proposal is not a return) and two short examples per criterion from the tune labels | v1 took Nova's own ticket summary as evidence, and passed replies that asked permission instead of looking |
| v3 | Resolved becomes a five-step checklist (parts, looked, correct, hand-off, cannot answer) | v2 still passed invented answers and bare hand-off lines |
| v4 | v3 plus a listening check | Three of v3's misses ignored what the customer had just said; v4 was the last tuning round, and was no better |
| v5 | v3 plus date facts worked out by code | On the test set, v3 read "last scan 9 days ago, 14 days past the estimate" as a recent scan |

## Agreement

TPR: of the replies the labels pass, the share the judge passes. TNR: of the replies the labels fail, the share
the judge fails. TNR is the dangerous direction: a judge with low TNR reports failures as passes.

| Prompt | Set | Grounded TPR | Grounded TNR | Resolved TPR | Resolved TNR |
|---|---|---|---|---|---|
| v1 | tune | 0.87 | 0.70 | 1.00 | 0.27 |
| v2 | tune | 0.93 | 0.80 | 1.00 | 0.47 |
| v3 | tune | 0.93 | **0.90** | 0.90 | **0.73** |
| v4 | tune | 0.93 | 0.90 | 0.90 | 0.67 |
| v5 | tune | 0.93 | 0.90 | 0.90 | 0.60 |
| **v3** | **test** | 0.81 [0.62–1.00] | **0.67** [0.33–1.00] | 0.89 [0.67–1.00] | **0.62** [0.38–0.88] |
| **v5** | **fresh** | 0.89 [0.72–1.00] | **0.43** [0.14–0.86] | 0.79 [0.57–1.00] | **0.55** [0.27–0.82] |

Intervals are 95% bootstrap over replies. With 7 to 16 failures in a set, one reply moves TNR by 6 to 14 points.

What the table says:

- **The tuning did not transfer.** Grounded TNR reached 0.90 on the replies the prompt was written against, and
  0.67 and 0.43 on replies it was not. Two definitions and two examples fitted to 25 replies taught the judge
  those 25, not the criterion.
- **Run-to-run noise is about one reply.** The grounded prompt is identical in v2, v3 and v4, yet its tune TNR
  read 0.80 once and 0.90 twice. The server batches requests, so temperature 0 is not fully repeatable.
  Differences between v3, v4 and v5 on the tune set are inside that noise.
- **TPR stays high, TNR does not.** The judge rarely fails a good reply. It passes bad ones, which is the
  failure Shankar et al. and Husain warn about: fluent, confident replies look right.

## What the judge gets wrong

Read from its own reasoning on every disagreement:

1. **No evidence against a claim is taken as evidence for it.** "Has not been lost" passed with "there is no
   indication of loss in the tracking data", even with the date facts showing no scan for 8 days and an estimate
   a week past. Its date reading was not the problem in the end: it treats unchecked reassurance as grounded.
2. **A hand-off or a refusal counts as a resolution, needed or not.** Return requests Nova could have handled
   itself ("I cannot process the return in this chat", then a ticket) passed as "a hand-off was required".
3. **Answers that fit the evidence but miss the question pass.** Bank details asked for without saying they go on
   the order page; a card-only answer to a general refund question.
4. **Where the labels are arguable, the judge sometimes has the better case.** "The customer will be notified by
   a teammate" promises something no tool says; the judge failed it, the label passed it. Treat these
   disagreements as label questions, not judge errors.

## Decision

The judge is **not used to score the systems**: with TNR around 0.4 to 0.7 on unseen replies, its pass rates would
hide about half the real failures. Every system number in the reports stays a code check, with the limits written
in `04a_layers.md`.

The labels are the part to keep: 75 replies with verdicts and reasons, reusable for any judge.

What to do next, in order:

1. **Move the common misses into code.** Most are mechanical: reassurance ("not lost", "on its way", "still with
   the carrier") when the date facts show a past estimate and no scan for 7 days; "the help center does not cover
   this" with no search; a hand-off claimed with no `escalate_to_human` result; a reply that asks permission to
   look with no tool call. Code catches these exactly, every time, for free.
2. **Try a stronger judge on the same 75 labels**, once one is available (the frontier model the comparison needs
   anyway), and keep it only if TNR on the fresh set reaches 0.8.
3. **Label more failures blind**: the fresh set has only 7 grounding failures, so a single reply moves TNR by 14
   points.

## Cost

| | |
|---|---|
| Weights download to the volume (CPU) | about $0.10 |
| Judge on an H100: v1–v5 on the tune set, v3 on test, v5 on fresh, three cold starts | about $1.65 |
| **Total** | **about $1.75 (≈ ₹155)**, Modal free credit, billed $0 |

## Reproduce

```bash
uv run --group teacher modal run serving/modal_judge.py::download
uv run --group teacher modal deploy serving/modal_judge.py
export JUDGE_URL=<judge url>
uv run python evals/judge.py agree --split tune --prompt v3
uv run python evals/judge.py agree --split test --prompt v3
uv run python evals/judge.py agree --split fresh --prompt v5
```
