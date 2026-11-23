"""A scripted 15-turn chat that switches between two orders, run with the real model, three ways.

    uv run --group local-model --group rag python evals/long_chat.py --out evals/runs/2026-11-23_long-chat
    uv run --group local-model --group rag python evals/long_chat.py --script b --out evals/runs/2026-11-23_long-chat-b

Customer 416 asks about order 11904 (a webcam, in transit) and order 10689 (a screen protector and a tote
bag, delivered), goes back and forth, and asks one policy question in the middle. Every mode uses the same
model, prompt v2, tools v2 and temperature 0.2:

  full     every message sent, no state (how the loop worked before)
  state    the state block plus the history that fits the budget (agent/state.py)
  trimmed  the same trimming with a state that never learns anything: what the state is for

Per turn it records the prompt tokens the model was given (the client's own count) and whether the turn is
about the order the customer meant (judge(): no lookup of the other order, no fact only the other order
has, and a lookup of the right one or one of its facts). --rescore judges saved runs again.
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

WEBCAM, TOTE = 11904, 10689
CUSTOMER = 416
# (customer message, the order the reply must be about; None for the policy question)
SCRIPT = [
    ("where is my order 11904?", WEBCAM),
    ("which courier is it with?", WEBCAM),
    ("and when was it supposed to arrive?", WEBCAM),
    ("ok. what about order 10689, did that arrive?", TOTE),
    ("what was in that one?", TOTE),
    ("how much did i pay for it?", TOTE),
    ("going back to the webcam order, where was it last scanned?", WEBCAM),
    ("whats the tracking number again?", WEBCAM),
    ("how long do refunds take for card payments?", None),
    ("can i return the tote bag?", TOTE),
    ("when was it delivered?", TOTE),
    ("ok and the webcam one, is it delayed?", WEBCAM),
    ("should i wait or will you do something?", WEBCAM),
    ("what was the total of that order?", WEBCAM),
    ("thanks. and the tote bag order, how much was that one?", TOTE),
]
# Facts only one of the two orders has: its number, tracking number, places, dates and amounts. Item names
# are left out on purpose: the customer says them too ("the webcam order"), so a reply can echo them while
# describing the wrong order ("The webcam order (Order 10689) was last scanned in Mysuru").
FACTS = {WEBCAM: ["11904", "ss70001836", "nagpur", "2799", "2,799", "2026-11-16", "november 16", "nov 16",
                  "2026-11-18", "november 18", "nov 18"],
         TOTE: ["10689", "ss70000689", "mysuru", "947", "2026-09-24", "september 24", "sep 24", "449", "249"]}


# A second chat, written after the state layout was chosen on the first, to check it on something it was not
# tuned on: customer 10 (ten orders), a speaker on its way and a steam iron delivered in July, other wording.
SPEAKER, IRON = 11652, 10208
SCRIPT_B = [
    ("hi, my speaker hasnt come yet, order 11652", SPEAKER),
    ("who is delivering it?", SPEAKER),
    ("when was it meant to get here?", SPEAKER),
    ("also i bought a steam iron in july, order 10208. did it reach me?", IRON),
    ("what did i pay for the iron?", IRON),
    ("was that by upi?", IRON),
    ("back to the speaker - where is it right now?", SPEAKER),
    ("can you give me its tracking id?", SPEAKER),
    ("do you deliver on sundays?", None),
    ("the iron, can i still send it back?", IRON),
    ("which courier brought it?", IRON),
    ("and the speaker, is it late?", SPEAKER),
    ("what should i do about it?", SPEAKER),
    ("how much was it?", SPEAKER),
    ("ok last thing, what was the iron's tracking number?", IRON),
]
FACTS_B = {SPEAKER: ["11652", "ss70001588", "swiftship", "ahmedabad", "1299", "1,299", "2026-11-15", "november 15",
                     "nov 15", "2026-11-18", "november 18", "cash on delivery"],
           IRON: ["10208", "bl70000208", "blueline", "mumbai", "1499", "1,499", "2026-07-15", "july 15", "2026-07-16"]}

SCRIPTS = {"a": (CUSTOMER, SCRIPT, FACTS), "b": (10, SCRIPT_B, FACTS_B)}


def judge(reply: str, tools: list, want: int, facts: dict = FACTS) -> bool:
    """The turn is about the order the customer meant: no lookup of the other order, no fact that only the
    other order has, and either a lookup of the right order or one of its facts in the reply."""
    other = next(o for o in facts if o != want)
    text = (reply or "").lower()
    looked_up = {json.loads(args).get("order_id") for _, args in tools if args and args.startswith("{")}
    if other in looked_up or any(f in text for f in facts[other]):
        return False
    return want in looked_up or any(f in text for f in facts[want])


def run(mode: str, client, tools_mod, conns, owner, script: str = "a") -> dict:
    from agent.loop import run_turn
    from agent.prompts import system_prompt
    from agent.state import Context, State, token_counter
    from config import now

    class Frozen(State):
        def update(self, *_):
            pass

    customer, lines, facts = SCRIPTS[script]
    tools_mod.clear_agent_writes(owner)
    session = tools_mod.Session.open(conns, customer)
    ctx = None if mode == "full" else Context(token_counter(tools_mod.TOOLS),
                                              state=State() if mode == "state" else Frozen())
    messages = [{"role": "system", "content": system_prompt(now(), session.customer_name, "v2")}]
    turns = []
    for n, (text, want) in enumerate(lines, 1):
        messages.append({"role": "user", "content": text})
        reply, trace = run_turn(client, "Qwen/Qwen3.5-2B", messages, tools_mod.TOOLS, tools_mod.DISPATCH, session,
                                trace_id=f"long-{script}-{mode}-{n}", context=ctx)
        prompt = [c["prompt_tokens"] for c in trace["model_calls"]]
        turns.append({"turn": n, "customer": text, "want": want, "reply": reply,
                      "right_order": judge(reply, [(c["name"], c["args"]) for c in trace["tool_calls"]], want, facts)
                      if want else None,
                      "tools": [(c["name"], c["args"]) for c in trace["tool_calls"]],
                      "prompt_tokens": prompt, "escalated": trace["escalated"]})
        print(f"  {mode} t{n:2d} {max(prompt):5d} tok  {'ok ' if turns[-1]['right_order'] else '-- ' if want else '   '}"
              f"{(reply or '')[:80]!r}", flush=True)
    tools_mod.clear_agent_writes(owner)
    scored = [t for t in turns if t["want"]]
    return {"script": script, "customer": customer, "mode": mode, "right_order": sum(t["right_order"] for t in scored), "of": len(scored),
            "max_prompt_tokens": max(max(t["prompt_tokens"]) for t in turns), "turns": turns}


def rescore(out: Path, modes: list[str], script: str = "a") -> list[str]:
    """Judge saved runs again (no model calls) and rewrite their files and the summary."""
    summary = []
    for mode in modes:
        r = json.loads((out / f"{mode}.json").read_text())
        for t in r["turns"]:
            t["right_order"] = judge(t["reply"], t["tools"], t["want"], SCRIPTS[script][2]) if t["want"] else None
        r["right_order"] = sum(bool(t["right_order"]) for t in r["turns"] if t["want"])
        (out / f"{mode}.json").write_text(json.dumps(r, indent=1, ensure_ascii=False, default=str) + "\n")
        summary.append(f"{mode:8s} right order {r['right_order']}/{r['of']}, largest prompt {r['max_prompt_tokens']} tokens")
    (out / "summary.txt").write_text("\n".join(summary) + "\n")
    return summary


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--modes", nargs="*", default=["full", "state", "trimmed"])
    ap.add_argument("--rescore", action="store_true", help="judge the saved runs in --out again; no model calls")
    ap.add_argument("--script", choices=list(SCRIPTS), default="a", help="a: the chat the state was tuned on; b: held out")
    a = ap.parse_args()
    if a.rescore:
        print("\n".join(rescore(a.out, a.modes, a.script)))
        return

    import psycopg
    from agent import tools_v2
    from agent.local_client import LocalChatClient
    from evals.run_eval import DB_URL

    client = LocalChatClient("Qwen/Qwen3.5-2B")
    conns, owner = tools_v2.connect(DB_URL), psycopg.connect(DB_URL, autocommit=True)
    a.out.mkdir(parents=True, exist_ok=True)
    summary = []
    for mode in a.modes:
        r = run(mode, client, tools_v2, conns, owner, a.script)
        (a.out / f"{mode}.json").write_text(json.dumps(r, indent=1, ensure_ascii=False, default=str) + "\n")
        summary.append(f"{mode:8s} right order {r['right_order']}/{r['of']}, largest prompt {r['max_prompt_tokens']} tokens")
    (a.out / "summary.txt").write_text("\n".join(summary) + "\n")
    print("\n".join(summary))


if __name__ == "__main__":
    main()
