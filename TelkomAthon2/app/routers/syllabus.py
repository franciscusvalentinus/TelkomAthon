from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Syllabus
from app.routers.auth import get_current_user
from app.services.vector_search import search_similar_chunks
from app.services.ai_agent import call_llm, parse_llm_json

router = APIRouter(tags=["syllabus"])

COURSE_TYPES = ["B2B Sales", "Innovation", "Technology", "Leadership", "Operations",
                "Customer Experience", "Finance", "HR & People", "Digital Marketing", "Other"]


# ── Step 1: Analyze org profile ───────────────────────────────────────────────

class AnalyzeOrgRequest(BaseModel):
    document_ids: List[str]


@router.post("/syllabus/analyze-org")
def analyze_org(
    req: AnalyzeOrgRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Read org profile docs and return a structured summary + context overview."""
    chunks = search_similar_chunks(
        "profil organisasi visi misi strategi bisnis kompetensi",
        db, top_k=8, document_ids=req.document_ids
    )
    if not chunks:
        raise HTTPException(status_code=404, detail="Tidak ada konten yang ditemukan dari dokumen yang dipilih.")

    context_texts = [c["chunk_text"] for c in chunks]

    system_prompt = """Kamu adalah Learning Strategist untuk Telkom Indonesia.
Tugasmu adalah membaca dokumen profil organisasi dan menghasilkan ringkasan terstruktur.

Format output WAJIB dalam JSON dengan struktur:
{
  "organization_name": "nama organisasi",
  "industry": "industri/sektor",
  "vision": "visi organisasi",
  "mission": "misi organisasi",
  "strategic_priorities": ["prioritas strategis 1", "prioritas strategis 2"],
  "core_competencies": ["kompetensi inti 1", "kompetensi inti 2"],
  "learning_context": "narasi singkat 2-3 kalimat tentang konteks pembelajaran yang relevan untuk organisasi ini",
  "recommended_course_types": ["tipe course yang paling relevan berdasarkan profil"]
}"""

    raw = call_llm(system_prompt, "Analisis profil organisasi berikut dan buat ringkasan terstruktur.", context_texts)

    import json, re
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-z]*\n?", "", cleaned)
        cleaned = re.sub(r"\n?```$", "", cleaned)
    try:
        result = json.loads(cleaned)
    except Exception:
        raise HTTPException(status_code=422, detail=f"Gagal memparse respons AI: {raw[:300]}")

    return {"org_profile": result}


# ── Step 2: Generate TLOs ─────────────────────────────────────────────────────

class GenerateTLORequest(BaseModel):
    course_type: str
    org_profile: dict
    document_ids: List[str] = []


class TLOItem(BaseModel):
    tlo_number: int
    tlo: str
    rationale: str


@router.post("/syllabus/generate-tlo")
def generate_tlo(
    req: GenerateTLORequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Generate Terminal Learning Objectives based on course type and org profile."""
    chunks = search_similar_chunks(req.course_type, db, top_k=5, document_ids=req.document_ids or None)
    context_texts = [c["chunk_text"] for c in chunks]

    system_prompt = """Kamu adalah Learning Design Expert.
Tugasmu adalah membuat Terminal Learning Objectives (TLO) untuk sebuah program pelatihan.

TLO adalah pernyataan tingkat tinggi tentang apa yang peserta mampu lakukan setelah menyelesaikan seluruh program.
Gunakan kata kerja Bloom's Taxonomy level tinggi (menganalisis, mengevaluasi, merancang, dll).

Format output WAJIB dalam JSON array:
[
  {
    "tlo_number": 1,
    "tlo": "Setelah mengikuti program ini, peserta mampu [kata kerja] [objek] [kondisi/standar]",
    "rationale": "alasan mengapa TLO ini relevan dengan konteks organisasi"
  }
]
Hasilkan 5-7 TLO yang beragam dan relevan."""

    org_summary = (
        f"Organisasi: {req.org_profile.get('organization_name', '')}\n"
        f"Industri: {req.org_profile.get('industry', '')}\n"
        f"Prioritas Strategis: {', '.join(req.org_profile.get('strategic_priorities', []))}\n"
        f"Kompetensi Inti: {', '.join(req.org_profile.get('core_competencies', []))}\n"
        f"Konteks Pembelajaran: {req.org_profile.get('learning_context', '')}"
    )

    user_message = f"Tipe Course: {req.course_type}\n\nProfil Organisasi:\n{org_summary}\n\nBuatkan TLO yang relevan."
    raw = call_llm(system_prompt, user_message, context_texts)

    try:
        items = parse_llm_json(raw, TLOItem)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Gagal memparse TLO: {str(e)}")

    return {"tlos": items}


# ── Step 3: Generate Performance Objectives ───────────────────────────────────

class GeneratePerfRequest(BaseModel):
    selected_tlos: List[dict]
    org_profile: dict
    document_ids: List[str] = []


class PerfItem(BaseModel):
    perf_number: int
    related_tlo: str
    performance_objective: str
    condition: str
    standard: str


@router.post("/syllabus/generate-performance")
def generate_performance(
    req: GeneratePerfRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Generate Performance Objectives based on selected TLOs."""
    tlo_text = "\n".join(f"- TLO {t['tlo_number']}: {t['tlo']}" for t in req.selected_tlos)
    chunks = search_similar_chunks(tlo_text[:500], db, top_k=5, document_ids=req.document_ids or None)
    context_texts = [c["chunk_text"] for c in chunks]

    system_prompt = """Kamu adalah Instructional Designer.
Tugasmu adalah membuat Performance Objectives berdasarkan Terminal Learning Objectives (TLO) yang diberikan.

Performance Objective mendeskripsikan perilaku yang dapat diamati dan diukur.
Setiap Performance Objective harus memiliki: Perilaku (Behavior), Kondisi (Condition), dan Standar (Standard).

Format output WAJIB dalam JSON array:
[
  {
    "perf_number": 1,
    "related_tlo": "TLO 1",
    "performance_objective": "Peserta dapat [perilaku spesifik yang dapat diamati]",
    "condition": "Diberikan [kondisi/sumber daya/situasi]",
    "standard": "dengan [kriteria keberhasilan yang terukur]"
  }
]
Hasilkan 2-3 Performance Objective per TLO."""

    user_message = f"TLO yang dipilih:\n{tlo_text}\n\nBuatkan Performance Objectives yang terukur."
    raw = call_llm(system_prompt, user_message, context_texts)

    try:
        items = parse_llm_json(raw, PerfItem)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Gagal memparse Performance Objectives: {str(e)}")

    return {"performance_objectives": items}


# ── Step 4: Generate ELOs ─────────────────────────────────────────────────────

class GenerateELORequest(BaseModel):
    selected_tlos: List[dict]
    selected_performances: List[dict]
    org_profile: dict
    document_ids: List[str] = []


class ELOItem(BaseModel):
    elo_number: int
    related_performance: str
    elo: str
    bloom_level: str
    delivery_method: str
    duration_minutes: int


@router.post("/syllabus/generate-elo")
def generate_elo(
    req: GenerateELORequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Generate Enabling Learning Objectives based on selected TLOs and Performance Objectives."""
    tlo_text = "\n".join(f"- {t['tlo']}" for t in req.selected_tlos)
    perf_text = "\n".join(f"- {p['performance_objective']}" for p in req.selected_performances)

    chunks = search_similar_chunks(perf_text[:500], db, top_k=5, document_ids=req.document_ids or None)
    context_texts = [c["chunk_text"] for c in chunks]

    system_prompt = """Kamu adalah Instructional Designer spesialis kurikulum.
Tugasmu adalah membuat Enabling Learning Objectives (ELO) — tujuan pembelajaran pendukung yang membantu peserta mencapai Performance Objectives.

ELO bersifat lebih spesifik dan granular, fokus pada pengetahuan/keterampilan yang dibutuhkan.

Format output WAJIB dalam JSON array:
[
  {
    "elo_number": 1,
    "related_performance": "Performance Objective 1",
    "elo": "Peserta dapat [kata kerja Bloom] [konten spesifik]",
    "bloom_level": "Remember|Understand|Apply|Analyze|Evaluate|Create",
    "delivery_method": "Video|Reading|Quiz|Case Study|Role Play|Simulation|Workshop",
    "duration_minutes": 15
  }
]
Hasilkan 2-4 ELO per Performance Objective."""

    user_message = (
        f"TLO:\n{tlo_text}\n\n"
        f"Performance Objectives:\n{perf_text}\n\n"
        f"Buatkan ELO yang mendukung pencapaian Performance Objectives di atas."
    )
    raw = call_llm(system_prompt, user_message, context_texts)

    try:
        items = parse_llm_json(raw, ELOItem)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Gagal memparse ELO: {str(e)}")

    return {"elos": items}


# ── Step 5: Finalize & save syllabus ─────────────────────────────────────────

class FinalizeRequest(BaseModel):
    course_type: str
    org_profile: dict
    selected_tlos: List[dict]
    selected_performances: List[dict]
    selected_elos: List[dict]


@router.post("/syllabus/finalize")
def finalize_syllabus(
    req: FinalizeRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Compile all selected components into a final syllabus document and save to DB."""
    user_id = current_user["user_id"]

    output = {
        "org_profile": req.org_profile,
        "course_type": req.course_type,
        "tlos": req.selected_tlos,
        "performance_objectives": req.selected_performances,
        "elos": req.selected_elos,
    }

    topic = f"{req.course_type} — {req.org_profile.get('organization_name', 'Org')}"
    syllabus = Syllabus(
        user_id=user_id,
        topic=topic,
        level="Multi-level",
        output_json=output,
    )
    db.add(syllabus)
    db.commit()
    db.refresh(syllabus)

    return {"syllabus_id": str(syllabus.id), "result": output}
