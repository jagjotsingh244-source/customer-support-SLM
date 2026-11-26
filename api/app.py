"""Nova's backend API: the chat, the customer's Confirm click on a proposed return, health and warm-up.

    uv run --group api --group rag uvicorn api.app:app --port 8080

Configured only by environment variables, so the same code runs on a laptop, in CI and in production:

    DATABASE_URL    the store's owner URL; only its host and database are used, each role connects with its
                    own password (NOVA_READER_PASSWORD, NOVA_WRITER_PASSWORD, NOVA_CONFIRMER_PASSWORD).
                    DB_URL is read when DATABASE_URL is not set.
    MODEL_BASE_URL  the model server's OpenAI-compatible URL, e.g. https://.../v1 (api/model_endpoint.py, the
                    backend's only network client; this module and the tools reach only Postgres)
    NOVA_KEY        the model server's API key
    MODEL_NAME      the served model name (default nova)
    NOW_MODE        real in production, frozen (the default) in tests and evals (config.py)
    DEMO_CUSTOMERS  comma-separated customer ids that /demo-login accepts (default: any eval-partition customer)
    DB_POOL         conversations that can be mid-turn at once, each with its own connections (default 16)
    COOKIE_SECURE   1 (default): the session cookie is sent over https only; 0 for local http

The customer comes from the session cookie that /demo-login sets, never from the body or the conversation.
Conversations live in this process's memory (one instance; the deployment pins it), and nothing a customer
writes is logged: the log line per turn holds timings and tool names only.
"""

import json
import logging
import os
import queue
import secrets
import sys
import threading
import time
from collections import OrderedDict
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from functools import cache
from pathlib import Path

import psycopg
from fastapi import Cookie, Depends, FastAPI, Header, HTTPException, Response
from fastapi.responses import JSONResponse
from psycopg.rows import dict_row
from pydantic import BaseModel, Field

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from api import model_endpoint  # noqa: E402
from api.returns import confirm_return  # noqa: E402
from config import now, partition_for  # noqa: E402
from db.roles import role_url  # noqa: E402

DB_URL = os.environ.get("DATABASE_URL") or os.environ.get("DB_URL", "postgresql://nimbus:nimbus@localhost:5433/nimbus")
MODEL_NAME = os.environ.get("MODEL_NAME", "nova")
PROMPT, MAX_CALLS, TEMPERATURE = "v3", 4, 0.2   # the shipping configuration the golden set measures
SESSIONS_KEPT = 2000

@asynccontextmanager
async def lifespan(_app):
    """Load everything slow before the first customer arrives: the tools' connections, the embedding model
    and the prompt token counter. The model endpoint is not woken here; /warmup does that."""
    from agent import tools_v2
    pool()
    tools_v2._embedder().query("warm up")
    _counter()
    yield


app = FastAPI(title="Nova backend", lifespan=lifespan)
log = logging.getLogger("nova.api")
logging.basicConfig(level=logging.INFO, format="%(message)s")


# Database --------------------------------------------------------------------------------------------

IDLE_CHECK_S = 60      # a managed database that scales to zero drops idle connections (Neon: after ~5 minutes)


def _alive(conns) -> bool:
    try:
        for c in conns:
            c.execute("SELECT 1")
        return True
    except psycopg.Error:
        return False


_CONFIRMER = {"conn": None, "last_used": 0.0}
_CONFIRMER_LOCK = threading.Lock()


def confirmer() -> psycopg.Connection:
    """The confirm role's connection, reopened if the database dropped it while idle."""
    with _CONFIRMER_LOCK:
        conn = _CONFIRMER["conn"]
        stale = time.monotonic() - _CONFIRMER["last_used"] > IDLE_CHECK_S
        if conn is None or conn.closed or (stale and not _alive([conn])):
            conn = psycopg.connect(role_url("nova_confirmer", DB_URL), autocommit=True, row_factory=dict_row)
            conn.execute("SET TIME ZONE 'Asia/Kolkata'")
            _CONFIRMER["conn"] = conn
        _CONFIRMER["last_used"] = time.monotonic()
        return conn


@cache
def pool() -> "queue.Queue":
    """Connections for the tools, one reader + writer pair per conversation that is mid-turn. A turn holds its
    pair for the whole turn, so row-level security's per-transaction customer setting can never meet another
    customer's query on the same connection."""
    from agent import tools_v2
    q = queue.Queue()
    for _ in range(int(os.environ.get("DB_POOL", "16"))):
        q.put((tools_v2.connect(DB_URL), time.monotonic()))
    return q


class Conns:
    """Check a pair out of the pool for one turn. A pair idle for more than a minute is pinged first and
    replaced if the database dropped it; a pair that failed during the turn is replaced afterwards."""

    def __enter__(self):
        from agent import tools_v2
        self.conns, last_used = pool().get()
        if time.monotonic() - last_used > IDLE_CHECK_S and not _alive(self.conns):
            log.info(json.dumps({"event": "db_reconnect", "reason": "idle connection dropped"}))
            self.conns = tools_v2.connect(DB_URL)
        return self.conns

    def __exit__(self, exc_type, *exc):
        from agent import tools_v2
        if exc_type is not None and issubclass(exc_type, psycopg.OperationalError):
            log.info(json.dumps({"event": "db_reconnect", "reason": "connection failed mid-turn"}))
            self.conns = tools_v2.connect(DB_URL)
        pool().put((self.conns, time.monotonic()))


# Sessions --------------------------------------------------------------------------------------------

@dataclass
class Chat:
    customer_id: int
    customer_name: str
    messages: list
    context: object
    guard: object
    rules: object
    lock: threading.Lock = field(default_factory=threading.Lock)
    turns: int = 0


SESSIONS: "OrderedDict[str, Chat]" = OrderedDict()
SESSIONS_LOCK = threading.Lock()


def demo_customers() -> set[int] | None:
    raw = os.environ.get("DEMO_CUSTOMERS", "").strip()
    return {int(x) for x in raw.split(",") if x.strip()} if raw else None


@cache
def _counter():
    from agent import tools_v2
    from agent.state import token_counter
    return token_counter(tools_v2.TOOLS)


def new_chat(customer_id: int) -> Chat:
    from agent import tools_v2
    from agent.escalation import HandoffRules
    from agent.guardrails import Guard
    from agent.prompts import system_prompt
    from agent.state import Context
    with Conns() as conns:
        session = tools_v2.Session.open(conns, customer_id)
    messages = [{"role": "system", "content": system_prompt(now(), session.customer_name, PROMPT)}]
    return Chat(customer_id, session.customer_name, messages, Context(_counter()), Guard(messages[0]["content"]),
                HandoffRules())


def current_chat(nova_session: str | None = Cookie(default=None)) -> Chat:
    with SESSIONS_LOCK:
        chat = SESSIONS.get(nova_session or "")
        if chat is None:
            raise HTTPException(401, "not signed in: POST /demo-login first")
        SESSIONS.move_to_end(nova_session)
        return chat


# Routes ----------------------------------------------------------------------------------------------

class Login(BaseModel):
    customer_id: int


class Message(BaseModel):
    message: str = Field(min_length=1, max_length=4000)


@app.post("/demo-login")
def demo_login(body: Login, response: Response):
    allowed = demo_customers()
    if (allowed is not None and body.customer_id not in allowed) or partition_for(body.customer_id) != "eval":
        raise HTTPException(403, "not a demo account")
    try:
        chat = new_chat(body.customer_id)
    except ValueError:
        raise HTTPException(404, "no such customer") from None
    sid = secrets.token_urlsafe(24)
    with SESSIONS_LOCK:
        SESSIONS[sid] = chat
        while len(SESSIONS) > SESSIONS_KEPT:
            SESSIONS.popitem(last=False)
    response.set_cookie("nova_session", sid, httponly=True, samesite="lax",
                        secure=os.environ.get("COOKIE_SECURE", "1") == "1")   # 0 only for local http
    return {"customer_id": chat.customer_id, "name": chat.customer_name}


@app.post("/chat")
def chat(body: Message, response: Response, c: Chat = Depends(current_chat)):
    from agent import tools_v2
    from agent.loop import run_turn
    t0 = time.perf_counter()
    with c.lock, Conns() as conns:                     # one turn at a time per conversation
        session = tools_v2.Session(conns, c.customer_id, c.customer_name)
        c.messages.append({"role": "user", "content": body.message})
        c.turns += 1
        reply, trace = run_turn(model_endpoint.client(), MODEL_NAME, c.messages, tools_v2.TOOLS, tools_v2.DISPATCH, session,
                                max_steps=MAX_CALLS, temperature=TEMPERATURE, context=c.context, guard=c.guard,
                                rules=c.rules)
    turn_s = time.perf_counter() - t0
    model_s = sum(m["latency_s"] for m in trace["model_calls"])
    tools = [t["name"] for t in trace["tool_calls"]]
    log.info(json.dumps({"event": "turn", "turn_s": round(turn_s, 3), "model_s": round(model_s, 3),
                         "model_calls": len(trace["model_calls"]), "tools": tools, "escalated": trace["escalated"]}))
    response.headers["Server-Timing"] = f"turn;dur={turn_s * 1000:.0f}, model;dur={model_s * 1000:.0f}"
    return {"reply": reply, "turn_s": round(turn_s, 3), "model_s": round(model_s, 3),
            "model_calls": len(trace["model_calls"]), "tools": tools, "escalated": trace["escalated"]}


@app.get("/health")
def health():
    """The database answers, and whether the model endpoint is awake. A scale-to-zero model that is asleep is
    reported, not an error: the first chat (or /warmup) wakes it."""
    out = {"now_mode": os.environ.get("NOW_MODE", "frozen")}
    try:
        with confirmer().cursor() as cur:
            cur.execute("SELECT 1")
        out["database"] = "ok"
    except Exception as e:
        out["database"] = f"error: {type(e).__name__}"
    _, detail = model_endpoint.ready(timeout=3)
    out["model"] = detail
    status = 200 if out["database"] == "ok" else 503
    return JSONResponse(out, status_code=status)


@app.post("/warmup")
def warmup():
    """Wake the model endpoint and wait until it answers (the UI's "Waking Nova up..." button)."""
    t0 = time.perf_counter()
    while time.perf_counter() - t0 < 600:
        ready, detail = model_endpoint.ready(timeout=30)
        if ready:
            return {"model": "ready", "waited_s": round(time.perf_counter() - t0, 1)}
        if detail.startswith("HTTP 4"):
            raise HTTPException(502, f"model endpoint refused: {detail}")
        time.sleep(2)
    raise HTTPException(504, "model endpoint did not wake within 10 minutes")


def signed_in_customer(x_customer_id: int | None = Header(default=None),
                       nova_session: str | None = Cookie(default=None)) -> int:
    """The session cookie from /demo-login; the X-Customer-Id header is the development stand-in."""
    if nova_session:
        return current_chat(nova_session).customer_id
    if x_customer_id is None:
        raise HTTPException(401, "not signed in")
    return x_customer_id


@app.post("/returns/{proposal_id}/confirm")
def confirm(proposal_id: int, customer_id: int = Depends(signed_in_customer)):
    outcome = confirm_return(confirmer(), customer_id, proposal_id, now())
    return JSONResponse(outcome.body, status_code=outcome.status)
