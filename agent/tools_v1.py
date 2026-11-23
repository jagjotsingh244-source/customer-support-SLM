"""Nova's tools with real help-center retrieval.

The order tools are the first versions (agent/tools_v0.py), unchanged.
search_help_center now runs vector search over kb_chunks (rag/search.py, model
choice in evals/reports/02a_rag.md) and returns compact, labelled results the
model can cite as [kb:<id>]. Results scoring below MIN_SCORE are dropped; when
none is left the tool says so instead of handing over the nearest unrelated text.

Needs the `rag` dependency group (sentence-transformers) and kb_chunks embedded
with the default model: uv run --group rag python rag/index.py --model BAAI/bge-small-en-v1.5
"""

import sys
from functools import cache
from pathlib import Path

import psycopg
from pgvector.psycopg import register_vector

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from agent import tools_v0 as v0  # noqa: E402
from agent.tools_v0 import Session  # noqa: E402,F401  (re-exported: callers import it from here)
from rag import search  # noqa: E402
from rag.embeddings import Embedder  # noqa: E402

TOOLS_VERSION = "v1"
TOP_K = 3
# Chosen with evals/retrieval_threshold.py: at 0.68 every answerable query the
# models wrote keeps its recall@3 (0.95) and all 12 unanswerable ones return
# nothing; chunks scoring 0.65-0.70 answered the question 29% of the time. The
# margin is thin (the highest unanswerable query scored 0.668): recheck it
# whenever the help center, the embedding model or the query style changes.
MIN_SCORE = 0.68
CITE_NOTE = "Cite results as [kb:<id>]. If none answer the question, say so."
NO_MATCH = "No help-center page matches. Offer to connect a teammate."


@cache
def _embedder() -> Embedder:
    return Embedder()


def connect(url: str) -> psycopg.Connection:
    """The first tools' read-only connection, plus pgvector types and a check of the index's model."""
    conn = v0.connect(url)
    register_vector(conn)
    _embedder().check_index(conn)
    return conn


def search_help_center(session: Session, query: str) -> dict:
    """Up to 3 help-center sections at or above MIN_SCORE, best first."""
    if not isinstance(query, str) or not query.strip():
        return {"error": "empty_query"}
    hits = [h for h in search.vector(session.conn, _embedder().query(query), TOP_K) if h["score"] >= MIN_SCORE]
    if not hits:
        return {"results": [], "note": NO_MATCH}
    return {"results": [{"id": h["chunk_id"], "title": h["path"], "text": h["body"],
                         "effective_date": str(h["effective_date"])} for h in hits],
            "note": CITE_NOTE}


_SEARCH = v0._fn(
    "search_help_center",
    "Search NimbusCart's help center for policy: returns, refunds, shipping, payments, warranty. "
    "Returns up to 3 sections with ids to cite, or none if nothing matches.",
    {"query": {"type": "string", "description": "What the customer wants to know, in a few words"}},
    ["query"])

TOOLS = [_SEARCH if t["function"]["name"] == "search_help_center" else t for t in v0.TOOLS]
REGISTRY = {**v0.REGISTRY, "search_help_center": search_help_center}
assert set(REGISTRY) == {t["function"]["name"] for t in TOOLS}
