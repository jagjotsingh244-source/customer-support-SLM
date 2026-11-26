"""Drive the chat stream the way the page does and time what a visitor sees.

    uv run python serving/stream_check.py --base-url http://localhost:8080 --out serving/stream/mac.json
    uv run python serving/stream_check.py --base-url https://<backend> --token "$(gcloud auth print-identity-token)"

Each of the five scenario customers signs in and sends their suggested message (GET /demo-customers), REPEATS times.
For every turn it records, from the client's side, when the first event arrived (the first sign of life), when
each status line arrived, and when the reply arrived; from the done event, the final model call's latency and the
reply checks' time.

The hold is what buffering costs. Streamed token by token, the reply's first words would show about one time to
first token after the final model call starts; buffered, they show when that call has finished and the checks
have run. So the hold is final_call_s + checks_ms minus the time to first token, and final_call_s + checks_ms is
its upper bound, reported here.
"""

import argparse
import json
import statistics
import sys
import time
from pathlib import Path

import httpx


def events(resp):
    kind, data = None, ""
    for line in resp.iter_lines():
        if line.startswith("event:"):
            kind = line[6:].strip()
        elif line.startswith("data:"):
            data += line[5:].strip()
        elif line == "" and kind:
            yield kind, json.loads(data)
            kind, data = None, ""


def one_turn(client, message):
    t0 = time.perf_counter()
    out = {"message": message, "statuses": [], "first_event_s": None}
    with client.stream("POST", "/chat/stream", json={"message": message}, timeout=900) as r:
        r.raise_for_status()
        for kind, data in events(r):
            t = round(time.perf_counter() - t0, 3)
            if out["first_event_s"] is None:
                out["first_event_s"] = t
            if kind == "status":
                out["statuses"].append({"t_s": t, "text": data["text"], "waking": data.get("waking", False)})
            elif kind == "reply":
                out["reply_s"] = t
                out["reply"] = data["text"]
            elif kind in ("confirm_card", "handoff"):
                out[kind] = data
            elif kind == "done":
                out["done"] = data
            elif kind == "error":
                out["error"] = data["text"]
    return out


def pct(xs, q):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, round(q * (len(xs) - 1)))] if xs else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default="http://localhost:8080")
    ap.add_argument("--token", help="a Google identity token, for the private backend")
    ap.add_argument("--repeats", type=int, default=1)
    ap.add_argument("--out")
    a = ap.parse_args()
    headers = {"Authorization": f"Bearer {a.token}"} if a.token else {}
    turns = []
    people = httpx.get(f"{a.base_url}/demo-customers", headers=headers, timeout=60).json()["featured"]
    for _ in range(a.repeats):
        for p in people:
            with httpx.Client(base_url=a.base_url, headers=headers) as client:
                client.post("/demo-login", json={"customer_id": p["customer_id"]}).raise_for_status()
                turn = one_turn(client, p["try"])
            turn["customer_id"] = p["customer_id"]
            turns.append(turn)
            d = turn.get("done", {})
            print(f"{p['customer_id']:>4}  first event {turn['first_event_s']} s  reply {turn.get('reply_s')} s  "
                  f"tools {d.get('tools')}  final call {d.get('final_call_s')} s  checks {d.get('checks_ms')} ms  "
                  f"{'card ' if 'confirm_card' in turn else ''}{'handoff' if 'handoff' in turn else ''}"
                  f"{turn.get('error', '')}", file=sys.stderr)
    ok = [t for t in turns if "done" in t]
    holds = [t["done"]["final_call_s"] + t["done"]["checks_ms"] / 1000 for t in ok if t["done"]["final_call_s"]]
    summary = {
        "turns": len(turns), "failed": len(turns) - len(ok),
        "first_event_s": {"p50": pct([t["first_event_s"] for t in ok], .5), "p95": pct([t["first_event_s"] for t in ok], .95)},
        "reply_s": {"p50": pct([t["reply_s"] for t in ok], .5), "p95": pct([t["reply_s"] for t in ok], .95)},
        "hold_upper_bound_s": {"p50": pct(holds, .5), "p95": pct(holds, .95)},
        "checks_ms": {"p50": pct([t["done"]["checks_ms"] for t in ok], .5),
                      "max": max((t["done"]["checks_ms"] for t in ok), default=None)},
        "turns_with_status_before_reply": sum(1 for t in ok if t["statuses"]),
        "mean_tools_per_turn": round(statistics.mean(len(t["done"]["tools"]) for t in ok), 2) if ok else None,
    }
    print(json.dumps(summary, indent=2))
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(json.dumps({"base_url_kind": "local" if "localhost" in a.base_url else "deployed",
                                           "summary": summary, "turns": turns}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
