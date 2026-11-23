"""Three ways to search kb_chunks, each returning [{chunk_id, score}], best first.

- vector:   cosine similarity between the query embedding and each chunk's.
            Finds paraphrases ("money back" -> refund); weak on exact tokens.
- fulltext: Postgres full-text search. `all_words=True` needs every word of the
            question to match (websearch_to_tsquery, like the first rough
            tool); `all_words=False` ranks chunks matching any of its words.
- hybrid:   both lists merged with reciprocal rank fusion: each chunk scores
            1 / (RRF_K + rank) in each list, summed. Ranks are merged, never raw
            scores, because cosine similarity and ts_rank are not on one scale.

The connection needs pgvector's types registered (pgvector.psycopg.register_vector).
Rows are read as tuples whatever the connection's row factory, so the agent's
dict-row connection works too.
"""

from psycopg.rows import tuple_row

RRF_K = 60       # from the original RRF paper (Cormack, Clarke and Büttcher, 2009)
CANDIDATES = 20  # how deep each list goes before fusion

# The question as a tsquery. "Any word" is built in SQL from to_tsvector, so
# stop words are dropped and words are stemmed exactly as the chunks were; each
# lexeme is quoted, so no character in a question can break the query syntax.
# A question of only stop words gives NULL, which matches nothing.
_ALL_WORDS = "websearch_to_tsquery('english', %(q)s)"
_ANY_WORD = ("(SELECT string_agg(quote_literal(l), ' | ')::tsquery "
             "FROM unnest(tsvector_to_array(to_tsvector('english', %(q)s))) l)")


def _tsquery(all_words: bool) -> str:
    """A FROM item with one row and one column, tq."""
    return f"(SELECT {_ALL_WORDS if all_words else _ANY_WORD} AS tq) query"


def _rows(conn, sql: str, params: dict) -> list[tuple]:
    return conn.cursor(row_factory=tuple_row).execute(sql, params).fetchall()


def vector(conn, qv, k: int = 3) -> list[dict]:
    """Nearest chunks with their text, for the tool to hand to the model."""
    rows = _rows(conn, """
        SELECT chunk_id, 1 - (embedding <=> %(qv)s) AS score, path, body, effective_date
        FROM kb_chunks ORDER BY embedding <=> %(qv)s, chunk_id LIMIT %(k)s""",
        {"qv": qv, "k": k})
    return [{"chunk_id": r[0], "score": float(r[1]), "path": r[2], "body": r[3], "effective_date": r[4]}
            for r in rows]


def fulltext(conn, q: str, k: int = 3, all_words: bool = False) -> list[dict]:
    rows = _rows(conn, f"""
        SELECT chunk_id, ts_rank(tsv, tq) AS score
        FROM kb_chunks, {_tsquery(all_words)}
        WHERE tsv @@ tq ORDER BY score DESC, chunk_id LIMIT %(k)s""",
        {"q": q, "k": k})
    return [{"chunk_id": r[0], "score": float(r[1])} for r in rows]


def hybrid(conn, q: str, qv, k: int = 3, all_words: bool = False) -> list[dict]:
    rows = _rows(conn, f"""
        WITH vec AS (
          SELECT chunk_id, row_number() OVER (ORDER BY embedding <=> %(qv)s, chunk_id) AS r
          FROM kb_chunks ORDER BY embedding <=> %(qv)s, chunk_id LIMIT %(n)s),
        fts AS (
          SELECT chunk_id, row_number() OVER (ORDER BY ts_rank(tsv, tq) DESC, chunk_id) AS r
          FROM kb_chunks, {_tsquery(all_words)}
          WHERE tsv @@ tq ORDER BY r LIMIT %(n)s)
        SELECT chunk_id, sum(1.0 / (%(rrf)s + r)) AS score
        FROM (SELECT * FROM vec UNION ALL SELECT * FROM fts) both_lists
        GROUP BY chunk_id ORDER BY score DESC, chunk_id LIMIT %(k)s""",
        {"q": q, "qv": qv, "k": k, "n": CANDIDATES, "rrf": RRF_K})
    return [{"chunk_id": r[0], "score": float(r[1])} for r in rows]
