from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Recommendation
from app.routers.auth import get_current_user
from app.services.ai_agent import call_llm, parse_llm_json

router = APIRouter(tags=["career_roadmap"])


class CareerRoadmapRequest(BaseModel):
    participant_name: str
    current_position: str
    target_position: str
    timeline_months: int = 12
    additional_context: Optional[str] = None
    syllabus_id: Optional[str] = None


class RoadmapModule(BaseModel):
    module_title: str
    description: str
    urgency: str          # Critical | Important | Nice-to-have
    delivery_method: str
    duration_minutes: int


class RoadmapPhase(BaseModel):
    phase_number: int
    phase_name: str
    month_range: str
    focus: str
    modules: List[dict]


@router.post("/career-roadmap")
def generate_career_roadmap(
    req: CareerRoadmapRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    user_id = current_user["user_id"]

    # Hitung jumlah phase berdasarkan timeline
    if req.timeline_months <= 3:
        num_phases = 2
    elif req.timeline_months <= 6:
        num_phases = 3
    else:
        num_phases = min(4, req.timeline_months // 3)

    months_per_phase = req.timeline_months // num_phases

    # Syllabus context opsional
    syllabus_context = ""
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
            elos = output.get("elos", [])
            levels = output.get("levels_covered", [])
            syllabus_context = (
                f"\nKonteks Silabus:\n"
                f"Perusahaan: {profile.get('organization_name', '-')} | "
                f"Industri: {profile.get('industry', '-')}\n"
                f"Tipe Course: {output.get('course_type', '-')}\n"
                f"Level: {' → '.join(levels)}\n\n"
                f"Enabling Learning Objectives (ELO) — gunakan sebagai referensi kompetensi:\n"
                + "\n".join(
                    f"- ELO {e.get('elo_number', '')}. {e.get('elo', '')} "
                    f"(Bloom: {e.get('bloom_level', '')}, Metode: {e.get('delivery_method', '')}, "
                    f"{e.get('duration_minutes', '')} menit)"
                    for e in elos
                )
                + "\n\nGunakan ELO di atas sebagai referensi kompetensi yang perlu dikuasai "
                  "untuk mencapai target posisi. Susun roadmap yang aligned dengan progression level silabus.\n"
            )

    system_prompt = f"""Kamu adalah Career Development Advisor yang berpengalaman.
Tugasmu adalah menyusun learning path roadmap karir yang terstruktur dan diprioritaskan berdasarkan urgensi.

Roadmap harus:
- Realistis sesuai timeline yang diberikan
- Diprioritaskan berdasarkan urgensi untuk mencapai target posisi
- Setiap modul diberi label urgensi: Critical (wajib), Important (sangat disarankan), Nice-to-have (opsional)
- Disusun secara progresif dari fondasi ke advanced

Format output WAJIB dalam JSON array dengan {num_phases} phase:
[
  {{
    "phase_number": 1,
    "phase_name": "nama phase (contoh: Foundation, Core Skills, Advanced, Mastery)",
    "month_range": "Bulan 1-{months_per_phase}",
    "focus": "fokus utama phase ini dalam 1 kalimat",
    "modules": [
      {{
        "module_title": "judul modul spesifik",
        "description": "deskripsi singkat konten modul dalam 1-2 kalimat",
        "urgency": "Critical|Important|Nice-to-have",
        "delivery_method": "Video|Reading|Workshop|Hands-on Lab|Case Study|Mentoring|Certification",
        "duration_minutes": 60
      }}
    ]
  }}
]
Hasilkan 3-5 modul per phase. Pastikan modul Critical ada di phase awal."""

    user_message = (
        f"Peserta: {req.participant_name}\n"
        f"Posisi Saat Ini: {req.current_position}\n"
        f"Target Posisi: {req.target_position}\n"
        f"Timeline: {req.timeline_months} bulan\n"
    )
    if req.additional_context:
        user_message += f"Konteks Tambahan: {req.additional_context}\n"
    if syllabus_context:
        user_message += syllabus_context
    user_message += (
        f"\nSusunkan career roadmap learning path dari '{req.current_position}' "
        f"menuju '{req.target_position}' dalam {req.timeline_months} bulan."
    )

    raw = call_llm(system_prompt, user_message, max_tokens=8000)

    try:
        phases = parse_llm_json(raw, RoadmapPhase)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Failed to parse AI response: {str(e)}")

    # Hitung total durasi
    total_minutes = sum(
        m.get("duration_minutes", 0)
        for phase in phases
        for m in phase.get("modules", [])
    )

    # Simpan ke DB sebagai Recommendation
    rec = Recommendation(
        user_id=user_id,
        participant_name=req.participant_name,
        gap_input=f"Career: {req.current_position} → {req.target_position} ({req.timeline_months} bulan)",
        recommended_modules=phases,
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)

    return {
        "roadmap_id": str(rec.id),
        "phases": phases,
        "total_duration_minutes": total_minutes,
        "summary": {
            "participant": req.participant_name,
            "from": req.current_position,
            "to": req.target_position,
            "timeline_months": req.timeline_months,
            "num_phases": len(phases),
        }
    }
