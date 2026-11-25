# Filtering the teacher's conversations

A strong teacher is still wrong sometimes, and a student copies its mistakes as faithfully as its strengths. Every
generated conversation goes through every check in `synth/verify.py`; only what passes all of them is trained on.
Code checks come first (exact, free, repeatable); two model judges cover what code cannot. Rejects keep their
reasons (`nova-rejects-v1`).

## The checks

| Check | Rejects a conversation when |
|---|---|
| schema | a tool call fails its argument model, a model call was a format error, or call markup reaches a reply |
| tool_before_fact | an order or tracking number is stated before any lookup returned it (a number the customer typed may be repeated only in a refusal) |
| grounded_numbers | a number, a day count ("7 days") or a date is not in the lookup and help-center results before it; day counts and dates are matched whole, and "N days ago" style arithmetic is refused outright |
| citations | a `[kb:...]` id was not returned by a search, or a citation is not a help-center id at all (`[order:11129]`) |
| end_state | an eligible return gets no proposal, an ineligible one gets one, "press Confirm" comes before any eligible proposal, or a reply says a return (or, where Nova cannot cancel, a cancellation) is done |
| escalation | a lost parcel is never handed off; an easy case is handed off nobody asked for; a late parcel is offered a hand-off; a hand-off or a teammate's call is claimed or promised without `escalate_to_human`; a ticket number did not come from a hand-off |
| call_limit | a turn ran out of model calls and fell back to the fixed hand-off reply |
| privacy | a phone number or email, another customer's order details, or Nova's own instructions or tool names appear in a reply |
| right_order | the customer named an item of their order and Nova looked up a different order first |
| needless_tool | a tool is called for a greeting, "are you a bot?", out-of-scope chat, or a plain thanks or goodbye |
| length | a reply over 80 words or written as a list |
| style | a closing offer of more help, several paragraphs, "I will ensure / keep an eye", telling the customer to ship an item back (NimbusCart picks up), or emails, labels or links no result mentioned |
| judge_tone | the tone judge fails it: the reply ignores the customer, lectures or scolds, apologises twice, or contradicts itself |
| judge_facts | the fact-check judge fails it: a reply misreads a result (the wrong shipment, a delivery date taken for a pickup date), states a store rule no help-center result gave, works out a date or weekday, or promises a process nothing supports |
| dedup | same scenario, same tool calls and a near-identical first message as a conversation already kept |

Each check has a conversation it must pass and one it must fail, written by hand (`tests/test_synth_verify.py`).

## The two judges, tested before use

Both run on the teacher's server with a pass/fail rubric (`synth/judge.py`), and both were tested on planted faults:
kept conversations with one reply rewritten, alongside the untouched originals.

| Judge | Planted test | Result |
|---|---|---|
| Tone | 12 originals; 12 each with a rude reply, a reply that ignores the customer, a reply that contradicts an earlier one | First version 47/48 (it failed Nova for using the customer's name, which it did not know Nova sees). With that context: **48/48** |
| Facts | 12 originals; 12 each with a date shifted by three days, an invented SMS and return label, a worked-out weekday | Caught **36/36** planted faults; passed only 4 of 12 originals. Read one by one, six of the eight were real slips (a "next Thursday" worked out, "more than 7 days ago", a 15-day window cited from the wrong section); two were the judge not knowing the customer's name and treating "shortly" as a promised time. Both added to its rubric |

## Reading kept conversations by hand

The bar: of 100 kept conversations read by hand, no more than 5 bad.

- **First read: 17 bad of 90.** Day counts and worked-out dates (6), hand-offs or tickets that never happened (3),
  invented processes such as "send it back" and "you'll receive instructions" (2), "eligible, press Confirm"
  before any proposal (1), "I will ensure..." (1), a made-up citation format (1), the wrong tool or the wrong
  help-center section (3). The number check had missed "7 days" because a 7 existed in every result inside a time
  like 07:14. Checks tightened: day counts and dates matched whole, promised and claimed hand-offs, ticket numbers,
  Confirm before a proposal, shipping-back instructions, promises, citation format.
- **Second read, after tightening: about 7 bad of 37.** The code-checkable patterns were gone; what remained were
  misreadings only a reader with the results could see (a weekday wrong, a return's pickup confused with the
  order's delivery, plausible steps nobody stated). That is what the fact-check judge was built for.

## How the keep rate moved

Same 200 situations each time (`--seed 4242`), all checks as they stood at the end:

| Pilot | Teacher rules | Code checks only | With the tone judge |
|---|---|---|---|
| 1 | r3 | 60% | 46% (judge before its context fix) |
| 2 | r4: three-call limit, cite only returned ids, no chasing the carrier, Nova cannot cancel | 70% | 54% |
| 3 | r5: what to do instead of "I cannot cancel"; judge told what Nova sees | 78% | 57% |

Fixes the teacher would not follow from rules alone were made mechanical in the generator, teacher-side only and
never recorded: on the fourth step of a turn the teacher is sent no tools and told to reply (the server's parser
turned an attempted fifth call into an empty reply, so the note goes last and an empty reply is retried once);
replies that offer a late parcel a hand-off, call a proposed return "done", or claim a hand-off that was not made go
back to the teacher for a rewrite.

The final keep rate, per check, scenario and persona: `final.md` in this folder.

## One word, 454 conversations: "a teammate will reply shortly"

Grouping the fact-check judge's reasons by scenario showed why the hardest scenarios kept 4-7%: in 454
conversations its only objection was a hand-off reply promising a time ("they will reply to you shortly"). The
hand-off tool's result says to tell the customer "without promising a time", and the judge sided with it over its
own rubric, which had called "shortly" acceptable. Hand-offs cluster in exactly the thin scenarios (lost and delayed
parcels, rejected returns, frustrated customers), so one teacher habit emptied whole rows of the coverage grid.

- **Repair** (`synth/repair.py`): the time words are removed in code from every Nova message in sentences about a
  teammate acting; nothing else changes. The 725 repaired conversations whose fact verdict had failed for a time
  promise were judged again: 327 pass (the rest have a real slip later on, which the judge used to stop before).
- **Prevention:** `style` now rejects a time promise after a hand-off, the generator sends such a reply back for a
  rewrite, and the teacher's rules (r6) forbid it.
- **Fill** (`synth/coverage.py`, `synth/generate.py --cells`): 479 conversations generated for the 27 cells still
  below two kept; 106 pass every check.

| | Kept | Empty cells (of 128) |
|---|---|---|
| Before (v1) | 1,006 | 28 |
| After the repair | 1,210 | 15 |
| After the fill | 1,264 | 3 |
| After the agent-written conversations (v2) | 1,267 | 2 |

The last row is 12 conversations written by a coding agent through `synth/agent_server.py`: 7 passed the code
checks and were judged by hand (tone and facts, the same rubrics), 3 were kept. Two of the rejects told the
customer "your return is all set" for a return that was only proposed; `RETURN_DONE` in `verify.py` now matches
"all set" and "sorted" too.

Retraining SFT-2a on the v2 mix did not move the golden or the fresh score (`evals/reports/03_sft2.md`, "Second
round"). v2's hand-off replies came out shorter and sometimes without the facts the cases check, a possible side
effect of the repair: a wording fix in the data should be followed by a check of what the fixed replies still
say.
