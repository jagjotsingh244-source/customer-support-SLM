"""Generation speed of a served model: output tokens per second, one conversation at a time and many at once.

Uses a real agent request (system prompt, state, tool schemas: about 1,200 prompt tokens) captured by
serving/template_check.py, and asks for a fixed number of output tokens (ignore_eos) so every format does the same
work. Greedy, no tool parsing involved in the timing.

    python serving/decode_speed.py --base-url http://localhost:8000/v1 --model sft2a_v1 \\
        --requests requests.jsonl --concurrency 1 8 32 --out serving/speed-adapter.json

Reports, per concurrency level, the median of three rounds: aggregate output tokens/s, tokens/s per conversation,
and time to first token (streamed) for a single request.
"""

import argparse
import json
import os
import statistics
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from openai import OpenAI


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base-url", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--requests", type=Path, required=True)
    ap.add_argument("--tokens", type=int, default=256)
    ap.add_argument("--concurrency", type=int, nargs="+", default=[1, 8, 32])
    ap.add_argument("--rounds", type=int, default=3)
    ap.add_argument("--out", type=Path)
    a = ap.parse_args()

    req = next(json.loads(line)["request"] for line in a.requests.open())
    client = OpenAI(base_url=a.base_url, api_key=os.environ.get("NOVA_KEY", "EMPTY"))
    kw = {"model": a.model, "messages": req["messages"], "tools": req.get("tools"), "tool_choice": "none",
              "temperature": 0.0, "max_tokens": a.tokens, "extra_body": {"ignore_eos": True, "min_tokens": a.tokens}}

    def one():
        t0 = time.perf_counter()
        r = client.chat.completions.create(**kw)
        return r.usage.completion_tokens, time.perf_counter() - t0, r.usage.prompt_tokens

    one()                                                   # warm-up
    ttft = []
    for _ in range(a.rounds):
        t0 = time.perf_counter()
        for chunk in client.chat.completions.create(**kw, stream=True):
            if chunk.choices and chunk.choices[0].delta.content:
                ttft.append(time.perf_counter() - t0)
                break
    result = {"model": a.model, "prompt_tokens": one()[2], "output_tokens": a.tokens,
              "ttft_s_median": round(statistics.median(ttft), 3), "levels": []}
    for c in a.concurrency:
        rounds = []
        for _ in range(a.rounds):
            t0 = time.perf_counter()
            with ThreadPoolExecutor(c) as ex:
                done = list(ex.map(lambda _: one(), range(c)))
            wall = time.perf_counter() - t0
            rounds.append((sum(d[0] for d in done) / wall, statistics.mean(d[0] / d[1] for d in done)))
        level = {"concurrency": c, "tokens_per_s": round(statistics.median(r[0] for r in rounds), 1),
                 "tokens_per_s_per_conversation": round(statistics.median(r[1] for r in rounds), 1)}
        result["levels"].append(level)
        print(level, flush=True)
    print(json.dumps(result))
    if a.out:
        a.out.write_text(json.dumps(result, indent=1) + "\n")


if __name__ == "__main__":
    main()
