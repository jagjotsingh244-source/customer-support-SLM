# Baseline on the phrasing probes: does messy wording hurt?

12 probes in `evals/probes/phrasing.jsonl`, 3 each of offensive, typo-heavy, polite and keyword-only messages.
Each rewords a golden case and keeps its customer, order and expectations, so a probe that fails while its
clean twin passes failed because of the wording. Same setups as the golden baselines: prompt v0, six rough tools,
temperature 0.2, at most 4 model calls per turn, scorer `eval-v1`, local database copy.

| System | Run | Probes, all | Twins, all | Probes, all_required | Twins, all_required |
|---|---|---|---|---|---|
| Floor: `Qwen/Qwen3.5-2B` (Transformers on a Mac GPU) | `2026-11-23_floor-probes` vs `2026-11-22_floor` | 1/12 | 2/12 | 1/12 | 2/12 |
| Ceiling: `gemini-4-hydrogen` | `2026-11-23_ceiling-probes` vs `2026-11-22_ceiling` | 0/12 | 1/12 | 6/12 | 5/12 |

`all` uses the strict tool checks (exactly the expected calls); `all_required` allows extra calls in between.

## Reading it

**The ceiling shows no wording effect.** By `all_required` the probes do as well as their twins (6 against 5),
and the differences go both ways (`pol-phr-05` passes while its twin fails; `una-phr-12` the reverse): noise.
Its strict scores are near zero on probes and twins alike for the reason in `00_baseline_ceiling.md`: it searches
more than the case needs.

**The floor has one difference, and it looks real.** The clean frying-pan return (`ret-001`) passes; the rude
version (`ret-phr-02`, *"i want to return this damn frying pan, dont need the stupid thing anymore"*) fails.
To tell luck from wording, the 12 clean twins were run a second time (`2026-11-23_floor-twins`): every twin got
the same result as in the first run, and `ret-001` passed both times.

> ret-001 · clean → `list_my_orders` → `get_order_status(11324)` → `propose_return(11324, 1, "changed_mind")` →
> *"The frying pan is eligible for return..."*
>
> ret-phr-02 · rude → `list_my_orders` → `get_order_status(11324)` → `search_help_center("return policy")` → `[]`
> → `search_help_center("return")` → out of calls → *"Let me connect you with a teammate."*

Same order found, same status read; with the insult in the message it searched the policy instead of proposing
the return, and ran into failure type 2 of the floor baseline (spends its calls, ends in the fallback hand-off).

**What this can and cannot say.** With 3 probes per phrasing, one case is the whole signal: the probes flag a large
gap, they cannot measure a small one. The floor passes only 2 of the 12 twins to begin with, so for the prompted
2B the probes mostly cannot show a wording effect at all; they become informative once a fine-tuned model passes
most twins. The thing to watch after fine-tuning: rude messages leading to hedging and hand-offs instead of the
action the customer asked for.
