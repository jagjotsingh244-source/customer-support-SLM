"""Run one scripted conversation through the agent loop and print every message.

    # the prompted 2B model, served by vLLM (on the GPU machine)
    uv run python -m agent.chat --base-url http://localhost:8000/v1 --model Qwen/Qwen3.5-2B \
        --customer 416 "hi where is my order?? it was supposed to come days ago"

    # a frontier model: same prompt, tools and loop; only base_url, model and key change
    OPENAI_API_KEY=... uv run python -m agent.chat --base-url https://... --model ... --customer 416 "..."

Each extra positional argument is one more user turn (scripted: later turns do
not react to Nova's replies). The database comes from DB_URL (default: local
Docker). --out saves the full transcript and trace as JSON.
"""

import argparse
import json
import os
import statistics
import sys
import time
from pathlib import Path

from openai import OpenAI

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from agent.loop import run_turn  # noqa: E402
from agent.prompts import PROMPT_VERSION, system_prompt  # noqa: E402
from agent.tools_v0 import REGISTRY, TOOLS, Session, connect  # noqa: E402
from config import now  # noqa: E402

DB_URL = os.environ.get("DB_URL", "postgresql://nimbus:nimbus@localhost:5433/nimbus")


def show(m: dict) -> None:
    role = m["role"]
    if role == "system":
        print(f"\n[system]\n{m['content']}")
    elif role == "user":
        print(f"\n[user] {m['content']}")
    elif role == "tool":
        print(f"[tool result] {m['content'][:1500]}")
    else:
        for c in m.get("tool_calls", []):
            print(f"[assistant -> tool] {c['function']['name']}({c['function']['arguments']})")
        if m.get("content"):
            print(f"[assistant] {m['content']}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--customer", type=int, required=True)
    ap.add_argument("--temperature", type=float, default=0.2)
    ap.add_argument("--out", help="save transcript and trace to this JSON file")
    ap.add_argument("turns", nargs="+", help="user messages, one per turn")
    a = ap.parse_args()

    client = OpenAI(base_url=a.base_url, api_key=os.environ.get("OPENAI_API_KEY", "EMPTY"))
    session = Session.open(connect(DB_URL), a.customer)
    messages = [{"role": "system", "content": system_prompt(now(), session.customer_name)}]
    show(messages[0])

    traces = []
    for text in a.turns:
        start = len(messages)
        messages.append({"role": "user", "content": text})
        t0 = time.perf_counter()
        _, trace = run_turn(client, a.model, messages, TOOLS, REGISTRY, session, temperature=a.temperature)
        trace["turn_s"] = round(time.perf_counter() - t0, 3)   # model calls + tools + database
        traces.append(trace)
        for m in messages[start:]:
            show(m)
        calls = trace["model_calls"]
        print(f"  -- {trace['turn_s']:.2f}s for the turn ({sum(c['latency_s'] for c in calls):.2f}s in "
              f"{len(calls)} model call(s)), "
              f"tokens in/out per call: {[(c['prompt_tokens'], c['completion_tokens']) for c in calls]}"
              f"{', ESCALATED' if trace['escalated'] else ''}")

    turn_s = [t["turn_s"] for t in traces]
    print(f"\nmodel={a.model} prompt={PROMPT_VERSION} temp={a.temperature} "
          f"median turn latency={statistics.median(turn_s):.2f}s")
    if a.out:
        Path(a.out).write_text(json.dumps({"model": a.model, "prompt_version": PROMPT_VERSION,
                                           "customer_id": a.customer, "temperature": a.temperature,
                                           "messages": messages, "traces": traces},
                                          indent=2, default=str))
        print(f"saved {a.out}")


if __name__ == "__main__":
    main()
