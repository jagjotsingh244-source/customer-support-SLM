"""Traces: one per chat turn, sent to Langfuse with every step nested inside it.

The backend's second way out, next to the model server (api/model_endpoint.py). Like that one it has a fixed
destination set at deploy time: nothing a customer or the model writes can choose where data goes. The tools and
the loop never import this module; the backend hands the loop a span opener (agent/loop.py `spans`).

    LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY   the project's keys; without both, tracing is off and nothing leaves
    LANGFUSE_HOST                              e.g. https://us.cloud.langfuse.com
    MODEL_VERSION                              what serves MODEL_NAME, for the adapter tag (default sft2a-v1-fp8);
                                               a canary conversation is tagged with CANARY_VERSION instead, and
                                               the trace's version says which model answered (api/app.py)

What is sent, per turn (the trace's id is the turn's trace id, which /feedback takes):

    turn               the customer's message and Nova's reply, the events the page was sent
      input_check      flags on the message
      model_call ×n    sizes, tokens in and out, what the model asked for; never the prompt or the conversation
      tool:<name> ×n   arguments, a compact result (top-level fields, lists counted), errors
        retrieval      the help-center query, section ids and scores, whether the cutoff kept any
      rule:<name>      a hand-off or tracking check the rules made on their own
      reply_checks     output-filter hits and grounding issues

Tags: adapter:<MODEL_VERSION>, prompt:<version>, kb:<index version>, now:<mode>. Scores, for filtering and comparing
versions (and a dashboard, once there is traffic): escalated, tool_errors, grounding_issues, filter_hits, input_flags on every turn, thumbs when a visitor clicks.

Everything passes through agent.privacy.redact_obj before it leaves (the SDK's mask hook): phone numbers masked,
card numbers and email addresses replaced. The customer's name is never sent; the customer is "customer-<id>".
"""

import hashlib
import os
from contextlib import contextmanager
from functools import cache

MODEL_VERSION = os.environ.get("MODEL_VERSION", "sft2a-v1-fp8")


class _NoStep:
    def update(self, **_):
        return self


@contextmanager
def _no_span(*_args, **_kw):
    yield _NoStep()


def _mask(*, data, **_):
    from agent.privacy import redact_obj
    return redact_obj(data)


@cache
def client():
    """The Langfuse client, or None when the keys are not set (tests, evals, local runs without them)."""
    if not (os.environ.get("LANGFUSE_PUBLIC_KEY") and os.environ.get("LANGFUSE_SECRET_KEY")):
        return None
    from langfuse import Langfuse
    return Langfuse(public_key=os.environ["LANGFUSE_PUBLIC_KEY"], secret_key=os.environ["LANGFUSE_SECRET_KEY"],
                    host=os.environ.get("LANGFUSE_HOST", "https://us.cloud.langfuse.com"),
                    environment=os.environ.get("LANGFUSE_ENVIRONMENT", "demo"), release=MODEL_VERSION, mask=_mask)


def enabled() -> bool:
    return client() is not None


def kb_version(reader_conn) -> str:
    """A short fingerprint of the help-center index: embedding model plus every chunk id and policy version, so a
    reindex that changes anything changes the tag."""
    rows = reader_conn.execute("""SELECT embedding_model, chunk_id, policy_version FROM kb_chunks
                                  ORDER BY chunk_id""").fetchall()
    rows = [tuple(r.values()) if isinstance(r, dict) else tuple(r) for r in rows]
    digest = hashlib.sha256("\n".join("|".join(map(str, r)) for r in rows).encode()).hexdigest()[:8]
    return f"{len(rows)}-{digest}"


@contextmanager
def turn(trace_id: str, *, customer_id: int, conversation_id: str, message: str, tags: list[str],
         version: str = MODEL_VERSION):
    """One trace for one turn. Yields (root, spans): root.update(output=...) at the end, spans(name, **kw) to open
    a nested step (handed to the loop)."""
    lf = client()
    if lf is None:
        yield _NoStep(), None
        return
    from langfuse import propagate_attributes

    def spans(name, **kw):
        return lf.start_as_current_observation(name=name, **kw)

    with lf.start_as_current_observation(trace_context={"trace_id": trace_id}, name="turn", as_type="agent",
                                         input={"message": message}) as root, \
            propagate_attributes(user_id=f"customer-{customer_id}", session_id=conversation_id, tags=tags,
                                 trace_name="turn", version=version):
        yield root, spans


def turn_scores(trace_id: str, trace: dict) -> dict:
    """The per-turn numbers a canary comparison reads, from the loop's own trace."""
    return {
        "escalated": 1 if trace["escalated"] else 0,
        "tool_errors": sum(1 for t in trace["tool_calls"] if not t["ok"]),
        "grounding_issues": len(trace.get("grounding") or []),
        "filter_hits": len((trace.get("output_guard") or {}).get("hits") or []),
        "input_flags": len(trace.get("input_flags") or []),
    }


def score_turn(trace_id: str, scores: dict) -> None:
    lf = client()
    if lf is None:
        return
    for name, value in scores.items():
        lf.create_score(name=name, value=value, trace_id=trace_id, score_id=f"{trace_id}-{name}",
                        data_type="BOOLEAN" if name == "escalated" else "NUMERIC")


def feedback(trace_id: str, rating: str) -> None:
    """Thumbs on a turn. The score id is fixed per trace, so a changed mind replaces the earlier click."""
    lf = client()
    if lf is None:
        return
    lf.create_score(name="thumbs", value=1 if rating == "up" else 0, data_type="BOOLEAN", trace_id=trace_id,
                    score_id=f"{trace_id}-thumbs")


def flush() -> None:
    """Send what is queued now: Cloud Run gives the container CPU only while a request is open."""
    lf = client()
    if lf is not None:
        lf.flush()
