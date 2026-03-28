from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Recommendation
from app.routers.auth import get_current_user
from app.services.ai_agent import call_llm, parse_llm_json

router = APIRouter(tags=["bulk_recommend"])

SYSTEM_PROMPT = """Kamu adalah Learning Advisor yang berpengalaman.
Tugasmu adalah merekomendasikan modul mikro yang paling relevan berdasarkan profil dan gap kompetensi peserta.

Pertimbangkan semua informasi profil peserta yang tersedia (jabatan, lama bekerja, departemen,
pendidikan terakhir, preferensi belajar, waktu belajar per minggu) untuk mempersonalisasi rekomendasi.

Urutkan rekomendasi dari modul yang paling fundamental ke yang paling advanced.
Jelaskan mengapa setiap modul relevan dengan gap dan profil peserta.

Jika daftar ELO/modul dari silabus tersedia, rekomendasikan dari daftar tersebut.
Jika tidak, generate rekomendasi modul mikro yang relevan berdasarkan gap dan profil.

Tentukan recommended_level (1–5) yang paling sesuai untuk peserta berdasarkan profil dan gap:
- Level 1 (Intro): Belum pernah terpapar topik, baru mulai
- Level 2 (Beginner): Sudah mengenal dasar, perlu fondasi lebih kuat
- Level 3 (Intermediate): Sudah praktik, perlu pendalaman
- Level 4 (Advanced): Sudah mahir, perlu spesialisasi
- Level 5 (Mastery): Expert, perlu inovasi dan kepemimpinan

Format output WAJIB dalam JSON object:
{
  "recommended_level": 2,
  "level_label": "Beginner",
  "modules": [
    {
      "rank": 1,
      "module_title": "judul modul mikro",
      "relevance_reason": "alasan relevansi dengan gap dan profil peserta",
      "priority": "High|Medium|Low",
      "estimated_duration_minutes": 10
    }
  ]
}"""


class ParticipantProfile(BaseModel):
    nama: str
    jabatan: Optional[str] = None
    lama_bekerja: Optional[str] = None
    departemen: Optional[str] = None
    gap_kompetensi: str
    pendidikan_terakhir: Optional[str] = None
    preferensi_belajar: Optional[str] = None
    waktu_belajar_per_minggu: Optional[str] = None


class BulkRecommendRequest(BaseModel):
    participants: List[ParticipantProfile]
    top_k: int = 5
    syllabus_id: Optional[str] = None


class RecommendationItem(BaseModel):
    rank: int
    module_title: str
    relevance_reason: str
    priority: str
    estimated_duration_minutes: int


def _build_syllabus_context(syllabus_id: str, user_id, db: Session) -> tuple[str, list]:
    """Return (syllabus_context_str, elos_list)."""
    from app.db.models import Syllabus
    syllabus = db.query(Syllabus).filter(
        Syllabus.id == syllabus_id,
        Syllabus.user_id == user_id,
    ).first()
    if not syllabus or not syllabus.output_json:
        return "", []

    output = syllabus.output_json
    profile = output.get("org_profile", {})
    syllabus_elos = output.get("elos", [])
    levels = output.get("levels_covered", [])

    ctx = (
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
    return ctx, syllabus_elos


def _build_user_message(p: ParticipantProfile, top_k: int, syllabus_context: str, has_elos: bool) -> str:
    profile_lines = [f"Nama: {p.nama}", f"Gap Kompetensi: {p.gap_kompetensi}"]
    if p.jabatan:
        profile_lines.append(f"Jabatan: {p.jabatan}")
    if p.departemen:
        profile_lines.append(f"Departemen: {p.departemen}")
    if p.lama_bekerja:
        profile_lines.append(f"Lama Bekerja: {p.lama_bekerja}")
    if p.pendidikan_terakhir:
        profile_lines.append(f"Pendidikan Terakhir: {p.pendidikan_terakhir}")
    if p.preferensi_belajar:
        profile_lines.append(f"Preferensi Belajar: {p.preferensi_belajar}")
    if p.waktu_belajar_per_minggu:
        profile_lines.append(f"Waktu Belajar per Minggu: {p.waktu_belajar_per_minggu}")

    msg = "Profil Peserta:\n" + "\n".join(profile_lines)
    if syllabus_context:
        msg += "\n" + syllabus_context
    if has_elos:
        msg += f"\nGenerate {top_k} rekomendasi modul mikro dari ELO silabus yang paling relevan untuk peserta ini."
    else:
        msg += f"\nGenerate {top_k} rekomendasi modul mikro yang relevan berdasarkan gap dan profil peserta."
    msg += "\nRekomendasikan learning path yang paling relevan untuk peserta ini."
    return msg


@router.post("/bulk-recommend")
def bulk_recommend(
    req: BulkRecommendRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    user_id = current_user["user_id"]

    # One session ID per batch — groups all results from this generate run
    import uuid as _uuid
    bulk_session_id = str(_uuid.uuid4())

    # Build syllabus context once (shared across all participants)
    syllabus_context, syllabus_elos = "", []
    if req.syllabus_id:
        syllabus_context, syllabus_elos = _build_syllabus_context(req.syllabus_id, user_id, db)

    results = []
    errors = []

    for p in req.participants:
        try:
            user_message = _build_user_message(p, req.top_k, syllabus_context, bool(syllabus_elos))
            raw = call_llm(SYSTEM_PROMPT, user_message)

            # Parse outer object to extract level + modules array
            import json, re
            cleaned = raw.strip()
            cleaned = re.sub(r"^```[a-zA-Z]*\s*", "", cleaned)
            cleaned = re.sub(r"\s*```\s*$", "", cleaned).strip()
            outer = json.loads(cleaned)

            recommended_level = outer.get("recommended_level")
            level_label = outer.get("level_label", "")
            modules_raw = outer.get("modules", [])
            items = [RecommendationItem(**m).model_dump() for m in modules_raw]

            # Save to DB — tag with bulk_session_id and extra profile fields in gap_input prefix
            rec = Recommendation(
                user_id=user_id,
                participant_name=p.nama,
                gap_input=p.gap_kompetensi,
                recommended_modules=items,
                bulk_session_id=bulk_session_id,
            )
            db.add(rec)
            db.commit()
            db.refresh(rec)

            results.append({
                "recommendation_id": str(rec.id),
                "nama": p.nama,
                "jabatan": p.jabatan,
                "departemen": p.departemen,
                "gap_kompetensi": p.gap_kompetensi,
                "recommended_level": recommended_level,
                "level_label": level_label,
                "recommendations": items,
            })
        except Exception as e:
            errors.append({"nama": p.nama, "error": str(e)})

    return {
        "bulk_session_id": bulk_session_id,
        "total_processed": len(results),
        "total_errors": len(errors),
        "results": results,
        "errors": errors,
    }
