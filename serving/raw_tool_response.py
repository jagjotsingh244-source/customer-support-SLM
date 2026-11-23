"""Send one tool-using request to a running vLLM server and keep the raw response JSON.

Shows what the server's tool-call parser does: with `--tool-call-parser qwen3_coder` the call comes
back in `tool_calls`; without a parser it stays as text in `content`, or the request is refused.
Two requests per run, same prompt as notes/tool-call-anatomy/round_trip.txt (Nova's system prompt,
the six tools, "Where is my order 11904?"), greedy:

  auto  tool_choice "auto", what the agent loop sends
  none  tool_choice "none": the tools are still in the prompt, but the server is told not to parse

    python serving/raw_tool_response.py --label with-parser    --out notes/tool-call-anatomy/vllm_with_parser.json
    python serving/raw_tool_response.py --label without-parser --out notes/tool-call-anatomy/vllm_without_parser.json

Standard library only, plus the repo's tool schemas and prompt (import needs psycopg and pgvector).
"""

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from agent.loop import has_tool_markup  # noqa: E402
from agent.prompts import system_prompt  # noqa: E402
from agent.tools_v1 import TOOLS  # noqa: E402
from config import now  # noqa: E402

MODEL = "Qwen/Qwen3.5-2B"
CUSTOMER_NAME = "Pranav Sood"          # customer 416, as in the round-trip render
QUESTION = "Where is my order 11904?"


def post(base_url: str, body: dict) -> tuple[int, dict]:
    req = urllib.request.Request(f"{base_url}/chat/completions", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:              # a refused request is a result too
        raw = e.read().decode(errors="replace")
        try:
            return e.code, json.loads(raw)
        except json.JSONDecodeError:
            return e.code, {"raw": raw}


def summary(status: int, resp: dict) -> dict:
    if status != 200:
        return {"http_status": status, "error": resp.get("error", resp)}
    choice = resp["choices"][0]
    msg = choice["message"]
    return {"http_status": status, "finish_reason": choice["finish_reason"],
            "content": msg.get("content"), "tool_calls": msg.get("tool_calls"),
            "call_left_in_content": has_tool_markup(msg.get("content")),
            "prompt_tokens": resp["usage"]["prompt_tokens"], "completion_tokens": resp["usage"]["completion_tokens"]}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base-url", default="http://localhost:8000/v1")
    ap.add_argument("--label", required=True, help="how the server was started, e.g. with-parser")
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()

    messages = [{"role": "system", "content": system_prompt(now(), CUSTOMER_NAME)},
                {"role": "user", "content": QUESTION}]
    out = {"label": a.label, "model": MODEL, "question": QUESTION, "requests": {}}
    for choice in ("auto", "none"):
        body = {"model": MODEL, "messages": messages, "tools": TOOLS, "tool_choice": choice,
                "temperature": 0, "max_tokens": 200}
        status, resp = post(a.base_url, body)
        out["requests"][choice] = {"summary": summary(status, resp), "raw_response": resp}
        print(f"\n===== {a.label} · tool_choice={choice} · HTTP {status} =====")
        print(json.dumps(resp, indent=2, ensure_ascii=False))
        print("--- summary ---")
        print(json.dumps(out["requests"][choice]["summary"], indent=2, ensure_ascii=False))
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n")
    print(f"\nsaved {a.out}")


if __name__ == "__main__":
    main()
