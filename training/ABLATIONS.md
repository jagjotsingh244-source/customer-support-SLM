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

**Results.** *Not run yet.*

**Choice.** *Made from the results: the smallest rank whose held-out-intent loss and probe replies are as good
as the larger ones.*
