from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Recommendation, Document, DocumentChunk
from app.routers.auth import get_current_user
from app.services.vector_search import search_similar_chunks
from app.services.ai_agent import call_llm, parse_llm_json

router = APIRouter(tags=["recommend"])

SYSTEM_PROMPT = """Kamu adalah Learning Advisor yang berpengalaman.
Tugasmu adalah merekomendasikan modul mikro yang paling relevan berdasarkan profil dan gap kompetensi peserta.

Pertimbangkan semua informasi profil peserta yang tersedia (jabatan, lama bekerja, departemen,
pendidikan terakhir, preferensi belajar, waktu belajar per minggu) untuk mempersonalisasi rekomendasi.

Urutkan rekomendasi dari modul yang paling fundamental ke yang paling advanced.
Jelaskan mengapa setiap modul relevan dengan gap dan profil peserta.

Jika daftar modul tersedia, rekomendasikan dari daftar tersebut.
Jika tidak ada daftar modul, generate rekomendasi modul mikro yang relevan berdasarkan gap dan konteks silabus.

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
    syllabus_id: Optional[str] = None
    jabatan: Optional[str] = None
    lama_bekerja: Optional[str] = None
    departemen: Optional[str] = None
    pendidikan_terakhir: Optional[str] = None
    preferensi_belajar: Optional[str] = None
    waktu_belajar_per_minggu: Optional[str] = None


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

    # ── Syllabus context (optional) ───────────────────────────────────────────
    syllabus_context = ""
    syllabus_elos = []
    if req.syllabus_id:
        from app.db.models import Syllabus
        syllabus = db.query(Syllabus).filter(
            Syllabus.id == req.syllabus_id,
            Syllabus.user_id == user_id,
        ).first()
        if syllabus and syllabus.output_json:
            output = syllabus.output_json
            profile = output.get("org_profile", {})
            tlos = output.get("tlos", [])
            pos = output.get("performance_objectives", [])
            syllabus_elos = output.get("elos", [])
            levels = output.get("levels_covered", [])

            syllabus_context = (
                f"\nKonteks Silabus Pelatihan:\n"
                f"Perusahaan: {profile.get('organization_name', '-')} | "
                f"Industri: {profile.get('industry', '-')}\n"
                f"Tipe Course: {output.get('course_type', '-')}\n"
                f"Level: {' → '.join(levels)}\n\n"
                f"Enabling Learning Objectives (ELO) — gunakan sebagai basis modul:\n"
                + "\n".join(
                    f"- ELO {e.get('elo_number', '')}. [{e.get('related_performance', '').replace('PO ', 'PCS ')}] "
                    f"{e.get('elo', '')} "
                    f"(Bloom: {e.get('bloom_level', '')}, Metode: {e.get('delivery_method', '')}, "
                    f"{e.get('duration_minutes', '')} menit)"
                    for e in syllabus_elos
                )
                + "\n\nGunakan ELO di atas sebagai katalog modul. "
                  "Rekomendasikan ELO yang paling relevan dengan gap peserta, "
                  "urutkan dari yang paling fundamental ke advanced sesuai progression level.\n"
            )

    # ── Build modules context — purely generative, no DB lookup ─────────────
    if syllabus_elos:
        modules_context = (
            f"\nGunakan ELO dari silabus di atas sebagai basis modul yang direkomendasikan. "
            f"Generate {req.top_k} rekomendasi modul mikro yang paling relevan dengan gap peserta."
        )
    else:
        modules_context = (
            f"\nGenerate {req.top_k} rekomendasi modul mikro yang relevan berdasarkan gap kompetensi peserta."
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
        f"Gap Kompetensi: {req.gap_description}\n"
    )
    if req.jabatan:
        user_message += f"Jabatan: {req.jabatan}\n"
    if req.departemen:
        user_message += f"Departemen: {req.departemen}\n"
    if req.lama_bekerja:
        user_message += f"Lama Bekerja: {req.lama_bekerja}\n"
    if req.pendidikan_terakhir:
        user_message += f"Pendidikan Terakhir: {req.pendidikan_terakhir}\n"
    if req.preferensi_belajar:
        user_message += f"Preferensi Belajar: {req.preferensi_belajar}\n"
    if req.waktu_belajar_per_minggu:
        user_message += f"Waktu Belajar per Minggu: {req.waktu_belajar_per_minggu}\n"
    if syllabus_context:
        user_message += syllabus_context
    user_message += modules_context
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
