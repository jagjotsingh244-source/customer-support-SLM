"""Malformed tool calls get one plain, helpful error, and never reach the database.

The first part needs no database: the session records any attempt to run SQL, and every malformed call
must leave it untouched. The second part sweeps every tool over the eval customers' real orders and checks
that no result holds an empty list, a null or a raw exception.

    uv run --group dev pytest tests/test_tool_errors.py
"""

import json
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from agent import tools_v2 as t  # noqa: E402
from agent.loop import run_turn  # noqa: E402


class NoSQL:
    """A session that fails the test if a tool gets as far as the database."""
    customer_id, customer_name = 416, "Pranav Sood"

    def __init__(self):
        self.touched = False

    def _db(self, *_, **__):
        self.touched = True
        raise AssertionError("SQL was reached")

    read = write = all = _db


# 15 malformed calls: (tool, raw arguments, words the detail must contain)
MALFORMED = [
    ("get_tracking", '{"order_id": "#10482"}', ["5 digits", "list_my_orders"]),           # a habit to train away
    ("get_tracking", '{"order_id": 10482.0}', ["5 digits"]),                              # no silent coercion
    ("get_order_status", '{"order_id": "ten four eight two"}', ["5 digits"]),
    ("get_order_status", '{"order_id": "10482"}', ["5 digits"]),                          # digits as text: still refused
    ("get_tracking", '{"order_id": 999}', ["5 digits"]),
    ("get_tracking", "{}", ["order_id is required", "5 digits"]),
    ("list_my_orders", '{"limit": 5, "customer_id": 1088}', ["not an argument", "signed-in account"]),
    ("get_order_status", '{"order_id": 10482, "include_all": true}', ["include_all is not an argument"]),
    ("cancel_order", '{"order_id": 10482}', ["no tool cancel_order", "get_order_status"]),
    ("get_tracking", "order_id=10482", ["JSON object", '{"order_id": 10482}']),
    ("get_tracking", "[10482]", ["JSON object"]),
    ("list_my_orders", '{"limit": -1}', ["1 to 10"]),
    ("propose_return", '{"order_id": 11360, "line_no": 1, "reason": "broken"}', ["faulty", "changed_mind"]),
    ("propose_return", '{"order_id": 11360, "reason": "faulty"}', ["line_no is required"]),
    ("escalate_to_human", '{"reason": "angry_customer", "summary": "Customer wants a manager now."}',
     ["lost_parcel", "other"]),
]


@pytest.mark.parametrize("name,raw,words", MALFORMED, ids=[f"{n}:{r[:30]}" for n, r, _ in MALFORMED])
def test_malformed_call_gets_a_helpful_error_and_no_sql(name, raw, words):
    session = NoSQL()
    out = t.call_tool(name, raw, session, attempts={})
    assert not session.touched, "the call reached the database"
    assert set(out) == {"error", "detail"}, out                       # one shape for every error
    assert out["error"] in ("invalid_arguments", "unknown_tool")
    d = out["detail"]
    assert d.endswith(".") and len(d) < 220, d                        # one or two plain sentences
    for leak in ("Traceback", "pydantic", "Input should", "ValidationError", "errors.pydantic.dev"):
        assert leak not in d, d
    for w in words:
        assert w in d, (w, d)


def test_second_failure_on_the_same_tool_stops_the_retries():
    attempts, session = {}, NoSQL()
    first = t.call_tool("get_tracking", '{"order_id": "#10482"}', session, attempts)
    second = t.call_tool("get_tracking", '{"order_id": "10482 "}', session, attempts)
    assert "5 digits" in first["detail"]
    assert second == {"error": "invalid_arguments", "detail": t.GIVE_UP}
    assert "escalate_to_human" in second["detail"] and not session.touched
    other = t.call_tool("list_my_orders", '{"limit": 0}', session, attempts)  # another tool has its own count
    assert other["detail"] != t.GIVE_UP


def test_a_failing_tool_returns_no_stack_trace(monkeypatch):
    def broken(session, order_id):
        raise RuntimeError("connection to server at 10.0.0.5 failed: password authentication failed")
    monkeypatch.setitem(t.FUNCTIONS, "get_tracking", broken)
    out = t.call_tool("get_tracking", '{"order_id": 10482}', NoSQL(), attempts={})
    assert out["error"] == "tool_failed" and set(out) == {"error", "detail"}
    assert "10.0.0.5" not in out["detail"] and "password" not in out["detail"]


def test_the_loop_sends_the_error_to_the_model_and_logs_the_call(caplog):
    """End to end: a bad call, the error goes back as the tool message, the model then answers."""
    from openai.types.chat import ChatCompletion

    def completion(content=None, calls=None):
        return ChatCompletion.model_validate({
            "id": "x", "object": "chat.completion", "created": 0, "model": "m",
            "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
            "choices": [{"index": 0, "finish_reason": "tool_calls" if calls else "stop",
                         "message": {"role": "assistant", "content": content, "tool_calls": calls}}]})

    bad = {"id": "c0", "type": "function", "function": {"name": "get_tracking", "arguments": '{"order_id": "#10482"}'}}
    replies = [completion(calls=[bad]), completion("Could you send the order number without the #?")]

    class Client:
        chat = completions = None

        def create(self, **_):
            return replies.pop(0)
    client = Client()
    client.chat = client
    client.completions = client

    messages = [{"role": "user", "content": "where is #10482"}]
    with caplog.at_level("INFO", logger="nova.tools"):
        reply, trace = run_turn(client, "m", messages, [], t.DISPATCH, NoSQL(), trace_id="t-1")
    assert reply.startswith("Could you")
    tool_msg = json.loads(messages[2]["content"])
    assert tool_msg["error"] == "invalid_arguments" and "5 digits" in tool_msg["detail"]
    assert trace["tool_calls"][0]["ok"] is False
    line = json.loads(caplog.records[-1].getMessage())
    assert line == {"trace_id": "t-1", "turn": 1, "tool": "get_tracking", "args": '{"order_id": "#10482"}',
                    "ok": False, "latency_ms": line["latency_ms"], "result_bytes": line["result_bytes"]}


# With the database: no tool result has a blank in it ------------------------------------------------------

def blanks(value, path="result"):
    """Every place in a result that is an empty list or a null."""
    if value is None:
        return [path]
    if isinstance(value, list):
        return [path] if not value else [b for i, v in enumerate(value) for b in blanks(v, f"{path}[{i}]")]
    if isinstance(value, dict):
        return [b for k, v in value.items() for b in blanks(v, f"{path}.{k}")]
    return []


@pytest.fixture(scope="module")
def db():
    import psycopg
    from psycopg.rows import dict_row
    url = os.environ.get("DB_URL", "postgresql://nimbus:nimbus@localhost:5433/nimbus")
    try:
        owner = psycopg.connect(url, autocommit=True, row_factory=dict_row)
        conns = t.connect(url, search=False)
    except psycopg.OperationalError as e:
        pytest.skip(f"database or roles not available: {e}")
    t.clear_agent_writes(owner)
    yield owner, conns
    t.clear_agent_writes(owner)


def test_no_tool_result_has_a_blank(db):
    """Every order of every eval customer, through every order tool, every return reason."""
    owner, conns = db
    rows = owner.execute("""SELECT o.customer_id, o.order_id, count(i.*) AS lines FROM orders o
                            JOIN customers c USING (customer_id) JOIN order_items i USING (order_id)
                            WHERE c.partition = 'eval' GROUP BY 1, 2 ORDER BY 1, 2""").fetchall()
    found, checked = [], 0
    for cid in sorted({r["customer_id"] for r in rows}):
        s = t.Session.open(conns, cid)
        found += blanks(t.call_tool("list_my_orders", '{"limit": 10}', s, {}), f"{cid} list_my_orders")
        for r in (r for r in rows if r["customer_id"] == cid):
            oid = r["order_id"]
            for name in ("get_order_status", "get_tracking"):
                found += blanks(t.call_tool(name, json.dumps({"order_id": oid}), s, {}), f"{oid} {name}")
            for line in range(1, r["lines"] + 2):                       # one line past the end too
                for reason in ("changed_mind", "faulty"):
                    out = t.call_tool("propose_return", json.dumps({"order_id": oid, "line_no": line,
                                                                    "reason": reason}), s, {})
                    found += blanks(out, f"{oid}/{line} propose_return")
                    checked += 1
        t.clear_agent_writes(owner)
    assert checked > 1000 and not found, found[:10]


def test_empty_results_are_stated(db):
    owner, conns = db
    def order_in(scenario):
        return owner.execute("""SELECT o.customer_id, o.order_id FROM scenarios s JOIN orders o USING (order_id)
                                WHERE s.scenario = %s ORDER BY 1 LIMIT 1""", (scenario,)).fetchone()
    r = order_in("not_yet_shipped")
    out = t.call_tool("get_tracking", json.dumps({"order_id": r["order_id"]}), t.Session.open(conns, r["customer_id"]), {})
    assert out["shipped"] is False and out["note"] == "Not shipped yet, so there is no tracking number."
    r = order_in("cancelled_before_ship")
    out = t.call_tool("get_tracking", json.dumps({"order_id": r["order_id"]}), t.Session.open(conns, r["customer_id"]), {})
    assert out["note"].startswith("The order was cancelled before it shipped")
    out = t.call_tool("get_order_status", json.dumps({"order_id": r["order_id"]}), t.Session.open(conns, r["customer_id"]), {})
    assert out["returns"] == "No return has been started for this order."
    out = t.call_tool("get_tracking", '{"order_id": 12578}', t.Session.open(conns, 416), {})
    assert out == t.NOT_FOUND


def test_no_orders_and_no_search_match_are_stated(monkeypatch):
    s = NoSQL()
    monkeypatch.setattr(t.v0, "list_my_orders", lambda session, limit: [])
    assert t.call_tool("list_my_orders", "{}", s, {}) == {"note": "This account has no orders."}

    class Fake:
        def query(self, q):
            return [0.0]
    import contextlib
    monkeypatch.setattr(t, "_embedder", lambda: Fake())
    monkeypatch.setattr(s, "read", lambda: contextlib.nullcontext(None))
    rag_search = pytest.importorskip("rag.search")
    monkeypatch.setattr(rag_search, "vector", lambda conn, vec, k: [{"score": 0.2, "chunk_id": "x"}])
    assert t.call_tool("search_help_center", '{"query": "do you sell cars"}', s, {}) == {"note": t.NO_MATCH}
