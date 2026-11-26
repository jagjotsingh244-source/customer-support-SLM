"""Traces (api/tracing.py): one chat turn is one trace with nested steps, tagged, scored, and redacted before it
leaves. The Langfuse SDK runs for real but exports to memory, and its host points at a closed port, so nothing
is sent anywhere. The model is a scripted stand-in; tools, guards and the local store are real."""

import json
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("DB_POOL", "2")
os.environ["MODEL_BASE_URL"] = "http://127.0.0.1:9/v1"
os.environ["COOKIE_SECURE"] = "0"
pytest.importorskip("langfuse")

try:
    import psycopg
    from fastapi.testclient import TestClient
    from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

    from agent.tools_v2 import clear_agent_writes
    from api import app as backend
    from api import tracing
    backend.pool()
    from tests.test_api_stream import Scripted, completion, events, sign_in
except Exception as e:  # pragma: no cover - no local database
    pytest.skip(f"database or roles not available: {e}", allow_module_level=True)


@pytest.fixture
def traced(monkeypatch):
    """A real Langfuse client that exports spans to memory and records scores instead of sending them."""
    from langfuse import Langfuse
    exporter, scores = InMemorySpanExporter(), []
    import uuid                                          # the SDK keeps one client per key: a fresh key each test
    lf = Langfuse(public_key=f"pk-lf-test-{uuid.uuid4().hex}", secret_key="sk-lf-test", host="http://127.0.0.1:9",
                  span_exporter=exporter, mask=tracing._mask, flush_at=1)
    monkeypatch.setattr(lf, "create_score", lambda **kw: scores.append(kw))
    monkeypatch.setattr(tracing, "client", lambda: lf)
    yield exporter, scores, lf
    lf.flush()


@pytest.fixture
def client():
    yield TestClient(backend.app)
    with psycopg.connect(backend.DB_URL) as owner:
        clear_agent_writes(owner)


def model(monkeypatch, *steps):
    fake = Scripted(*steps)
    monkeypatch.setattr(backend.model_endpoint, "client", lambda base_url=None: fake)
    monkeypatch.setattr(backend.model_endpoint, "ready", lambda timeout, base_url=None: (True, "ready"))
    monkeypatch.setattr(backend, "_MODEL", {backend.model_endpoint.MODEL_BASE_URL: 1e18})


def spans_of(exporter, lf):
    lf.flush()
    return {s.name: s for s in exporter.get_finished_spans()}


def text_of(span) -> str:
    return json.dumps({k: str(v) for k, v in span.attributes.items()})


def test_one_turn_is_one_trace_with_nested_steps(client, traced, monkeypatch):
    exporter, scores, lf = traced
    sign_in(client, 57)
    model(monkeypatch, completion(call=("search_help_center", {"query": "how long do refunds take"})),
          completion("Refunds take 5 to 7 working days."))
    evs, _ = events(client, "How long do refunds take? Call me on 9876543210")
    trace_id = dict(evs)["done"]["trace_id"]
    spans = spans_of(exporter, lf)
    assert {"turn", "input_check", "model_call", "tool:search_help_center", "retrieval", "reply_checks"} <= set(spans)
    assert {format(s.context.trace_id, "032x") for s in spans.values()} == {trace_id}      # one trace
    turn, tool, retrieval = spans["turn"], spans["tool:search_help_center"], spans["retrieval"]
    assert tool.parent.span_id == turn.context.span_id                                     # nested in the turn
    assert retrieval.parent.span_id == tool.context.span_id                                # nested in its tool
    assert "chunks" in text_of(retrieval) and "min_score" in text_of(retrieval)
    tags = text_of(turn)
    assert "adapter:" in tags and "prompt:v3" in tags and "kb:" in tags and "now:frozen" in tags
    assert {s["name"] for s in scores} == {"escalated", "tool_errors", "grounding_issues", "filter_hits",
                                           "input_flags"}
    assert all(s["trace_id"] == trace_id for s in scores)


def test_nothing_personal_leaves_in_a_trace(client, traced, monkeypatch):
    exporter, _, lf = traced
    sign_in(client, 57)
    name = backend.SESSIONS[client.cookies["nova_session"]].customer_name
    model(monkeypatch, completion(call=("list_my_orders", {})), completion("Your order is on its way."))
    events(client, "Where is my order? My number is 9876543210 and email me at someone@example.com")
    sent = " ".join(text_of(s) for s in spans_of(exporter, lf).values())
    assert len(sent) > 200                                                            # something was captured
    assert "9876543210" not in sent and "someone@example.com" not in sent            # masked before export
    assert name not in sent                                                           # the prompt is never sent
    assert "customer-57" in sent


def test_thumbs_become_a_score_on_the_trace(client, traced, monkeypatch):
    _, scores, _ = traced
    sign_in(client, 57)
    model(monkeypatch, completion("Hello! How can I help?"))
    trace_id = dict(events(client, "hi")[0])["done"]["trace_id"]
    client.post("/feedback", json={"trace_id": trace_id, "rating": "down"})
    thumbs = [s for s in scores if s["name"] == "thumbs"]
    assert thumbs == [{"name": "thumbs", "value": 0, "data_type": "BOOLEAN", "trace_id": trace_id,
                       "score_id": f"{trace_id}-thumbs"}]


def test_without_keys_nothing_is_traced(client, monkeypatch):
    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    tracing.client.cache_clear()
    assert tracing.enabled() is False
    sign_in(client, 57)
    model(monkeypatch, completion("Hello!"))
    assert dict(events(client, "hi")[0])["done"]["trace_id"]
