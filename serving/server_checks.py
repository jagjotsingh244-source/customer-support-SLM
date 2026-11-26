"""Checks on a running Nova model server (serving/launch_vllm.sh), with real agent requests.

    python serving/server_checks.py auth  --base-url http://localhost:8000
    python serving/server_checks.py ttft  --base-url http://localhost:8000 --requests requests.jsonl --out ttft.json
    python serving/server_checks.py burst --base-url http://localhost:8000 --requests requests.jsonl -n 20

auth   a request without the key, with a wrong key and with the right one (NOVA_KEY): 401, 401, 200.
ttft   time to first token, streamed, one request at a time, for 20 different first-turn requests (different
       customers and messages, same tool schemas). Every Nova prompt starts with the same tool block, so with
       prefix caching the server computes it once; run once with caching on and once with it off.
       Also the same request sent again (its whole prompt cached), for reference.
burst  n requests at once (real agent requests with tools, normal length limits): latency per request,
       errors, and whether the tool calls still parse.

Requests come from serving/template_check.py capture (the agent's real requests); --model overrides the model
name they were captured with.
"""

import argparse
import json
import os
import statistics
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


def post(url: str, body: dict, key: str | None, stream: bool = False):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), method="POST",
                                 headers={"Content-Type": "application/json"})
    if key is not None:
        req.add_header("Authorization", f"Bearer {key}")
    return urllib.request.urlopen(req, timeout=300)


def load(path: Path, model: str, first_turn_only: bool) -> list[dict]:
    rows = [json.loads(line)["request"] for line in path.open()]
    out, seen = [], set()
    for r in rows:
        last_user = next(m["content"] for m in reversed(r["messages"]) if m["role"] == "user")
        if first_turn_only and (r["messages"][-1]["role"] != "user"
                                or sum(m["role"] == "user" for m in r["messages"]) > 1):
            continue
        if last_user in seen:
            continue
        seen.add(last_user)
        out.append({**r, "model": model})
    return out


def auth(a) -> dict:
    body = {"model": a.model, "messages": [{"role": "user", "content": "hi"}], "max_tokens": 5}
    result = {}
    for name, key in [("no key", None), ("wrong key", "not-the-key"), ("right key", os.environ["NOVA_KEY"])]:
        try:
            with post(f"{a.base_url}/v1/chat/completions", body, key) as r:
                result[name] = r.status
        except urllib.error.HTTPError as e:
            result[name] = e.code
    print(result)
    result["pass"] = result == {"no key": 401, "wrong key": 401, "right key": 200}
    return result


def ttft_one(a, req: dict) -> tuple[float, int]:
    body = {**req, "stream": True, "max_tokens": 1, "temperature": 0.0,
            "stream_options": {"include_usage": True}}
    t0 = time.perf_counter()
    first, prompt_tokens = None, 0
    with post(f"{a.base_url}/v1/chat/completions", body, os.environ["NOVA_KEY"]) as r:
        for line in r:
            if not line.startswith(b"data: ") or line.strip() == b"data: [DONE]":
                continue
            chunk = json.loads(line[6:])
            if first is None and chunk.get("choices"):
                first = time.perf_counter() - t0
            if chunk.get("usage"):
                prompt_tokens = chunk["usage"]["prompt_tokens"]
    return first if first is not None else time.perf_counter() - t0, prompt_tokens


def ttft(a) -> dict:
    reqs = load(a.requests, a.model, first_turn_only=True)[: a.n]
    times = [ttft_one(a, r) for r in reqs]
    again = [ttft_one(a, reqs[0])[0] for _ in range(5)]
    res = {"requests": len(reqs), "prompt_tokens_median": statistics.median(t[1] for t in times),
           "first_request_s": round(times[0][0], 3),
           "ttft_median_s": round(statistics.median(t[0] for t in times[1:]), 3),
           "ttft_max_s": round(max(t[0] for t in times[1:]), 3),
           "same_request_again_median_s": round(statistics.median(again), 3)}
    print(res)
    return res


def burst(a) -> dict:
    reqs = load(a.requests, a.model, first_turn_only=False)
    reqs = (reqs * (a.n // len(reqs) + 1))[: a.n]

    def one(req):
        t0 = time.perf_counter()
        try:
            with post(f"{a.base_url}/v1/chat/completions", {**req, "max_tokens": 512}, os.environ["NOVA_KEY"]) as r:
                d = json.load(r)
            msg = d["choices"][0]["message"]
            ok = bool(msg.get("tool_calls")) or bool((msg.get("content") or "").strip())
            raw_call = "<tool_call>" in (msg.get("content") or "")
            return time.perf_counter() - t0, None, ok and not raw_call
        except Exception as e:
            return time.perf_counter() - t0, f"{type(e).__name__}: {e}"[:200], False

    t0 = time.perf_counter()
    with ThreadPoolExecutor(a.n) as ex:
        done = list(ex.map(one, reqs))
    lat = sorted(d[0] for d in done)
    res = {"requests": a.n, "wall_s": round(time.perf_counter() - t0, 2),
           "latency_median_s": round(statistics.median(lat), 2), "latency_max_s": round(lat[-1], 2),
           "errors": [d[1] for d in done if d[1]], "usable_replies": sum(d[2] for d in done)}
    print(res)
    return res


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("check", choices=["auth", "ttft", "burst"])
    ap.add_argument("--base-url", default="http://localhost:8000")
    ap.add_argument("--model", default="nova")
    ap.add_argument("--requests", type=Path)
    ap.add_argument("-n", type=int, default=20)
    ap.add_argument("--out", type=Path)
    a = ap.parse_args()
    res = {"auth": auth, "ttft": ttft, "burst": burst}[a.check](a)
    if a.out:
        a.out.write_text(json.dumps(res, indent=1) + "\n")


if __name__ == "__main__":
    main()
