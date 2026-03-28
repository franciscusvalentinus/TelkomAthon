from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Syllabus
from app.routers.auth import get_current_user
from app.services.ai_agent import call_llm, parse_llm_json

router = APIRouter(tags=["quiz"])

SYSTEM_PROMPT_QUIZ = """Kamu adalah Instructional Designer spesialis assessment.
Tugasmu adalah membuat soal pilihan ganda berkualitas tinggi berdasarkan ELO (Enabling Learning Objective) yang diberikan.

Setiap soal harus:
- Relevan langsung dengan ELO yang dituju
- Memiliki 4 pilihan jawaban (A, B, C, D)
- Memiliki satu jawaban yang jelas benar
- Memiliki distraktor yang masuk akal

Format output WAJIB dalam JSON array:
[
  {
    "nomor": 1,
    "elo_reference": "ELO X — judul ELO",
    "pertanyaan": "teks pertanyaan",
    "pilihan": {
      "A": "pilihan A",
      "B": "pilihan B",
      "C": "pilihan C",
      "D": "pilihan D"
    },
    "jawaban_benar": "A",
    "penjelasan": "penjelasan singkat mengapa jawaban ini benar"
  }
]"""


class QuizItem(BaseModel):
    nomor: int
    elo_reference: str
    pertanyaan: str
    pilihan: dict
    jawaban_benar: str
    penjelasan: str


class GenerateQuizRequest(BaseModel):
    syllabus_id: str
    mode: str  # "prepost" | "single"
    jumlah_soal: int = 10


@router.post("/generate-quiz")
def generate_quiz(
    req: GenerateQuizRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    user_id = current_user["user_id"]

    syllabus = db.query(Syllabus).filter(
        Syllabus.id == req.syllabus_id,
        Syllabus.user_id == user_id,
    ).first()
    if not syllabus or not syllabus.output_json:
        raise HTTPException(status_code=404, detail="Silabus tidak ditemukan.")

    output = syllabus.output_json
    elos = output.get("elos", [])

    # Filter ELO yang delivery_method-nya Quiz (case-insensitive)
    quiz_elos = [
        e for e in elos
        if "quiz" in e.get("delivery_method", "").lower()
    ]

    if not quiz_elos:
        return {"has_quiz_elos": False, "quiz_elos": [], "results": []}

    elo_context = "\n".join(
        f"- ELO {e.get('elo_number', '')}. {e.get('elo', '')} "
        f"(Bloom: {e.get('bloom_level', '')}, Durasi: {e.get('duration_minutes', '')} menit)"
        for e in quiz_elos
    )

    course_type = output.get("course_type", "")
    profile = output.get("org_profile", {})

    def _generate(label: str, n: int) -> list:
        user_msg = (
            f"Perusahaan: {profile.get('organization_name', '-')} | Course: {course_type}\n\n"
            f"ELO yang perlu diassess ({label}):\n{elo_context}\n\n"
            f"Buat {n} soal pilihan ganda untuk {label}. "
            f"Distribusikan soal secara merata ke semua ELO di atas."
        )
        raw = call_llm(SYSTEM_PROMPT_QUIZ, user_msg, max_tokens=4096)
        return parse_llm_json(raw, QuizItem)

    if req.mode == "prepost":
        pre = _generate("Pre-test", req.jumlah_soal)
        post = _generate("Post-test", req.jumlah_soal)
        return {
            "has_quiz_elos": True,
            "quiz_elos": [e.get("elo_number") for e in quiz_elos],
            "mode": "prepost",
            "pre_test": pre,
            "post_test": post,
        }
    else:
        quiz = _generate("Quiz", req.jumlah_soal)
        return {
            "has_quiz_elos": True,
            "quiz_elos": [e.get("elo_number") for e in quiz_elos],
            "mode": "single",
            "quiz": quiz,
        }
