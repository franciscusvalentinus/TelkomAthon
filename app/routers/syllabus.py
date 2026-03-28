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

LEVEL_MAP = {
    1: "Intro",
    2: "Beginner",
    3: "Intermediate",
    4: "Advanced",
    5: "Mastery",
}


def levels_description(start_level: int) -> str:
    levels = [f"Level {l} ({LEVEL_MAP[l]})" for l in range(start_level, 6)]
    return ", ".join(levels)


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
        "profil perusahaan visi misi strategi bisnis kompetensi",
        db, top_k=8, document_ids=req.document_ids
    )
    if not chunks:
        raise HTTPException(status_code=404, detail="Tidak ada konten yang ditemukan dari dokumen yang dipilih.")

    context_texts = [c["chunk_text"] for c in chunks]

    system_prompt = """Kamu adalah Learning Strategist.
Tugasmu adalah membaca dokumen profil perusahaan dan menghasilkan ringkasan terstruktur.

ATURAN PENTING dalam menentukan nama perusahaan:
- Cari entitas yang namanya mengandung kata "PT" (Perseroan Terbatas) — itulah perusahaan utama yang dimaksud.
- Jika ada beberapa entitas "PT", pilih yang paling sering disebut atau yang menjadi subjek utama dokumen.
- Abaikan nama lembaga/vendor/mitra lain yang bukan subjek utama dokumen (misalnya nama penyelenggara pelatihan, nama universitas, nama konsultan, dll.).
- Jika tidak ada entitas "PT", gunakan nama perusahaan yang paling dominan sebagai subjek dokumen.

Format output WAJIB dalam JSON dengan struktur:
{
  "organization_name": "nama perusahaan (utamakan yang mengandung PT)",
  "industry": "industri/sektor",
  "vision": "visi perusahaan",
  "mission": "misi perusahaan",
  "strategic_priorities": ["prioritas strategis 1", "prioritas strategis 2"],
  "core_competencies": ["kompetensi inti 1", "kompetensi inti 2"],
  "learning_context": "narasi singkat 2-3 kalimat tentang konteks pembelajaran yang relevan untuk perusahaan ini",
  "recommended_course_types": ["tipe course yang paling relevan berdasarkan profil"]
}"""

    raw = call_llm(system_prompt, "Analisis dokumen profil perusahaan berikut. Fokuskan pada perusahaan yang namanya mengandung 'PT' sebagai subjek utama, bukan lembaga penyelenggara atau mitra. Buat ringkasan terstruktur.", context_texts)

    import json, re

    def _parse_json(text: str):
        cleaned = text.strip()
        cleaned = re.sub(r"^```[a-zA-Z]*\s*", "", cleaned)
        cleaned = re.sub(r"\s*```\s*$", "", cleaned)
        return json.loads(cleaned.strip())

    try:
        result = _parse_json(raw)
    except Exception:
        retry_raw = call_llm(
            "You are a JSON formatter. Return ONLY valid JSON object, no explanation, no markdown.",
            f"Fix this and return only the valid JSON object:\n{raw}"
        )
        try:
            result = _parse_json(retry_raw)
        except Exception:
            raise HTTPException(status_code=422, detail=f"Gagal memparse respons AI: {raw[:300]}")

    return {"org_profile": result}


# ── Step 1b: Analyze org from manual input (no document) ─────────────────────

class AnalyzeOrgManualRequest(BaseModel):
    company_name: str
    industry: str


@router.post("/syllabus/analyze-org-manual")
def analyze_org_manual(
    req: AnalyzeOrgManualRequest,
    current_user: dict = Depends(get_current_user),
):
    """Generate org profile from company name + industry using LLM knowledge."""
    system_prompt = """Kamu adalah Learning Strategist yang berpengalaman.
Tugasmu adalah menyusun profil perusahaan berdasarkan nama dan industri yang diberikan.
Gunakan pengetahuanmu tentang industri tersebut untuk mengisi detail yang relevan.

Format output WAJIB dalam JSON:
{
  "organization_name": "nama perusahaan persis seperti yang diberikan",
  "industry": "industri/sektor",
  "vision": "contoh visi yang umum dan relevan untuk perusahaan di industri ini",
  "mission": "contoh misi yang umum dan relevan untuk perusahaan di industri ini",
  "strategic_priorities": ["prioritas strategis yang umum di industri ini", "..."],
  "core_competencies": ["kompetensi inti yang umumnya dibutuhkan di industri ini", "..."],
  "learning_context": "narasi singkat 2-3 kalimat tentang konteks pembelajaran yang relevan untuk perusahaan di industri ini",
  "recommended_course_types": ["tipe course yang paling relevan untuk industri ini"]
}
Catatan: Tandai bahwa profil ini dibuat berdasarkan inferensi industri, bukan dokumen resmi."""

    user_message = (
        f"Nama Perusahaan: {req.company_name}\n"
        f"Industri: {req.industry}\n\n"
        f"Susunkan profil perusahaan yang relevan berdasarkan nama dan industri di atas."
    )

    raw = call_llm(system_prompt, user_message)

    import json, re

    def _parse_json(text: str):
        cleaned = text.strip()
        # Strip markdown code fences (```json ... ``` or ``` ... ```)
        cleaned = re.sub(r"^```[a-zA-Z]*\s*", "", cleaned)
        cleaned = re.sub(r"\s*```\s*$", "", cleaned)
        cleaned = cleaned.strip()
        return json.loads(cleaned)

    try:
        result = _parse_json(raw)
    except Exception:
        # Retry: ask LLM to return only valid JSON
        retry_raw = call_llm(
            "You are a JSON formatter. Return ONLY valid JSON object, no explanation, no markdown.",
            f"Fix this and return only the valid JSON object:\n{raw}"
        )
        try:
            result = _parse_json(retry_raw)
        except Exception:
            raise HTTPException(status_code=422, detail=f"Gagal memparse respons AI: {raw[:300]}")

    return {"org_profile": result}


# ── Step 2: Generate TLOs ─────────────────────────────────────────────────────

class GenerateTLORequest(BaseModel):
    course_type: str
    org_profile: dict
    document_ids: List[str] = []
    start_level: int = 1
    current_condition: str = ""
    desired_condition: str = ""


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
    # RAG hanya untuk konteks perusahaan, bukan untuk konten course
    chunks = search_similar_chunks(
        f"profil bisnis strategi {req.org_profile.get('industry', '')}",
        db, top_k=4, document_ids=req.document_ids or None
    )
    context_texts = [c["chunk_text"] for c in chunks]

    levels_desc = levels_description(req.start_level)
    level_count = 6 - req.start_level  # jumlah level yang akan dicakup

    condition_context = ""
    if req.current_condition or req.desired_condition:
        condition_context = f"""
KONTEKS KONDISI PESERTA:
- Kondisi Saat Ini: {req.current_condition or 'tidak disebutkan'}
- Kondisi yang Diinginkan: {req.desired_condition or 'tidak disebutkan'}

TLO harus menjembatani gap antara kondisi saat ini dan kondisi yang diinginkan."""

    system_prompt = f"""Kamu adalah Learning Design Expert.
Tugasmu adalah membuat Terminal Learning Objectives (TLO) untuk program pelatihan bertopik SPESIFIK berikut:

TOPIK COURSE: "{req.course_type}"
LEVEL YANG DICAKUP: {levels_desc}
{condition_context}
TLO WAJIB membahas konten yang berkaitan langsung dengan "{req.course_type}".
TLO harus mencerminkan progression dari {LEVEL_MAP[req.start_level]} hingga Mastery.
Setiap TLO harus menunjukkan kedalaman yang berbeda sesuai levelnya.
Jangan membuat TLO yang generik atau tidak berkaitan dengan topik tersebut.

TLO adalah pernyataan tingkat tinggi tentang apa yang peserta mampu lakukan setelah menyelesaikan seluruh program.
Gunakan kata kerja Bloom's Taxonomy yang sesuai dengan level masing-masing.

Format output WAJIB dalam JSON array:
[
  {{
    "tlo_number": 1,
    "tlo": "Setelah mengikuti program ini, peserta mampu [kata kerja] [objek spesifik terkait {req.course_type}] [kondisi/standar]",
    "rationale": "alasan mengapa TLO ini relevan dengan topik {req.course_type} dan konteks perusahaan"
  }}
]
Hasilkan {max(5, level_count * 2)} TLO yang beragam, spesifik, dan semuanya berkaitan langsung dengan "{req.course_type}".
Pastikan ada TLO yang mencerminkan setiap level: {levels_desc}."""

    org_summary = (
        f"Perusahaan: {req.org_profile.get('organization_name', '')}\n"
        f"Industri: {req.org_profile.get('industry', '')}\n"
        f"Prioritas Strategis: {', '.join(req.org_profile.get('strategic_priorities', []))}\n"
        f"Kompetensi Inti: {', '.join(req.org_profile.get('core_competencies', []))}\n"
        f"Konteks Pembelajaran: {req.org_profile.get('learning_context', '')}"
    )

    user_message = (
        f"Topik Course yang HARUS menjadi fokus: {req.course_type}\n"
        f"Level yang dicakup: {levels_desc}\n\n"
        f"Profil Perusahaan (sebagai konteks):\n{org_summary}\n\n"
    )
    if req.current_condition:
        user_message += f"Kondisi Saat Ini (masalah/kendala peserta):\n{req.current_condition}\n\n"
    if req.desired_condition:
        user_message += f"Kondisi yang Diinginkan (target setelah pelatihan):\n{req.desired_condition}\n\n"
    user_message += (
        f"Buatkan TLO yang SPESIFIK untuk topik '{req.course_type}', "
        f"mencerminkan progression dari {LEVEL_MAP[req.start_level]} hingga Mastery, "
        f"disesuaikan dengan konteks bisnis perusahaan dan kondisi peserta di atas."
    )
    raw = call_llm(system_prompt, user_message, context_texts)

    try:
        items = parse_llm_json(raw, TLOItem)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Gagal memparse TLO: {str(e)}")

    return {"tlos": items}


# ── Step 3: Generate PCS ───────────────────────────────────

class GeneratePerfRequest(BaseModel):
    selected_tlos: List[dict]
    org_profile: dict
    document_ids: List[str] = []
    start_level: int = 1


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
    """Generate PCS based on selected TLOs."""
    tlo_text = "\n".join(f"- TLO {t['tlo_number']}: {t['tlo']}" for t in req.selected_tlos)

    # Ekstrak topik dari TLO untuk query RAG yang lebih relevan
    chunks = search_similar_chunks(
        f"profil bisnis strategi {req.org_profile.get('industry', '')}",
        db, top_k=3, document_ids=req.document_ids or None
    )
    context_texts = [c["chunk_text"] for c in chunks]

    # Deteksi course type dari TLO pertama untuk memperkuat instruksi
    first_tlo = req.selected_tlos[0].get("tlo", "") if req.selected_tlos else ""

    levels_desc = levels_description(req.start_level)

    system_prompt = f"""Kamu adalah Instructional Designer.
Tugasmu adalah membuat PCS berdasarkan TLO yang diberikan.

LEVEL YANG DICAKUP: {levels_desc}

PENTING: PCS HARUS spesifik dan berkaitan langsung dengan konten yang ada di TLO.
Setiap PO harus mencerminkan tingkat kesulitan yang sesuai dengan levelnya — dari {LEVEL_MAP[req.start_level]} hingga Mastery.
Jangan membuat PCS yang generik.

PCS harus memiliki tiga komponen:
- Perilaku (Behavior): tindakan spesifik yang dapat diamati
- Kondisi (Condition): situasi/sumber daya yang diberikan
- Standar (Standard): kriteria keberhasilan yang terukur

Format output WAJIB dalam JSON array:
[
  {{
    "perf_number": 1,
    "related_tlo": "TLO 1",
    "performance_objective": "Peserta dapat [perilaku spesifik sesuai topik TLO]",
    "condition": "Diberikan [kondisi/tools/skenario spesifik]",
    "standard": "dengan [kriteria terukur yang spesifik]"
  }}
]
Hasilkan 2-3 PCS per TLO. Pastikan ada variasi tingkat kesulitan sesuai level: {levels_desc}."""

    user_message = (
        f"TLO yang dipilih (jadikan dasar konten PO):\n{tlo_text}\n\n"
        f"Konteks Perusahaan: {req.org_profile.get('organization_name', '')} — {req.org_profile.get('industry', '')}\n\n"
        f"Buatkan PCS yang SPESIFIK sesuai konten setiap TLO di atas."
    )
    raw = call_llm(system_prompt, user_message, context_texts)

    try:
        items = parse_llm_json(raw, PerfItem)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Gagal memparse PCS: {str(e)}")

    return {"performance_objectives": items}


# ── Step 4: Generate ELOs ─────────────────────────────────────────────────────

class GenerateELORequest(BaseModel):
    selected_tlos: List[dict]
    selected_performances: List[dict]
    org_profile: dict
    document_ids: List[str] = []
    start_level: int = 1


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
    """Generate Enabling Learning Objectives based on selected TLOs and PCS."""
    tlo_text = "\n".join(f"- {t['tlo']}" for t in req.selected_tlos)
    perf_text = "\n".join(f"- PCS {p['perf_number']}: {p['performance_objective']}" for p in req.selected_performances)

    chunks = search_similar_chunks(
        f"profil bisnis strategi {req.org_profile.get('industry', '')}",
        db, top_k=3, document_ids=req.document_ids or None
    )
    context_texts = [c["chunk_text"] for c in chunks]

    levels_desc = levels_description(req.start_level)

    system_prompt = f"""Kamu adalah Instructional Designer spesialis kurikulum.
Tugasmu adalah membuat Enabling Learning Objectives (ELO) yang mendukung pencapaian PCS.

LEVEL YANG DICAKUP: {levels_desc}

PENTING: ELO HARUS spesifik dan berkaitan langsung dengan konten PCS yang diberikan.
ELO adalah unit pembelajaran terkecil — fokus pada satu pengetahuan atau keterampilan spesifik.
Gunakan kata kerja Bloom's Taxonomy yang sesuai dengan level masing-masing:
- {LEVEL_MAP[1]}/Intro: Remember, Understand
- Beginner: Understand, Apply
- Intermediate: Apply, Analyze
- Advanced: Analyze, Evaluate
- Mastery: Evaluate, Create

Format output WAJIB dalam JSON array:
[
  {{
    "elo_number": 1,
    "related_performance": "PCS 1",
    "elo": "Peserta dapat [kata kerja Bloom sesuai level] [konten spesifik sesuai topik PO]",
    "bloom_level": "Remember|Understand|Apply|Analyze|Evaluate|Create",
    "delivery_method": "Video|Reading|Quiz|Case Study|Role Play|Simulation|Workshop|Hands-on Lab",
    "duration_minutes": 15
  }}
]
Hasilkan 2-4 ELO per PCS. Pastikan ada variasi Bloom level sesuai level: {levels_desc}."""

    user_message = (
        f"TLO (konteks program):\n{tlo_text}\n\n"
        f"PCS (jadikan dasar konten ELO):\n{perf_text}\n\n"
        f"Konteks Perusahaan: {req.org_profile.get('organization_name', '')} — {req.org_profile.get('industry', '')}\n\n"
        f"Buatkan ELO yang SPESIFIK untuk setiap PCS di atas. "
        f"Pastikan konten ELO mencerminkan sub-topik nyata yang perlu dipelajari."
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
    start_level: int = 1
    current_condition: str = ""
    desired_condition: str = ""


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
        "start_level": req.start_level,
        "levels_covered": [f"Level {l} — {LEVEL_MAP[l]}" for l in range(req.start_level, 6)],
        "current_condition": req.current_condition,
        "desired_condition": req.desired_condition,
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
