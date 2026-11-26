"""The backend's sign-in, session and health routes (api/app.py), on the local store. The model is not called:
/chat's agent loop is covered by the evals; here, who may chat and what the routes report."""

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("DB_POOL", "2")
os.environ["MODEL_BASE_URL"] = "http://127.0.0.1:9/v1"       # nothing listens there: the model is "asleep"
os.environ["COOKIE_SECURE"] = "0"
pytest.importorskip("fastapi")

from config import partition_for  # noqa: E402

try:
    from fastapi.testclient import TestClient

    from api import app as backend
    backend.pool()
except Exception as e:  # pragma: no cover - no local database
    pytest.skip(f"database or roles not available: {e}", allow_module_level=True)

EVAL = next(c for c in range(1, 501) if partition_for(c) == "eval")
TRAIN = next(c for c in range(1, 501) if partition_for(c) == "train")


@pytest.fixture
def client():
    return TestClient(backend.app)                  # no lifespan: the embedding model is not loaded


def test_only_eval_partition_customers_can_sign_in(client):
    assert client.post("/demo-login", json={"customer_id": TRAIN}).status_code == 403
    r = client.post("/demo-login", json={"customer_id": EVAL})
    assert r.status_code == 200 and r.json()["customer_id"] == EVAL and "nova_session" in client.cookies


def test_demo_customers_list_narrows_sign_in(client, monkeypatch):
    other = next(c for c in range(EVAL + 1, 501) if partition_for(c) == "eval")
    monkeypatch.setenv("DEMO_CUSTOMERS", str(EVAL))
    assert client.post("/demo-login", json={"customer_id": other}).status_code == 403
    assert client.post("/demo-login", json={"customer_id": EVAL}).status_code == 200


def test_chat_needs_a_session(client):
    assert client.post("/chat", json={"message": "hi"}).status_code == 401
    client.cookies.set("nova_session", "made-up")
    assert client.post("/chat", json={"message": "hi"}).status_code == 401


def test_confirm_takes_the_customer_from_the_session(client):
    client.post("/demo-login", json={"customer_id": EVAL})
    sid = client.cookies["nova_session"]
    assert backend.signed_in_customer(x_customer_id=TRAIN, nova_session=sid) == EVAL   # the header cannot override


def test_health_reports_database_and_a_sleeping_model(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["database"] == "ok" and r.json()["model"] != "ready"


def test_a_connection_the_database_dropped_is_replaced(client):
    """A managed database that scales to zero closes idle connections; the next turn must not fail on them."""
    pairs = [backend.pool().get() for _ in range(backend.pool().qsize())]
    for conns, _ in pairs:
        for c in conns:
            c.close()
    for conns, _ in pairs:
        backend.pool().put((conns, 0.0))             # idle "forever": checked before use
    assert client.post("/demo-login", json={"customer_id": EVAL}).status_code == 200
    backend._CONFIRMER["conn"].close()
    assert client.get("/health").json()["database"] == "ok"
