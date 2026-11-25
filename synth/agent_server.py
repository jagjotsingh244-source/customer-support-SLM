"""A mailbox model server: lets a coding agent (or a person) be the teacher and the simulated customer.

synth/generate.py talks to an OpenAI-compatible server. This file is such a server, except that no model sits
behind it: every chat-completion request is written to a queue folder and the server waits until an answer
file appears. The generator, its tools, its database, its recording of the student's view and every check run
exactly as with a GPU teacher; only who writes the next message changes.

    # terminal 1: the mailbox (records --teacher as the model name in every conversation)
    uv run python -m synth.agent_server serve --teacher "<agent and model name>"
    # terminal 2: the generator, pointed at it, one or two conversations at a time
    TEACHER_URL=http://127.0.0.1:8765 TEACHER_API_KEY=local uv run --group rag --group local-model --group data \
        python -m synth.generate --cells-file synth/agent_plan.json --label agent-r1 --workers 1 --stall-s 3600
    # the agent, in a loop (synth/agent_generation.md):
    uv run python -m synth.agent_server next              # shows the oldest waiting request
    uv run python -m synth.agent_server answer <id> --say "..."            # a message
    uv run python -m synth.agent_server answer <id> --call get_tracking '{"order_id": 11904}'   # a tool call
"""

import argparse
import json
import sys
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
QUEUE = ROOT / "data" / "synthetic" / "agent-queue"
INBOX, OUTBOX = QUEUE / "inbox", QUEUE / "outbox"
CUSTOMER_MARK = "###DONE###"           # the simulator's prompt mentions its end markers; Nova's never does


def role_of(req: dict) -> str:
    system = next((m.get("content") or "" for m in req["messages"] if m["role"] == "system"), "")
    return "customer" if CUSTOMER_MARK in system else "nova"


def response(req: dict, answer: dict) -> dict:
    """An OpenAI chat-completion response carrying the agent's answer."""
    msg = {"role": "assistant", "content": answer.get("say")}
    if answer.get("call"):
        msg["content"] = None
        msg["tool_calls"] = [{"id": f"call_{uuid.uuid4().hex[:8]}", "type": "function",
                              "function": {"name": answer["call"], "arguments": json.dumps(answer["args"])}}]
    return {"id": f"chatcmpl-{uuid.uuid4().hex[:12]}", "object": "chat.completion", "created": int(time.time()),
            "model": req.get("model", "teacher"),
            "choices": [{"index": 0, "message": msg, "finish_reason": "tool_calls" if answer.get("call") else "stop"}],
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}}


def serve(port: int, teacher: str) -> None:
    INBOX.mkdir(parents=True, exist_ok=True)
    OUTBOX.mkdir(parents=True, exist_ok=True)
    stale = QUEUE / "stale" / time.strftime("%Y%m%d-%H%M%S")
    for f in [*INBOX.iterdir(), *OUTBOX.iterdir()]:     # requests from a stopped run: nobody waits for them now
        stale.mkdir(parents=True, exist_ok=True)
        f.rename(stale / f.name)
    info = {"id": "teacher", "object": "model", "root": teacher, "owned_by": "agent"}

    class Handler(BaseHTTPRequestHandler):
        def _send(self, code, obj):
            body = json.dumps(obj).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if self.path == "/health":
                return self._send(200, {})
            if self.path == "/v1/models":
                return self._send(200, {"object": "list", "data": [info]})
            self._send(404, {"error": "not found"})

        def do_POST(self):
            req = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
            rid = f"{time.strftime('%H%M%S')}-{uuid.uuid4().hex[:6]}"
            (INBOX / f"{rid}.json").write_text(json.dumps({"id": rid, "role": role_of(req), "request": req}))
            out = OUTBOX / f"{rid}.json"
            while not out.exists():                       # the generator's own timeout bounds this wait
                time.sleep(0.5)
            answer = json.loads(out.read_text())
            out.unlink()
            for f in [INBOX / f"{rid}.json", *INBOX.glob(f"{rid}.*.claimed")]:
                f.unlink(missing_ok=True)
            self._send(200, response(req, answer))

        def log_message(self, *a):
            pass

    print(f"mailbox on http://127.0.0.1:{port}, teacher recorded as {teacher!r}; queue {QUEUE}", flush=True)
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()


def tool_line(fn: dict) -> str:
    """One tool as the model would see it: name, purpose, and each argument with its type and allowed values."""
    params = fn.get("parameters") or {}
    req = set(params.get("required") or [])
    args = []
    for name, spec in (params.get("properties") or {}).items():
        kind = "|".join(map(str, spec["enum"])) if spec.get("enum") else spec.get("type", "any")
        if "minimum" in spec or "maximum" in spec:
            kind += f" {spec.get('minimum', '')}-{spec.get('maximum', '')}"
        note = f" ({spec['description']})" if spec.get("description") and not spec.get("enum") else ""
        args.append(f"{name}{'*' if name in req else ''}: {kind}{note}")
    desc = (fn.get("description") or "").split(". ")[0]
    return f"- {fn['name']}({', '.join(args)}): {desc}"


SEEN = QUEUE / "seen"                  # which instruction texts each agent has already been shown


def show(item: dict, agent: str = "a1", full: bool = False) -> str:
    """The waiting request, written for the agent: who to play, the instructions, the conversation so far.
    Instructions are printed in full the first time an agent sees them (per role and conversation); after that a
    one-line reminder, so the agent reads mostly what is new."""
    import hashlib
    req, role = item["request"], item["role"]
    lines = [f"REQUEST {item['id']}  -  you are writing the next message as: {role.upper()}"]
    for m in req["messages"]:
        if m["role"] == "system":
            text = m["content"]
            key = hashlib.sha1(text[:300].encode()).hexdigest()[:16]     # the start is fixed per conversation and role
            mark = SEEN / agent / key
            if full or not mark.exists():
                lines += ["", f"=== INSTRUCTIONS {key} (follow them exactly) ===", text, "=== END INSTRUCTIONS ==="]
            else:
                before = set(mark.read_text().splitlines())
                changed = [ln for ln in text.splitlines() if ln.strip() and ln not in before]
                lines += ["", f"(instructions {key}: as shown before" + (", with these lines new or changed:" if changed
                              else ", unchanged") + ")", *changed]
            mark.parent.mkdir(parents=True, exist_ok=True)
            mark.write_text(text)
        elif m.get("tool_calls"):
            for c in m["tool_calls"]:
                lines.append(f"[nova calls] {c['function']['name']} {c['function']['arguments']}")
        elif m["role"] == "tool":
            lines.append(f"[tool result] {m['content']}")
        else:
            who = {"user": "customer" if role == "nova" else "nova", "assistant": role}[m["role"]]
            lines.append(f"[{who}] {m.get('content') or ''}")
    if req.get("tools") and role == "nova":
        lines += ["", "Tools you may call (or reply instead). Use exactly these argument names; * = required:"]
        lines += [tool_line(t["function"]) for t in req["tools"]]
    elif role == "nova":
        lines += ["", "No tools this time: reply to the customer."]
    lines += ["", f"Answer with: python -m synth.agent_server answer {item['id']} --say \"...\""
                  + ("  or  --call <tool> '<json args>'" if req.get("tools") and role == "nova" else "")]
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("serve")
    s.add_argument("--port", type=int, default=8765)
    s.add_argument("--teacher", required=True, help="who answers, recorded in every conversation")
    n = sub.add_parser("next", help="claim and show the oldest waiting request")
    n.add_argument("--agent", default="a1", help="a name per agent when several run in parallel")
    n.add_argument("--full", action="store_true", help="always show the full instructions")
    sub.add_parser("status", help="how many requests are waiting")
    a = sub.add_parser("answer")
    a.add_argument("id")
    g = a.add_mutually_exclusive_group(required=True)
    g.add_argument("--say", help="the message text")
    g.add_argument("--call", nargs=2, metavar=("TOOL", "JSON_ARGS"), help="a tool call (Nova only)")
    x = ap.parse_args()
    if x.cmd == "serve":
        return serve(x.port, x.teacher)
    waiting = sorted(INBOX.glob("*.json")) if INBOX.exists() else []
    if x.cmd == "status":
        return print(f"{len(waiting)} waiting, {len(list(INBOX.glob('*.claimed')))} being answered")
    if x.cmd == "next":
        for path in waiting:                       # claim atomically: parallel agents never get the same one
            claimed = path.with_name(f"{path.stem}.{x.agent}.claimed")
            try:
                path.rename(claimed)
            except FileNotFoundError:
                continue
            return print(show(json.loads(claimed.read_text()), x.agent, x.full))
        return print("nothing waiting")
    path = next(iter(INBOX.glob(f"{x.id}.*.claimed")), INBOX / f"{x.id}.json")
    if not path.exists():
        sys.exit(f"no waiting request {x.id}")
    if x.call:
        item = json.loads(path.read_text())
        names = {t["function"]["name"] for t in item["request"].get("tools") or []}
        if item["role"] != "nova" or x.call[0] not in names:
            sys.exit(f"{x.call[0]} is not a tool offered in this request ({', '.join(sorted(names)) or 'none'})")
        answer = {"call": x.call[0], "args": json.loads(x.call[1])}
    else:
        answer = {"say": x.say}
    (OUTBOX / f"{x.id}.json").write_text(json.dumps(answer))
    print("sent")


if __name__ == "__main__":
    main()
