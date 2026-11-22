# Guide

Readable write-ups of how Nova was designed and why: the decisions, the evidence behind them,
and the questions they answer. The source of truth stays in `DESIGN.md` and `notes/`; these PDFs
explain it end to end.

| PDF | Covers |
|---|---|
| [foundations.pdf](foundations.pdf) | Where each capability lives, the budgets, the model choice, training on free GPUs, how the model produces a reply, the GPU risk tests and the vLLM fix, and likely interview questions with answers |
| [store-and-data.pdf](store-and-data.pdf) | The store Nova works in: the schema designed from customer questions, state machines, the frozen clock and train/eval split, the scenario seed, the help center written for retrieval, the five layers of checks, bugs found, and likely interview questions with answers |

Each PDF is built from the HTML file of the same name in `src/`. After editing it, rebuild with:

```bash
./guide/build.sh
```

(This needs Google Chrome; set `CHROME` to another Chrome or Chromium binary if it is not in `/Applications`.)
