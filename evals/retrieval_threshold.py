"""Choose the score cutoff below which search_help_center returns nothing.

    uv run --group rag python evals/retrieval_threshold.py

Vector search always returns the 3 nearest chunks, even for a question the help
center cannot answer. The tool drops every chunk scoring below a cutoff, and
says so when none is left. This script sweeps the cutoff over the labelled
retrieval sets (kb_chunks must be embedded with the default model):

- answerable (questions.jsonl, model_queries.jsonl): recall@3 that survives the
  cutoff, and how often a chunk at a given score answers the question;
- unanswerable (unanswerable.jsonl, unanswerable_model_queries.jsonl): how
  often nothing is left, which is the right result.

Each kind is shown for customer messages and for the queries the models wrote,
because the tool receives the second kind and their scores run differently.
"""

import json
import sys
from pathlib import Path

import psycopg
from pgvector.psycopg import register_vector

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from db.seed import DB_URL  # noqa: E402
from evals.retrieval_eval import covered  # noqa: E402
from rag import search  # noqa: E402
from rag.embeddings import Embedder  # noqa: E402

SETS = {  # name -> (file, answerable)
    "customer messages": ("questions.jsonl", True),
    "model queries": ("model_queries.jsonl", True),
    "unanswerable messages": ("unanswerable.jsonl", False),
    "unanswerable model queries": ("unanswerable_model_queries.jsonl", False),
}
CUTOFFS = [round(0.50 + 0.02 * i, 2) for i in range(21)]


def load(conn, emb) -> dict[str, list[dict]]:
    out = {}
    for name, (fname, _) in SETS.items():
        rows = [json.loads(line) for line in open(ROOT / "evals" / "retrieval" / fname)]
        for r in rows:
            r["top"] = search.vector(conn, emb.query(r["question"]), 3)
        out[name] = rows
    return out


def kept(r: dict, t: float) -> list[str]:
    return [x["chunk_id"] for x in r["top"] if x["score"] >= t]


def main() -> None:
    emb = Embedder()
    conn = psycopg.connect(DB_URL, autocommit=True)
    register_vector(conn)
    emb.check_index(conn)
    data = load(conn, emb)

    print(f"{emb.name}, vector top 3, query prefix {'on' if emb.use_prefix else 'off'}\n")
    print("How often a retrieved chunk answers the question, by its score (answerable sets, top 3):\n")
    print("| score | customer messages | model queries |")
    print("|---|---|---|")
    edges = [0.5, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 1.01]
    for lo, hi in zip(edges, edges[1:]):
        cells = []
        for name in ("customer messages", "model queries"):
            hits = [any(x["chunk_id"] in g for g in r["answers"])
                    for r in data[name] for x in r["top"] if lo <= x["score"] < hi]
            cells.append(f"{sum(hits)}/{len(hits)}" + (f" ({100 * sum(hits) / len(hits):.0f}%)" if hits else ""))
        print(f"| {lo:.2f}–{min(hi, 1):.2f} | " + " | ".join(cells) + " |")

    print("\nCutoff sweep (recall@3 after the cutoff; share of unanswerable questions left with no result):\n")
    print("| cutoff | recall@3, messages | recall@3, model queries | empty, unanswerable messages | "
          "empty, unanswerable model queries |")
    print("|---|---|---|---|---|")
    for t in CUTOFFS:
        cells = []
        for name, (_, answerable) in SETS.items():
            rows = data[name]
            ok = [covered(r["answers"], kept(r, t)) if answerable else not kept(r, t) for r in rows]
            cells.append(f"{sum(ok) / len(rows):.2f}")
        print(f"| {t:.2f} | " + " | ".join(cells) + " |")

    print("\nTop score of each unanswerable question:")
    for name in ("unanswerable messages", "unanswerable model queries"):
        for r in data[name]:
            print(f"  {r['top'][0]['score']:.3f}  {r['question']}  ->  {r['top'][0]['chunk_id']}")


if __name__ == "__main__":
    main()
