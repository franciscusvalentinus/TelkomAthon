from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import DocumentChunk, MicroModule
from app.routers.auth import get_current_user
from app.services.ai_agent import call_llm, parse_llm_json
from app.services.embedder import embed_text

router = APIRouter(tags=["decompose"])

SYSTEM_PROMPT = """Kamu adalah Instructional Designer spesialis microlearning.
Tugasmu adalah memecah modul pelatihan besar menjadi modul mikro yang mandiri.

Setiap modul mikro harus:
- Berdiri sendiri (standalone), tidak bergantung pada modul lain
- Fokus pada SATU tujuan pembelajaran spesifik
- Dapat diselesaikan dalam 5-15 menit

Format output WAJIB dalam JSON array:
[
  {
    "module_number": 1,
    "title": "judul modul mikro",
    "specific_objective": "setelah menyelesaikan modul ini, peserta dapat...",
    "content_summary": "ringkasan konten dalam 2-3 kalimat",
    "delivery_format": "Video|Infographic|Quiz|Case Study|Simulation",
    "duration_minutes": 10
  }
]"""


class DecomposeRequest(BaseModel):
    document_id: str
    guide_document_id: Optional[str] = None


class MicroModuleItem(BaseModel):
    module_number: int
    title: str
    specific_objective: str
    content_summary: str
    delivery_format: str
    duration_minutes: int


@router.post("/decompose")
def decompose_module(
    req: DecomposeRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    user_id = current_user["user_id"]

    # Fetch all chunks from source document
    source_chunks = db.query(DocumentChunk).filter(
        DocumentChunk.document_id == req.document_id
    ).order_by(DocumentChunk.chunk_index).all()

    if not source_chunks:
        # Fallback: try to use raw content from documents table
        from app.db.models import Document
        doc = db.query(Document).filter(Document.id == req.document_id).first()
        if not doc or not doc.content:
            raise HTTPException(status_code=422, detail="Document not found or has no content. Please re-upload the document.")
        # Use raw content directly split into chunks
        from app.services.parser import chunk_text
        raw_chunks = chunk_text(doc.content)
        context_texts = raw_chunks[:8]
    else:
        context_texts = [c.chunk_text for c in source_chunks[:8]]

    # Optionally add microlearning guide context
    if req.guide_document_id:
        guide_chunks = db.query(DocumentChunk).filter(
            DocumentChunk.document_id == req.guide_document_id
        ).order_by(DocumentChunk.chunk_index).all()
        guide_context = "\n\n".join(c.chunk_text for c in guide_chunks[:3])
        user_message = (
            f"Panduan Microlearning:\n{guide_context}\n\n"
            f"Pecah materi di atas menjadi modul mikro yang mandiri."
        )
    else:
        user_message = "Pecah materi di atas menjadi modul mikro yang mandiri."

    raw = call_llm(SYSTEM_PROMPT, user_message, context_texts[:8])

    try:
        items = parse_llm_json(raw, MicroModuleItem)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Failed to parse AI response: {str(e)}")

    # Save micro modules with embeddings
    saved = []
    for item in items:
        emb = embed_text(f"{item['title']} {item['specific_objective']}")
        module = MicroModule(
            user_id=user_id,
            source_document_id=req.document_id,
            title=item["title"],
            objective=item["specific_objective"],
            summary=item["content_summary"],
            delivery_format=item["delivery_format"],
            duration_minutes=item["duration_minutes"],
            embedding=emb,
        )
        db.add(module)
        saved.append(item)

    db.commit()
    return {"modules": saved}
