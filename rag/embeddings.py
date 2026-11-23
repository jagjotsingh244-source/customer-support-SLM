"""Embedding models for the help center, with each model's query convention.

Chunks and queries must be embedded by the same model with the same settings;
kb_chunks.embedding_model records which one wrote the vectors, and Embedder
refuses to query vectors written by another model.

Needs the `rag` dependency group: uv run --group rag ...
"""

from dataclasses import dataclass
from functools import cache

import numpy as np
from psycopg.rows import tuple_row

# Query prefixes from the model cards, used only with use_prefix=True. bge models were trained with an
# instruction in front of short retrieval queries and none in front of passages;
# MiniLM uses no prefix at all.
MODELS = {
    "BAAI/bge-small-en-v1.5": "Represent this sentence for searching relevant passages: ",
    "BAAI/bge-base-en-v1.5": "Represent this sentence for searching relevant passages: ",
    "sentence-transformers/all-MiniLM-L6-v2": "",
}
DEFAULT_MODEL = "BAAI/bge-small-en-v1.5"


@cache
def _load(name: str):
    from sentence_transformers import SentenceTransformer  # heavy import (torch): only when embedding
    return SentenceTransformer(name, device="cpu")


@dataclass(frozen=True)
class Embedder:
    name: str = DEFAULT_MODEL
    # Off by default: on the retrieval sets, bge-small scored the same without
    # the prefix on customer messages and one query better on model-written
    # queries (evals/reports/02a_rag.md); its card calls the prefix optional.
    use_prefix: bool = False

    def __post_init__(self):
        if self.name not in MODELS:
            raise ValueError(f"unknown embedding model {self.name}; known: {sorted(MODELS)}")

    def passages(self, texts: list[str]) -> np.ndarray:
        return _load(self.name).encode(texts, normalize_embeddings=True, batch_size=32)

    def query(self, text: str) -> np.ndarray:
        prefix = MODELS[self.name] if self.use_prefix else ""
        return _load(self.name).encode(prefix + text, normalize_embeddings=True)

    def check_index(self, conn) -> None:
        """Fail loudly if kb_chunks holds vectors from a different model, or none."""
        models = {r[0] for r in conn.cursor(row_factory=tuple_row).execute(
            "SELECT DISTINCT embedding_model FROM kb_chunks").fetchall()}
        if models != {self.name}:
            raise RuntimeError(f"kb_chunks is embedded with {sorted(map(str, models))}, not {self.name}; "
                               f"run: uv run --group rag python rag/index.py --model {self.name}")
