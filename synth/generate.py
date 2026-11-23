"""Generate synthetic conversations: the teacher plays Nova inside the real loop, a simulator plays the customer.

Every tool call the teacher makes runs against the real tools (agent/tools_v2.py), the real database (train
customers only) and the real help-center search, so every fact in a conversation comes from the world and only
the behaviour comes from the teacher. Each conversation is recorded with Nova's serving prompt, state block and
trimming (synth/record.py), and appended to a new file under data/synthetic/raw/ as soon as it is done.

    # the teacher on Modal (serving/modal_teacher.py); TEACHER_URL and TEACHER_API_KEY from .env
    uv run --group rag --group local-model python -m synth.generate --n 20 --label 27b-first20

The local database is the default (DB_URL); the generator is the only writer while it runs, and it removes the
returns and tickets each conversation created before the next one for the same customer starts.
"""

import argparse
import json
import os
import random
import sys
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from openai import OpenAI

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from agent import tools_v2 as tools  # noqa: E402
from agent.grounding import grounding_issues, tool_contents_before  # noqa: E402
from agent.loop import FALLBACK_REPLY, run_turn  # noqa: E402
from agent.prompts import system_prompt  # noqa: E402
from agent.state import ContextOverflow, token_counter  # noqa: E402
from config import now  # noqa: E402
from synth import teacher_rules  # noqa: E402
from synth.record import RecordingContext, RunFile, clean, finish_steps  # noqa: E402
from synth.scenarios import SCENARIOS, World, pick  # noqa: E402
from synth.simulator import CustomerSimulator  # noqa: E402
from synth.style import REWRITE_NOTE, style_problems  # noqa: E402

DB_URL = os.environ.get("DB_URL", "postgresql://nimbus:nimbus@localhost:5433/nimbus")
RAW = ROOT / "data" / "synthetic" / "raw"
STUDENT_PROMPT = "v2"        # the serving prompt with the state rules; what the student is trained and served with
MAX_TURNS = 8                # customer messages per conversation, at most
MAX_STEPS = 4                # model calls per turn, as in serving and the eval
MAX_REWRITES = 2             # asks to the teacher to fix a reply that breaks a style rule (synth/style.py)
# Qwen3.5 model card, non-thinking mode, without the presence penalty (it can bend numbers and IDs).
TEACHER_SAMPLING = {"temperature": 0.7, "top_p": 0.8,
                    "extra_body": {"top_k": 20, "chat_template_kwargs": {"enable_thinking": False}}}
SIM_SAMPLING = {"temperature": 1.0, "top_p": 0.95,
                "extra_body": {"top_k": 40, "chat_template_kwargs": {"enable_thinking": False}}}


def env_from_dotenv(*keys: str) -> None:
    """Read only the named keys from .env (the database passwords there are Neon's, not local Docker's)."""
    path = ROOT / ".env"
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        k, _, v = line.partition("=")
        if k.strip() in keys and k.strip() not in os.environ:
            os.environ[k.strip()] = v.strip().strip('"').strip("'")


class Generator:
    def __init__(self, teacher: OpenAI, sim: OpenAI, sim_model: str, db_url: str = DB_URL):
        self.teacher, self.sim, self.sim_model, self.db_url = teacher, sim, sim_model, db_url
        self.count = token_counter(tools.TOOLS)
        self.local = threading.local()
        self.busy: set[int] = set()                 # customers in a conversation right now
        self.lock = threading.Condition()
        self.owner = World(db_url)                  # shared only for the scenario catalog; rows read per thread

    def _thread(self):
        if not hasattr(self.local, "conns"):
            self.local.conns = tools.connect(self.db_url)
            self.local.world = World(self.db_url)
        return self.local.conns, self.local.world

    def _claim(self, cid: int) -> None:
        with self.lock:
            while cid in self.busy:
                self.lock.wait()
            self.busy.add(cid)

    def _release(self, cid: int) -> None:
        """Remove this customer's agent-created returns and tickets, so the next conversation finds the world
        as seeded, then let the next one start."""
        conn = self.owner.conn
        with conn.transaction():
            conn.execute("DELETE FROM return_items WHERE return_id >= %s AND order_id IN "
                         "(SELECT order_id FROM orders WHERE customer_id = %s)", (tools.AGENT_IDS_FROM, cid))
            conn.execute("DELETE FROM returns WHERE return_id >= %s AND order_id IN "
                         "(SELECT order_id FROM orders WHERE customer_id = %s)", (tools.AGENT_IDS_FROM, cid))
            conn.execute("DELETE FROM tickets WHERE ticket_id >= %s AND customer_id = %s",
                         (tools.AGENT_IDS_FROM, cid))
        with self.lock:
            self.busy.discard(cid)
            self.lock.notify_all()

    def one(self, scenario: str, seed: int, persona: dict | None = None) -> dict:
        conns, world = self._thread()
        rng = random.Random(seed)
        sc = pick(scenario, world, rng)
        self._claim(sc.customer_id)
        try:
            return self._converse(sc, conns, seed, persona)
        finally:
            self._release(sc.customer_id)

    def _rewrite(self, messages: list[dict], ctx, tr: dict, sampling: dict) -> str:
        """If the reply breaks a style rule, ask the teacher to rewrite it, at most MAX_REWRITES times.

        The note asking for it goes only to the teacher, after its own draft; the record keeps the request the
        student would have seen and, as its target, the rewritten reply. A rewrite that calls a tool or comes
        back empty is ignored, and so is one that breaks more rules than the draft it replaces."""
        reply = messages[-1]["content"]
        sources = "\n".join(m["content"] for m in messages if m["role"] == "tool")
        earlier = {m["content"].strip() for m in messages[:-1] if m["role"] == "assistant" and m.get("content")}
        problems = style_problems(reply, sources)
        tr["rewrites"] = []
        for _ in range(MAX_REWRITES):
            if not problems:
                break
            ask = ctx.last_sent + [{"role": "assistant", "content": reply},
                                   {"role": "user", "content": REWRITE_NOTE.format(problems="; ".join(problems))}]
            r = self.teacher.chat.completions.create(model="teacher", messages=ask, tools=tools.TOOLS,
                                                     temperature=TEACHER_SAMPLING["temperature"], max_tokens=512,
                                                     **sampling)
            new = (r.choices[0].message.content or "").strip()
            usable = new and not r.choices[0].message.tool_calls and new not in earlier   # not a copy of a reply
            better = style_problems(new, sources) if usable else None
            tr["rewrites"].append({"problems": problems, "accepted": better is not None and len(better) < len(problems),
                                   "prompt_tokens": r.usage.prompt_tokens if r.usage else None,
                                   "completion_tokens": r.usage.completion_tokens if r.usage else None})
            if not tr["rewrites"][-1]["accepted"]:
                continue
            reply, problems = new, better
            messages[-1]["content"] = reply
            tr["grounding"] = grounding_issues(reply, tool_contents_before(messages, len(messages)))
        tr["style_problems"] = problems                # what is still wrong; the filtering step decides
        return reply

    def _converse(self, sc, conns, seed, persona) -> dict:
        t0 = time.perf_counter()
        session = tools.Session.open(conns, sc.customer_id)
        student = system_prompt(now(), session.customer_name, STUDENT_PROMPT)
        ctx = RecordingContext(count_tokens=self.count, teacher_system=teacher_rules.teacher_prompt(student))
        sim = CustomerSimulator(self.sim, self.sim_model, sc, persona, temperature=SIM_SAMPLING["temperature"],
                                sampling={k: v for k, v in SIM_SAMPLING.items() if k != "temperature"})
        messages = [{"role": "system", "content": student}]
        traces, text, error = [], sim.opening(), None
        sampling = {k: v for k, v in TEACHER_SAMPLING.items() if k != "temperature"}
        for n in range(1, MAX_TURNS + 1):
            messages.append({"role": "user", "content": text})
            try:
                reply, tr = run_turn(self.teacher, "teacher", messages, tools.TOOLS, tools.DISPATCH, session,
                                     max_steps=MAX_STEPS, temperature=TEACHER_SAMPLING["temperature"],
                                     sampling=sampling, trace_id=f"{seed}-{n}", context=ctx)
            except ContextOverflow as e:
                error = f"context overflow: {e}"
                break
            tr.pop("sent", None)
            if reply != FALLBACK_REPLY:
                reply = self._rewrite(messages, ctx, tr, sampling)
            traces.append(tr)
            if sim.ended:                           # the closing line has had its answer
                break
            nxt = sim.respond(reply)
            if nxt is None:
                break
            text = nxt
        calls = [c for tr in traces for c in tr["model_calls"]]
        steps = finish_steps(ctx.steps[:len(calls)], messages, calls)
        return {
            "id": uuid.uuid4().hex[:12],
            "messages": [clean(m) for m in messages],
            "steps": steps,
            "traces": traces,
            "meta": {"scenario": sc.name, "persona": (persona or {}).get("name", "plain"),
                     "customer_id": sc.customer_id, "order_id": sc.order_id, "goal": sc.goal,
                     "knowledge": sc.knowledge, "facts": sc.facts, "seed": seed,
                     "outcome": sim.ended or ("error" if error else "max_turns"), "error": error,
                     "customer_turns": sum(m["role"] == "user" for m in messages),
                     "student_prompt": STUDENT_PROMPT, "tools": tools.TOOLS_VERSION,
                     "teacher_rules": teacher_rules.RULES_VERSION,
                     "teacher_tokens": {"prompt": sum(c["prompt_tokens"] or 0 for c in calls) +
                                        sum(w["prompt_tokens"] or 0 for t in traces for w in t.get("rewrites", [])),
                                        "completion": sum(c["completion_tokens"] or 0 for c in calls) +
                                        sum(w["completion_tokens"] or 0 for t in traces for w in t.get("rewrites", [])),
                                        "calls": len(calls),
                                        "rewrites": sum(len(t.get("rewrites", [])) for t in traces)},
                     "sim_tokens": sim.usage, "seconds": round(time.perf_counter() - t0, 1)},
        }


def free_path(folder: Path, label: str) -> Path:
    """<label>.jsonl, or <label>-2.jsonl and so on if taken. Named by label, not by the time: only config.now()
    may read a clock (scripts/check_clock.sh), and a run's label says what it was for."""
    path, n = folder / f"{label}.jsonl", 2
    while path.exists():
        path, n = folder / f"{label}-{n}.jsonl", n + 1
    return path


def served_model(client: OpenAI) -> str:
    """The real model behind the endpoint's served name, recorded in every run."""
    return ",".join(getattr(m, "root", None) or m.id for m in client.models.list().data)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--label", required=True, help="part of the file name, e.g. 27b-first20")
    ap.add_argument("--scenarios", nargs="*", default=SCENARIOS)
    ap.add_argument("--workers", type=int, default=8, help="conversations in parallel")
    ap.add_argument("--seed", type=int, default=3407)
    ap.add_argument("--sim-url", help="a different server for the simulator (default: the teacher's)")
    ap.add_argument("--sim-model", default="teacher")
    ap.add_argument("--max-dollars", type=float, help="stop starting new conversations once the GPU time since "
                    "launch (cold start included) would cost more than this")
    ap.add_argument("--dollars-per-hour", type=float, default=2.50,
                    help="what the running servers cost together (Modal: A100-80GB 2.50, 4xH100 15.80)")
    a = ap.parse_args()

    launched = time.perf_counter()
    env_from_dotenv("TEACHER_URL", "TEACHER_API_KEY", "SIM_URL", "SIM_API_KEY")
    teacher = OpenAI(base_url=os.environ["TEACHER_URL"].rstrip("/") + "/v1", api_key=os.environ["TEACHER_API_KEY"],
                     timeout=600)
    sim_url = a.sim_url or os.environ.get("SIM_URL")
    # Another Modal teacher app serves the simulator with the same key, unless SIM_API_KEY says otherwise.
    sim = OpenAI(base_url=sim_url.rstrip("/") + "/v1",
                 api_key=os.environ.get("SIM_API_KEY") or os.environ["TEACHER_API_KEY"],
                 timeout=600) if sim_url else teacher
    print("waiting for the teacher (a cold start loads the weights)...", flush=True)
    model_id = served_model(teacher)
    sim_id = served_model(sim) if sim is not teacher else model_id
    print("teacher:", model_id, "| simulator:", sim_id, flush=True)

    gen = Generator(teacher, sim, a.sim_model)
    out = RunFile(free_path(RAW, a.label))
    jobs = [(a.scenarios[i % len(a.scenarios)], a.seed * 100_000 + i) for i in range(a.n)]
    stopped = False
    t0, done, totals = time.perf_counter(), 0, {"prompt": 0, "completion": 0, "sim_prompt": 0, "sim_completion": 0}
    with ThreadPoolExecutor(a.workers) as pool:
        futures = {pool.submit(gen.one, s, seed): (s, seed) for s, seed in jobs}
        for f in as_completed(futures):
            if f.cancelled():                       # not started because of the budget
                continue
            s, seed = futures[f]
            spent = (time.perf_counter() - launched) / 3600 * a.dollars_per_hour
            if a.max_dollars and spent > a.max_dollars and not stopped:
                stopped = True
                cancelled = sum(x.cancel() for x in futures)
                print(f"  budget: ${spent:.2f} > ${a.max_dollars:.2f}; {cancelled} conversations not started",
                      flush=True)
            try:
                conv = f.result()
            except Exception as e:                  # one broken conversation must not stop the run
                print(f"  FAILED {s} seed={seed}: {type(e).__name__}: {e}", flush=True)
                continue
            conv["meta"]["teacher"] = model_id
            conv["meta"]["simulator"] = sim_id
            conv["meta"]["run"] = out.path.name
            out.write(conv)
            done += 1
            m = conv["meta"]
            totals["prompt"] += m["teacher_tokens"]["prompt"]
            totals["completion"] += m["teacher_tokens"]["completion"]
            totals["sim_prompt"] += m["sim_tokens"]["prompt_tokens"]
            totals["sim_completion"] += m["sim_tokens"]["completion_tokens"]
            print(f"  [{done}/{a.n}] {s:<26} {m['outcome']:<9} {m['customer_turns']} turns "
                  f"{m['teacher_tokens']['calls']} calls {m['seconds']}s", flush=True)
    out.close()
    wall = time.perf_counter() - t0
    since_launch_h = (time.perf_counter() - launched) / 3600
    summary = {"file": str(out.path.relative_to(ROOT)), "conversations": done, "wall_s": round(wall),
               "gpu_dollars_since_launch": round(since_launch_h * a.dollars_per_hour, 2),
               "s_per_conversation": round(wall / max(done, 1), 1), "tokens": totals,
               "tokens_per_conversation": {k: round(v / max(done, 1)) for k, v in totals.items()}}
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
