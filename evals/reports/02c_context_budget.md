# Conversation state and the context budget: long chats that stay short and on the right order

Until now the loop sent every message of the conversation on every model call. The prompt grew without limit, and
nothing but the history told the model which order "it" was. Now (`agent/state.py`, used by `agent/loop.py` when a
`Context` is given, and by `evals/run_eval.py --state`):

- **A fixed budget, enforced before every model call:** 4,200 tokens of prompt plus 512 for the reply, inside an
  8,192-token window. Counted with Qwen3.5-2B's tokenizer on the rendered chat template, never estimated from
  characters. The measured split is in `DESIGN.md`, "Budgets".
- **History trimmed by code:** at most the last 6 messages, cut only at a customer message, so a tool call is never
  separated from its result; older turns are dropped whole; the current turn is never dropped.
- **A state block** at the end of the system prompt, rebuilt from tool results on every model call: each order the
  chat has looked up, labelled by its items, with the facts found so far (status, total, tracking, refunds), the
  last order looked up, and any return waiting for the customer's Confirm. Code writes it; the model never does.
- **Prompt v2:** v1 plus "call one tool at a time" and "use the conversation state". The loop runs at most two tool
  calls per step and answers any further one with a "skipped" error.

**In one line:** over two scripted 15-turn chats with the real 2B model, the state kept the model on the right order
in **28 of 28** order turns with prompts of at most 2,119 tokens, against 25 of 28 for the old loop, whose prompt
reached 5,042 tokens and broke the budget in the last turns. Trimming without the state got 16 of 28. The first
layout of the state was worse than no state at all; what fixed it was labelling each order by what is in it.

## The 15-turn chats

`evals/long_chat.py`: a scripted customer switches between two orders, mostly without repeating the order number
("going back to the webcam order", "how much was it?"), and asks one policy question in the middle. Each turn counts as
right if no lookup hit the other order, the reply states no fact that only the other order has, and it looked up the
right order or stated one of its facts (item names do not count: the customer says them too). Qwen3.5-2B on the Mac,
prompt v2, tools v2, temperature 0.2.

| Chat | Mode | Right order (of 14) | Largest prompt (tokens) |
|---|---|---|---|
| A: customer 416, a webcam in transit and a delivered tote bag | full history, no state (the old loop) | 13 | 5,042 |
| | **trimmed + state** | **14** | 2,049 |
| | trimmed, no state | 9 | 1,598 |
| B (held out): customer 10, a speaker in transit and a steam iron from July | full history, no state | 12 | 4,500 |
| | **trimmed + state** | **14** | 2,119 |
| | trimmed, no state | 7 | 2,007 |

Chat B was written after the state's layout had been chosen on chat A, so it checks the layout on a chat it was not
tuned on. Runs: `evals/runs/2026-11-23_long-chat/` and `2026-11-23_long-chat-b/`.

What the misses were:
- **Trimmed, no state:** once the message that named the order was gone, the model looked up the wrong one ("The
  webcam order (10689) was last scanned at Mysuru", the tote bag's order), asked which order was meant, or handed
  off: 5 misses in chat A, 7 in chat B.
- **Full history:** three misses. Two were hand-offs nobody asked for, late in the chat ("should i wait or will you
  do something?" escalated as `lost_parcel`); the third was a correct "Yes, the payment was made via UPI." made
  without a lookup, which the check does not credit. The prompt grew by about 270 tokens a turn; at that rate a
  25-turn chat needs about 7,750 tokens of prompt, and with the 512-token reply it no longer fits in 8,192.

## The first layout of the state, and why it failed

The first version put the order in focus on its own line (`Order in focus: 10689`) above one line of facts per
order. On chat A it got **9 of 14**, worse than trimming with no state (11 of 14 on the same run). When the customer
said "going back to the webcam order", the model looked up the order in focus, the tote bag's, although the state
listed the webcam's order two lines below. The wrong lookup then moved the focus, and the next "that order" was
wrong too.

Two layouts were tried on chat A with the real model:

| Layout | Right order (of 14) |
|---|---|
| `Order in focus: N` + one line per order (first version) | 9 |
| no focus line | 11 |
| each order labelled by its items (`1080p webcam = order 11904: ...`), and `Last order looked up: N (items). If the customer names another item, use that item's order.` | **14** |

The third is now `State.render()`. Customers name orders by what is in them; a number alone gave the 2B model no way
to connect "the webcam" to an order.

A second flaw was found by measuring the block: the first version kept one line per order, so a status lookup
replaced the tracking line found earlier, and the tracking number vanished from the state. Each order now keeps one
fact per kind of lookup.

## Golden multi-turn cases, state on and off

Only 3 golden cases have more than one turn (`adv-010`, `esc-009`, `ret-002`), and they are 2 or 3 turns long, so
their history fits the budget either way. With prompt v2 and tools v2, state off and on both pass 0 of 3; with the
state, `facts` went from 1 to 2 and `required_calls` from 2 to 1. The failures are behaviour, not context: extra
lookups, a hand-off after a proposal. Runs: `2026-11-23_floor-multiturn-state-off` and `-on`. The golden set needs
longer conversations to measure this; that belongs with the evaluation harness.

## Tests

`tests/test_state.py` (in CI): the state's rules (errors and order lists do not move the focus, a status lookup keeps
the tracking line, only the last 4 orders are shown, an open proposal appears once), the trimmer's rules (cut only
at a customer message, never a result without its call, the current turn kept, `ContextOverflow` when even that is
too long), and the 15-turn chat with a stand-in model on real tool results: every prompt under budget (1,094 to
1,628 tokens; the full history would be 4,912 by the last turn), every reply on the right order, and the same chat
with a state that never learns anything going wrong from turn 7, which is what the state is for.

## For the next fine-tune

The training conversations must be built the way production prompts are: trimmed by `fit()` and with the state block
in the system prompt, or the model trains on long, untrimmed histories it never sees in production. `fit()` takes
only a counting function, so the data pipeline can import it as is.
