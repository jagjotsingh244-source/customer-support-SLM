"""Run the golden set through the agent loop, save every trace, score it, write the report.

    # floor: prompted Qwen3.5-2B served by vLLM (on the GPU machine)
    uv run python evals/run_eval.py --run 2026-11-23_floor --provider openai \\
        --base-url http://localhost:8000/v1 --model Qwen/Qwen3.5-2B

    # ceiling: Gemini on Vertex AI (VERTEX_API_KEY and VERTEX_PROJECT set)
    uv run python evals/run_eval.py --run 2026-11-23_ceiling --provider gemini --model gemini-4-hydrogen

    # re-score saved traces with the current metrics, without calling any model
    uv run python evals/run_eval.py --rescore evals/runs/2026-11-23_floor

Each run writes evals/runs/<run>/:
  config.json   what was measured: model, provider, served models, prompt version, sampling, commit
  traces.jsonl  one line per case with every message, tool call, result and timing; written as it goes,
                so an interrupted run (a free GPU session ending, a rate limit) resumes where it stopped
  report.md     per-category scorecard with counts and percentages, latency and tokens

The run name is given, never read from the clock (scripts/check_clock.sh): name runs <date>_<system>.

Scoring (deterministic, yes/no per case):
  tool_names  called tools match the expected names, in order
  tool_args   names and arguments match exactly; expected args of null match anything (free text),
              and default arguments are filled in on both sides first ({} == {"limit": 5})
  valid_json  every tool call's arguments parsed
  facts       every must_include appears in Nova's replies (all turns), after evals.validate.normalize
  forbidden   no must_not_include appears in any reply
  escalation  handed off exactly when should_escalate
  all         every check above passed
"""

import argparse
import json
import os
import statistics
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from agent.loop import run_turn  # noqa: E402
from agent.prompts import PROMPT_VERSION, system_prompt  # noqa: E402
from agent.tools_v0 import REGISTRY, TOOLS, Session, connect  # noqa: E402
from config import now  # noqa: E402
from evals.validate import QUOTAS, load, normalize  # noqa: E402

RUNS = ROOT / "evals" / "runs"
DB_URL = os.environ.get("DB_URL", "postgresql://nimbus:nimbus@localhost:5433/nimbus")
METRICS = ["tool_names", "tool_args", "valid_json", "facts", "forbidden", "escalation", "all"]
DEFAULT_ARGS = {"list_my_orders": {"limit": 5}}
SAMPLING = {   # named settings for the sampling comparison; temperature is passed separately
    "default": {},
    # Qwen3.5 model card, non-thinking: temperature 1.0, top_p 1.0, top_k 20, presence_penalty 2.0
    "model-card": {"top_p": 1.0, "presence_penalty": 2.0, "extra_body": {"top_k": 20}},
}


# Running ---------------------------------------------------------------------------

def make_client(a):
    if a.provider == "gemini":
        from agent.gemini_adapter import GeminiChatClient
        return GeminiChatClient(api_key=os.environ["VERTEX_API_KEY"], project=os.environ["VERTEX_PROJECT"],
                                location=os.environ.get("VERTEX_LOCATION", "global"))
    from openai import OpenAI
    return OpenAI(base_url=a.base_url, api_key=os.environ.get("OPENAI_API_KEY", "EMPTY"))


def run_case(case, client, a, conn) -> dict:
    """One golden case, fresh session for its customer; scripted user turns."""
    session = Session.open(conn, case.customer_id)
    messages = [{"role": "system", "content": system_prompt(now(), session.customer_name)}]
    turns = []
    for text in case.turns:
        messages.append({"role": "user", "content": text})
        t0 = time.perf_counter()
        reply, tr = run_turn(client, a.model, messages, TOOLS, REGISTRY, session,
                             temperature=a.temperature, sampling=SAMPLING[a.sampling])
        tr["turn_s"] = round(time.perf_counter() - t0, 3)
        tr["reply"] = reply
        turns.append(tr)
    calls = []
    for t in turns:
        for c in t["tool_calls"]:
            calls.append({"name": c["name"], "raw_args": c["args"], "parsed": c["parsed"],
                          "args": json.loads(c["args"]) if c["parsed"] else None, "result": c["result"]})
    return {"id": case.id, "category": case.category, "customer_id": case.customer_id,
            "replies": [t["reply"] for t in turns], "final_reply": turns[-1]["reply"],
            "tool_calls": calls, "escalated": any(t["escalated"] for t in turns),
            "turns": turns, "messages": messages}


def git_commit() -> str:
    head = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, cwd=ROOT).stdout.strip()
    dirty = subprocess.run(["git", "status", "--porcelain", "--", "agent", "evals/golden"],
                           capture_output=True, text=True, cwd=ROOT).stdout.strip()
    return head + ("+uncommitted changes" if dirty else "")


def run(a) -> Path:
    out = RUNS / a.run
    out.mkdir(parents=True, exist_ok=True)
    cases, errors = load()
    if errors:
        sys.exit("golden set has format errors; run evals/validate.py")
    cases = [c for _, c in cases if (not a.ids or c.id in a.ids)]
    if a.limit:
        cases = cases[: a.limit]

    path = out / "traces.jsonl"
    done = {}
    if path.exists():                                 # resume: keep finished cases, retry failed ones
        for line in path.read_text().splitlines():
            t = json.loads(line)
            if "error" not in t:
                done[t["id"]] = t
        path.write_text("".join(json.dumps(t, default=str, ensure_ascii=False) + "\n" for t in done.values()))

    config = {"run": a.run, "system": a.system, "provider": a.provider, "model": a.model,
              "base_url": a.base_url, "prompt_version": PROMPT_VERSION, "temperature": a.temperature,
              "sampling": a.sampling, "sampling_settings": SAMPLING[a.sampling], "max_model_calls_per_turn": 4,
              "cases": len(cases), "commit": git_commit(), "db_host": DB_URL.split("@")[-1].split("/")[0],
              "notes": a.notes}
    client, conn = make_client(a), connect(DB_URL)
    todo = [c for c in cases if c.id not in done]
    print(f"{a.run}: {len(cases)} cases, {len(done)} already done, {len(todo)} to run")
    with path.open("a") as f:
        for i, case in enumerate(todo, 1):
            try:
                trace = run_case(case, client, a, conn)
            except Exception as e:                     # record and move on; a resumed run retries it
                trace = {"id": case.id, "category": case.category, "error": f"{type(e).__name__}: {str(e)[:300]}"}
            f.write(json.dumps(trace, default=str, ensure_ascii=False) + "\n")
            f.flush()
            status = trace.get("error") or f"{sum(t['turn_s'] for t in trace['turns']):.1f}s"
            print(f"  [{i}/{len(todo)}] {case.id}: {status}")
    served = sorted({c.get("served_model") for t in read_traces(out) for tr in t.get("turns", [])
                     for c in tr["model_calls"] if c.get("served_model")})
    config["served_models"] = served
    (out / "config.json").write_text(json.dumps(config, indent=2))
    return out


# Scoring ---------------------------------------------------------------------------

def read_traces(out: Path) -> list[dict]:
    p = out / "traces.jsonl"
    return [json.loads(line) for line in p.read_text().splitlines()] if p.exists() else []


def _args(name: str, args) -> dict:
    return {**DEFAULT_ARGS.get(name, {}), **(args or {})}


def score(case, trace: dict) -> dict:
    if "error" in trace:
        return {m: False for m in METRICS}
    e = case.expect
    got, exp = trace["tool_calls"], e.tool_calls
    replies = normalize(" ".join(r or "" for r in trace["replies"]))
    s = {
        "tool_names": [c["name"] for c in got] == [c.name for c in exp],
        "tool_args": len(got) == len(exp) and all(
            g["name"] == x.name and (x.args is None or _args(x.name, x.args) == _args(g["name"], g["args"]))
            for g, x in zip(got, exp)),
        "valid_json": all(c["parsed"] for c in got),
        "facts": all(normalize(f) in replies for f in e.must_include),
        "forbidden": not any(normalize(f) in replies for f in e.must_not_include),
        "escalation": trace["escalated"] == e.should_escalate,
    }
    s["all"] = all(s.values())
    return s


def pct(k: int, n: int) -> str:
    return f"{k}/{n} ({100 * k / n:.0f}%)" if n else "-"


def report(out: Path) -> str:
    config = json.loads((out / "config.json").read_text())
    cases = {c.id: c for _, c in load()[0]}
    traces = [t for t in read_traces(out) if t["id"] in cases]
    scores = {t["id"]: score(cases[t["id"]], t) for t in traces}
    (out / "scores.json").write_text(json.dumps(scores, indent=1))

    by_cat = defaultdict(list)
    for t in traces:
        by_cat[t["category"]].append(scores[t["id"]])
    rows = ["| Category | n | " + " | ".join(METRICS) + " |", "|---|---|" + "---|" * len(METRICS)]
    for cat in [c for c in QUOTAS if c in by_cat]:
        ss = by_cat[cat]
        rows.append(f"| {cat} | {len(ss)} | " + " | ".join(pct(sum(s[m] for s in ss), len(ss)) for m in METRICS) + " |")
    allss = list(scores.values())
    rows.append(f"| **all** | {len(allss)} | " + " | ".join(f"**{pct(sum(s[m] for s in allss), len(allss))}**"
                                                          for m in METRICS) + " |")

    ok = [t for t in traces if "error" not in t]
    turn_s = sorted(tr["turn_s"] for t in ok for tr in t["turns"])
    calls = [c for t in ok for tr in t["turns"] for c in tr["model_calls"]]
    def q(xs, p):
        return xs[min(len(xs) - 1, int(p * len(xs)))] if xs else 0
    errors = [t for t in traces if "error" in t]
    lines = [
        f"## {config['run']} · {config['system']} · `{config['model']}` · prompt {config['prompt_version']} · "
        f"temperature {config['temperature']} · sampling {config['sampling']}",
        "",
        f"Provider `{config['provider']}`; served by {', '.join(f'`{m}`' for m in config.get('served_models', [])) or 'n/a'}; "
        f"commit `{config['commit']}`; database `{config['db_host']}`; up to {config['max_model_calls_per_turn']} model calls per turn."
        + (f" Notes: {config['notes']}" if config.get("notes") else ""),
        "",
        *rows,
        "",
        f"Latency per turn (model calls + tools + database): median {statistics.median(turn_s):.2f} s, "
        f"p95 {q(turn_s, 0.95):.2f} s, max {turn_s[-1]:.2f} s over {len(turn_s)} turns." if turn_s else "No turns.",
        f"Model calls: {len(calls)}; mean prompt tokens {statistics.mean(c['prompt_tokens'] or 0 for c in calls):.0f}, "
        f"mean completion tokens {statistics.mean(c['completion_tokens'] or 0 for c in calls):.0f}." if calls else "",
        f"Cases that errored (scored as failures): {len(errors)}" + (": " + ", ".join(t["id"] for t in errors) if errors else "."),
        "",
        "Failed cases: " + ", ".join(i for i, s in sorted(scores.items()) if not s["all"]),
    ]
    text = "\n".join(lines) + "\n"
    (out / "report.md").write_text(text)
    return text


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", help="run name, e.g. 2026-11-23_floor (folder under evals/runs)")
    ap.add_argument("--system", choices=["floor", "ceiling", "candidate"], help="what the run measures")
    ap.add_argument("--provider", choices=["openai", "gemini"], default="openai")
    ap.add_argument("--base-url", help="OpenAI-compatible server, for --provider openai")
    ap.add_argument("--model")
    ap.add_argument("--temperature", type=float, default=0.2)
    ap.add_argument("--sampling", choices=list(SAMPLING), default="default")
    ap.add_argument("--limit", type=int, help="only the first N cases (smoke test)")
    ap.add_argument("--ids", nargs="*", help="only these case ids")
    ap.add_argument("--notes", default="", help="free text stored in config.json")
    ap.add_argument("--rescore", type=Path, help="re-score an existing run folder; no model calls")
    a = ap.parse_args()

    if a.rescore:
        print(report(a.rescore))
        return
    if not (a.run and a.system and a.model):
        ap.error("--run, --system and --model are required (or use --rescore)")
    if a.provider == "openai" and not a.base_url:
        ap.error("--base-url is required with --provider openai")
    print(report(run(a)))


if __name__ == "__main__":
    main()
