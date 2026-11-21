# Learning log

One entry per session: what I did, what surprised me, what I'd do differently.

## Module 0

### 2026-11-20 · Lesson 0.1: what each tool changes
- Did: wrote DESIGN.md, mapping 12 capabilities to prompt / RAG / tool / fine-tune / code, plus budgets with numbers.
- Surprised me: most capabilities need two or three mechanisms. A tool gives the data, but fine-tuning is what makes the model call it.
- Next time: rules that must hold every time go in code. A prompt only works "most of the time".

### 2026-11-20 · Lesson 0.2: a training setup that survives free GPUs
- Did: built the repo layout and the Hub repos, ran Postgres + pgvector in Docker (port 5433, because a system Postgres 18 holds 5432), ran the disconnect drill on Colab and a closed-tab run on Kaggle.
- Surprised me: the drill resumed from step 250, not 100. The tiny model trained faster than I could click, so the newest save was at 250. Added a pause at step 120.
- Next time: keep checkpoints on the Hub, never only on the notebook's own disk; leave no logic in the notebook.

### 2026-11-20 · Lesson 0.3: how a small model produces a reply
- Did: rendered the real chat template, counted tokens (6 draft tools = 656), wrote the greedy loop and matched `generate`, compared sampling (temperature 1.0 made replies vary 106–284 tokens, against 101–129 at 0.2) and thinking on vs off, saved the raw tool-call format.
- Surprised me: the model config's stop token is `<|endoftext|>`, not `<|im_end|>`, so `generate` ran past the end of the turn. Thinking is turned off by an empty `<think></think>` block in the prompt.
- Next time: always decode with special tokens visible when debugging, and check stop tokens on every new serving setup.

### 2026-11-20 · Lesson 0.4: risk tests on a T4
- Did: ran the four risk tests on Kaggle. Transformers and Unsloth passed first time; vLLM failed, and I fixed it with a run 2 notebook that tried fixes in a set order. Pinned training and serving versions in separate files.
- Surprised me: the cause of the failure was a missing file name (`libcuda.so`), hidden 300 lines above the error the report showed. vLLM was 4.5x faster than Transformers on the same GPU.
- Next time: always read the full log for the first real error, not the last line; keep training and serving in separate environments.

