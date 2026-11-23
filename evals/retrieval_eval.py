"""Score retrieval on its own, before any answer is generated.

    uv run --group rag python rag/index.py --model BAAI/bge-small-en-v1.5
    uv run --group rag python evals/retrieval_eval.py --model BAAI/bge-small-en-v1.5
    uv run --group rag python evals/retrieval_eval.py --model ... --prefix   # with the model card's query prefix
    uv run python evals/retrieval_eval.py --check-labels   # every label is a real chunk ID (no model needed)
    uv run --group rag python evals/retrieval_eval.py --model ... --misses hybrid_any

Reads evals/retrieval/questions.jsonl (or --file: model_queries.jsonl holds
the search queries the models wrote in the baseline runs; hinglish_probe.jsonl
is unscored). Each question has one or more answer
groups: a group lists every chunk that answers that part of the question, and
any one of them counts. Most questions have one group; a two-part question has
two, and needs a chunk from each.

- recall@3: share of questions with every answer group represented in the top
  3. Nova reads the top 3, so this is the number that decides.
- MRR: mean of 1 / rank of the first answering chunk in the top 10 (0 if none).

Methods (rag/search.py): vector; full-text needing all words or any word; and
hybrid (RRF) of vector with each full-text variant. kb_chunks must already be
embedded with --model. Writes per-question rankings to evals/retrieval/runs/.
"""

import argparse
import json
import statistics
import sys
import time
from pathlib import Path

import psycopg
from pgvector.psycopg import register_vector

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from db.seed import DB_URL  # noqa: E402
from rag import search  # noqa: E402
from rag.embeddings import Embedder  # noqa: E402

K, DEPTH = 3, 10
METHODS = {
    "vector": lambda c, q, qv: search.vector(c, qv, DEPTH),
    "fulltext_all": lambda c, q, qv: search.fulltext(c, q, DEPTH, all_words=True),
    "fulltext_any": lambda c, q, qv: search.fulltext(c, q, DEPTH, all_words=False),
    "hybrid_all": lambda c, q, qv: search.hybrid(c, q, qv, DEPTH, all_words=True),
    "hybrid_any": lambda c, q, qv: search.hybrid(c, q, qv, DEPTH, all_words=False),
}


def covered(groups: list[list[str]], ids: list[str]) -> bool:
    return all(any(c in ids for c in g) for g in groups)


def first_rank(groups: list[list[str]], ids: list[str]) -> int | None:
    relevant = {c for g in groups for c in g}
    return next((i for i, c in enumerate(ids, 1) if c in relevant), None)


def check_labels() -> None:
    """Every answer chunk in every retrieval file is a current chunk ID."""
    ids = set((ROOT / "rag" / "chunk_ids.txt").read_text().split())
    bad, n = [], 0
    for f in sorted((ROOT / "evals" / "retrieval").glob("*.jsonl")):
        for line in open(f):
            q = json.loads(line)
            n += 1
            bad += [f"{f.name} {q['id']}: {c}" for g in q["answers"] for c in g if c not in ids]
    if bad:
        sys.exit("retrieval labels name chunks that do not exist:\n" + "\n".join(bad))
    print(f"{n} retrieval questions, every label is a current chunk id")


def segment(source: str) -> str:
    return source.split(":")[0]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model")
    ap.add_argument("--prefix", action="store_true")
    ap.add_argument("--check-labels", action="store_true")
    ap.add_argument("--file", default=str(ROOT / "evals" / "retrieval" / "questions.jsonl"))
    ap.add_argument("--misses", metavar="METHOD", help="print every question this method misses at k=3")
    args = ap.parse_args()
    if args.check_labels:
        return check_labels()
    if not args.model:
        ap.error("--model is required")

    emb = Embedder(args.model, use_prefix=args.prefix)
    questions = [json.loads(line) for line in open(args.file)]
    conn = psycopg.connect(DB_URL, autocommit=True)
    register_vector(conn)
    emb.check_index(conn)

    emb.query("warm up")
    per_q, times = [], []
    for qn in questions:
        start = time.perf_counter()
        qv = emb.query(qn["question"])
        times.append((time.perf_counter() - start) * 1000)
        res = {name: fn(conn, qn["question"], qv) for name, fn in METHODS.items()}
        per_q.append({**qn, "results": res})

    def score(rows, name):
        hits = [covered(r["answers"], [x["chunk_id"] for x in r["results"][name][:K]]) for r in rows]
        ranks = [first_rank(r["answers"], [x["chunk_id"] for x in r["results"][name]]) for r in rows]
        return sum(hits) / len(rows), sum(1 / r for r in ranks if r) / len(rows)

    segments = sorted({segment(r["source"]) for r in per_q})
    label = args.model + (" (with query prefix)" if args.prefix else "")
    print(f"\n{label}: {len(per_q)} questions from {Path(args.file).name}; "
          f"query embedding median {statistics.median(times):.1f} ms on CPU\n")
    print(f"| method | recall@{K} | MRR | " + " | ".join(f"recall@{K} {s}" for s in segments) + " |")
    print("|---|---|---|" + "---|" * len(segments))
    summary = {}
    for name in METHODS:
        rec, mrr = score(per_q, name)
        segs = {s: score([r for r in per_q if segment(r["source"]) == s], name)[0] for s in segments}
        summary[name] = {"recall@3": rec, "mrr": mrr, "by_segment": segs}
        print(f"| {name} | {rec:.2f} | {mrr:.2f} | " + " | ".join(f"{segs[s]:.2f}" for s in segments) + " |")

    out_dir = ROOT / "evals" / "retrieval" / "runs"
    out_dir.mkdir(parents=True, exist_ok=True)
    slug = args.model.split("/")[-1] + ("-prefix" if args.prefix else "") + "-" + Path(args.file).stem
    (out_dir / f"{slug}.json").write_text(json.dumps(
        {"model": args.model, "query_prefix": args.prefix, "file": Path(args.file).name,
         "query_ms_median": statistics.median(times), "summary": summary, "questions": per_q},
        indent=1, ensure_ascii=False))
    print(f"\nrankings: {(out_dir / f'{slug}.json').relative_to(ROOT)}")

    if args.misses:
        print(f"\nmisses at k={K} for {args.misses}:")
        for r in per_q:
            got = r["results"][args.misses]
            if not covered(r["answers"], [x["chunk_id"] for x in got[:K]]):
                rank = first_rank(r["answers"], [x["chunk_id"] for x in got])
                print(f"\n{r['id']} [{r['source']}] {r['question']}")
                print(f"  wanted: {r['answers']}")
                print(f"  first answering rank in top {DEPTH}: {rank}")
                for x in got[:K]:
                    print(f"  got: {x['chunk_id']} ({x['score']:.3f})")


if __name__ == "__main__":
    main()
