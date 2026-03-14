from typing import List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Recommendation, Document, DocumentChunk
from app.routers.auth import get_current_user
from app.services.vector_search import search_similar_modules, search_similar_chunks
from app.services.ai_agent import call_llm, parse_llm_json

router = APIRouter(tags=["recommend"])

SYSTEM_PROMPT = """Kamu adalah Learning Advisor untuk Telkom Indonesia.
Tugasmu adalah merekomendasikan modul mikro yang paling relevan berdasarkan gap kompetensi peserta.

Urutkan rekomendasi dari modul yang paling fundamental ke yang paling advanced.
Jelaskan mengapa setiap modul relevan dengan gap yang ada.

Format output WAJIB dalam JSON array:
[
  {
    "rank": 1,
    "module_title": "judul modul mikro",
    "relevance_reason": "alasan relevansi dengan gap peserta",
    "priority": "High|Medium|Low",
    "estimated_duration_minutes": 10
  }
]"""


class RecommendRequest(BaseModel):
    participant_name: str
    gap_description: str
    top_k: int = 5


class RecommendationItem(BaseModel):
    rank: int
    module_title: str
    relevance_reason: str
    priority: str
    estimated_duration_minutes: int


@router.post("/recommend")
def recommend(
    req: RecommendRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    user_id = current_user["user_id"]

    # Find relevant micro modules via vector search
    similar_modules = search_similar_modules(req.gap_description, db, user_id, top_k=req.top_k)
    if not similar_modules:
        raise HTTPException(status_code=404, detail="No micro modules found. Please decompose a training module first.")

    modules_context = "\n".join(
        f"- {m['title']}: {m['objective']} ({m['delivery_format']}, {m['duration_minutes']} menit)"
        for m in similar_modules
    )

    # Try to get competency standards context
    std_docs = db.query(Document).filter(
        Document.user_id == user_id,
        Document.filename.ilike("%STD%Competency%"),
    ).first()

    std_context = ""
    if std_docs:
        std_chunks = search_similar_chunks(req.gap_description, db, top_k=3, document_ids=[str(std_docs.id)])
        std_context = "\n".join(c["chunk_text"] for c in std_chunks)

    user_message = (
        f"Profil Peserta: {req.participant_name}\n"
        f"Gap Kompetensi: {req.gap_description}\n\n"
        f"Modul Mikro yang Tersedia:\n{modules_context}\n"
    )
    if std_context:
        user_message += f"\nStandar Kompetensi:\n{std_context}\n"
    user_message += "\nRekomendasikan learning path yang paling relevan untuk peserta ini."

    raw = call_llm(SYSTEM_PROMPT, user_message)

    try:
        items = parse_llm_json(raw, RecommendationItem)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Failed to parse AI response: {str(e)}")

    rec = Recommendation(
        user_id=user_id,
        participant_name=req.participant_name,
        gap_input=req.gap_description,
        recommended_modules=items,
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)

    return {"recommendation_id": str(rec.id), "recommendations": items}
