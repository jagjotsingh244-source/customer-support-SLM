"""Short chats where tools are available and the right answer uses none.

A model trained only on tool-using conversations calls a tool for everything: "thanks!" gets list_my_orders and
"are you a bot?" gets a help-center search. These chats teach the other half: Nova's tools are in the prompt, as
always, and this message does not need one. Each is one customer message and Nova's reply, written by the teacher
inside the real loop (so a tool call is possible and would be recorded), with the student's prompt, state block
and tools, exactly like the other training conversations.

The customer messages come from hand-written seeds per category, rewritten by the simulator model in a persona's
style, so they do not all sound like the seeds. A teacher reply that calls a tool is a reject: if a message really
needs a tool, it does not belong in this set.

    uv run --group rag --group local-model --group data python -m synth.no_tool --n 220 --label no-tool
"""

import argparse
import json
import os
import random
import sys
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from openai import OpenAI

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from agent import tools_v2 as tools  # noqa: E402
from agent.loop import run_turn  # noqa: E402
from agent.prompts import system_prompt  # noqa: E402
from agent.state import token_counter  # noqa: E402
from config import now  # noqa: E402
from synth import teacher_rules  # noqa: E402
from synth.generate import (RAW, STUDENT_PROMPT, TEACHER_SAMPLING, LastStepWithoutTools, env_from_dotenv,  # noqa: E402
                            free_path, wait_ready)
from synth.personas import PERSONAS  # noqa: E402
from synth.record import RecordingContext, RunFile, clean, finish_steps  # noqa: E402
from synth.scenarios import World  # noqa: E402

# Seeds per category. None of them names an order, an item, a refund or a policy: those need a tool.
CATEGORIES = {
    "greeting": ["hi", "hello there", "good morning!", "hey nova", "namaste", "hi, anyone there?"],
    "thanks": ["thanks!", "thank you so much, that's all", "ok great, thanks", "cool thx", "perfect, cheers",
               "that helps, thank you"],
    "goodbye": ["bye", "ok that's it for now, bye", "talk later", "have a good day"],
    "bot_question": ["are you a bot?", "am I talking to a real person?", "are you human or AI?",
                     "is this an automated chat?", "who am i talking to"],
    "capabilities": ["what can you help me with?", "what can you do?", "how does this chat work?",
                     "can you help with orders?"],
    "out_of_scope": ["what's the weather in Mumbai today?", "can you recommend a good laptop?",
                     "write me a poem about mangoes", "who won the cricket match yesterday?",
                     "can you help me with my maths homework", "tell me a joke",
                     "do you sell groceries?", "can you book me a train ticket"],
    "small_talk": ["how are you?", "you're doing a great job", "lol", "ok", "hmm", "nice"],
    "unclear": ["??", "help", "hello? i have a question", "wait", "one sec"],
}
REWRITE = """\
Rewrite this message from a shopper to an online store's chat assistant in the style described, keeping its \
meaning and keeping it about as short. Do not add any request about an order, a refund, a product or a policy.
Style: {style}
Message: {text}
Write only the rewritten message."""


def customer_message(sim: OpenAI, category: str, rng: random.Random) -> tuple[str, str]:
    """A seed, sometimes kept as it is and otherwise rewritten in a random persona's style."""
    seed = rng.choice(CATEGORIES[category])
    persona = rng.choice([p for p in PERSONAS if p.name not in ("adversarial", "two_in_one")])
    if rng.random() < 0.3:
        return seed, "seed"
    r = sim.chat.completions.create(model="teacher", temperature=1.0, max_tokens=60,
                                    messages=[{"role": "user", "content": REWRITE.format(style=persona.style, text=seed)}],
                                    extra_body={"chat_template_kwargs": {"enable_thinking": False}})
    text = (r.choices[0].message.content or "").strip().strip('"')
    return (text or seed), persona.name


def one(teacher, sim, conns, world, count, k: int, category: str, seed: int) -> dict:
    rng = random.Random(seed)
    cid = rng.choice(world.train_customers)
    text, style = customer_message(sim, category, rng)
    session = tools.Session.open(conns, cid)
    student = system_prompt(now(), session.customer_name, STUDENT_PROMPT)
    ctx = RecordingContext(count_tokens=count, teacher_system=teacher_rules.teacher_prompt(student))
    messages = [{"role": "system", "content": student}, {"role": "user", "content": text}]
    t0 = time.perf_counter()
    reply, tr = run_turn(teacher, "teacher", messages, tools.TOOLS, tools.DISPATCH, session, max_steps=4,
                         temperature=TEACHER_SAMPLING["temperature"],
                         sampling={x: v for x, v in TEACHER_SAMPLING.items() if x != "temperature"}, context=ctx)
    tr.pop("sent", None)
    steps = finish_steps(ctx.steps[:len(tr["model_calls"])], messages, tr["model_calls"])
    return {"id": uuid.uuid4().hex[:12], "messages": [clean(m) for m in messages], "steps": steps, "traces": [tr],
            "meta": {"scenario": "no_tool", "category": category, "persona": style, "customer_id": cid,
                     "order_id": None, "goal": f"({category}) no tool needed", "knowledge": [], "facts": {},
                     "seed": seed, "outcome": "done", "customer_turns": 1, "student_prompt": STUDENT_PROMPT,
                     "tools": tools.TOOLS_VERSION, "teacher_rules": teacher_rules.RULES_VERSION,
                     "teacher_tokens": {"prompt": sum(c["prompt_tokens"] or 0 for c in tr["model_calls"]),
                                        "completion": sum(c["completion_tokens"] or 0 for c in tr["model_calls"]),
                                        "calls": len(tr["model_calls"]), "rewrites": 0},
                     "sim_tokens": {"calls": 0, "prompt_tokens": 0, "completion_tokens": 0},
                     "seconds": round(time.perf_counter() - t0, 1)}}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=220)
    ap.add_argument("--label", default="no-tool")
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--seed", type=int, default=7007)
    a = ap.parse_args()
    env_from_dotenv("TEACHER_URL", "TEACHER_API_KEY")
    url = os.environ["TEACHER_URL"]
    print(f"ready after {wait_ready(url):.0f}s", flush=True)
    client = OpenAI(base_url=url.rstrip("/") + "/v1", api_key=os.environ["TEACHER_API_KEY"], timeout=300)
    teacher, count = LastStepWithoutTools(client), token_counter(tools.TOOLS)
    db = os.environ.get("DB_URL", "postgresql://nimbus:nimbus@localhost:5433/nimbus")
    cats = list(CATEGORIES)
    jobs = [(k, cats[k % len(cats)], a.seed * 1000 + k) for k in range(a.n)]
    out = RunFile(free_path(RAW, a.label))

    local = threading.local()

    def run(job):
        if not hasattr(local, "conns"):                 # one set of connections per thread, not per chat
            local.conns, local.world = tools.connect(db), World(db)
        return one(teacher, client, local.conns, local.world, count, *job)

    with ThreadPoolExecutor(a.workers) as pool:
        for conv in pool.map(run, jobs):
            out.write(conv)
    out.close()
    convs = [json.loads(line) for line in out.path.read_text().splitlines()]
    called = sum(1 for c in convs if c["traces"][0]["tool_calls"])
    print(f"{len(convs)} written to {out.path.name}; {called} called a tool (rejected by the filter)")


if __name__ == "__main__":
    main()
