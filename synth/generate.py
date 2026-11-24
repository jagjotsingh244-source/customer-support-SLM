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
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
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
from synth.personas import BY_NAME, PERSONAS, Grid, Openers, dress  # noqa: E402
from synth.scenarios import SCENARIOS, World, pick  # noqa: E402
from synth.simulator import CustomerSimulator  # noqa: E402
from synth.style import REWRITE_NOTE, style_problems  # noqa: E402
from synth.record import LAST_STEP  # noqa: E402
from synth.verify import CLAIMED_HANDOFF, HANDOFF_OFFER, LATE, PERSON_ASK, RETURN_DONE  # noqa: E402
from agent.grounding import CITE, retrieved_ids  # noqa: E402

DB_URL = os.environ.get("DB_URL", "postgresql://nimbus:nimbus@localhost:5433/nimbus")
RAW = ROOT / "data" / "synthetic" / "raw"
BITEXT_QUESTIONS = ROOT / "data" / "processed" / "bitext_questions.parquet"
STUDENT_PROMPT = "v2"        # the serving prompt with the state rules; what the student is trained and served with
MAX_TURNS = 8                # customer messages per conversation, at most
MAX_STEPS = 4                # model calls per turn, as in serving and the eval
STALL_S = 300                # stop a run when no conversation has finished for this long
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


def source_problems(reply: str, tool_texts: list[str]) -> list[str]:
    """Numbers and citations the reply cannot back up, as rewrite instructions (the same test as the filter's
    grounded_numbers and citations checks; today's date in the system prompt counts as a source)."""
    out = []
    bad = [x.split()[1] for x in grounding_issues(CITE.sub(" ", reply), tool_texts) if x.startswith("number")]
    if bad:
        out.append(f"it states {', '.join(bad)}, which no tool or help-center result gave; leave out numbers and "
                   "rules you were not given")
    known = retrieved_ids(tool_texts)
    if cited := [c for c in CITE.findall(reply) if c not in known]:
        out.append(f"it cites {', '.join(cited)}, which no search returned; cite only returned ids, or none")
    return out


def policy_problems(reply: str, messages: list[dict], scenario: str, had_return: bool = False) -> list[str]:
    """Policy the teacher keeps breaking despite its rules, as rewrite instructions (the same tests as the
    filter's escalation and end_state checks): offering a teammate for a parcel that is only late (18 and 22
    conversations in two pilots), saying a return is done or initiated when it is only proposed (8 of 13 return
    conversations in the third), and saying it handed off without calling escalate_to_human."""
    out = []
    asked = PERSON_ASK.search("\n".join(m["content"] for m in messages if m["role"] == "user"))
    if scenario in LATE and HANDOFF_OFFER.search(reply) and not asked:
        out.append("it offers a teammate for a parcel that is only late and still with the carrier; give the last "
                   "scan and say it is still on its way, with no hand-off")
    if RETURN_DONE.search(reply) and not had_return:
        out.append("it says the return is done or started; it is only proposed until the customer presses "
                   "Confirm, and you cannot see whether they did")
    handed = any(t["function"]["name"] == "escalate_to_human" for m in messages for t in m.get("tool_calls") or [])
    if CLAIMED_HANDOFF.search(reply) and not handed:
        out.append("it says you handed the customer to a teammate, but you never called escalate_to_human; do not "
                   "claim it")
    return out


class LastStepWithoutTools:
    """Wraps the teacher's client for the last step of a turn (the request carries LAST_STEP, synth/record.py).

    Told in the system prompt, the teacher still called a fourth tool in 19 turns of the third pilot. Sent with
    no tools, it still tried in 38 turns of the first 500 of the full run, and the server's tool parser turned
    each attempt into an empty reply. So the request also ends with the note as the last thing the teacher reads,
    and an empty reply is asked for once more. All of this is the teacher's view only: the recorded step keeps
    Nova's own request, and training renders it with the tools."""

    def __init__(self, client):
        self.client, self.chat, self.completions, self.models = client, self, self, client.models

    def create(self, **kw):
        if LAST_STEP not in kw["messages"][0]["content"]:
            return self.client.chat.completions.create(**kw)
        kw.pop("tools", None)
        kw.pop("tool_choice", None)
        kw["messages"] = kw["messages"] + [{"role": "user", "content": f"(Note from your supervisor: {LAST_STEP})"}]
        r = self.client.chat.completions.create(**kw)
        if not (r.choices[0].message.content or "").strip():
            r = self.client.chat.completions.create(**{**kw, "temperature": 1.0})
        return r


class Generator:
    def __init__(self, teacher: OpenAI, sim: OpenAI, sim_model: str, db_url: str = DB_URL):
        self.teacher, self.sim, self.sim_model, self.db_url = LastStepWithoutTools(teacher), sim, sim_model, db_url
        self.count = token_counter(tools.TOOLS)
        self.local = threading.local()
        self.busy: set[int] = set()                 # customers in a conversation right now
        self.lock = threading.Condition()
        self.owner = World(db_url)                  # shared only for the scenario catalog; rows read per thread
        self.openers = Openers(BITEXT_QUESTIONS)

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
        as seeded, then let the next one start.

        On this thread's own connection: the first pilot shared one connection between 16 threads, transactions
        interleaved ("commit at the wrong nesting level"), and a customer whose cleanup failed stayed claimed, so
        the conversations waiting for it hung while the GPU kept running. The customer is released even if the
        cleanup fails; a conversation that then sees a leftover row is caught by the filtering step."""
        try:
            conn = self.local.world.conn
            with conn.transaction():
                conn.execute("DELETE FROM return_items WHERE return_id >= %s AND order_id IN "
                             "(SELECT order_id FROM orders WHERE customer_id = %s)", (tools.AGENT_IDS_FROM, cid))
                conn.execute("DELETE FROM returns WHERE return_id >= %s AND order_id IN "
                             "(SELECT order_id FROM orders WHERE customer_id = %s)", (tools.AGENT_IDS_FROM, cid))
                conn.execute("DELETE FROM tickets WHERE ticket_id >= %s AND customer_id = %s",
                             (tools.AGENT_IDS_FROM, cid))
        finally:
            with self.lock:
                self.busy.discard(cid)
                self.lock.notify_all()

    def one(self, scenario: str, seed: int, persona: str = "direct") -> dict:
        conns, world = self._thread()
        rng = random.Random(seed)
        p = BY_NAME[persona]
        sc = pick(scenario, world, rng, p.knows_number)
        sc, opener = dress(sc, p, world, self.openers, rng)
        self._claim(sc.customer_id)
        try:
            return self._converse(sc, conns, seed, {"name": p.name, "description": p.description, "style": p.style},
                                  opener)
        finally:
            self._release(sc.customer_id)

    def _rewrite(self, messages: list[dict], ctx, tr: dict, sampling: dict, scenario: str = "",
                 had_return: bool = False) -> str:
        """If the reply breaks a style rule, ask the teacher to rewrite it, at most MAX_REWRITES times.

        The note asking for it goes only to the teacher, after its own draft; the record keeps the request the
        student would have seen and, as its target, the rewritten reply. A rewrite that calls a tool or comes
        back empty is ignored, and so is one that breaks more rules than the draft it replaces."""
        reply = messages[-1]["content"]
        sources = "\n".join(m["content"] for m in messages if m["role"] == "tool")
        earlier = {m["content"].strip() for m in messages[:-1] if m["role"] == "assistant" and m.get("content")}
        tool_texts = tool_contents_before(messages, len(messages) - 1) + [messages[0]["content"]]
        problems = (style_problems(reply, sources) + source_problems(reply, tool_texts) +
                    policy_problems(reply, messages, scenario, had_return))
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
            better = (style_problems(new, sources) + source_problems(new, tool_texts) +
                      policy_problems(new, messages, scenario, had_return)) if usable else None
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

    def _converse(self, sc, conns, seed, persona, opener) -> dict:
        t0 = time.perf_counter()
        session = tools.Session.open(conns, sc.customer_id)
        student = system_prompt(now(), session.customer_name, STUDENT_PROMPT)
        ctx = RecordingContext(count_tokens=self.count, teacher_system=teacher_rules.teacher_prompt(student))
        sim = CustomerSimulator(self.sim, self.sim_model, sc, persona, temperature=SIM_SAMPLING["temperature"],
                                sampling={k: v for k, v in SIM_SAMPLING.items() if k != "temperature"},
                                opener=opener)
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
                reply = self._rewrite(messages, ctx, tr, sampling, sc.name, bool(sc.facts.get("returns")))
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
            "meta": {"scenario": sc.name, "persona": persona["name"], "opener": opener,
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


def wait_ready(base_url: str, limit_s: int = 1200) -> float:
    """Poll the server's /health with short requests until it answers 200; returns the seconds waited.

    One long first request is not enough on a cold start: on 24 November it never reached the server, which
    came up, sat idle and scaled to zero while the generator waited on that request for half an hour. Short
    polls keep waking the container until vLLM is ready, and give up after `limit_s`."""
    import urllib.error
    import urllib.request
    t0 = time.perf_counter()
    while time.perf_counter() - t0 < limit_s:
        try:
            with urllib.request.urlopen(base_url.rstrip("/") + "/health", timeout=20) as r:
                if r.status == 200:
                    return time.perf_counter() - t0
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            pass
        time.sleep(10)
    raise TimeoutError(f"{base_url} not ready after {limit_s}s")


def served_model(client: OpenAI) -> str:
    """The real model behind the endpoint's served name, recorded in every run."""
    return ",".join(getattr(m, "root", None) or m.id for m in client.models.list().data)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--label", required=True, help="part of the file name, e.g. 27b-first20")
    ap.add_argument("--scenarios", nargs="*", default=SCENARIOS)
    ap.add_argument("--personas", nargs="*", default=[p.name for p in PERSONAS])
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
    for url in {os.environ["TEACHER_URL"], sim_url or os.environ["TEACHER_URL"]}:
        print(f"  ready after {wait_ready(url):.0f}s: {url}", flush=True)
    model_id = served_model(teacher)
    sim_id = served_model(sim) if sim is not teacher else model_id
    print("teacher:", model_id, "| simulator:", sim_id, flush=True)

    gen = Generator(teacher, sim, a.sim_model)
    out = RunFile(free_path(RAW, a.label))
    grid, rng = Grid(a.scenarios, [BY_NAME[p] for p in a.personas]), random.Random(a.seed)
    jobs = [(*grid.next(rng), a.seed * 100_000 + i) for i in range(a.n)]
    stopped = False
    t0, done, totals = time.perf_counter(), 0, {"prompt": 0, "completion": 0, "sim_prompt": 0, "sim_completion": 0}
    pool = ThreadPoolExecutor(a.workers)
    futures = {pool.submit(gen.one, s, seed, p): (s, seed) for s, p, seed in jobs}
    pending, last_done = set(futures), time.perf_counter()
    while pending:
        finished, pending = wait(pending, timeout=30, return_when=FIRST_COMPLETED)
        spent = (time.perf_counter() - launched) / 3600 * a.dollars_per_hour
        stalled = time.perf_counter() - last_done > STALL_S
        if not stopped and ((a.max_dollars and spent > a.max_dollars) or stalled):
            stopped = True
            cancelled = sum(x.cancel() for x in pending)
            why = f"${spent:.2f} > ${a.max_dollars:.2f}" if not stalled else f"nothing finished for {STALL_S}s"
            print(f"  stopping ({why}); {cancelled} conversations not started", flush=True)
        if stopped and (stalled or spent > (a.max_dollars or 0) * 1.1):
            break                                   # do not wait on stuck conversations while the GPU bills
        for f in finished:
            last_done = time.perf_counter()
            if f.cancelled():                       # not started: the budget ran out
                continue
            s, seed = futures[f]
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
            print(f"  [{done}/{a.n}] {s:<26} {m['persona']:<12} {m['outcome']:<9} {m['customer_turns']} turns "
                  f"{m['teacher_tokens']['calls']} calls {m['seconds']}s", flush=True)
    pool.shutdown(wait=False, cancel_futures=True)
    out.close()
    wall = time.perf_counter() - t0
    since_launch_h = (time.perf_counter() - launched) / 3600
    summary = {"file": str(out.path.relative_to(ROOT)), "conversations": done, "wall_s": round(wall),
               "gpu_dollars_since_launch": round(since_launch_h * a.dollars_per_hour, 2),
               "s_per_conversation": round(wall / max(done, 1), 1), "tokens": totals,
               "tokens_per_conversation": {k: round(v / max(done, 1)) for k, v in totals.items()}}
    print(json.dumps(summary, indent=2), flush=True)
    if stopped:
        os._exit(0)                                 # worker threads may still be blocked; the caller stops the GPU


if __name__ == "__main__":
    main()
