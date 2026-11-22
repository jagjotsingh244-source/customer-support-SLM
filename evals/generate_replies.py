"""Generate replies to the fixed held-out prompts, and compare two sets of replies to the same prompts.

The prompts come from evals/style_metrics.held_out_prompts(): each is the system prompt the training rows were
built with plus one customer message, and no tools, so a base model and a fine-tune answer exactly the same
messages. Decoding is greedy, with the agent loop's 512-token cap, so differences come from the model.

    # through a vLLM server (the base model by its name, a LoRA module by its --lora-modules name)
    python evals/generate_replies.py generate --provider openai --base-url http://localhost:8000/v1 \\
        --model nova-sft1 --out evals/style/sft1.jsonl

    # in the process with Transformers, an adapter merged into the base (a notebook, or a Mac)
    python evals/generate_replies.py generate --provider local --model Qwen/Qwen3.5-2B \\
        --adapter 123jagjot/sft1-r16-lr2e-4-bitext_v1 --set export --out evals/style/sft1-notebook-export.jsonl

    # export check: the same 10 prompts in the notebook and through vLLM
    python evals/generate_replies.py compare evals/style/sft1-notebook-export.jsonl evals/style/sft1-vllm-export.jsonl

Sets: "heldout" is all 200 prompts (style metrics, blind side-by-side); "export" is 10 of them, the first five
of each split.
"""

import argparse
import difflib
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from evals.style_metrics import held_out_prompts  # noqa: E402

MAX_TOKENS = 512  # the agent loop's cap per model call


def prompt_set(name):
    rows = held_out_prompts()
    if name == "export":
        rows = [r for r in rows if r["split"] == "validation"][:5] + \
               [r for r in rows if r["split"] == "test_unseen_intents"][:5]
    return rows


def client_for(a):
    if a.provider == "local":
        from agent.local_client import LocalChatClient
        return LocalChatClient(a.model, adapter=a.adapter)
    from openai import OpenAI
    return OpenAI(base_url=a.base_url, api_key=os.environ.get("OPENAI_API_KEY", "EMPTY"))


def generate(a):
    rows = prompt_set(a.set)
    client = client_for(a)
    extra = {"tools": None} if a.provider == "local" else {}  # the local client's signature wants tools

    def one(row):
        r = client.chat.completions.create(model=a.model, messages=row["messages"], temperature=0,
                                           max_tokens=MAX_TOKENS, **extra)
        choice = r.choices[0]
        return {"id": row["id"], "split": row["split"], "intent": row["intent"],
                "prompt": row["messages"][-1]["content"], "reply": (choice.message.content or "").strip(),
                "finish_reason": choice.finish_reason, "tokens": r.usage.completion_tokens}

    workers = 1 if a.provider == "local" else 16
    with ThreadPoolExecutor(workers) as pool:
        out = list(pool.map(one, rows))
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text("".join(json.dumps(o, ensure_ascii=False) + "\n" for o in out))
    cut = sum(o["finish_reason"] == "length" for o in out)
    print(f"{len(out)} replies from {a.model}{' + ' + a.adapter if a.adapter else ''} -> {a.out} "
          f"({cut} hit the {MAX_TOKENS}-token cap)")


def read(path):
    return {r["id"]: r for r in (json.loads(x) for x in Path(path).read_text().splitlines() if x.strip())}


def compare(a):
    """Per prompt: word-level similarity, lengths and how each ended. 'differs in kind' means one reply ran
    into the cap while the other stopped, or one is more than twice as long: check the chat template and the
    end-of-turn token before anything else."""
    x, y = read(a.a), read(a.b)
    kinds = 0
    for k in [k for k in x if k in y]:
        p, q = x[k], y[k]
        ratio = difflib.SequenceMatcher(None, p["reply"].split(), q["reply"].split()).ratio()
        lp, lq = len(p["reply"].split()), len(q["reply"].split())
        in_kind = p["finish_reason"] != q["finish_reason"] or max(lp, lq) > 2 * max(1, min(lp, lq))
        kinds += in_kind
        verdict = "same" if ratio == 1 else "differs in kind" if in_kind else f"wording ({ratio:.0%} same)"
        print(f"\n[{k}] {p['prompt']!r}: {verdict}\n  A ({lp}w, {p['finish_reason']}): {p['reply']}\n"
              f"  B ({lq}w, {q['finish_reason']}): {q['reply']}")
    same = sum(x[k]["reply"] == y[k]["reply"] for k in x if k in y)
    print(f"\n{same} identical, {kinds} differ in kind, of {sum(k in y for k in x)} prompts")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("generate")
    g.add_argument("--provider", choices=["openai", "local"], default="openai")
    g.add_argument("--base-url")
    g.add_argument("--model", required=True)
    g.add_argument("--adapter", help="for --provider local: a LoRA adapter merged into --model")
    g.add_argument("--set", choices=["heldout", "export"], default="heldout")
    g.add_argument("--out", required=True)
    c = sub.add_parser("compare")
    c.add_argument("a")
    c.add_argument("b")
    a = ap.parse_args()
    if a.cmd == "generate":
        if a.provider == "openai" and not a.base_url:
            ap.error("--base-url is required with --provider openai")
        generate(a)
    else:
        compare(a)


if __name__ == "__main__":
    main()
