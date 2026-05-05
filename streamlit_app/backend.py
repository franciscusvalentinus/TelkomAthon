"""
Backend logic — replaces all FastAPI routers.
All functions take a db session and user_id directly.
"""
import io
import json
import re
import uuid
import shutil
import tempfile
import os
from typing import List, Optional
from pydantic import BaseModel

from streamlit_app.db.models import (
    Document, DocumentChunk, Syllabus, MicroModule, Recommendation
)
from streamlit_app.services.ai_agent import call_llm, parse_llm_json
from streamlit_app.services.embedder import embed_text, embed_chunks
from streamlit_app.services.parser import parse_document_bytes, chunk_text
from streamlit_app.services.vector_search import search_similar_chunks


# ── Helpers ───────────────────────────────────────────────────────────────────

LEVEL_MAP = {1: "Intro", 2: "Beginner", 3: "Intermediate", 4: "Advanced", 5: "Mastery"}


def _parse_json_safe(text: str) -> dict:
    cleaned = text.strip()
    cleaned = re.sub(r"^```[a-zA-Z]*\s*", "", cleaned)
    cleaned = re.sub(r"\s*```\s*$", "", cleaned).strip()
    return json.loads(cleaned)


def levels_description(start_level: int) -> str:
    return ", ".join(f"Level {l} ({LEVEL_MAP[l]})" for l in range(start_level, 6))


# ── Upload ────────────────────────────────────────────────────────────────────

def upload_document(db, user_id: str, file_bytes: bytes, filename: str) -> dict:
    """Parse, chunk, embed and save a document. Returns document info dict."""
    ext = filename.rsplit(".", 1)[-1].lower()
    allowed = {"pdf", "pptx", "docx", "xlsx"}
    if ext not in allowed:
        raise ValueError(f"Tipe file tidak didukung: {ext}")

    raw_text = parse_document_bytes(file_bytes, ext)

    doc = Document(user_id=user_id, filename=filename, file_type=ext, content=raw_text)
    db.add(doc)
    db.commit()
    db.refresh(doc)

    chunks = chunk_text(raw_text)
    vectors = embed_chunks(chunks)
    for idx, (chunk, vector) in enumerate(zip(chunks, vectors)):
        db.add(DocumentChunk(
            document_id=doc.id,
            chunk_text=chunk,
            embedding=vector,
            chunk_index=idx,
        ))
    db.commit()
    return {"document_id": str(doc.id), "filename": filename, "chunks_created": len(chunks)}


def list_documents(db, user_id: str) -> list:
    docs = db.query(Document).filter(Document.user_id == user_id).order_by(Document.uploaded_at.desc()).all()
    return [
        {"document_id": str(d.id), "filename": d.filename, "file_type": d.file_type, "uploaded_at": d.uploaded_at}
        for d in docs
    ]


# ── Syllabus ──────────────────────────────────────────────────────────────────

def analyze_org_from_docs(db, user_id: str, document_ids: List[str]) -> dict:
    chunks = search_similar_chunks(
        "profil perusahaan visi misi strategi bisnis kompetensi",
        db, top_k=8, document_ids=document_ids
    )
    if not chunks:
        raise ValueError("Tidak ada konten yang ditemukan dari dokumen yang dipilih.")
    context_texts = [c["chunk_text"] for c in chunks]

    system_prompt = """Kamu adalah Learning Strategist.
Tugasmu adalah membaca dokumen profil perusahaan dan menghasilkan ringkasan terstruktur.

ATURAN PENTING: Cari entitas yang namanya mengandung kata "PT" — itulah perusahaan utama.
Abaikan nama lembaga/vendor/mitra lain.

Format output WAJIB dalam JSON:
{
  "organization_name": "nama perusahaan",
  "industry": "industri/sektor",
  "vision": "visi perusahaan",
  "mission": "misi perusahaan",
  "strategic_priorities": ["prioritas 1", "prioritas 2"],
  "core_competencies": ["kompetensi 1", "kompetensi 2"],
  "learning_context": "narasi singkat 2-3 kalimat tentang konteks pembelajaran",
  "recommended_course_types": ["tipe course yang paling relevan"]
}"""

    raw = call_llm(system_prompt, "Analisis dokumen profil perusahaan berikut.", context_texts)
    try:
        return _parse_json_safe(raw)
    except Exception:
        retry = call_llm(
            "You are a JSON formatter. Return ONLY valid JSON object, no explanation, no markdown.",
            f"Fix this and return only the valid JSON object:\n{raw}"
        )
        return _parse_json_safe(retry)


def analyze_org_manual(company_name: str, industry: str) -> dict:
    system_prompt = """Kamu adalah Learning Strategist yang berpengalaman.
Susun profil perusahaan berdasarkan nama dan industri yang diberikan.

Format output WAJIB dalam JSON:
{
  "organization_name": "nama perusahaan persis seperti yang diberikan",
  "industry": "industri/sektor",
  "vision": "contoh visi yang relevan",
  "mission": "contoh misi yang relevan",
  "strategic_priorities": ["prioritas strategis yang umum di industri ini"],
  "core_competencies": ["kompetensi inti yang umumnya dibutuhkan"],
  "learning_context": "narasi singkat 2-3 kalimat tentang konteks pembelajaran",
  "recommended_course_types": ["tipe course yang paling relevan untuk industri ini"]
}"""
    raw = call_llm(system_prompt, f"Nama Perusahaan: {company_name}\nIndustri: {industry}")
    try:
        return _parse_json_safe(raw)
    except Exception:
        retry = call_llm(
            "You are a JSON formatter. Return ONLY valid JSON object, no explanation, no markdown.",
            f"Fix this and return only the valid JSON object:\n{raw}"
        )
        return _parse_json_safe(retry)


class TLOItem(BaseModel):
    tlo_number: int
    tlo: str
    rationale: str


def generate_tlo(
    db, user_id: str, course_type: str, org_profile: dict,
    document_ids: List[str], start_level: int = 1,
    current_condition: str = "", desired_condition: str = ""
) -> list:
    chunks = search_similar_chunks(
        f"profil bisnis strategi {org_profile.get('industry', '')}",
        db, top_k=4, document_ids=document_ids or None
    )
    context_texts = [c["chunk_text"] for c in chunks]
    levels_desc = levels_description(start_level)
    level_count = 6 - start_level

    condition_context = ""
    if current_condition or desired_condition:
        condition_context = (
            f"\nKONTEKS KONDISI PESERTA:\n"
            f"- Kondisi Saat Ini: {current_condition or 'tidak disebutkan'}\n"
            f"- Kondisi yang Diinginkan: {desired_condition or 'tidak disebutkan'}\n"
            f"TLO harus menjembatani gap antara kondisi saat ini dan kondisi yang diinginkan."
        )

    system_prompt = f"""Kamu adalah Learning Design Expert.
Tugasmu adalah membuat Terminal Learning Objectives (TLO) untuk program pelatihan bertopik SPESIFIK berikut:

TOPIK COURSE: "{course_type}"
LEVEL YANG DICAKUP: {levels_desc}
{condition_context}
TLO WAJIB membahas konten yang berkaitan langsung dengan "{course_type}".
TLO harus mencerminkan progression dari {LEVEL_MAP[start_level]} hingga Mastery.

Format output WAJIB dalam JSON array:
[
  {{
    "tlo_number": 1,
    "tlo": "Setelah mengikuti program ini, peserta mampu [kata kerja] [objek spesifik terkait {course_type}]",
    "rationale": "alasan mengapa TLO ini relevan"
  }}
]
Hasilkan {max(5, level_count * 2)} TLO yang beragam dan spesifik."""

    org_summary = (
        f"Perusahaan: {org_profile.get('organization_name', '')}\n"
        f"Industri: {org_profile.get('industry', '')}\n"
        f"Prioritas Strategis: {', '.join(org_profile.get('strategic_priorities', []))}\n"
        f"Kompetensi Inti: {', '.join(org_profile.get('core_competencies', []))}"
    )
    user_message = (
        f"Topik Course: {course_type}\nLevel: {levels_desc}\n\n"
        f"Profil Perusahaan:\n{org_summary}\n"
    )
    if current_condition:
        user_message += f"\nKondisi Saat Ini: {current_condition}"
    if desired_condition:
        user_message += f"\nKondisi yang Diinginkan: {desired_condition}"

    raw = call_llm(system_prompt, user_message, context_texts)
    return parse_llm_json(raw, TLOItem)


class PerfItem(BaseModel):
    perf_number: int
    related_tlo: str
    performance_objective: str
    condition: str
    standard: str


def generate_performance(
    db, user_id: str, selected_tlos: list, org_profile: dict,
    document_ids: List[str], start_level: int = 1
) -> list:
    tlo_text = "\n".join(f"- TLO {t['tlo_number']}: {t['tlo']}" for t in selected_tlos)
    chunks = search_similar_chunks(
        f"profil bisnis strategi {org_profile.get('industry', '')}",
        db, top_k=3, document_ids=document_ids or None
    )
    context_texts = [c["chunk_text"] for c in chunks]
    levels_desc = levels_description(start_level)

    system_prompt = f"""Kamu adalah Instructional Designer.
Tugasmu adalah membuat PCS berdasarkan TLO yang diberikan.
LEVEL YANG DICAKUP: {levels_desc}

PCS harus memiliki tiga komponen: Perilaku, Kondisi, Standar.

Format output WAJIB dalam JSON array:
[
  {{
    "perf_number": 1,
    "related_tlo": "TLO 1",
    "performance_objective": "Peserta dapat [perilaku spesifik]",
    "condition": "Diberikan [kondisi/tools/skenario]",
    "standard": "dengan [kriteria terukur]"
  }}
]
Hasilkan 2-3 PCS per TLO."""

    user_message = (
        f"TLO yang dipilih:\n{tlo_text}\n\n"
        f"Konteks: {org_profile.get('organization_name', '')} — {org_profile.get('industry', '')}"
    )
    raw = call_llm(system_prompt, user_message, context_texts)
    return parse_llm_json(raw, PerfItem)


class ELOItem(BaseModel):
    elo_number: int
    related_performance: str
    elo: str
    bloom_level: str
    delivery_method: str
    duration_minutes: int


def generate_elo(
    db, user_id: str, selected_tlos: list, selected_performances: list,
    org_profile: dict, document_ids: List[str], start_level: int = 1
) -> list:
    tlo_text = "\n".join(f"- {t['tlo']}" for t in selected_tlos)
    perf_text = "\n".join(f"- PCS {p['perf_number']}: {p['performance_objective']}" for p in selected_performances)
    chunks = search_similar_chunks(
        f"profil bisnis strategi {org_profile.get('industry', '')}",
        db, top_k=3, document_ids=document_ids or None
    )
    context_texts = [c["chunk_text"] for c in chunks]
    levels_desc = levels_description(start_level)

    system_prompt = f"""Kamu adalah Instructional Designer spesialis kurikulum.
Tugasmu adalah membuat Enabling Learning Objectives (ELO) yang mendukung pencapaian PCS.
LEVEL YANG DICAKUP: {levels_desc}

Format output WAJIB dalam JSON array:
[
  {{
    "elo_number": 1,
    "related_performance": "PCS 1",
    "elo": "Peserta dapat [kata kerja Bloom] [konten spesifik]",
    "bloom_level": "Remember|Understand|Apply|Analyze|Evaluate|Create",
    "delivery_method": "Video|Reading|Quiz|Case Study|Role Play|Simulation|Workshop|Hands-on Lab",
    "duration_minutes": 15
  }}
]
Hasilkan 2-4 ELO per PCS."""

    user_message = (
        f"TLO (konteks):\n{tlo_text}\n\n"
        f"PCS (jadikan dasar ELO):\n{perf_text}\n\n"
        f"Konteks: {org_profile.get('organization_name', '')} — {org_profile.get('industry', '')}"
    )
    raw = call_llm(system_prompt, user_message, context_texts)
    return parse_llm_json(raw, ELOItem)


def finalize_syllabus(
    db, user_id: str, course_type: str, org_profile: dict,
    selected_tlos: list, selected_performances: list, selected_elos: list,
    start_level: int = 1, current_condition: str = "", desired_condition: str = ""
) -> dict:
    output = {
        "org_profile": org_profile,
        "course_type": course_type,
        "start_level": start_level,
        "levels_covered": [f"Level {l} — {LEVEL_MAP[l]}" for l in range(start_level, 6)],
        "current_condition": current_condition,
        "desired_condition": desired_condition,
        "tlos": selected_tlos,
        "performance_objectives": selected_performances,
        "elos": selected_elos,
    }
    topic = f"{course_type} — {org_profile.get('organization_name', 'Org')}"
    syllabus = Syllabus(user_id=user_id, topic=topic, level="Multi-level", output_json=output)
    db.add(syllabus)
    db.commit()
    db.refresh(syllabus)
    return {"syllabus_id": str(syllabus.id), "result": output}


def list_syllabi(db, user_id: str) -> list:
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
            "created_at": s.created_at.isoformat() if s.created_at else "",
            "output_json": s.output_json,
        }
        for s in syllabi
    ]


# ── Decompose ─────────────────────────────────────────────────────────────────

class MicroModuleItem(BaseModel):
    module_number: int
    title: str
    specific_objective: str
    content_summary: str
    delivery_format: str
    duration_minutes: int


class MicroModuleFromSyllabus(MicroModuleItem):
    related_elo: str = ""


DECOMPOSE_SYSTEM_PROMPT = """Kamu adalah Instructional Designer spesialis microlearning.
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


def _syllabus_to_context_header(output_json: dict) -> str:
    lines = []
    profile = output_json.get("org_profile", {})
    lines.append(f"Perusahaan: {profile.get('organization_name', '-')} | Industri: {profile.get('industry', '-')}")
    lines.append(f"Tipe Course: {output_json.get('course_type', '-')}")
    if output_json.get("levels_covered"):
        lines.append(f"Level: {' → '.join(output_json['levels_covered'])}")
    lines.append("")
    lines.append("TLO:")
    for t in output_json.get("tlos", []):
        lines.append(f"  TLO {t.get('tlo_number', '')}. {t.get('tlo', '')}")
    lines.append("")
    lines.append("Performance Objectives:")
    for p in output_json.get("performance_objectives", []):
        lines.append(f"  PO {p.get('perf_number', '')}. {p.get('performance_objective', '')}")
    return "\n".join(lines)


def decompose_from_syllabus(
    db, user_id: str, syllabus_id: str, guide_document_id: str
) -> dict:
    syllabus = db.query(Syllabus).filter(
        Syllabus.id == syllabus_id, Syllabus.user_id == user_id
    ).first()
    if not syllabus:
        raise ValueError("Silabus tidak ditemukan.")

    output_json = syllabus.output_json or {}
    elos = output_json.get("elos", [])
    if not elos:
        raise ValueError("Silabus tidak memiliki ELO. Pastikan silabus sudah lengkap.")

    header_context = _syllabus_to_context_header(output_json)

    guide_text = ""
    guide_chunks = db.query(DocumentChunk).filter(
        DocumentChunk.document_id == guide_document_id
    ).order_by(DocumentChunk.chunk_index).all()
    if guide_chunks:
        guide_text = "\n\n".join(c.chunk_text for c in guide_chunks[:4])

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
        raw = call_llm(DECOMPOSE_SYSTEM_PROMPT, user_message, max_tokens=16000)
        batch_items = parse_llm_json(raw, MicroModuleFromSyllabus)
        for item in batch_items:
            item["module_number"] = module_counter
            module_counter += 1
            all_items.append(item)

    for item in all_items:
        emb = embed_text(f"{item['title']} {item['specific_objective']}")
        db.add(MicroModule(
            user_id=user_id,
            source_document_id=None,
            title=item["title"],
            objective=item["specific_objective"],
            summary=item["content_summary"],
            delivery_format=item["delivery_format"],
            duration_minutes=item["duration_minutes"],
            embedding=emb,
        ))
    db.commit()

    return {
        "modules": all_items,
        "syllabus": {"id": str(syllabus.id), "topic": syllabus.topic, "output_json": syllabus.output_json},
    }


# ── Quiz ──────────────────────────────────────────────────────────────────────

class QuizItem(BaseModel):
    nomor: int
    elo_reference: str
    pertanyaan: str
    pilihan: dict
    jawaban_benar: str
    penjelasan: str


QUIZ_SYSTEM_PROMPT = """Kamu adalah Instructional Designer spesialis assessment.
Tugasmu adalah membuat soal pilihan ganda berkualitas tinggi berdasarkan ELO yang diberikan.

Format output WAJIB dalam JSON array:
[
  {
    "nomor": 1,
    "elo_reference": "ELO X — judul ELO",
    "pertanyaan": "teks pertanyaan",
    "pilihan": {"A": "...", "B": "...", "C": "...", "D": "..."},
    "jawaban_benar": "A",
    "penjelasan": "penjelasan singkat mengapa jawaban ini benar"
  }
]"""


def generate_quiz(db, user_id: str, syllabus_id: str, mode: str, jumlah_soal: int) -> dict:
    syllabus = db.query(Syllabus).filter(
        Syllabus.id == syllabus_id, Syllabus.user_id == user_id
    ).first()
    if not syllabus or not syllabus.output_json:
        raise ValueError("Silabus tidak ditemukan.")

    output = syllabus.output_json
    elos = output.get("elos", [])
    quiz_elos = [e for e in elos if "quiz" in e.get("delivery_method", "").lower()]

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
        raw = call_llm(QUIZ_SYSTEM_PROMPT, user_msg, max_tokens=4096)
        return parse_llm_json(raw, QuizItem)

    if mode == "prepost":
        return {
            "has_quiz_elos": True,
            "quiz_elos": [e.get("elo_number") for e in quiz_elos],
            "mode": "prepost",
            "pre_test": _generate("Pre-test", jumlah_soal),
            "post_test": _generate("Post-test", jumlah_soal),
        }
    else:
        return {
            "has_quiz_elos": True,
            "quiz_elos": [e.get("elo_number") for e in quiz_elos],
            "mode": "single",
            "quiz": _generate("Quiz", jumlah_soal),
        }


# ── Recommend ─────────────────────────────────────────────────────────────────

class RecommendationItem(BaseModel):
    rank: int
    module_title: str
    relevance_reason: str
    priority: str
    estimated_duration_minutes: int


RECOMMEND_SYSTEM_PROMPT = """Kamu adalah Learning Advisor yang berpengalaman.
Tugasmu adalah merekomendasikan modul mikro yang paling relevan berdasarkan profil dan gap kompetensi peserta.

Urutkan rekomendasi dari modul yang paling fundamental ke yang paling advanced.
Jelaskan mengapa setiap modul relevan dengan gap dan profil peserta.

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


def recommend(
    db, user_id: str, participant_name: str, gap_description: str,
    top_k: int = 5, syllabus_id: Optional[str] = None,
    jabatan: str = "", lama_bekerja: str = "", departemen: str = "",
    pendidikan_terakhir: str = "", preferensi_belajar: str = "",
    waktu_belajar_per_minggu: str = ""
) -> dict:
    syllabus_context = ""
    syllabus_elos = []
    if syllabus_id:
        syllabus = db.query(Syllabus).filter(
            Syllabus.id == syllabus_id, Syllabus.user_id == user_id
        ).first()
        if syllabus and syllabus.output_json:
            output = syllabus.output_json
            profile = output.get("org_profile", {})
            syllabus_elos = output.get("elos", [])
            levels = output.get("levels_covered", [])
            syllabus_context = (
                f"\nKonteks Silabus Pelatihan:\n"
                f"Perusahaan: {profile.get('organization_name', '-')} | Industri: {profile.get('industry', '-')}\n"
                f"Tipe Course: {output.get('course_type', '-')}\n"
                f"Level: {' → '.join(levels)}\n\n"
                f"Enabling Learning Objectives (ELO):\n"
                + "\n".join(
                    f"- ELO {e.get('elo_number', '')}. {e.get('elo', '')} "
                    f"(Bloom: {e.get('bloom_level', '')}, Metode: {e.get('delivery_method', '')}, "
                    f"{e.get('duration_minutes', '')} menit)"
                    for e in syllabus_elos
                )
                + "\n\nGunakan ELO di atas sebagai katalog modul.\n"
            )

    user_message = f"Profil Peserta: {participant_name}\nGap Kompetensi: {gap_description}\n"
    for label, val in [
        ("Jabatan", jabatan), ("Departemen", departemen), ("Lama Bekerja", lama_bekerja),
        ("Pendidikan Terakhir", pendidikan_terakhir), ("Preferensi Belajar", preferensi_belajar),
        ("Waktu Belajar per Minggu", waktu_belajar_per_minggu),
    ]:
        if val and val.strip():
            user_message += f"{label}: {val}\n"
    if syllabus_context:
        user_message += syllabus_context
    user_message += (
        f"\n{'Generate ' + str(top_k) + ' rekomendasi modul mikro dari ELO silabus yang paling relevan.' if syllabus_elos else 'Generate ' + str(top_k) + ' rekomendasi modul mikro yang relevan berdasarkan gap kompetensi peserta.'}"
        "\nRekomendasikan learning path yang paling relevan untuk peserta ini."
    )

    raw = call_llm(RECOMMEND_SYSTEM_PROMPT, user_message)
    items = parse_llm_json(raw, RecommendationItem)

    rec = Recommendation(
        user_id=user_id, participant_name=participant_name,
        gap_input=gap_description, recommended_modules=items,
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return {"recommendation_id": str(rec.id), "recommendations": items}


# ── Bulk Recommend ────────────────────────────────────────────────────────────

BULK_SYSTEM_PROMPT = """Kamu adalah Learning Advisor yang berpengalaman.
Tugasmu adalah merekomendasikan modul mikro yang paling relevan berdasarkan profil dan gap kompetensi peserta.

Tentukan recommended_level (1–5) yang paling sesuai untuk peserta:
- Level 1 (Intro): Belum pernah terpapar topik
- Level 2 (Beginner): Sudah mengenal dasar
- Level 3 (Intermediate): Sudah praktik, perlu pendalaman
- Level 4 (Advanced): Sudah mahir, perlu spesialisasi
- Level 5 (Mastery): Expert, perlu inovasi

Format output WAJIB dalam JSON object:
{
  "recommended_level": 2,
  "level_label": "Beginner",
  "modules": [
    {
      "rank": 1,
      "module_title": "judul modul mikro",
      "relevance_reason": "alasan relevansi",
      "priority": "High|Medium|Low",
      "estimated_duration_minutes": 10
    }
  ]
}"""


def bulk_recommend(
    db, user_id: str, participants: list, top_k: int = 5,
    syllabus_id: Optional[str] = None
) -> dict:
    bulk_session_id = str(uuid.uuid4())

    syllabus_context, syllabus_elos = "", []
    if syllabus_id:
        syllabus = db.query(Syllabus).filter(
            Syllabus.id == syllabus_id, Syllabus.user_id == user_id
        ).first()
        if syllabus and syllabus.output_json:
            output = syllabus.output_json
            profile = output.get("org_profile", {})
            syllabus_elos = output.get("elos", [])
            levels = output.get("levels_covered", [])
            syllabus_context = (
                f"\nKonteks Silabus:\n"
                f"Perusahaan: {profile.get('organization_name', '-')} | Industri: {profile.get('industry', '-')}\n"
                f"Tipe Course: {output.get('course_type', '-')}\n"
                f"Level: {' → '.join(levels)}\n\n"
                f"ELO:\n"
                + "\n".join(
                    f"- ELO {e.get('elo_number', '')}. {e.get('elo', '')} "
                    f"(Bloom: {e.get('bloom_level', '')}, Metode: {e.get('delivery_method', '')}, "
                    f"{e.get('duration_minutes', '')} menit)"
                    for e in syllabus_elos
                )
                + "\n\nGunakan ELO di atas sebagai katalog modul.\n"
            )

    results, errors = [], []
    for p in participants:
        try:
            profile_lines = [f"Nama: {p['nama']}", f"Gap Kompetensi: {p['gap_kompetensi']}"]
            for col in ["jabatan", "departemen", "lama_bekerja", "pendidikan_terakhir",
                        "preferensi_belajar", "waktu_belajar_per_minggu"]:
                if p.get(col):
                    profile_lines.append(f"{col.replace('_', ' ').title()}: {p[col]}")

            msg = "Profil Peserta:\n" + "\n".join(profile_lines)
            if syllabus_context:
                msg += "\n" + syllabus_context
            msg += (
                f"\n{'Generate ' + str(top_k) + ' rekomendasi modul mikro dari ELO silabus.' if syllabus_elos else 'Generate ' + str(top_k) + ' rekomendasi modul mikro yang relevan.'}"
                "\nRekomendasikan learning path yang paling relevan untuk peserta ini."
            )

            raw = call_llm(BULK_SYSTEM_PROMPT, msg)
            cleaned = raw.strip()
            cleaned = re.sub(r"^```[a-zA-Z]*\s*", "", cleaned)
            cleaned = re.sub(r"\s*```\s*$", "", cleaned).strip()
            outer = json.loads(cleaned)

            recommended_level = outer.get("recommended_level")
            level_label = outer.get("level_label", "")
            items = [RecommendationItem(**m).model_dump() for m in outer.get("modules", [])]

            rec = Recommendation(
                user_id=user_id, participant_name=p["nama"],
                gap_input=p["gap_kompetensi"], recommended_modules=items,
                bulk_session_id=bulk_session_id,
            )
            db.add(rec)
            db.commit()
            db.refresh(rec)

            results.append({
                "recommendation_id": str(rec.id),
                "nama": p["nama"],
                "jabatan": p.get("jabatan"),
                "departemen": p.get("departemen"),
                "gap_kompetensi": p["gap_kompetensi"],
                "recommended_level": recommended_level,
                "level_label": level_label,
                "recommendations": items,
            })
        except Exception as e:
            errors.append({"nama": p.get("nama", "?"), "error": str(e)})

    return {
        "bulk_session_id": bulk_session_id,
        "total_processed": len(results),
        "total_errors": len(errors),
        "results": results,
        "errors": errors,
    }


# ── Career Roadmap ────────────────────────────────────────────────────────────

class RoadmapPhase(BaseModel):
    phase_number: int
    phase_name: str
    month_range: str
    focus: str
    modules: List[dict]


def generate_career_roadmap(
    db, user_id: str, participant_name: str, current_position: str,
    target_position: str, timeline_months: int = 12,
    additional_context: str = "", syllabus_id: Optional[str] = None
) -> dict:
    if timeline_months <= 3:
        num_phases = 2
    elif timeline_months <= 6:
        num_phases = 3
    else:
        num_phases = min(4, timeline_months // 3)

    months_per_phase = timeline_months // num_phases

    syllabus_context = ""
    if syllabus_id:
        syllabus = db.query(Syllabus).filter(
            Syllabus.id == syllabus_id, Syllabus.user_id == user_id
        ).first()
        if syllabus and syllabus.output_json:
            output = syllabus.output_json
            profile = output.get("org_profile", {})
            elos = output.get("elos", [])
            levels = output.get("levels_covered", [])
            syllabus_context = (
                f"\nKonteks Silabus:\n"
                f"Perusahaan: {profile.get('organization_name', '-')} | Industri: {profile.get('industry', '-')}\n"
                f"Tipe Course: {output.get('course_type', '-')}\n"
                f"Level: {' → '.join(levels)}\n\n"
                f"ELO (gunakan sebagai referensi kompetensi):\n"
                + "\n".join(
                    f"- ELO {e.get('elo_number', '')}. {e.get('elo', '')} "
                    f"(Bloom: {e.get('bloom_level', '')}, Metode: {e.get('delivery_method', '')}, "
                    f"{e.get('duration_minutes', '')} menit)"
                    for e in elos
                )
                + "\n\nGunakan ELO di atas sebagai referensi kompetensi yang perlu dikuasai.\n"
            )

    system_prompt = f"""Kamu adalah Career Development Advisor yang berpengalaman.
Tugasmu adalah menyusun learning path roadmap karir yang terstruktur dan diprioritaskan berdasarkan urgensi.

Format output WAJIB dalam JSON array dengan {num_phases} phase:
[
  {{
    "phase_number": 1,
    "phase_name": "nama phase",
    "month_range": "Bulan 1-{months_per_phase}",
    "focus": "fokus utama phase ini dalam 1 kalimat",
    "modules": [
      {{
        "module_title": "judul modul spesifik",
        "description": "deskripsi singkat dalam 1-2 kalimat",
        "urgency": "Critical|Important|Nice-to-have",
        "delivery_method": "Video|Reading|Workshop|Hands-on Lab|Case Study|Mentoring|Certification",
        "duration_minutes": 60
      }}
    ]
  }}
]
Hasilkan 3-5 modul per phase. Pastikan modul Critical ada di phase awal."""

    user_message = (
        f"Peserta: {participant_name}\n"
        f"Posisi Saat Ini: {current_position}\n"
        f"Target Posisi: {target_position}\n"
        f"Timeline: {timeline_months} bulan\n"
    )
    if additional_context:
        user_message += f"Konteks Tambahan: {additional_context}\n"
    if syllabus_context:
        user_message += syllabus_context
    user_message += (
        f"\nSusunkan career roadmap dari '{current_position}' menuju '{target_position}' "
        f"dalam {timeline_months} bulan."
    )

    raw = call_llm(system_prompt, user_message, max_tokens=8000)
    phases = parse_llm_json(raw, RoadmapPhase)

    total_minutes = sum(
        m.get("duration_minutes", 0)
        for phase in phases
        for m in phase.get("modules", [])
    )

    rec = Recommendation(
        user_id=user_id,
        participant_name=participant_name,
        gap_input=f"Career: {current_position} → {target_position} ({timeline_months} bulan)",
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
            "participant": participant_name,
            "from": current_position,
            "to": target_position,
            "timeline_months": timeline_months,
            "num_phases": len(phases),
        },
    }


# ── History ───────────────────────────────────────────────────────────────────

def get_history(db, user_id: str) -> dict:
    from collections import defaultdict

    syllabi = db.query(Syllabus).filter(Syllabus.user_id == user_id).order_by(Syllabus.created_at.desc()).all()
    modules = db.query(MicroModule).filter(MicroModule.user_id == user_id).order_by(MicroModule.created_at.desc()).all()
    recs = db.query(Recommendation).filter(Recommendation.user_id == user_id).order_by(Recommendation.created_at.desc()).all()

    doc_ids = list({str(m.source_document_id) for m in modules if m.source_document_id})
    doc_map = {}
    if doc_ids:
        docs = db.query(Document).filter(Document.id.in_(doc_ids)).all()
        doc_map = {str(d.id): d.filename for d in docs}

    groups: dict = defaultdict(list)
    for m in modules:
        src_id = str(m.source_document_id) if m.source_document_id else "unknown"
        date_str = m.created_at.strftime("%Y-%m-%d") if m.created_at else "unknown"
        groups[f"{src_id}||{date_str}"].append(m)

    micro_module_groups = []
    for key, mods in groups.items():
        src_id, date_str = key.split("||", 1)
        micro_module_groups.append({
            "source_document_id": src_id,
            "source_filename": doc_map.get(src_id, "Unknown Document"),
            "date": date_str,
            "modules": [
                {"id": str(m.id), "title": m.title, "objective": m.objective,
                 "summary": m.summary, "delivery_format": m.delivery_format,
                 "duration_minutes": m.duration_minutes}
                for m in mods
            ],
        })

    personal_recs, roadmap_recs, bulk_recs = [], [], []
    for r in recs:
        entry = {
            "id": str(r.id), "participant_name": r.participant_name,
            "gap_input": r.gap_input, "recommended_modules": r.recommended_modules,
            "bulk_session_id": r.bulk_session_id, "created_at": r.created_at,
        }
        if r.gap_input and r.gap_input.startswith("Career:"):
            roadmap_recs.append(entry)
        elif r.bulk_session_id:
            bulk_recs.append(entry)
        else:
            personal_recs.append(entry)

    bulk_sessions: dict = defaultdict(list)
    for r in bulk_recs:
        bulk_sessions[r["bulk_session_id"]].append(r)

    bulk_groups = []
    for session_id, members in bulk_sessions.items():
        members_sorted = sorted(members, key=lambda x: x["created_at"])
        bulk_groups.append({
            "bulk_session_id": session_id,
            "date": members_sorted[0]["created_at"].strftime("%Y-%m-%d %H:%M") if members_sorted[0]["created_at"] else "-",
            "total_participants": len(members_sorted),
            "participants": members_sorted,
        })
    bulk_groups.sort(key=lambda x: x["date"], reverse=True)

    return {
        "syllabi": [
            {"id": str(s.id), "topic": s.topic, "level": s.level,
             "output_json": s.output_json,
             "created_at": s.created_at.isoformat() if s.created_at else ""}
            for s in syllabi
        ],
        "micro_module_groups": micro_module_groups,
        "recommendations": personal_recs,
        "bulk_groups": bulk_groups,
        "roadmaps": roadmap_recs,
    }
