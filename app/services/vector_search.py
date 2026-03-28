from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.services.embedder import embed_text


def _vec_str(vector: List[float]) -> str:
    """Format embedding list as pgvector literal string."""
    return "[" + ",".join(str(v) for v in vector) + "]"


def search_similar_chunks(
    query: str,
    db: Session,
    top_k: int = 5,
    document_ids: Optional[List[str]] = None,
) -> List[dict]:
    """
    Embed query and find top_k most similar document chunks via pgvector cosine similarity.
    Vector is inlined into SQL to avoid psycopg binding issues with ::vector cast.
    """
    vec = _vec_str(embed_text(query))

    if document_ids:
        uuid_list = ", ".join(f"'{uid}'" for uid in document_ids)
        sql = text(f"""
            SELECT chunk_text, document_id::text,
                   1 - (embedding <=> '{vec}'::vector) AS similarity
            FROM document_chunks
            WHERE document_id::text IN ({uuid_list})
            ORDER BY embedding <=> '{vec}'::vector
            LIMIT :top_k
        """)
    else:
        sql = text(f"""
            SELECT chunk_text, document_id::text,
                   1 - (embedding <=> '{vec}'::vector) AS similarity
            FROM document_chunks
            ORDER BY embedding <=> '{vec}'::vector
            LIMIT :top_k
        """)

    rows = db.execute(sql, {"top_k": top_k}).fetchall()
    return [{"chunk_text": r[0], "document_id": r[1], "similarity": r[2]} for r in rows]


def search_similar_modules(
    query: str,
    db: Session,
    user_id: str,
    top_k: int = 5,
) -> List[dict]:
    """Find top_k micro_modules most similar to query, scoped to user_id."""
    vec = _vec_str(embed_text(query))

    sql = text(f"""
        SELECT id::text, title, objective, summary, delivery_format, duration_minutes,
               1 - (embedding <=> '{vec}'::vector) AS similarity
        FROM micro_modules
        WHERE user_id = :user_id
        ORDER BY embedding <=> '{vec}'::vector
        LIMIT :top_k
    """)
    rows = db.execute(sql, {"user_id": user_id, "top_k": top_k}).fetchall()

    return [
        {
            "id": r[0], "title": r[1], "objective": r[2],
            "summary": r[3], "delivery_format": r[4],
            "duration_minutes": r[5], "similarity": r[6],
        }
        for r in rows
    ]
