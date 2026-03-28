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


# ── Decompose from saved syllabus ─────────────────────────────────────────────

class DecomposeFromSyllabusRequest(BaseModel):
    syllabus_id: str
    guide_document_id: Optional[str] = None


@router.get("/syllabi")
def list_syllabi(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Return list of saved syllabi for the current user."""
    from app.db.models import Syllabus
    user_id = current_user["user_id"]
    syllabi = (
        db.query(Syllabus)
        .filter(Syllabus.user_id == user_id)
        .order_by(Syllabus.created_at.desc())
        .all()
    )
    return [
        {
            "id": str(s.id),
            "topic": s.topic,
            "level": s.level,
            "created_at": s.created_at,
            "output_json": s.output_json,
        }
        for s in syllabi
    ]


def _syllabus_to_context(output_json: dict) -> str:
    """Flatten syllabus output_json into a rich plain-text context for the LLM."""
    lines = []
    profile = output_json.get("org_profile", {})
    lines.append("=== PROFIL PERUSAHAAN ===")
    lines.append(f"Perusahaan : {profile.get('organization_name', '-')}")
    lines.append(f"Industri   : {profile.get('industry', '-')}")
    lines.append(f"Visi       : {profile.get('vision', '-')}")
    lines.append(f"Misi       : {profile.get('mission', '-')}")
    lines.append(f"Prioritas Strategis: {', '.join(profile.get('strategic_priorities', []))}")
    lines.append(f"Kompetensi Inti    : {', '.join(profile.get('core_competencies', []))}")
    lines.append(f"Konteks Pembelajaran: {profile.get('learning_context', '-')}")
    lines.append("")

    lines.append(f"Tipe Course : {output_json.get('course_type', '-')}")
    if output_json.get("levels_covered"):
        lines.append(f"Level       : {' → '.join(output_json['levels_covered'])}")
    if output_json.get("current_condition"):
        lines.append(f"Kondisi Saat Ini   : {output_json['current_condition']}")
    if output_json.get("desired_condition"):
        lines.append(f"Kondisi Diinginkan : {output_json['desired_condition']}")
    lines.append("")

    lines.append("=== TERMINAL LEARNING OBJECTIVES (TLO) ===")
    for t in output_json.get("tlos", []):
        lines.append(f"TLO {t.get('tlo_number', '')}. {t.get('tlo', '')}")
        lines.append(f"  Rationale: {t.get('rationale', '')}")
    lines.append("")

    lines.append("=== PERFORMANCE OBJECTIVES ===")
    for p in output_json.get("performance_objectives", []):
        lines.append(f"PO {p.get('perf_number', '')}. [{p.get('related_tlo', '')}] {p.get('performance_objective', '')}")
        lines.append(f"  Kondisi: {p.get('condition', '')} | Standar: {p.get('standard', '')}")
    lines.append("")

    lines.append("=== ENABLING LEARNING OBJECTIVES (ELO) ===")
    total_dur = sum(e.get("duration_minutes", 0) for e in output_json.get("elos", []))
    for e in output_json.get("elos", []):
        lines.append(f"ELO {e.get('elo_number', '')}. [{e.get('related_performance', '')}] {e.get('elo', '')}")
        lines.append(f"  Bloom: {e.get('bloom_level', '')} | Metode: {e.get('delivery_method', '')} | Durasi: {e.get('duration_minutes', '')} menit")
    lines.append(f"\nTotal Estimasi Durasi: {total_dur} menit")

    return "\n".join(lines)


def _syllabus_to_context_header(output_json: dict) -> str:
    """Flatten only profil + TLO + PO (without ELO) — used as shared context in batch processing."""
    lines = []
    profile = output_json.get("org_profile", {})
    lines.append(f"Perusahaan: {profile.get('organization_name', '-')} | Industri: {profile.get('industry', '-')}")
    lines.append(f"Tipe Course: {output_json.get('course_type', '-')}")
    if output_json.get("levels_covered"):
        lines.append(f"Level: {' → '.join(output_json['levels_covered'])}")
    if output_json.get("current_condition"):
        lines.append(f"Kondisi Saat Ini: {output_json['current_condition']}")
    if output_json.get("desired_condition"):
        lines.append(f"Kondisi Diinginkan: {output_json['desired_condition']}")
    lines.append("")
    lines.append("TLO:")
    for t in output_json.get("tlos", []):
        lines.append(f"  TLO {t.get('tlo_number', '')}. {t.get('tlo', '')}")
    lines.append("")
    lines.append("Performance Objectives:")
    for p in output_json.get("performance_objectives", []):
        lines.append(f"  PO {p.get('perf_number', '')}. {p.get('performance_objective', '')}")
    return "\n".join(lines)


@router.post("/decompose-from-syllabus")
def decompose_from_syllabus(
    req: DecomposeFromSyllabusRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Decompose micro modules based on a saved syllabus — processes all ELOs in batches."""
    from app.db.models import Syllabus, DocumentChunk
    user_id = current_user["user_id"]

    syllabus = db.query(Syllabus).filter(
        Syllabus.id == req.syllabus_id,
        Syllabus.user_id == user_id,
    ).first()
    if not syllabus:
        raise HTTPException(status_code=404, detail="Silabus tidak ditemukan.")

    if not req.guide_document_id:
        raise HTTPException(status_code=422, detail="Panduan microlearning wajib dipilih.")

    output_json = syllabus.output_json or {}
    elos = output_json.get("elos", [])
    if not elos:
        raise HTTPException(status_code=422, detail="Silabus tidak memiliki ELO. Pastikan silabus sudah lengkap.")

    # Build header context (profil + TLO + PO) — dipakai di semua batch
    header_context = _syllabus_to_context_header(output_json)

    # Guide context
    guide_text = ""
    guide_chunks = db.query(DocumentChunk).filter(
        DocumentChunk.document_id == req.guide_document_id
    ).order_by(DocumentChunk.chunk_index).all()
    if guide_chunks:
        guide_text = "\n\n".join(c.chunk_text for c in guide_chunks[:4])

    system_prompt = """Kamu adalah Instructional Designer spesialis microlearning.
Tugasmu adalah membuat modul mikro berdasarkan daftar ELO yang diberikan.

WAJIB: Buat TEPAT SATU modul mikro untuk SETIAP ELO dalam daftar. Jangan skip ELO manapun.

Setiap modul mikro harus:
- Berdiri sendiri (standalone)
- Fokus pada ELO yang menjadi dasarnya
- Dapat diselesaikan dalam 5-15 menit

Format output WAJIB dalam JSON array (jumlah item = jumlah ELO yang diberikan):
[
  {
    "module_number": 1,
    "title": "judul modul mikro spesifik",
    "specific_objective": "setelah menyelesaikan modul ini, peserta dapat...",
    "content_summary": "ringkasan konten dalam 2-3 kalimat",
    "delivery_format": "Video|Infographic|Quiz|Case Study|Simulation|Workshop|Hands-on Lab",
    "duration_minutes": 10,
    "related_elo": "nomor dan teks ELO yang menjadi dasar modul ini"
  }
]"""

    class MicroModuleFromSyllabus(MicroModuleItem):
        related_elo: str = ""

    # Proses ELO dalam batch 8 agar tidak melebihi token limit
    BATCH_SIZE = 8
    all_items = []
    module_counter = 1

    for batch_start in range(0, len(elos), BATCH_SIZE):
        batch_elos = elos[batch_start:batch_start + BATCH_SIZE]

        elo_list = "\n".join(
            f"ELO {e.get('elo_number', batch_start + i + 1)}. [{e.get('related_performance', '')}] {e.get('elo', '')}\n"
            f"  Bloom: {e.get('bloom_level', '')} | Metode: {e.get('delivery_method', '')} | Durasi: {e.get('duration_minutes', '')} menit"
            for i, e in enumerate(batch_elos)
        )

        user_message = (
            f"{f'Panduan Microlearning:{chr(10)}{guide_text}{chr(10)}{chr(10)}' if guide_text else ''}"
            f"Konteks Silabus:\n{header_context}\n\n"
            f"Daftar ELO yang HARUS dibuatkan modul mikro (buat {len(batch_elos)} modul, "
            f"mulai dari module_number {module_counter}):\n{elo_list}\n\n"
            f"Buat TEPAT {len(batch_elos)} modul mikro, satu per ELO di atas."
        )

        raw = call_llm(system_prompt, user_message, max_tokens=16000)

        try:
            batch_items = parse_llm_json(raw, MicroModuleFromSyllabus)
        except Exception as e:
            raise HTTPException(status_code=422, detail=f"Gagal memparse batch ELO {batch_start+1}-{batch_start+len(batch_elos)}: {str(e)}")

        # Renumber module_number secara berurutan
        for item in batch_items:
            item["module_number"] = module_counter
            module_counter += 1
            all_items.append(item)

    # Simpan semua modul ke DB
    saved = []
    for item in all_items:
        emb = embed_text(f"{item['title']} {item['specific_objective']}")
        module = MicroModule(
            user_id=user_id,
            source_document_id=None,
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
    return {
        "modules": saved,
        "syllabus": {
            "id": str(syllabus.id),
            "topic": syllabus.topic,
            "output_json": syllabus.output_json,
        },
    }


# ── Decompose without syllabus (from profile doc + level + course type) ───────

LEVEL_MAP = {1: "Intro", 2: "Beginner", 3: "Intermediate", 4: "Advanced", 5: "Mastery"}


class DecomposeWithoutSyllabusRequest(BaseModel):
    profile_document_id: str
    guide_document_id: str
    course_type: str
    start_level: int = 1


@router.post("/decompose-without-syllabus")
def decompose_without_syllabus(
    req: DecomposeWithoutSyllabusRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Generate micro modules from org profile doc + course type + level (no syllabus needed)."""
    from app.db.models import Document
    from app.services.vector_search import search_similar_chunks
    import json, re
    user_id = current_user["user_id"]

    # Validate profile doc
    profile_doc = db.query(Document).filter(
        Document.id == req.profile_document_id,
        Document.user_id == user_id,
    ).first()
    if not profile_doc:
        raise HTTPException(status_code=404, detail="Dokumen profil tidak ditemukan.")

    # ── Step 1: Extract structured org profile ────────────────────────────────
    profile_chunks = search_similar_chunks(
        "profil perusahaan visi misi strategi bisnis kompetensi industri",
        db, top_k=8, document_ids=[req.profile_document_id]
    )
    profile_context_texts = [c["chunk_text"] for c in profile_chunks]

    org_system_prompt = """Kamu adalah Learning Strategist.
Baca dokumen profil perusahaan dan hasilkan ringkasan terstruktur.

ATURAN: Cari entitas yang namanya mengandung "PT" sebagai perusahaan utama.
Abaikan nama lembaga/vendor/mitra lain.

Format output WAJIB dalam JSON:
{
  "organization_name": "nama perusahaan",
  "industry": "industri/sektor",
  "vision": "visi perusahaan",
  "mission": "misi perusahaan",
  "strategic_priorities": ["prioritas 1", "prioritas 2"],
  "core_competencies": ["kompetensi 1", "kompetensi 2"],
  "learning_context": "narasi singkat konteks pembelajaran"
}"""

    org_raw = call_llm(org_system_prompt,
                       "Analisis profil perusahaan berikut dan buat ringkasan terstruktur.",
                       profile_context_texts)
    cleaned = org_raw.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-z]*\n?", "", cleaned)
        cleaned = re.sub(r"\n?```$", "", cleaned)
    try:
        org_profile = json.loads(cleaned)
    except Exception:
        # Fallback: minimal profile
        org_profile = {
            "organization_name": profile_doc.filename,
            "industry": "-",
            "vision": "-",
            "mission": "-",
            "strategic_priorities": [],
            "core_competencies": [],
            "learning_context": "",
        }

    # ── Step 2: Build context for module generation ───────────────────────────
    profile_summary = (
        f"Perusahaan: {org_profile.get('organization_name', '-')}\n"
        f"Industri: {org_profile.get('industry', '-')}\n"
        f"Visi: {org_profile.get('vision', '-')}\n"
        f"Misi: {org_profile.get('mission', '-')}\n"
        f"Prioritas Strategis: {', '.join(org_profile.get('strategic_priorities', []))}\n"
        f"Kompetensi Inti: {', '.join(org_profile.get('core_competencies', []))}\n"
        f"Konteks Pembelajaran: {org_profile.get('learning_context', '-')}"
    )

    # Get guide context
    guide_chunks = db.query(DocumentChunk).filter(
        DocumentChunk.document_id == req.guide_document_id
    ).order_by(DocumentChunk.chunk_index).all()
    guide_text = "\n\n".join(c.chunk_text for c in guide_chunks[:4]) if guide_chunks else ""

    levels = [f"Level {l} ({LEVEL_MAP[l]})" for l in range(req.start_level, 6)]
    levels_str = ", ".join(levels)

    system_prompt = f"""Kamu adalah Instructional Designer spesialis microlearning.
Tugasmu adalah membuat modul mikro pelatihan berdasarkan profil perusahaan, tipe course, dan level peserta.

TOPIK COURSE: "{req.course_type}"
LEVEL YANG DICAKUP: {levels_str}

Buat modul mikro yang:
- Relevan dengan topik course dan konteks spesifik perusahaan
- Mencerminkan progression dari {LEVEL_MAP[req.start_level]} hingga Mastery
- Berdiri sendiri (standalone), 5-15 menit per modul
- Konten harus mencerminkan industri dan kebutuhan perusahaan

Format output WAJIB dalam JSON array:
[
  {{
    "module_number": 1,
    "title": "judul modul mikro spesifik",
    "specific_objective": "setelah menyelesaikan modul ini, peserta dapat...",
    "content_summary": "ringkasan konten dalam 2-3 kalimat",
    "delivery_format": "Video|Infographic|Quiz|Case Study|Simulation|Workshop|Hands-on Lab",
    "duration_minutes": 10,
    "related_elo": "level dan sub-topik yang menjadi dasar modul ini"
  }}
]
Hasilkan minimal {len(levels) * 4} modul yang mencakup semua level: {levels_str}."""

    user_message = (
        f"{f'Panduan Microlearning:{chr(10)}{guide_text}{chr(10)}{chr(10)}' if guide_text else ''}"
        f"Profil Perusahaan:\n{profile_summary}\n\n"
        f"Topik Course: {req.course_type}\n"
        f"Level yang dicakup: {levels_str}\n\n"
        f"Buatkan modul mikro yang komprehensif, spesifik sesuai konteks perusahaan dan topik di atas."
    )

    raw = call_llm(system_prompt, user_message, max_tokens=16000)

    class MicroModuleManual(MicroModuleItem):
        related_elo: str = ""

    try:
        items = parse_llm_json(raw, MicroModuleManual)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Failed to parse AI response: {str(e)}")

    saved = []
    for item in items:
        emb = embed_text(f"{item['title']} {item['specific_objective']}")
        module = MicroModule(
            user_id=user_id,
            source_document_id=req.profile_document_id,
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
    return {
        "modules": saved,
        "org_profile": org_profile,
        "course_type": req.course_type,
        "levels_covered": levels,
    }
