"""Run the simulated cases: the customer simulator plays an eval customer with a hidden goal, Nova answers inside
the real loop, and the database is read after each conversation to record the end state.

    # Nova on the student server (serving/modal_student.py), the simulator on the teacher server
    uv run --group rag python evals/simulate.py --run 2026-11-25_sim-sft2a-r1 --system candidate \\
        --base-url <student url>/v1 --model sft2a --sim-url <teacher url>

Each run writes evals/runs/<run>/ like a golden run (config.json, traces.jsonl, resumable), with
case_set "simulated"; evals/scorecard.py scores it. Each trace also holds:
  sim   how the customer ended (done, gave_up, max_turns), its turns and token use
  db    the returns and tickets the chat left for that customer, read as the database owner before cleanup

Cases run in parallel (--workers): every case has its own customer, and each cleans up only that customer's
rows, so no case can see another's writes. Two runs on the same database at once would still clash on the
same customers: give parallel runs their own database copy (--db-url).

Nova runs exactly as served: prompt v2, tools v2, the state block and history trimming, temperature 0.2, at
most 4 model calls per turn. The simulator runs as it did for the training data (temperature 1.0), so each
run meets a slightly different customer: that variation is part of what pass^3 measures.
"""

import argparse
import json
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict
from pathlib import Path

import psycopg
from openai import OpenAI
from psycopg.rows import dict_row

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from agent import tools_v2 as tools  # noqa: E402
from agent.loop import run_turn  # noqa: E402
from agent.prompts import system_prompt  # noqa: E402
from agent.state import Context, token_counter  # noqa: E402
from config import now  # noqa: E402
from evals.build_simulated import load_cases  # noqa: E402
from evals.run_eval import RUNS, git_commit, read_traces  # noqa: E402
from synth.generate import SIM_SAMPLING, env_from_dotenv  # noqa: E402
from synth.scenarios import Scenario  # noqa: E402
from synth.simulator import CustomerSimulator  # noqa: E402
from synth.personas import BY_NAME  # noqa: E402

DB_URL = os.environ.get("DB_URL", "postgresql://nimbus:nimbus@localhost:5433/nimbus")
PROMPT, MAX_CALLS, MAX_TURNS = "v2", 4, 8


def end_state_db(owner, customer_id: int) -> dict:
    """The returns and tickets the tools created for this customer (IDs from AGENT_IDS_FROM)."""
    rets = owner.execute("""SELECT r.return_id, r.order_id, r.status, r.reason, array_agg(x.line_no) AS lines
                            FROM returns r JOIN orders o USING (order_id) LEFT JOIN return_items x USING (return_id, order_id)
                            WHERE r.return_id >= %s AND o.customer_id = %s GROUP BY 1, 2, 3, 4""",
                         (tools.AGENT_IDS_FROM, customer_id)).fetchall()
    tickets = owner.execute("SELECT ticket_id, reason, status FROM tickets WHERE ticket_id >= %s AND customer_id = %s",
                            (tools.AGENT_IDS_FROM, customer_id)).fetchall()
    return {"returns": rets, "tickets": tickets}


def clear_customer(owner, customer_id: int) -> None:
    with owner.transaction():
        owner.execute("DELETE FROM return_items WHERE return_id >= %s AND order_id IN "
                      "(SELECT order_id FROM orders WHERE customer_id = %s)", (tools.AGENT_IDS_FROM, customer_id))
        owner.execute("DELETE FROM returns WHERE return_id >= %s AND order_id IN "
                      "(SELECT order_id FROM orders WHERE customer_id = %s)", (tools.AGENT_IDS_FROM, customer_id))
        owner.execute("DELETE FROM tickets WHERE ticket_id >= %s AND customer_id = %s",
                      (tools.AGENT_IDS_FROM, customer_id))


class Runner:
    def __init__(self, a, nova: OpenAI, sim: OpenAI):
        self.a, self.nova, self.sim = a, nova, sim
        self.count = token_counter(tools.TOOLS)
        self.local = threading.local()

    def _conns(self):
        if not hasattr(self.local, "conns"):
            self.local.conns = tools.connect(self.a.db_url)
            self.local.owner = psycopg.connect(self.a.db_url, autocommit=True, row_factory=dict_row)
        return self.local.conns, self.local.owner

    def one(self, case) -> dict:
        conns, owner = self._conns()
        clear_customer(owner, case.customer_id)
        try:
            return self._converse(case, conns, owner)
        finally:
            clear_customer(owner, case.customer_id)

    def _converse(self, case, conns, owner) -> dict:
        t0 = time.perf_counter()
        session = tools.Session.open(conns, case.customer_id)
        messages = [{"role": "system", "content": system_prompt(now(), session.customer_name, PROMPT)}]
        context = Context(self.count)
        p = BY_NAME[case.persona]
        sc = Scenario(case.scenario or "general", case.customer_id, case.order_id, case.goal, case.knowledge, {}, [])
        sim = CustomerSimulator(self.sim, self.a.sim_model, sc,
                                {"name": p.name, "description": p.description, "style": p.style},
                                temperature=SIM_SAMPLING["temperature"],
                                sampling={k: v for k, v in SIM_SAMPLING.items() if k != "temperature"})
        turns, text = [], sim.opening()
        for n in range(1, MAX_TURNS + 1):
            messages.append({"role": "user", "content": text})
            t1 = time.perf_counter()
            reply, tr = run_turn(self.nova, self.a.model, messages, tools.TOOLS, tools.DISPATCH, session,
                                 max_steps=MAX_CALLS, temperature=self.a.temperature, trace_id=f"{case.id}-{n}",
                                 context=context)
            tr["turn_s"] = round(time.perf_counter() - t1, 3)
            tr["reply"] = reply
            tr.pop("sent", None)
            turns.append(tr)
            if sim.ended:                          # the customer's closing line has had its answer
                break
            nxt = sim.respond(reply)
            if nxt is None:
                break
            text = nxt
        calls = [{"name": c["name"], "raw_args": c["args"], "parsed": c["parsed"],
                  "args": json.loads(c["args"]) if c["parsed"] else None, "result": c["result"]}
                 for t in turns for c in t["tool_calls"]]
        return {"id": case.id, "category": case.category, "customer_id": case.customer_id,
                "replies": [t["reply"] for t in turns], "final_reply": turns[-1]["reply"], "tool_calls": calls,
                "escalated": any(t["escalated"] for t in turns), "turns": turns, "messages": messages,
                "sim": {"outcome": sim.ended or "max_turns", "usage": sim.usage, "opening": messages[1]["content"]},
                "db": end_state_db(owner, case.customer_id), "seconds": round(time.perf_counter() - t0, 1)}


def run(a) -> Path:
    out = RUNS / a.run
    out.mkdir(parents=True, exist_ok=True)
    cases = [c for c in load_cases() if (not a.ids or c.id in a.ids)]
    if a.limit:
        cases = cases[: a.limit]
    path = out / "traces.jsonl"
    done = {}
    if path.exists():                                  # resume: keep finished cases, retry failed ones
        done = {t["id"]: t for t in read_traces(out) if "error" not in t}
        path.write_text("".join(json.dumps(t, default=str, ensure_ascii=False) + "\n" for t in done.values()))
    env_from_dotenv("TEACHER_API_KEY")
    key = os.environ["TEACHER_API_KEY"]                # one key for both Modal apps (secret nova-teacher)
    nova = OpenAI(base_url=a.base_url, api_key=key, timeout=120, max_retries=2)
    sim = OpenAI(base_url=a.sim_url.rstrip("/") + "/v1", api_key=key, timeout=120, max_retries=2)
    config = {"run": a.run, "system": a.system, "provider": "openai", "model": a.model, "base_url": a.base_url,
              "prompt_version": PROMPT, "tools_version": "v2", "state": True, "temperature": a.temperature,
              "sampling": "default", "max_model_calls_per_turn": MAX_CALLS, "max_customer_turns": MAX_TURNS,
              "case_set": "simulated", "cases": len(cases), "simulator": {"url": a.sim_url, "model": a.sim_model,
              "sampling": SIM_SAMPLING}, "commit": git_commit(), "db": a.db_url.split("@")[-1], "notes": a.notes}
    todo = [c for c in cases if c.id not in done]
    print(f"{a.run}: {len(cases)} cases, {len(done)} already done, {len(todo)} to run", flush=True)
    runner, lock = Runner(a, nova, sim), threading.Lock()
    with path.open("a") as f, ThreadPoolExecutor(a.workers) as pool:
        futures = {pool.submit(runner.one, c): c for c in todo}
        for i, fut in enumerate(as_completed(futures), 1):
            case = futures[fut]
            try:
                trace = fut.result()
            except Exception as e:                     # record and move on; a resumed run retries it
                trace = {"id": case.id, "category": case.category, "error": f"{type(e).__name__}: {str(e)[:300]}"}
            with lock:
                f.write(json.dumps(trace, default=str, ensure_ascii=False) + "\n")
                f.flush()
            status = trace.get("error") or f"{trace['sim']['outcome']}, {len(trace['turns'])} turns, {trace['seconds']}s"
            print(f"  [{i}/{len(todo)}] {case.id}: {status}", flush=True)
    config["served_models"] = sorted({c.get("served_model") for t in read_traces(out) for tr in t.get("turns", [])
                                      for c in tr["model_calls"] if c.get("served_model")})
    (out / "config.json").write_text(json.dumps(config, indent=2))
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", required=True)
    ap.add_argument("--system", required=True, choices=["floor", "ceiling", "candidate", "diagnostic"])
    ap.add_argument("--base-url", required=True, help="Nova's OpenAI-compatible server")
    ap.add_argument("--model", required=True)
    ap.add_argument("--sim-url", required=True, help="the simulator's server (serving/modal_teacher.py), without /v1")
    ap.add_argument("--sim-model", default="teacher")
    ap.add_argument("--temperature", type=float, default=0.2)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--db-url", default=DB_URL)
    ap.add_argument("--ids", nargs="*")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--notes", default="")
    run(ap.parse_args())


if __name__ == "__main__":
    main()
