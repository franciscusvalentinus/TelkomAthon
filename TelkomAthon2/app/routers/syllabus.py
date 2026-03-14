from typing import List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Syllabus
from app.routers.auth import get_current_user
from app.services.vector_search import search_similar_chunks
from app.services.ai_agent import call_llm, parse_llm_json

router = APIRouter(tags=["syllabus"])

SYSTEM_PROMPT = """Kamu adalah Learning Design Expert untuk Telkom Indonesia.
Tugasmu adalah membuat draft silabus pelatihan yang terstruktur dan berjenjang.
Silabus harus selaras dengan konteks bisnis Telkom dan standar kompetensi internal.

Format output WAJIB dalam JSON array dengan struktur berikut:
[
  {
    "level": "Beginner|Intermediate|Advanced|Mastery",
    "topic": "nama topik utama",
    "subtopics": ["subtopik 1", "subtopik 2"],
    "learning_objectives": ["peserta mampu...", "peserta dapat..."],
    "delivery_method": "Video|Workshop|Hands-on|Self-paced|Blended",
    "duration_hours": 2
  }
]
Hasilkan untuk SEMUA level dari Beginner hingga Mastery dengan kedalaman yang berbeda."""


class SyllabusRequest(BaseModel):
    topic: str
    level: str
    document_ids: List[str] = []


class SyllabusItem(BaseModel):
    level: str
    topic: str
    subtopics: List[str]
    learning_objectives: List[str]
    delivery_method: str
    duration_hours: float


@router.post("/syllabus/generate")
def generate_syllabus(
    req: SyllabusRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    user_id = current_user["user_id"]

    # RAG: retrieve relevant context
    chunks = search_similar_chunks(req.topic, db, top_k=6, document_ids=req.document_ids or None)
    context_texts = [c["chunk_text"] for c in chunks]

    user_message = (
        f"Topik Pelatihan: {req.topic}\n"
        f"Target Level: {req.level}\n\n"
        f"Buatkan draft silabus berjenjang untuk topik ini."
    )

    raw = call_llm(SYSTEM_PROMPT, user_message, context_texts)

    try:
        items = parse_llm_json(raw, SyllabusItem)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Failed to parse AI response: {str(e)}")

    syllabus = Syllabus(user_id=user_id, topic=req.topic, level=req.level, output_json=items)
    db.add(syllabus)
    db.commit()
    db.refresh(syllabus)

    return {"syllabus_id": str(syllabus.id), "result": items}
