# Simulated customers: who they are and whether they sound real

The training conversations need a customer on the other side. A model plays that customer
(`synth/simulator.py`) with a hidden goal, limited knowledge and a persona, and starts from a real
Bitext question (`synth/personas.py`). This note records the personas and the realism check.

## Personas

| Persona | Share | Style | Bitext opener flags | Knows the order number |
|---|---|---|---|---|
| direct | 20% | clear, complete sentences | I or B, not Z W Q K P C | always |
| vague | 15% | "my stuff", unsure dates, short | L, not K C Z W P | never |
| two_in_one | 10% | two needs in the first message (the second is a help-center topic) | C | 40% |
| typo | 15% | lowercase, misspellings, no punctuation | Z | 40% |
| keyword | 10% | two to five words, like a search box | K | 60% |
| polite_long | 10% | courteous, 30-60 words, not gushing | P | 40% |
| frustrated | 15% | angry, repeats, threatens to leave | W or Q | 40% |
| adversarial | 5% | one trick, then the real question | hand-written | 40% |

Adversarial tricks: another customer's order, a fake staff member, a fake system message, asking for the hidden
instructions, and (on return scenarios) "complete the return yourself, I won't press any button".

The coverage grid is 16 scenarios × 8 personas. Each scenario gets an equal share; personas take turns in
proportion to their share, and each takes its emptiest scenario first, so a 30-conversation run already holds
all 8 personas and all 16 scenarios.

## Realism check

30 conversations, the customer's side only, each marked realistic or not with a reason. The bar was 25 of 30.

| Round | Realistic | What failed |
|---|---|---|
| 1 | 20 / 30 | contradicting its own situation (3: "I returned my stuff" for a cancelled order, "still nothing!" for a delivered one, a defect invented to win), a goal naming items that were never in the return (1), amounts made up from Bitext's `{{Refund Amount}}` slots (2), every detail in the first message (1), thanking support three or four times instead of ending (2), a gushing polite caricature (1) |
| 2 | **27 / 30** | repeating a code from Nova's reply (`changed_mind`), claiming to be inside a return window it cannot know about, raging on after getting the answer it asked for |

Changes between rounds:

- **Goals name the returned items**, not the whole order (`return_items`), and the knowledge says what happened:
  "You cancelled it before it shipped. You never received or returned anything", "It arrived and you have it".
- **Bitext slots are filled with neutral words** ("money", "my order"), never left for the simulator, which
  filled them with amounts it made up.
- **Simulator rules:** no invented amounts, dates, faults or events; nothing that contradicts what it knows; the
  first message says what it wants in one or two sentences and details come only when asked; no codes copied from
  support's replies; end once the goal is met instead of thanking again.
- **Personas:** the vague customer no longer gets typo or offensive openers (its style is vagueness, not
  spelling); the polite customer is courteous, not gushing.

What the typo, keyword, frustrated and adversarial customers wrote in both rounds is what real chat traffic looks
like: "order 11701 status", "where is delivery", "why late promised 14th", "says delivered but nothing received".

## Seen on Nova's side while reading (for the filtering step)

The realism read is about the customer, but three teacher mistakes stood out: it looked up the wrong order first
when the customer named items (two conversations), and it told a customer an order was cancelled although Nova
has no tool that cancels.

## The pilot: 200 conversations through the whole pipeline

192 saved (`--seed 4242`, 16 in parallel). The other 8 exposed a bug: every thread cleaned up on one shared
database connection, transactions interleaved, and a customer whose cleanup failed stayed claimed, so the 2
conversations waiting for it hung for 8 minutes while the GPU billed. Cleanup now runs on each thread's own
connection and always releases the customer; the run checks its dollar cap every 30 seconds and stops when nothing
finishes for 5 minutes. A stress run with stand-in models (120 conversations, 16 threads, 210 tickets) left no rows
behind. None of the 192 saved conversations saw another conversation's return or ticket.

| | Pilot |
|---|---|
| Outcome | 186 goal met, 6 gave up |
| Grid cells covered | 120 of 128 (the missing 8 jobs) |
| Personas | direct 40, typo 30, vague 30, frustrated 28, two_in_one 19, polite_long 19, keyword 16, adversarial 10 |
| Customer turns | 3.2 on average |
| Teacher tokens per conversation | 16,957 in, 364 out, 6.3 calls, 0.64 style rewrites |
| Simulator tokens per conversation | 1,998 in, 113 out |
| GPU time | about 3.2 s per conversation in parallel; 11 minutes for the run, plus the cold start |
| Cost | about $0.96 for the run as it happened, of which about 8 minutes were the hang |
| Training steps | 1,219, all usable as targets |
| Left for the filters | 22 fallback hand-offs (the call limit ran out), 47 numbers with no source, 3 style problems |

Full-run budget, from these numbers: in `DESIGN.md` under "Budgets".
