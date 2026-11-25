# Synthetic conversations and the second fine-tune: the whole story

An overview for the written guide. Detail lives in `notes/simulated-customers/` (personas, realism, the pilot),
`notes/trajectory-filters/` (checks, judges, hand-reads, keep rates), `DESIGN.md` (change log) and
`evals/reports/03_sft2.md` (the results).

## Why generate conversations at all

The first fine-tune (SFT-1, rewritten Bitext replies) learned Nova's voice and lost tool use entirely: it made no
tool call in any golden case. Training data for an agent needs multi-turn conversations with real tool calls,
real results, returns, hand-offs and grounded policy answers. Writing them by hand is slow and sounds like one
person; asking a big model to write them produces a fake database (invented orders, statuses, tracking formats).

**Trajectory distillation:** a stronger "teacher" model plays Nova inside the real agent loop. Every tool call hits
the real tools, the seeded database (train-side customers only) and the real help-center search. The teacher
supplies behaviour; the world supplies every fact.

## The teacher

| Considered | Outcome |
|---|---|
| Gemini (the baseline's ceiling model) | Blocked: the Google project was flagged on 23 November; its terms may also restrict training on outputs |
| Qwen3.5-397B-A17B (TAU2-Bench 86.7) | Out of memory loading on four H100s in 4-bit; eight H100s ($31.60/h) would have cost about $50 for the stage |
| **Qwen3.5-27B, full precision, one Modal A100-80GB** | Chosen. Apache-2.0, the student's own family and chat format, TAU2-Bench 79.0 |

Kaggle T4s were too slow for a 27B (estimated 25-75 GPU hours); Modal's free tier ($30 a month, no card) paid for
everything. Teacher served by vLLM 0.34.0 (`serving/modal_teacher.py`), thinking off, temperature 0.7.

**Context distillation:** the teacher reads Nova's prompt plus 27 extra rules (`synth/teacher_rules.py`), each tied
to a counted failure; the recording keeps only Nova's prompt, state block and trimming, so the student learns the
behaviour without the rules.

## What the first conversations taught us

- **A serving bug.** The history trimmer kept at most 6 messages; one lookup turn is 6 messages, so in 44 of 69
  later calls Nova could not see its own earlier replies. Fixed for serving and training alike (current turn whole,
  two earlier turns as message and reply); the real 2B still scored 14/14 on both long-chat scripts.
- **Habits the 27B would not drop from rules alone:** narration before tool calls (stripped when recording), closing
  offers and several paragraphs (a rewrite step sends a reply back to the teacher), "7 days" from its private rules,
  promising to follow up. Some rules only held once enforced in code: on its last step the teacher gets no tools.

## Simulated customers

Eight personas in fixed shares, each opening from a real Bitext question with the matching intent and phrasing
flag; adversarial customers try five tricks. A grid of 16 scenarios x 8 personas keeps coverage even. Customer
realism read by hand: 20/30, then 27/30 after fixing goals, knowledge and the simulator's rules.

## Filtering: hard, then harder

Fifteen checks (`synth/verify.py`), each unit-tested; a tone judge and a fact-check judge tested on planted faults
(tone 48/48; facts 36/36 planted faults caught). Hand-reads of kept conversations: 17 bad of 90 before tightening,
then about 7 of 37 (factual misreadings), which the fact judge targets.

| Stage | Conversations |
|---|---|
| Generated (pilots r4/r5, full run in six parts, no-tool chats) | 3,270 |
| Pass the code checks and the tone judge | 2,044 |
| **Pass every check, including the fact judge** | **1,006** (`nova-trajectories-v1`, private on the Hub) |
| Rejected, with reasons | 2,264 (`nova-rejects-v1`, private) |

The fact judge failed a conversation for one slip anywhere, and most failures were real (a weekday worked out, a
help-center section cited for a rule it does not state, bank details "to add" that a lookup showed added). Because
training is per step, the clean steps before the first slip it names are kept for training: 4,772 such steps.

## The training mix (`training/sft2_mix.py`)

9,485 training examples, one per model call, rendered with the six tool schemas as served: 4,511 steps from fully
clean conversations, 4,772 salvaged steps, 97 no-tool chats, 105 Bitext redirects (only Bitext rows right without a
tool and free of SFT-1's habits; about 5%, not the planned 20%). 266 validation examples from whole held-out
conversations. Median 1,463 tokens, p99 2,300, max_seq_length 2,432. The loss sees only the target (a tool call or
a reply): proven on two-tool-call steps, where the template marks three spans and only the last is trained.

## Cost and time (Modal, all within the free credit)

| | Spend |
|---|---|
| Teacher tests, pilots, the 397B attempt | about $6.5 |
| Full run (3,270 conversations incl. pilots), tone and fact judging | about $11 |
| Training SFT-2a and SFT-2b (about 15 minutes each on one A100) | about $0.80 |
| Golden-set comparison, four systems on one GPU server | about $0.40 |
| **Whole stage** | **about $18.3 of the $30 credit** |

Throughput: about 15 conversations a minute at 20 in parallel; at 48 the prefix cache hit rate collapsed from 47% to
8% and throughput fell to 9 a minute.

## The result (`evals/reports/03_sft2.md`)

Golden set, 107 cases, correct on everything: **base 29, SFT-1 11, SFT-2a 69, SFT-2b 67.** Both adapters tell a
"thanks!" from an order question from step 100 of training. SFT-2a (from the base model) is served; starting from
SFT-1 bought nothing, since SFT-1's habits had to be unlearned first. What still fails traces mostly to the data:
hand-offs for parcels stuck far past their estimate (the filters taught "late is not lost" too well), out-of-scope
requests declined without offering a teammate, and help-center sections misread.

## The second round (v2)

Repair of the time promises in hand-off replies, fill runs for the thin cells, and 12 conversations written by a
coding agent through a mailbox server (`synth/agent_server.py`) when the GPU credit ran out: 1,267 kept, 2 empty
cells, a 10,446-example mix. SFT-2a retrained on it on one L4 (Google Compute Engine, 84 minutes) scored 61%
pass@1 on golden against v1's 64%, and 60% against 66% on fresh: inside the noise, but no gain, so v1 stays.
Cost: the rest of the Modal credit (about $10) for the repair judging and fill runs, and about ₹500 of Google
Cloud credit for the VM.

## Mishaps worth keeping

- One database connection shared by 16 threads tangled transactions and hung a run while the GPU billed: cleanup now
  runs per thread, a stall stop and a time-based dollar cap were added.
- A first request lost during a cold start left the generator waiting for 30 minutes: it now polls health first.
- A session restart killed background jobs: long runs are launched detached.
- A shell loop waiting for a run to finish matched its own command line and never ended.
- Four eval runs sharing one database would clear each other's return proposals between cases: each ran on its own
  copy (`CREATE DATABASE ... TEMPLATE nimbus`).
- After a redeploy no container started for about ten minutes (no L4 free): the eval server now falls back to an
  A10G or an L40S.
- A fill run kept generating after it was told to stop and used up the Modal credit: `synth/generate.py` now has a
  hard wall-clock stop (`--max-hours`).
- An eval script on the VM did not load the database role passwords, and all eight runs failed on their first
  database connection; the earlier scripts had loaded `.env`, this one did not.
