"""Does the server build the same prompt the model was trained on? Token for token, on real agent requests.

The most common reason a fine-tune behaves worse once served is a chat template or end-of-turn token that differs
from training. This script compares, for the same request, two renderings:

- training: the request's messages and tools through the training stack's rendering (agent/chat_template.py's
  for_template, then the tokenizer's apply_chat_template(..., add_generation_prompt=True), encoded without extra
  special tokens), as training/masking.py does;
- server: the same request sent to vLLM's /tokenize endpoint, which runs the chat preprocessing the server uses for
  /v1/chat/completions. The prompt_tokens vLLM reported for the real request is a third check on the length.

Requests come from the agent itself, so they hold everything the server sees in production: the system prompt with
the state block, earlier turns, tool calls (arguments as JSON text) and tool results.

    # 1. a pass-through proxy in front of vLLM that saves every chat request (and its prompt_tokens)
    python serving/template_check.py capture --upstream http://localhost:8000 --port 8001 --out requests.jsonl &
    uv run python evals/run_eval.py ... --base-url http://localhost:8001/v1 --limit 15

    # 2. compare 10 requests, picked to cover first calls, calls after tool results and multi-turn history
    uv run python serving/template_check.py compare --requests requests.jsonl --server http://localhost:8000 \\
        --tokenizer outputs/sft2a-r16-lr2e-4-traj_v1 --tokenizer Qwen/Qwen3.5-2B --out serving/template_check.json

Pass: every picked request renders to identical token ids on both sides.
"""

import argparse
import json
import os
import sys
import threading
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def capture(upstream: str, port: int, out: Path) -> None:
    lock = threading.Lock()

    class Proxy(BaseHTTPRequestHandler):
        def _forward(self, body: bytes | None):
            req = urllib.request.Request(upstream + self.path, data=body, method=self.command)
            for h in ("Content-Type", "Authorization"):
                if self.headers.get(h):
                    req.add_header(h, self.headers[h])
            try:
                with urllib.request.urlopen(req, timeout=600) as r:
                    status, data = r.status, r.read()
            except urllib.error.HTTPError as e:
                status, data = e.code, e.read()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return status, data

        def do_GET(self):
            self._forward(None)

        def do_POST(self):
            body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
            status, data = self._forward(body)
            if self.path.endswith("/chat/completions") and status == 200:
                usage = json.loads(data).get("usage") or {}
                with lock, out.open("a") as f:
                    f.write(json.dumps({"request": json.loads(body),
                                        "prompt_tokens": usage.get("prompt_tokens")}) + "\n")

        def log_message(self, *_):
            pass

    print(f"proxy :{port} -> {upstream}, saving chat requests to {out}", flush=True)
    ThreadingHTTPServer(("127.0.0.1", port), Proxy).serve_forever()


def kind(req: dict) -> str:
    msgs = req["messages"]
    users = sum(m["role"] == "user" for m in msgs)
    after_tool = msgs[-1]["role"] == "tool"
    return f"{'multi' if users > 1 else 'first'}-turn, {'after tool result' if after_tool else 'customer message last'}"


def pick(rows: list[dict], n: int) -> list[dict]:
    """Round-robin over the request kinds, in capture order, so all four kinds are covered when present."""
    groups: dict[str, list[dict]] = {}
    for r in rows:
        groups.setdefault(kind(r["request"]), []).append(r)
    picked, i = [], 0
    while len(picked) < n and any(i < len(g) for g in groups.values()):
        for g in groups.values():
            if i < len(g) and len(picked) < n:
                picked.append(g[i])
        i += 1
    return picked


def training_ids(tok, req: dict) -> list[int]:
    from agent.chat_template import for_template

    text = tok.apply_chat_template(for_template(req["messages"]), tools=req.get("tools"),
                                   add_generation_prompt=True, tokenize=False)
    return tok(text, add_special_tokens=False)["input_ids"]


def server_ids(server: str, req: dict, model: str | None = None) -> list[int]:
    body = {"model": model or req["model"], "messages": req["messages"], "add_generation_prompt": True,
            "add_special_tokens": False}
    if req.get("tools"):
        body["tools"] = req["tools"]
    r = urllib.request.Request(server.rstrip("/") + "/tokenize", data=json.dumps(body).encode(), method="POST",
                               headers={"Content-Type": "application/json"})
    if os.environ.get("NOVA_KEY"):
        r.add_header("Authorization", f"Bearer {os.environ['NOVA_KEY']}")
    with urllib.request.urlopen(r, timeout=60) as resp:
        return json.load(resp)["tokens"]


def first_diff(a: list[int], b: list[int]) -> int | None:
    for i, (x, y) in enumerate(zip(a, b)):
        if x != y:
            return i
    return None if len(a) == len(b) else min(len(a), len(b))


def compare(requests: Path, server: str, tokenizers: list[str], n: int, out: Path | None,
            model: str | None = None) -> bool:
    from transformers import AutoTokenizer

    rows = [json.loads(line) for line in requests.open()]
    picked = pick(rows, n)
    toks = {name: AutoTokenizer.from_pretrained(name) for name in tokenizers}
    results, ok = [], True
    for i, row in enumerate(picked):
        req = row["request"]
        srv = server_ids(server, req, model)
        res = {"n": i + 1, "kind": kind(req), "messages": len(req["messages"]), "server_tokens": len(srv),
               "prompt_tokens_reported": row.get("prompt_tokens")}
        line = f"{i + 1:>2}. {kind(req):<42} {len(srv):>5} tokens on the server"
        if not model and row.get("prompt_tokens") is not None and row["prompt_tokens"] != len(srv):
            ok = False
            line += f"  (but the real request reported {row['prompt_tokens']})"
        for name, tok in toks.items():
            ids = training_ids(tok, req)
            d = first_diff(ids, srv)
            res[name] = {"tokens": len(ids), "identical": d is None}
            if d is None:
                line += f" | {Path(name).name}: identical"
            else:
                ok = False
                res[name]["first_difference_at"] = d
                res[name]["training_text"] = tok.decode(ids[max(0, d - 20):d + 20])
                res[name]["server_text"] = tok.decode(srv[max(0, d - 20):d + 20])
                line += f" | {Path(name).name}: DIFFERS at token {d} ({len(ids)} vs {len(srv)})"
        print(line)
        results.append(res)
    eos = {name: tok.eos_token for name, tok in toks.items()}
    print(f"end-of-turn token: {eos}")
    print("PASS: every request renders to identical token ids" if ok else "FAIL: see the differences above")
    if out:
        out.write_text(json.dumps({"server": server, "model": model, "tokenizers": tokenizers, "eos_token": eos, "pass": ok,
                                   "requests": results}, indent=1) + "\n")
    return ok


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("capture")
    c.add_argument("--upstream", default="http://localhost:8000")
    c.add_argument("--port", type=int, default=8001)
    c.add_argument("--out", type=Path, required=True)
    m = sub.add_parser("compare")
    m.add_argument("--requests", type=Path, required=True)
    m.add_argument("--server", default="http://localhost:8000")
    m.add_argument("--tokenizer", action="append", required=True,
                   help="a tokenizer to render with (repeat): the training one, and the base model's")
    m.add_argument("--n", type=int, default=10)
    m.add_argument("--out", type=Path)
    m.add_argument("--model", help="the served model to tokenize with, if not the one the requests were sent to")
    a = ap.parse_args()
    if a.cmd == "capture":
        capture(a.upstream, a.port, a.out)
    else:
        sys.exit(0 if compare(a.requests, a.server, a.tokenizer, a.n, a.out, a.model) else 1)


if __name__ == "__main__":
    main()
