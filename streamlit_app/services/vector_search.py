from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
try:
    from streamlit_app.services.embedder import embed_text
except ImportError:
    from embedder import embed_text  # type: ignore


def _vec_str(vector: List[float]) -> str:
    return "[" + ",".join(str(v) for v in vector) + "]"


def search_similar_chunks(
    query: str,
    db: Session,
    top_k: int = 5,
    document_ids: Optional[List[str]] = None,
) -> List[dict]:
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
