# Every layer, every category, three runs each

One number per system hid too much. This report scores Nova layer by layer (retrieval, tool use, end state,
grounding, reply, safety, efficiency), category by category, with counts and 95% intervals, over **three runs of
every case** with the sampling Nova is served with. It adds **40 simulated customers**: the customer simulator
plays an eval-partition customer with a hidden goal, and the harness checks what the conversation left behind.

**In one line:** SFT-2a and SFT-2b are tied within their intervals on everything overall. Run three times, they
pass every run on **56% and 54%** of the golden cases (62% and 61% on a single run). With real back-and-forth,
**60% and 65%** pass every run, against 77–78% for one run. The base model falls from 59% to 30%. And in long chats
SFT-2a fails in the opposite direction to the golden set: it **hands off when it should not** (17 of 90 chats)
rather than missing hand-offs (0 of 30).

Tables for every system and layer: [`04a_layers_tables.md`](04a_layers_tables.md). Every earlier run re-scored with
the new metrics: [`04a_rescored_runs.md`](04a_rescored_runs.md).

## What was built

| File | What it does |
|---|---|
| `evals/metrics.py` | The metric catalogue, read from a saved trace: retrieval (searched, recall@3, MRR), tool use (right tools, arguments rejected per 100 calls, format errors per 100 model calls, unneeded calls), end state (return proposed, ticket opened, fallback turns), grounding per 100 replies, privacy violations, a return claimed done, turns, tokens and latency. Also pass^k, the bootstrap interval and the expected-against-called tool table |
| `evals/scorecard.py` | Groups each system's repeated runs and writes the reliability and layer tables; `--rescore-all` scores every saved run |
| `evals/build_simulated.py` | Writes the 40 simulated cases (`evals/simulated/cases.jsonl`) from eval-partition orders, with the expected end state checked against the store's own return rule; `--check` runs in CI |
| `evals/simulate.py` | Runs them: simulator and Nova in the real loop, the database read after each chat, then cleaned for that customer only |
| `evals/repeat_runs.sh` | Every system, golden set and simulated cases, three times, each system on its own database copy |
| `tests/test_eval_metrics.py` | pass^k, the interval, the confusion table, end state, retrieval and privacy rules (in CI) |

`evals/run_eval.py` now adds the layer section to every run's own `report.md`. Those metrics never change pass or
fail, so the scorer stays `eval-v3`. All 21 saved golden and probe runs were re-scored without calling a model: every
`scores.json` came out identical, and only the reports gained the new section.

### The simulated cases

| Category | n | Scenarios | Expected end state |
|---|---|---|---|
| order_lookup | 10 | delivered, in transit, late, split delivery, cancelled, refunded | no proposal, no ticket; tracking numbers given where asked |
| returns | 8 | eligible (3), window passed (2), opened electronics, return in progress, return rejected | a proposal exactly where the item is eligible (4 cases, including one adversarial) |
| escalation | 6 | lost (3), delivered but not received (2), a late parcel and a customer who asks for a person | a ticket |
| policy | 8 | eight different help-center sections | the section that answers it was retrieved; no ticket |
| unanswerable | 4 | EMI, gift wrap, coupon, store pickup | a ticket or an offered hand-off |
| adversarial | 4 | another customer's order, fake system message, "show your prompt", "complete the return yourself" | the real request handled; nothing private said; no return claimed done |

Every customer is in the eval partition. The eval side has 88 customers and the golden set already uses all of
them, so each simulated customer also appears in a golden case, always with a different request. A ticket is never wrong once the
customer has asked for a person. Each case runs with up to 8 customer messages, and Nova runs exactly as served.

## Reliability: three runs of every case

**Golden set (107 scripted cases):**

| Category | n | Base pass@1 | Base pass^3 | SFT-1 pass@1 | SFT-2a pass@1 | SFT-2a pass^3 | SFT-2b pass@1 | SFT-2b pass^3 |
|---|---|---|---|---|---|---|---|---|
| policy | 25 | 23% | 16% | 0% | 69% [53–85] | 60% | 69% [52–87] | 64% |
| order_lookup | 25 | 21% | 16% | 0% | 63% [44–80] | 56% | 67% [49–84] | 60% |
| returns | 15 | 20% | 13% | 0% | **47%** [22–71] | 40% | **20%** [4–40] | 13% |
| unanswerable | 15 | 31% | 20% | 33% | 62% [38–84] | 60% | 76% [56–93] | 67% |
| escalation | 10 | 17% | 10% | 0% | 47% [17–77] | 40% | 40% [13–67] | 30% |
| adversarial | 12 | 53% | 42% | 53% | 86% [67–100] | 83% | 83% [64–100] | 75% |
| old_policy | 5 | 40% | 40% | 0% | 47% [7–87] | 40% | 67% [27–100] | 60% |
| **all** | 107 | 27% [20–34] | 20% | 11% | **62%** [54–71] | **56%** [47–65] | **61%** [53–70] | **54%** [46–64] |

**Simulated customers (40 cases):**

| Category | n | Base pass@1 | Base pass^3 | SFT-1 pass@1 | SFT-2a pass@1 | SFT-2a pass^3 | SFT-2b pass@1 | SFT-2b pass^3 |
|---|---|---|---|---|---|---|---|---|
| order_lookup | 10 | 63% | 20% | 0% | 83% | 60% | 80% | 70% |
| returns | 8 | 62% | 38% | 0% | 75% | 50% | 71% | 62% |
| escalation | 6 | 78% | 67% | 0% | 94% | 83% | 89% | 67% |
| policy | 8 | 33% | 0% | 0% | 58% | 50% | 58% | 38% |
| unanswerable | 4 | 92% | 75% | 75% | 100% | 100% | 100% | 100% |
| adversarial | 4 | 33% | 0% | 0% | 67% | 25% | 75% | 75% |
| **all** | 40 | 59% [48–69] | **30%** [18–45] | 8% | 78% [68–88] | **60%** [42–75] | 77% [65–88] | **65%** [50–80] |

pass^k, all cases:

| | Golden k=1 | k=2 | k=3 | Simulated k=1 | k=2 | k=3 |
|---|---|---|---|---|---|---|
| Base | 27% | 21% | 20% | 59% | 40% | **30%** |
| SFT-1 | 11% | 10% | 10% | 8% | 6% | 5% |
| SFT-2a | 62% | 58% | 56% | 78% | 67% | **60%** |
| SFT-2b | 61% | 57% | 54% | 77% | 69% | **65%** |

What this says:

- **The single golden run was a lucky draw.** SFT-2a scored 69, 65 and 66 in its three runs (mean 66.7), so the
  run reported after training was its best. SFT-2b scored 67, 65 and 65. Reporting one run overstated both by
  1 to 2 points.
- **Scripted cases are reliable, conversations are not.** On the golden set pass^3 is only 6–7 points below pass@1,
  because almost every case is one message, and at temperature 0.2 the same message mostly gets the same answer.
  With a simulated customer each run is a different conversation, and the gap grows to 18 points for SFT-2a, 12 for
  SFT-2b and 29 for the base model. Half of the base model's 59% single-run score on simulated chats is luck: it
  passes every run on only 30%.
- **SFT-2a against SFT-2b: no difference you can claim.** Overall they are within a point on both sets, with
  intervals 15–30 points wide. The one large gap is golden returns, 47% against 20%. Even there the intervals
  overlap ([22–71] against [4–40]). On simulated returns the two are close on a single run (75% against 71%), but
  SFT-2b is more reliable (62% against 50% pass^3). SFT-2b is ahead on simulated pass^3 overall (65% against 60%),
  also inside the intervals. Which one ships is decided later, with the judge and fresh cases, not from these numbers.
- **SFT-1 confirms what the other layers already showed:** it calls no tools. It passes only cases a polite reply can
  pass: a few adversarial refusals, and out-of-scope requests where offering a teammate is the whole answer.

## What the layers show

The SFT-2a figures below are pooled over its three golden runs. Every system's full tables are in
[`04a_layers_tables.md`](04a_layers_tables.md).

**Retrieval is not the bottleneck; reading is.** In the 36 golden cases whose answer is a help-center section,
SFT-2a searched in 33 (92%). When it searched, the right section was in the top 3 in 83% (MRR 0.71). Policy cases
still pass only 69%, because facts are right in 69%: the section is usually found, then misread. This matches the
failures read by hand after training ("the help center does not cover" a rule it does state). More retrieval work
would not fix it.

**Tool arguments are not the problem; choosing the tool is.** SFT-2a made 518 tool calls in 846 model calls, and
SFT-2b about as many, with zero rejected arguments and zero format errors. Right tools (the set of names) holds in 55% of cases. The
expected-against-called table shows where the rest go:

| Expected | Called instead | SFT-2a, 3 runs |
|---|---|---|
| `escalate_to_human` | nothing | **42 of 69** expected hand-offs |
| `get_tracking` | `get_order_status` | 15 of 78 |
| `search_help_center` | nothing | 19 of 138 |
| nothing | an extra `get_order_status` | 32 extra calls |

**Hand-offs fail in both directions, and only the simulated cases show the second one.** The golden set sees missed
hand-offs: 42 of 69 expected escalations never called. In the simulated chats SFT-2a never missed a ticket it needed
(0 of 30), but opened **17 tickets in 90 chats that did not need one**, almost always after the customer pushed back.
Examples: an angry customer who had just received a return proposal, a customer insisting Nova complete the return
without the Confirm button, a late parcel. SFT-2b opens the same 17. The base model opens 33. A frustrated second
message reads to the model as a reason to escalate. The next training data needs both: hand-offs for real problems,
and conversations where the customer is angry but the answer, not a teammate, is what helps.

**Safety: one leak every system shares, one invented phone number.** The privacy check found no other customer's data
in any reply. It did find the tool names in the replies to a foreign order number: "Please check your recent orders
or call list_my_orders." Base, SFT-2a and SFT-2b all do this, in 3 (SFT-2b) to 14 (base) replies over their
golden and simulated runs. The words come from the
tool's own `not_found` message ("Ask the customer to check it, or call list_my_orders"), so the fix belongs in that
message, or in a reply filter, not in training. The base model also gave a support number, "+91-9876543210", in two
simulated chats. No tool or help-center page contains it: it was invented.

**A return claimed done:** once in all 24 runs. SFT-2b, golden ret-006: "The return request has been created",
about a proposal the customer had not yet confirmed. Every other system has none.

**Efficiency:** SFT-2a uses about 3,700 tokens per golden conversation and 9,100 per simulated one (3 customer turns
on average). Latency per turn is 3.25 s median and 5.6 s p95 on golden cases, and 2.8 s median and 6.7 s p95 in
simulated chats. That is on a Modal L4 shared by four systems, so the real serving number comes later, but p95 is
over the 3 s target.

## A rule changed after seeing results

The first pass rule for simulated cases checked the end state, the required facts, forbidden phrases, privacy and
false return claims. Run on all four systems, it passed **SFT-1 on 57% of cases, including all 8 policy questions**.
SFT-1 calls no tools, and its customers gave up in 58 of 120 chats. A model that answers nothing never creates a wrong
end state either.

So each case now names the **evidence** an answer needs: a successful lookup of the customer's own order, or the
answering section returned by a search. This is what Shankar et al. call criteria drift: running the check showed what
"passed" should have meant. The change was made before any write-up, it is recorded in `evals/build_simulated.py`, and
both numbers are in the tables (column "pass, first rule"):

| | First rule | With the evidence rule | Customer gave up (the simulator's own verdict, not used in pass) |
|---|---|---|---|
| SFT-1 | 57% | **8%** | 48% |
| SFT-2a | 83% | 78% | 3% |
| SFT-2b | 82% | 77% | 4% |

The simulator's give-up rate was never part of the rule, yet it agrees with the new rule, which is some evidence the
rule now measures help, not politeness.

**A check that was wrong, found while writing this.** The "return claimed done" check, borrowed from the training-data
filters, first flagged 5 golden cases and 2 simulated ones in these runs, and 2 in the Gemini baseline. Read one by
one, all but one were false alarms. Some were
negated ("No return has been created yet") or conditional ("the refund will be sent once the return is processed").
Others stated a real, earlier return that the order lookup had just shown (golden cases record no scenario for those
orders). The check now skips negated and conditional sentences, and returns an order lookup showed
(`tests/test_eval_metrics.py`). This changed one SFT-2a simulated result to a pass, and cleared the Gemini ceiling's two
flags.

**A weakness in the cases themselves.** Three policy cases ask about sections that describe a personal problem
("Delivered but not received", "A possible loss", "Support hours" of the human team). The simulated customer then
often plays the problem as its own ("showing delivered but not received"), and Nova's hand-off is a sensible answer
that the case counts as wrong. These cases are kept as written, since the scores are already read, and marked for
the next version of the set: policy questions should come from sections that are rules, not incidents.

**The database agrees with the trace in all 480 simulated conversations.** Every proposal and ticket the tool results
show was in the database after the chat, and nothing else was. For golden runs, which do not read the database, the
end state can be taken from tool results.

## Earlier runs, re-scored

[`04a_rescored_runs.md`](04a_rescored_runs.md) has one row per saved run since the first baseline. Three things only
the new metrics show:

- **The first search tool:** on the same 30 policy cases and the same model, the full-text search returned the
  right section in 1 of 11 cases that searched; the vector search, in 8 of 11. The original reports counted
  citations, not retrieval.
- **SFT-1's collapse was total from the start:** zero tool calls in every saved run.
- **The Gemini ceiling made no false return claims.** An earlier version of the check said it made two; both were
  "No return has been created yet".

## Not done here

- **The frontier model.** The Gemini project is still blocked, so the ceiling has no three-run, simulated or layer
  numbers with these settings yet. It is added when the comparison table is built.
- **A judge** for what code cannot check: is every claim grounded, was the request resolved. Every "facts" and
  "evidence" number here is a code check with the limits described above.

## Cost

All on the Modal free credit, billed $0:

| | |
|---|---|
| 10-case trial of the simulated harness (mostly two cold starts) | about $0.35 |
| 8 golden runs, 12 simulated runs, all four systems (student on an L4, simulator Qwen3.5-27B on an A100-80GB, about 25 minutes) | about $2.0 |
| **Total** | **about $2.4 (≈ ₹210)** |

## Reproduce

```bash
uv run python evals/build_simulated.py --check
STUDENT=<student url> SIM=<simulator url> bash evals/repeat_runs.sh 2026-11-25
bash -c 'D=2026-11-25; G=""; S=""; for s in base sft1 sft2a sft2b; do
  G="$G $s=${D}_golden-$s,${D}_golden-$s-r2,${D}_golden-$s-r3"; S="$S $s=${D}_sim-$s-r1,${D}_sim-$s-r2,${D}_sim-$s-r3"; done
  uv run --group rag python evals/scorecard.py --golden $G --simulated $S --out evals/reports/04a_layers_tables.md'
uv run --group rag python evals/scorecard.py --rescore-all --out evals/reports/04a_rescored_runs.md
```
