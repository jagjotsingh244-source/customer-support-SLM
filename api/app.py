"""Nova's backend API: the chat page, the chat (streamed as events), the customer's Confirm click on a proposed
return, thumbs feedback, health and warm-up.

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
    DEMO_RESET      1 on the public demo: signing in clears what earlier visitors did for that customer
    DB_POOL         conversations that can be mid-turn at once, each with its own connections (default 16)
    COOKIE_SECURE   1 (default): the session cookie is sent over https only; 0 for local http
    MODEL_IDLE_S    seconds after which the model endpoint may be asleep (default 900, its scale-down window): the
                    next turn checks first and tells the customer it is waking

A turn on /chat/stream sends events: status as each tool starts, then reply once the reply has passed the
grounding check and output filter (it is never streamed token by token past them), confirm_card for a proposed
return, handoff for a ticket, and done with the trace id that /feedback takes. /chat runs the same turn and
answers once, in JSON.

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
import random
import time
import uuid
from collections import OrderedDict
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from functools import cache
from pathlib import Path
from typing import Literal

import psycopg
from fastapi import Cookie, Depends, FastAPI, Header, HTTPException, Response
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from psycopg.rows import dict_row
from pydantic import BaseModel, Field

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from api import model_endpoint, tracing  # noqa: E402
from api.returns import confirm_return  # noqa: E402
from config import now, partition_for  # noqa: E402
from db.roles import role_url  # noqa: E402

DB_URL = os.environ.get("DATABASE_URL") or os.environ.get("DB_URL", "postgresql://nimbus:nimbus@localhost:5433/nimbus")
MODEL_NAME = os.environ.get("MODEL_NAME", "nova")
PROMPT, MAX_CALLS, TEMPERATURE = "v3", 4, 0.2   # the shipping configuration the golden set measures
SESSIONS_KEPT = 2000
UI = Path(__file__).resolve().parent.parent / "ui"

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
    traces: dict = field(default_factory=dict)       # trace id -> turn number, for feedback
    feedback: dict = field(default_factory=dict)     # trace id -> "up" | "down"
    conversation_id: str = field(default_factory=lambda: uuid.uuid4().hex)   # the traces' session id
    route: "Route" = None                            # which model answers this conversation, fixed at sign-in


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


# Model routing: production and an optional canary ---------------------------------------------------------

@dataclass(frozen=True)
class Route:
    """Which model answers a conversation: the served name, its endpoint, and the version its traces are tagged
    with."""
    name: str
    base_url: str
    version: str
    canary: bool = False


def production_route() -> Route:
    return Route(MODEL_NAME, model_endpoint.MODEL_BASE_URL, tracing.MODEL_VERSION)


def pick_route() -> Route:
    """Production, or the canary for a CANARY_SHARE slice of new conversations (0 to 1). Read from the environment
    at every sign-in, so a rollback is one variable: CANARY_SHARE=0 (ops/set_env.sh). A conversation keeps the
    model it started with.

        CANARY_MODEL     the canary's served name, e.g. nova-next (a new, permanent name: never reuse one)
        CANARY_BASE_URL  its endpoint, when another server serves it (default MODEL_BASE_URL)
        CANARY_VERSION   its tag in traces (default CANARY_MODEL)
        CANARY_SHARE     share of new conversations it gets (default 0: off)"""
    share = float(os.environ.get("CANARY_SHARE", "0") or 0)
    name = os.environ.get("CANARY_MODEL", "").strip()
    if name and share > 0 and random.random() < share:
        return Route(name, os.environ.get("CANARY_BASE_URL") or model_endpoint.MODEL_BASE_URL,
                     os.environ.get("CANARY_VERSION") or name, canary=True)
    return production_route()


def new_chat(customer_id: int) -> Chat:
    from agent import tools_v2
    from agent.escalation import HandoffRules
    from agent.guardrails import Guard
    from agent.prompts import system_prompt
    from agent.state import Context
    with Conns() as conns:
        session = tools_v2.Session.open(conns, customer_id)
    messages = [{"role": "system", "content": system_prompt(now(), session.customer_name, PROMPT)}]
    route = pick_route()
    log.info(json.dumps({"event": "route", "model": route.name, "version": route.version, "canary": route.canary}))
    return Chat(customer_id, session.customer_name, messages, Context(_counter()), Guard(messages[0]["content"]),
                HandoffRules(), route=route)


def current_chat(nova_session: str | None = Cookie(default=None)) -> Chat:
    with SESSIONS_LOCK:
        chat = SESSIONS.get(nova_session or "")
        if chat is None:
            raise HTTPException(401, "not signed in: POST /demo-login first")
        SESSIONS.move_to_end(nova_session)
        return chat


# Demo customers -------------------------------------------------------------------------------------

# Five eval-partition customers, each showing a different part of Nova, listed first in the picker with a message
# to try. Every other eval-partition customer follows (db/demo.sql demo_customer_list()).
DEMO_PERSONAS = [
    {"customer_id": 57, "scenario": "A parcel on its way", "try": "Where is my order?"},
    {"customer_id": 116, "scenario": "Returning something", "try": "I'd like to return the wireless mouse I got last week."},
    {"customer_id": 137, "scenario": "A parcel that never came", "try": "My phone case still hasn't arrived and it's been weeks."},
    {"customer_id": 176, "scenario": "A late order", "try": "My order is late. When will it get here?"},
    {"customer_id": 372, "scenario": "A return window that has closed", "try": "Can I return the induction cooktop I bought in October?"},
]
ANY_CUSTOMER_TRY = "Where is my order?"
LATEST = {"placed": "just placed", "packed": "being packed", "shipped": "on its way",
          "out_for_delivery": "out for delivery", "delivered": "delivered", "cancelled": "cancelled",
          "return_requested": "return in progress", "refunded": "refunded"}
_DEMO_LIST: list = []                                   # read once per process: the store's customers do not change


# Turn events ----------------------------------------------------------------------------------------

# What the chat page shows while a tool runs. Only an order id (a number) is ever put into the text.
STATUS = {
    "list_my_orders": "Checking your orders…",
    "get_order_status": "Looking at order {order_id}…",
    "get_tracking": "Checking the tracking for order {order_id}…",
    "search_help_center": "Looking it up in the help center…",
    "propose_return": "Checking whether it can go back…",
    "escalate_to_human": "Passing this to a teammate…",
}
WAKING = "Nova is waking up. Sorry, the GPU sleeps when nobody's chatting (student budget). About 2 minutes."
TURN_FAILED = "Nova couldn't answer just now. Please send that again in a moment."
MODEL_IDLE_S = float(os.environ.get("MODEL_IDLE_S", "900"))  # the model endpoint sleeps after this long idle
HEARTBEAT_S = 15                                              # an SSE comment keeps proxies from closing a long wait
_MODEL: dict = {}                                             # endpoint -> when it last answered


NO_ORDER_ID = {"get_order_status": "Looking at your order…", "get_tracking": "Checking the tracking…"}


def status_text(tool: str, args: dict) -> str:
    oid = args.get("order_id")
    text = STATUS.get(tool, "Working on it…")
    if "{order_id}" in text:
        text = text.format(order_id=oid) if isinstance(oid, int) else NO_ORDER_ID[tool]
    return text


# The same steps in the past tense, for the "How Nova answered" list under a reply.
DONE_STEP = {
    "list_my_orders": "Checked your orders",
    "get_order_status": "Looked at order {order_id}",
    "get_tracking": "Checked the tracking for order {order_id}",
    "search_help_center": "Searched the help center",
    "propose_return": "Checked whether it can go back",
    "escalate_to_human": "Opened a ticket for a teammate",
}
NO_ORDER_ID_DONE = {"get_order_status": "Looked at your order", "get_tracking": "Checked the tracking"}


def step_text(tool: str, args: dict) -> str:
    oid = args.get("order_id")
    text = DONE_STEP.get(tool, "Used a tool")
    if "{order_id}" in text:
        text = text.format(order_id=oid) if isinstance(oid, int) else NO_ORDER_ID_DONE[tool]
    return text


def _steps(trace: dict, reply: str) -> dict:
    """What the turn did, for the page: each tool step with its time and outcome, the model's share, and the
    reply checks. Labels and numbers only: no tool results, no arguments beyond an order number."""
    from agent.loop import FALLBACK_REPLY, SKIPPED
    from agent.state import parse_args
    steps = [{"text": step_text(t["name"], parse_args(t["args"]) or {}), "ms": t["latency_ms"],
              "ok": bool(t["ok"]), "skipped": t["result"] == SKIPPED}
             for t in trace["tool_calls"]]
    return {"tools": steps,
            "model": {"calls": len(trace["model_calls"]),
                      "s": round(sum(m["latency_s"] for m in trace["model_calls"]), 2)},
            "checks": {"ms": trace.get("checks_ms"), "changed_reply": bool(trace.get("output_guard"))},
            "rule_handoff": bool(trace.get("forced_handoff")),
            "fallback": reply == FALLBACK_REPLY}


def _cards(trace: dict) -> tuple[list, dict | None]:
    """The Confirm cards (one per return proposed this turn) and the hand-off, from the tool results.
    A card carries the proposal id and what to show; Confirm sends back only the id."""
    cards, handoff = [], None
    for call in trace["tool_calls"]:
        r = call["result"] if isinstance(call["result"], dict) else {}
        if (call["name"] == "propose_return" and r.get("eligible") and r.get("proposal_id")
                and all(c["proposal_id"] != r["proposal_id"] for c in cards)):     # asked twice: one card
            cards.append({"proposal_id": r["proposal_id"], "order_id": r.get("order_id"), "item": r.get("item"),
                          "refund_estimate_inr": None if r.get("refund_estimate_inr") is None
                          else float(r["refund_estimate_inr"])})     # a Decimal from Postgres
        if call["name"] == "escalate_to_human" and r.get("handed_off") and r.get("ticket_id"):
            from agent.escalation import next_opening, support_open
            t = now()
            opens = next_opening(t)
            handoff = {"ticket_id": r["ticket_id"], "support_open": support_open(t),
                       "opens": None if support_open(t) else
                       ("today" if opens.date() == t.astimezone(opens.tzinfo).date() else "tomorrow")}
    return cards, handoff


def _run(c: Chat, text: str, trace_id: str, emit) -> tuple[str, dict]:
    """One turn through the shipping loop. The conversation is put back as it was if the turn fails."""
    from agent import tools_v2
    from agent.loop import FALLBACK_REPLY, run_turn
    with c.lock, Conns() as conns:                     # one turn at a time per conversation
        route = c.route or production_route()
        if (time.monotonic() - _MODEL.get(route.base_url, float("-inf")) > MODEL_IDLE_S
                and not model_endpoint.ready(timeout=2, base_url=route.base_url)[0]):
            emit("status", {"text": WAKING, "waking": True})
        session = tools_v2.Session(conns, c.customer_id, c.customer_name)
        kept = len(c.messages)
        c.messages.append({"role": "user", "content": text})
        with tracing.turn(trace_id, customer_id=c.customer_id, conversation_id=c.conversation_id, message=text,
                          tags=[f"adapter:{route.version}", *trace_tags(conns.reader)],
                          version=route.version) as (root, spans):
            try:
                reply, trace = run_turn(model_endpoint.client(route.base_url), route.name, c.messages, tools_v2.TOOLS,
                                        tools_v2.DISPATCH, session, max_steps=MAX_CALLS, temperature=TEMPERATURE,
                                        trace_id=trace_id, context=c.context, guard=c.guard, rules=c.rules,
                                        spans=spans,
                                        on_event=lambda kind, d: emit(kind, {"text": status_text(d["tool"], d["args"]),
                                                                             "tool": d["tool"]}))
            except Exception:
                del c.messages[kept:]
                raise
            cards, handoff = _cards(trace)
            root.update(output={"reply": reply,
                                "events": ["reply"] + ["confirm_card"] * len(cards) + (["handoff"] if handoff else [])},
                        metadata={"turn": c.turns + 1, "tools": [t["name"] for t in trace["tool_calls"]],
                                  "rule_handoff": trace.get("forced_handoff"), "fallback": reply == FALLBACK_REPLY})
        tracing.score_turn(trace_id, tracing.turn_scores(trace_id, trace))
        _MODEL[route.base_url] = time.monotonic()
        c.turns += 1
        c.traces[trace_id] = c.turns
        return reply, trace


_TAGS: list = []


def trace_tags(reader) -> list[str]:
    """What every trace is tagged with: which model, prompt, help-center index and clock answered. A canary is
    then a filter on the adapter tag. Read once, on the turn's own reader connection."""
    if not _TAGS:
        try:
            kb = tracing.kb_version(reader)
        except psycopg.Error:
            kb = "unknown"
        _TAGS.extend([f"prompt:{PROMPT}", f"kb:{kb}",
                      f"now:{os.environ.get('NOW_MODE', 'frozen')}"])
    return _TAGS


def turn_events(c: Chat, text: str):
    """(event, data) pairs for one turn: status as each tool starts, then reply (after every check), confirm_card
    and handoff if they happened, and done with the trace id. The turn runs in a worker thread so status events
    leave while it is still going; a None event is a heartbeat."""
    trace_id = uuid.uuid4().hex
    t0 = time.perf_counter()
    q: "queue.Queue" = queue.Queue()

    def emit(kind, data):
        q.put((kind, {**data, "t_ms": round(1000 * (time.perf_counter() - t0))}))

    def work():
        try:
            q.put(("_result", _run(c, text, trace_id, emit)))
        except Exception as e:                         # the customer sees a plain message; the log gets the type
            q.put(("_error", e))

    threading.Thread(target=work, daemon=True).start()
    while True:
        try:
            kind, data = q.get(timeout=HEARTBEAT_S)
        except queue.Empty:
            yield None, None
            continue
        if kind == "_error":
            log.error(json.dumps({"event": "turn_failed", "trace_id": trace_id, "error": type(data).__name__}))
            yield "error", {"text": TURN_FAILED, "trace_id": trace_id}
            return
        if kind != "_result":
            yield kind, data
            continue
        reply, trace = data
        turn_s = time.perf_counter() - t0
        reply_ms = round(1000 * turn_s)
        yield "reply", {"text": reply, "t_ms": reply_ms}
        cards, handoff = _cards(trace)
        for card in cards:
            yield "confirm_card", card
        if handoff:
            yield "handoff", handoff
        model_s = sum(m["latency_s"] for m in trace["model_calls"])
        final = trace["model_calls"][-1]["latency_s"] if trace["model_calls"] and not trace["format_errors"] else None
        done = {"trace_id": trace_id, "turn_s": round(turn_s, 3), "model_s": round(model_s, 3),
                "model_calls": len(trace["model_calls"]), "tools": [t["name"] for t in trace["tool_calls"]],
                "escalated": trace["escalated"], "final_call_s": final, "checks_ms": trace.get("checks_ms"),
                "model_version": (c.route or production_route()).version}
        log.info(json.dumps({"event": "turn", **done}))
        yield "done", {**done, "steps": _steps(trace, reply)}
        tracing.flush()                                # after the page has its answer: not in the visitor's wait
        return


# Routes ----------------------------------------------------------------------------------------------

class Login(BaseModel):
    customer_id: int


class Message(BaseModel):
    message: str = Field(min_length=1, max_length=4000)


class Feedback(BaseModel):
    trace_id: str = Field(min_length=1, max_length=64)
    rating: Literal["up", "down"]


@app.get("/", include_in_schema=False)
def page():
    return FileResponse(UI / "index.html", headers={"Cache-Control": "no-cache"})


@app.get("/demo-customers")
def demo_list():
    """The picker: the scenario customers first, then every eval-partition customer that sign-in accepts, with
    name, city and where their latest order is. Nothing else about a customer leaves."""
    if not _DEMO_LIST:
        rows = confirmer().execute("SELECT * FROM demo_customer_list()").fetchall()
        _DEMO_LIST.extend({"customer_id": r["customer_id"], "name": r["full_name"], "city": r["city"],
                           "latest": LATEST.get(r["latest_status"] or "", "no orders yet")} for r in rows)
    allowed = demo_customers()
    everyone = [c for c in _DEMO_LIST if allowed is None or c["customer_id"] in allowed]
    by_id = {c["customer_id"]: c for c in everyone}
    featured = [{**by_id[p["customer_id"]], **p} for p in DEMO_PERSONAS if p["customer_id"] in by_id]
    return {"featured": featured, "customers": [{**c, "try": ANY_CUSTOMER_TRY} for c in everyone]}


@app.post("/demo-login")
def demo_login(body: Login, response: Response):
    allowed = demo_customers()
    if (allowed is not None and body.customer_id not in allowed) or partition_for(body.customer_id) != "eval":
        raise HTTPException(403, "not a demo account")
    if os.environ.get("DEMO_RESET") == "1":         # every visitor starts from the seeded store (db/demo.sql)
        removed = confirmer().execute("SELECT demo_reset(%s) AS n", (body.customer_id,)).fetchone()["n"]
        log.info(json.dumps({"event": "demo_reset", "returns_removed": removed}))
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


@app.post("/chat/stream")
def chat_stream(body: Message, c: Chat = Depends(current_chat)):
    """One turn as server-sent events (see turn_events). The reply is held until every check has passed."""
    def sse():
        for kind, data in turn_events(c, body.message):
            if kind is None:
                yield ": keep-alive\n\n"
            else:
                yield f"event: {kind}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
    return StreamingResponse(sse(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.post("/chat")
def chat(body: Message, response: Response, c: Chat = Depends(current_chat)):
    """The same turn as one JSON answer (the load test and scripts use it)."""
    out = {"events": []}
    for kind, data in turn_events(c, body.message):
        if kind == "error":
            raise HTTPException(502, data["text"])
        if kind == "reply":
            out["reply"] = data["text"]
        elif kind == "done":
            out.update(data)
        elif kind is not None:
            out["events"].append({"event": kind, **data})
    response.headers["Server-Timing"] = f"turn;dur={out['turn_s'] * 1000:.0f}, model;dur={out['model_s'] * 1000:.0f}"
    return out


ORDER_STATUS = {**LATEST, "placed": "placed"}


@app.get("/my-orders")
def my_orders(c: Chat = Depends(current_chat)):
    """The signed-in customer's orders, newest first, as a shop's "Your orders" page would show them, so a visitor
    can see what to ask about and check Nova's answers. Read as the confirm role under row-level security."""
    from agent.tools_v2 import as_customer
    with as_customer(confirmer(), c.customer_id) as db:
        orders = db.execute("""
            SELECT o.order_id, o.status::text AS status, o.placed_at, o.total_inr,
                   (SELECT max(s.delivered_at) FROM shipments s WHERE s.order_id = o.order_id) AS delivered_at,
                   (SELECT min(s.eta) FROM shipments s WHERE s.order_id = o.order_id AND s.delivered_at IS NULL
                      AND s.status::text NOT IN ('cancelled', 'lost')) AS eta
              FROM orders o ORDER BY o.placed_at DESC""").fetchall()
        items = db.execute("""
            SELECT i.order_id, p.name, i.qty FROM order_items i JOIN products p USING (product_id)
             ORDER BY i.order_id, i.line_no""").fetchall()
        returns = db.execute("SELECT order_id, status::text AS status FROM returns ORDER BY proposed_at").fetchall()
    by_order: dict = {}
    for i in items:
        by_order.setdefault(i["order_id"], []).append(i["name"] if i["qty"] == 1 else f"{i['name']} ×{i['qty']}")
    ret = {r["order_id"]: r["status"] for r in returns}
    day = lambda t: t.date().isoformat() if t else None          # noqa: E731
    return [{"order_id": o["order_id"], "status": ORDER_STATUS.get(o["status"], o["status"]),
             "placed": day(o["placed_at"]), "delivered": day(o["delivered_at"]),
             "eta": o["eta"].isoformat() if o["eta"] else None, "total_inr": float(o["total_inr"]),
             "items": by_order.get(o["order_id"], []), "return": ret.get(o["order_id"])} for o in orders]


@app.post("/feedback")
def feedback(body: Feedback, c: Chat = Depends(current_chat)):
    """Thumbs up or down for one of this conversation's turns, by its trace id. The last click counts."""
    if body.trace_id not in c.traces:
        raise HTTPException(404, "no such turn in this conversation")
    c.feedback[body.trace_id] = body.rating
    log.info(json.dumps({"event": "feedback", "trace_id": body.trace_id, "rating": body.rating,
                         "turn": c.traces[body.trace_id]}))
    tracing.feedback(body.trace_id, body.rating)
    tracing.flush()
    return {"trace_id": body.trace_id, "rating": body.rating}


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
    out["canary"] = {"share": float(os.environ.get("CANARY_SHARE", "0") or 0),
                     "model": os.environ.get("CANARY_MODEL") or None}
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
