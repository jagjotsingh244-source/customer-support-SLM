"""Build the second fine-tune's training data: one example per model call, rendered with Nova's tools as served.

Three sources, mixed by conversation:

- Kept trajectories (nova-trajectories-v1): tool use, grounding, returns, hand-offs, multi-turn. Every recorded
  step becomes an example: the request the student would have been sent, and the teacher's message (a tool call
  or a reply) as the target.
- No-tool chats (the no_tool scenario in the same dataset): greetings, thanks, "are you a bot?", out of scope.
  Rendered with the same tools: tools are available, and this message does not need one.
- Clean leading steps of conversations rejected only by the fact-check judge: every step before the first reply it
  found a slip in. A conversation fails that judge for one slip anywhere, and training is per step, so the steps
  before the slip are kept (training split only).
- Bitext redirects (nimbus-bitext-v1): only intents where a reply without a tool is right (creating or switching
  accounts, placing an order, invoices) and only replies free of the habits the first fine-tune taught: no
  closing offer, no "I don't have access to your account", no offered hand-off. 105 of 4,447 rows qualify, so
  Bitext is about 5% of the mix, not the 20% first planned: the first fine-tune's report found exactly those habits
  stopped Nova calling tools, and a blind read preferred the base model 23 to 2. Their system prompt is replaced by
  Nova's serving prompt and an empty state block, so every example looks like serving.

Validation holds out 5% of trajectory and no-tool conversations, whole conversations, so no step of a held-out
conversation is trained on. Examples longer than max_seq_length are dropped and counted, never truncated.

    uv run --group data --group local-model --group rag python -m training.sft2_mix --max-seq-length 2432
"""

import argparse
import json
import random
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from agent.chat_template import for_template  # noqa: E402
from agent.prompts import system_prompt  # noqa: E402
from agent.state import State  # noqa: E402
from config import now  # noqa: E402
from synth.style import style_problems  # noqa: E402

TRAJ = ROOT / "data" / "synthetic" / "nova-trajectories-v1"
REJECTS = ROOT / "data" / "synthetic" / "nova-rejects-v1"
BITEXT = ROOT / "data" / "processed" / "nimbus-bitext-v1"
OUT = ROOT / "data" / "synthetic" / "nova-sft2-mix-v1"
STATS = ROOT / "training" / "sft2_mix_stats.json"
BITEXT_INTENTS = ["create_account", "delete_account", "edit_account", "switch_account", "registration_problems",
                  "check_invoice", "get_invoice", "place_order", "set_up_shipping_address", "recover_password"]
BITEXT_HABITS = re.compile(r"(do not|don't|cannot|can't) (have )?access|connect you with a teammate|would you like",
                           re.I)
VALIDATION_SHARE = 0.05


def step_examples(conv: dict, source: str) -> list[dict]:
    out = []
    for k, s in enumerate(json.loads(conv["steps"])):
        out.append({"messages": json.dumps(s["messages"] + [s["target"]], ensure_ascii=False), "source": source,
                    "conversation": conv["id"], "step": k, "scenario": conv["scenario"], "persona": conv["persona"],
                    "target": "call" if s["target"].get("tool_calls") else "reply"})
    return out


def prefix_examples(conv: dict) -> list[dict]:
    """The steps of a conversation rejected only by the fact-check judge that come before the first reply it
    found a slip in: those steps passed every check, and training is per step. Tool-call steps before that reply
    are kept; the reply and everything after it are dropped."""
    bad, replies, out = conv["fact_reply"], 0, []
    if bad < 1:
        return []
    for ex in step_examples(conv, "trajectory_prefix"):
        if ex["target"] == "reply":
            replies += 1
            if replies >= bad:
                break
        out.append(ex)
    return out


def bitext_examples(split) -> list[dict]:
    state = State().render()
    out = []
    for r in split:
        reply = r["messages"][-1]["content"]
        if r["intent"] not in BITEXT_INTENTS or style_problems(reply, "") or BITEXT_HABITS.search(reply):
            continue
        name = re.search(r"The signed-in customer is ([^.]+)\.", r["messages"][0]["content"]).group(1)
        system = system_prompt(now(), name, "v2") + "\n\n" + state
        msgs = [{"role": "system", "content": system}] + r["messages"][1:]
        out.append({"messages": json.dumps(msgs, ensure_ascii=False), "source": "bitext",
                    "conversation": f"bitext-{r['row_id']}", "step": 0, "scenario": r["intent"], "persona": r["flags"],
                    "target": "reply"})
    return out


def length(tok, tools, ex) -> int:
    msgs = for_template(json.loads(ex["messages"]))
    return len(tok.apply_chat_template(msgs, tools=tools, tokenize=True, return_dict=True)["input_ids"])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-seq-length", type=int, default=2432)
    ap.add_argument("--seed", type=int, default=3407)
    a = ap.parse_args()
    from datasets import Dataset, DatasetDict, load_from_disk
    from transformers import AutoTokenizer

    from agent.tools_v2 import TOOLS

    rng = random.Random(a.seed)
    convs = list(load_from_disk(str(TRAJ)))
    rng.shuffle(convs)
    by_kind = {"trajectory": [c for c in convs if c["scenario"] != "no_tool"],
               "no_tool": [c for c in convs if c["scenario"] == "no_tool"]}
    splits = {"train": [], "validation": []}
    for source, cs in by_kind.items():
        n_val = max(1, round(VALIDATION_SHARE * len(cs)))
        for c in cs[:n_val]:
            splits["validation"] += step_examples(c, source)
        for c in cs[n_val:]:
            splits["train"] += step_examples(c, source)
    # Conversations whose only failure is a fact slip: their clean leading steps, training split only.
    if REJECTS.exists():
        only_facts = [c for c in load_from_disk(str(REJECTS))
                      if all(r.startswith("judge_facts") for r in json.loads(c["reasons"]))]
        for c in only_facts:
            splits["train"] += prefix_examples(c)
    bitext = load_from_disk(str(BITEXT))
    splits["train"] += bitext_examples(bitext["train"])
    splits["validation"] += bitext_examples(bitext["validation"])

    tok = AutoTokenizer.from_pretrained("Qwen/Qwen3.5-2B")
    stats, dropped = {}, Counter()
    for name in splits:
        kept = []
        for ex in splits[name]:
            n = length(tok, TOOLS, ex)
            if n > a.max_seq_length:
                dropped[name] += 1
                continue
            kept.append({**ex, "tokens": n})
        rng.shuffle(kept)
        splits[name] = kept
        lens = sorted(x["tokens"] for x in kept)
        stats[name] = {"examples": len(kept), "dropped_over_max_len": dropped[name],
                       "conversations": dict(Counter(x["source"] for x in {x["conversation"]: x for x in kept}.values())),
                       "examples_by_source": dict(Counter(x["source"] for x in kept)),
                       "targets": dict(Counter(x["target"] for x in kept)),
                       "tokens": {"median": lens[len(lens) // 2], "p99": lens[int(0.99 * (len(lens) - 1))],
                                  "max": lens[-1], "total": sum(lens)}}
    DatasetDict({k: Dataset.from_list(v) for k, v in splits.items()}).save_to_disk(str(OUT))
    stats["max_seq_length"] = a.max_seq_length
    STATS.write_text(json.dumps(stats, indent=1))
    print(json.dumps(stats, indent=1))
    print("saved", OUT)


if __name__ == "__main__":
    main()
