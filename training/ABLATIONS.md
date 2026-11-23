# Training ablations

Each ablation changes one thing and keeps everything else fixed, so a difference has one cause.

## LoRA rank: r = 8, 16, 64

**Question.** How much adapter capacity does Nova's voice need? More rank means more trainable parameters
(5.5M, 10.9M, 43.6M; see `DESIGN.md`), which on a small, repetitive dataset mostly means memorising it faster.

**Setup.** `training/notebooks/sft-ablation.ipynb`, three runs of `training/sft.py` from
`training/configs/sft1.yaml` with `train_rows=1000` (the same seeded 1,000 rows of the train split for every
run), one epoch (63 steps), learning rate 2e-4, seed 3407, evaluation and probes every 10 steps.

**Alpha moves with r** (8/8, 16/16, 64/64). The update is scaled by alpha / r; holding alpha at 16 would scale
an r = 64 update by 0.25 and an r = 8 update by 2, so the runs would differ in step size as well as capacity.
With alpha = r the scale stays 1 and the rank is the only difference.

**What is compared.** Validation loss (seen intents) and held-out-intent loss (two intents never trained on), at
the end and at their best; the final reply to each probe; peak memory and time. The table comes from
`training/ablation_table.py` over the three run folders in `training/runs/`.

**Results.** Run on Kaggle (T4) on 2026-11-23 from commit `e3ee11b`; the run folders are in `training/runs/`.

| r / alpha | Trainable | Val loss, step 0 | Val loss, end | Held-out intents, end | Held-out − val | Peak GB | Train s |
|---|---|---|---|---|---|---|---|
| 8 / 8 | 5,455,872 | 2.075 | 0.849 | 1.021 | 0.172 | 4.90 | 1,090 |
| 16 / 16 | 10,911,744 | 2.075 | 0.802 | 0.981 | 0.179 | 4.94 | 976 |
| 64 / 64 | 43,646,976 | 2.075 | **0.734** | **0.928** | 0.194 | 5.13 | 957 |
| 16 / 16, all 4,447 rows (the first full run) | 10,911,744 | 2.075 | 0.621 | 0.828 | 0.207 | 4.94 | 2,412 |

Every run was still improving at step 63, so "best" equals "end" for all three. The trainable counts match the
hand count in `DESIGN.md`. Times differ by noise, not rank (r = 8 ran first, which likely included the one-off compile).

The lead of the higher ranks shrinks as training goes on:

| Validation loss at step | 10 | 20 | 30 | 63 |
|---|---|---|---|---|
| r = 8 | 1.793 | 1.108 | 0.962 | 0.849 |
| r = 16 | 1.626 | 1.023 | 0.904 | 0.802 |
| r = 64 | 1.335 | 0.912 | 0.831 | 0.734 |
| r = 64 lead over r = 8 | 0.458 | 0.196 | 0.131 | 0.115 |

Final reply to "i want to cancel my order" (greedy):

- r = 8: *I can help you with that. Let's get you the details on how to cancel your order. Would you like me to
  check your order for you?*
- r = 16: *I can help you with that. Let's take a look at your order to see what options are available for
  canceling it. Would you like me to check your order details?*
- r = 64: *I can help you with canceling your order. Let's get you the right details on what to do next. Would
  you like me to check your order for you?*

Across all eight probes, the three ranks read as the same voice, with the same faults: they offer to check an
order instead of checking it, "where is my order?" sometimes gets "I can't look up your order here" (r = 8 and
16), and "thanks, bye" gets an odd "You're welcome to say goodbye" (r = 16 and 64). No rank fixes a fault that
another has. r = 64 answers "hello" with an unprompted offer to check an order, the one reply clearly worse
than the others.

**Reading.**

1. Higher rank gives lower loss at 63 steps, on seen and unseen intents alike. Nothing overfits in one short
   epoch.
2. The lead is mostly speed, not capacity. With alpha = r the scale stays 1, but a rank-64 update is a sum of
   64 rank-one pieces that Adam all moves at the same rate, so it changes the model more per step. That is a
   larger effective step size, which shows up as a big early lead (0.46 at step 10) that shrinks towards the
   end (0.12). A capacity limit would show as a gap that opens up late, when the smaller adapter stalls, and
   none of the curves stall.
3. Data matters more than rank here. The r = 16 run on all 4,447 rows beats r = 64 on 1,000 rows by 0.11 on
   validation and 0.10 on held-out intents.
4. The held-out − val gap widens slightly with rank (0.172, 0.179, 0.194): the larger adapter fits the seen
   intents a little more than it gains on unseen ones.

**Choice: r = 16, alpha = 16, unchanged.** It is not the lowest loss at 63 steps, but the gap to r = 64 looks like
step size rather than missing capacity, the probe replies are the same in kind, and r = 64 costs four times the
adapter (175 MB against 44 MB in fp32), a higher `--max-lora-rank` in vLLM and a slightly wider seen/unseen
gap. r = 8 trails r = 16 by 0.04 on both losses at this length; r = 16 keeps the full run already trained and
evaluated, so nothing is retrained. `training/configs/sft1.yaml` keeps `r: 16`.

**Open question.** This design cannot separate capacity from step size in 63 steps. Holding the step size
fixed across ranks (rsLoRA's alpha / √r scaling, or a lower learning rate for r = 64) on the full data would
settle it. That is worth one run if a later model plateaus above the r = 16 loss.
