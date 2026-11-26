"""Preference pairs from Nova's own mistakes, for preference tuning (DPO) on top of SFT-2a.

The second fine-tune's training mix (training/sft2_mix.py) already holds, for every step, the request exactly as
the student is sent it and a checked teacher message. That is a prompt and a chosen reply. The rejected reply is
Nova's own answer to the same request: wherever SFT-2a, as served, does something different and wrong, the two
make a pair that differs in one decision. Pairs made from Nova's outputs (on-policy) target the habits it really
has; pairs made from the teacher's rejected conversations would teach it to avoid mistakes it does not make.

    # 1. Nova answers every training step (free: the GGUF on this machine, llama-server on :8090)
    uv run --group data python -m training.preference_pairs collect --base-url http://localhost:8090/v1
    # 2. keep the disagreements where Nova is wrong, with one tag each
    uv run --group data python -m training.preference_pairs build

Only the training split is used, so no validation conversation and no eval case reaches a pair. The request is
brought up to serving: prompt v3 (agent/prompts.py) and tool results labelled with their source
(agent/guardrails.py label), the input Nova reads when deployed.
"""

import argparse
import json
import re
import sys
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from agent.grounding import grounding_issues  # noqa: E402
from agent.guardrails import label  # noqa: E402
from agent.privacy import asks_for_secret, plain_tool_words  # noqa: E402
from agent.prompts import SYSTEM_V2, SYSTEM_V3  # noqa: E402

MIX = ROOT / "data" / "synthetic" / "nova-sft2-mix-v1"          # what SFT-2a was trained on
OUT = ROOT / "data" / "preference"
SAMPLES, PAIRS = OUT / "nova-samples-v1.jsonl", OUT / "nova-pairs-v1.jsonl"
V3_RULES = SYSTEM_V3[len(SYSTEM_V2):]
SOURCES = {"trajectory", "no_tool", "trajectory_prefix"}         # Bitext redirects carry no tool decisions
# A refusal with nothing after it: the habit behind the unanswerable failures ("I can only help with your own
# orders and account details. I cannot provide the contact information...").
DEAD_END = re.compile(r"\b(I can only (help|assist) with|I (cannot|can't|am unable to) (provide|help|share|handle|"
                      r"assist|do)|I don't have (access|information))", re.I)
OFFER = re.compile(r"\b(connect you|teammate|support team|hand (this|it) over|help center)\b", re.I)


# The request as served -------------------------------------------------------------------------------------

def as_served(messages: list[dict]) -> list[dict]:
    """Prompt v3 in place of v2, and every tool result labelled with its source."""
    out, names = [], {}
    for m in messages:
        m = dict(m)
        if m["role"] == "system" and V3_RULES not in m["content"]:
            head, sep, state = m["content"].partition("\n\nConversation state")
            m["content"] = head + V3_RULES + sep + state
        for c in m.get("tool_calls") or []:
            names[c["id"]] = c["function"]["name"]
        if m["role"] == "tool":
            try:
                m["content"] = json.dumps(label(names.get(m.get("tool_call_id"), ""), json.loads(m["content"])),
                                          ensure_ascii=False)
            except (json.JSONDecodeError, TypeError):
                pass
        out.append(m)
    return out


# Collect ---------------------------------------------------------------------------------------------------

def collect(a) -> None:
    from datasets import load_from_disk
    from openai import OpenAI

    from agent.tools_v2 import TOOLS
    rows = [r for r in load_from_disk(str(MIX))["train"] if r["source"] in SOURCES]
    if a.scenarios:
        rows = [r for r in rows if r["scenario"] in a.scenarios]
    rows = rows[: a.limit] if a.limit else rows
    OUT.mkdir(parents=True, exist_ok=True)
    done = set()
    if SAMPLES.exists():
        done = {(j["conversation"], j["step"]) for j in map(json.loads, SAMPLES.read_text().splitlines())}
    todo = [r for r in rows if (r["conversation"], r["step"]) not in done]
    print(f"{len(rows)} steps, {len(done)} already sampled, {len(todo)} to go", flush=True)
    client = OpenAI(base_url=a.base_url, api_key=a.api_key, timeout=120)

    def one(r):
        msgs = json.loads(r["messages"])
        prompt, target = as_served(msgs[:-1]), msgs[-1]
        t0 = time.perf_counter()
        try:
            resp = client.chat.completions.create(model=a.model, messages=prompt, tools=TOOLS,
                                                  temperature=a.temperature, max_tokens=512)
            m = resp.choices[0].message.model_dump(exclude_none=True)
        except Exception as e:                      # one failed step is recorded and skipped, not the whole run
            m = {"error": f"{type(e).__name__}: {e}"[:300]}
        return {"conversation": r["conversation"], "step": r["step"], "scenario": r["scenario"],
                "persona": r["persona"], "source": r["source"], "prompt": prompt, "target": target, "nova": m,
                "latency_s": round(time.perf_counter() - t0, 2)}

    with open(SAMPLES, "a") as f, ThreadPoolExecutor(a.workers) as pool:
        for k, rec in enumerate(pool.map(one, todo), 1):
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            f.flush()
            if k % 50 == 0:
                print(f"{k}/{len(todo)}", flush=True)


# Build -----------------------------------------------------------------------------------------------------

def _calls(m: dict) -> list[tuple[str, dict]]:
    out = []
    for c in m.get("tool_calls") or []:
        try:
            args = json.loads(c["function"].get("arguments") or "{}")
        except json.JSONDecodeError:
            args = {"unparsed": c["function"].get("arguments")}
        out.append((c["function"]["name"], args if isinstance(args, dict) else {"unparsed": args}))
    return out


def _same_call(x: tuple[str, dict], y: tuple[str, dict]) -> bool:
    """Same tool, and the same arguments where they decide something (free text and list sizes do not)."""
    if x[0] != y[0]:
        return False
    loose = {"query", "summary", "limit"}
    return {k: v for k, v in x[1].items() if k not in loose} == {k: v for k, v in y[1].items() if k not in loose}


def reply_problems(reply: str, prompt: list[dict]) -> list[str]:
    """What is wrong with a text reply, by the same code checks the served reply goes through."""
    evidence = [m.get("content") or "" for m in prompt if m["role"] in ("tool", "user")]
    out = []
    if DEAD_END.search(reply) and not OFFER.search(reply):
        out.append("dead_end_refusal")
    if asks_for_secret(reply):
        out.append("asks_for_secret")
    if plain_tool_words(reply)[1]:
        out.append("internal_name")
    if len(reply.split()) > 80:
        out.append("too_long")
    if grounding_issues(reply, evidence):
        out.append("ungrounded")
    return out


def tag(rec: dict) -> str | None:
    """Why Nova's message is clearly worse than the target, or None. Only clear-cut cases: reading the first pairs
    showed that a lookup the teacher skipped (tracking for a delivery date, a help-center search before a policy
    answer) is often Nova being more careful, not wrong, so those disagreements make no pair."""
    t, n = rec["target"], rec["nova"]
    tc, nc = _calls(t), _calls(n)
    reply = n.get("content") or ""
    if tc and nc:
        if _same_call(tc[0], nc[0]):
            return None
        if tc[0][0] == nc[0][0]:
            return f"wrong_args:{tc[0][0]}"
        if nc[0][0] == "escalate_to_human":
            return f"early_handoff:{tc[0][0]}"
        return f"wrong_tool:{tc[0][0]}<-{nc[0][0]}"
    if tc and not nc:
        if tc[0][0] == "search_help_center":           # answering without the search is wrong only if it is policy
            bad = reply_problems(reply, rec["prompt"])
            return f"skipped_call:search_help_center/{bad[0]}" if bad else \
                ("skipped_call:search_help_center/uncited_policy" if CITE_LIKE.search(reply) else None)
        return f"skipped_call:{tc[0][0]}"
    if nc and not tc:
        return "early_handoff:reply" if nc[0][0] == "escalate_to_human" else None
    bad = [b for b in reply_problems(reply, rec["prompt"]) if b != "ungrounded" or _invented_number(reply, rec)]
    if bad and not reply_problems(t.get("content") or "", rec["prompt"]):
        return "reply:" + bad[0]
    return None


CITE_LIKE = re.compile(r"\[kb:")


def _invented_number(reply: str, rec: dict) -> bool:
    """A number in the reply found in no tool result and no customer message (citations alone do not count)."""
    evidence = [m.get("content") or "" for m in rec["prompt"] if m["role"] in ("tool", "user")]
    return any(i.startswith("number") for i in grounding_issues(reply, evidence))


def build(a) -> None:
    recs = [json.loads(line) for line in SAMPLES.read_text().splitlines()]
    pairs, tags = [], Counter()
    for r in recs:
        if "error" in r["nova"] or not (why := tag(r)):
            continue
        tags[why.split(":")[0] + ":" + why.split(":")[1].split("<-")[0]] += 1
        nova = {k: v for k, v in r["nova"].items() if k in ("role", "content", "tool_calls")}
        pairs.append({"prompt": r["prompt"], "chosen": [r["target"]], "rejected": [nova], "tag": why,
                      "scenario": r["scenario"], "persona": r["persona"], "conversation": r["conversation"],
                      "step": r["step"]})
    PAIRS.write_text("".join(json.dumps(p, ensure_ascii=False) + "\n" for p in pairs))
    print(f"{len(recs)} steps sampled, {len(pairs)} pairs ({len(pairs) / max(1, len(recs)):.1%}) -> {PAIRS}")
    for k, v in tags.most_common():
        print(f"  {v:5d}  {k}")


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("collect")
    c.add_argument("--base-url", default="http://localhost:8090/v1")
    c.add_argument("--api-key", default="none")
    c.add_argument("--model", default="nova")
    c.add_argument("--temperature", type=float, default=0.2)      # as served
    c.add_argument("--workers", type=int, default=2)
    c.add_argument("--limit", type=int)
    c.add_argument("--scenarios", nargs="*")
    sub.add_parser("build")
    a = ap.parse_args()
    collect(a) if a.cmd == "collect" else build(a)


if __name__ == "__main__":
    main()
