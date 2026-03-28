# Design Document
# PRIMA — Personalized Responsive Intelligent Micro-Learning Assistant
# TelkomAthon 2025 — Tim LDD SoDSNP

---

## 1. High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                        STREAMLIT FRONTEND                        │
│                                                                  │
│  📋 Generate Silabus      🔬 Dekomposisi Modul                   │
│  🎯 Personalisasi User    👥 Personalisasi Multi User            │
│  🗺️  Roadmap Karir        📥 Riwayat & Export                    │
└────────────────────────┬─────────────────────────────────────────┘
                         │ HTTP/REST (localhost:8000)
┌────────────────────────▼─────────────────────────────────────────┐
│                        FASTAPI BACKEND                           │
│                                                                  │
│  /auth/*                  → register, login                      │
│  /upload, /documents      → document management                  │
│  /syllabus/*              → 5-step wizard endpoints              │
│  /decompose-from-syllabus → micro-module decomposition           │
│  /recommend               → personal recommendation             │
│  /bulk-recommend          → bulk recommendation (multi-user)     │
│  /career-roadmap          → career roadmap generation            │
│  /generate-quiz           → quiz generation (pre/post/single)    │
│  /history                 → aggregated history per user          │
└──────────┬──────────────────────────────────┬────────────────────┘
           │                                  │
┌──────────▼──────────┐           ┌───────────▼──────────────────┐
│   AZURE OPENAI      │           │   SUPABASE (PostgreSQL)      │
│  GPT-4o (LLM)       │           │  users, documents            │
│  text-embedding-    │           │  document_chunks (VECTOR)    │
│  3-large (3072 dim) │           │  syllabi, micro_modules      │
└─────────────────────┘           │  recommendations             │
                                  └──────────────────────────────┘
```

---

## 2. Navigation & Pages

Sidebar menggunakan `st.radio()`. Semua halaman hanya dapat diakses setelah login.

| Menu | Fungsi |
|---|---|
| 📋 Generate Silabus | Wizard 6 langkah: profil → course → TLO → PCS → ELO → finalisasi |
| 🔬 Dekomposisi Modul | Pecah silabus menjadi modul mikro + timeline + quiz opsional |
| 🎯 Personalisasi User | Rekomendasi learning path untuk 1 peserta |
| 👥 Personalisasi Multi User | Rekomendasi massal via upload Excel |
| 🗺️ Roadmap Karir | Roadmap pengembangan karir bertahap |
| 📥 Riwayat & Export | Riwayat semua hasil, dikelompokkan per fitur |

---

## 3. Authentication Design

### Flow
```
Register → POST /auth/register → hash password (bcrypt) → INSERT users
Login    → POST /auth/login    → verify hash → JWT token (8 jam)
Protected endpoint → Authorization: Bearer <token> → get_current_user() dependency
```

### JWT
```python
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 8
```

Semua endpoint yang membutuhkan data user menggunakan dependency `get_current_user()` dan menyertakan `user_id` di setiap query DB untuk isolasi data antar user.

---

## 4. Feature Design

### 4.1 Generate Silabus (Wizard 6 Langkah)

State wizard disimpan di `st.session_state` dengan keys: `syl_step`, `syl_org_profile`, `syl_doc_ids`, `syl_course_type`, `syl_start_level`, `syl_tlos`, `syl_selected_tlos`, `syl_performances`, `syl_selected_perfs`, `syl_elos`, `syl_selected_elos`, `syl_final`.

| Step | Endpoint | Deskripsi |
|---|---|---|
| 1 | `POST /syllabus/analyze-org` atau `POST /syllabus/analyze-org-manual` | Upload dokumen profil atau input manual → AI hasilkan profil terstruktur |
| 2 | — | User pilih tipe course & level awal (1–5) |
| 3 | `POST /syllabus/generate-tlo` | AI generate TLO; user pilih yang relevan |
| 4 | `POST /syllabus/generate-performance` | AI generate PCS; user pilih yang relevan |
| 5 | `POST /syllabus/generate-elo` | AI generate ELO; user pilih yang relevan |
| 6 | `POST /syllabus/finalize` | Simpan silabus ke DB; tampilkan & export |

**Output format silabus (JSONB):**
```json
{
  "org_profile": { "organization_name", "industry", "vision", "mission", ... },
  "course_type": "...",
  "levels_covered": ["Level 1 — Intro", ...],
  "current_condition": "...",
  "desired_condition": "...",
  "tlos": [{ "tlo_number", "tlo", "rationale" }],
  "performance_objectives": [{ "perf_number", "related_tlo", "performance_objective", "condition", "standard" }],
  "elos": [{ "elo_number", "related_performance", "elo", "bloom_level", "delivery_method", "duration_minutes" }]
}
```

---

### 4.2 Dekomposisi Modul Mikro

**Sumber materi:** wajib dari silabus yang sudah dibuat (selectbox dari `/syllabi`).

**Panduan microlearning:** user upload file (PDF/DOCX/PPTX/XLSX). File diupload ke `/upload` dan `document_id` di-cache di session state agar tidak re-upload setiap rerun.

**Endpoint:** `POST /decompose-from-syllabus`
```json
{
  "syllabus_id": "uuid",
  "guide_document_id": "uuid"
}
```

**Generate Quiz (opsional):**
- Checkbox "Generate Soal Quiz?" hanya muncul di mode dari silabus
- Radio: "Generate Pre-test & Post-test saja" | "Generate Quiz jadi 1 saja"
- Input jumlah soal (1–50)
- Caption dinamis menjelaskan jumlah soal yang akan digenerate
- Endpoint: `POST /generate-quiz` → filter ELO dengan `delivery_method` mengandung "quiz"
- Jika tidak ada ELO quiz → `has_quiz_elos: false` → tampilkan pesan info

**Render hasil (`_render_decompose_result`):**
1. Ringkasan metrik (total modul, total durasi)
2. Daftar modul mikro
3. Timeline (tab: Versi Singkat 2/minggu | Versi Lama 1/minggu)
4. Soal Quiz (jika ada) — tab Pre-test/Post-test atau Quiz tunggal
5. Export: DOCX, PDF, TXT — semua bagian dalam satu dokumen (Bagian 1: Silabus, Bagian 2: Modul Mikro, Bagian 3: Timeline, Bagian 4: Quiz)

---

### 4.3 Personalisasi User (Individual)

**Endpoint:** `POST /recommend`

**Request:**
```json
{
  "participant_name": "...",
  "gap_description": "...",
  "top_k": 5,
  "syllabus_id": "uuid (opsional)",
  "jabatan": "opsional",
  "lama_bekerja": "opsional",
  "departemen": "opsional",
  "pendidikan_terakhir": "opsional",
  "preferensi_belajar": "opsional",
  "waktu_belajar_per_minggu": "opsional"
}
```

Field opsional profil dimasukkan ke dalam user message LLM untuk mempersonalisasi rekomendasi. Jika `syllabus_id` diberikan, AI menggunakan ELO dari silabus sebagai katalog modul.

**Output per item:**
```json
{ "rank", "module_title", "relevance_reason", "priority", "estimated_duration_minutes" }
```

---

### 4.4 Personalisasi Multi User (Bulk)

**Endpoint:** `POST /bulk-recommend`

**Flow:**
1. User upload Excel → validasi kolom wajib (`nama`, `gap_kompetensi`)
2. Preview tabel peserta
3. Pilih silabus opsional + jumlah rekomendasi per peserta
4. Klik Submit → backend generate `bulk_session_id` (UUID) untuk batch ini
5. Loop per peserta: call LLM → parse response JSON `{ recommended_level, level_label, modules[] }`
6. Simpan ke `recommendations` dengan `bulk_session_id` yang sama
7. Return semua hasil + error per peserta

**Level peserta** (1–5) ditentukan AI berdasarkan profil dan gap, disimpan di level peserta (bukan per modul).

**Grouping di riwayat:** semua record dengan `bulk_session_id` yang sama ditampilkan sebagai satu group/batch.

**Export per batch:** XLSX (sheet Ringkasan + sheet per peserta), DOCX, PDF.

---

### 4.5 Roadmap Karir

**Endpoint:** `POST /career-roadmap`

**Request:**
```json
{
  "participant_name": "...",
  "current_position": "...",
  "target_position": "...",
  "timeline_months": 12,
  "additional_context": "opsional",
  "syllabus_id": "opsional"
}
```

**Output:** multi-phase roadmap, setiap phase berisi modul dengan urgency (Critical/Important/Nice-to-have).

---

### 4.6 Riwayat & Export

5 tab terpisah:

| Tab | Konten |
|---|---|
| 📋 Silabus | Daftar silabus per expander, export TXT/DOCX/PDF |
| 🔬 Modul Mikro | Dikelompokkan per dokumen sumber + tanggal |
| 🎯 Personalisasi User | Daftar rekomendasi personal (tanpa `bulk_session_id`) |
| 👥 Personalisasi Multi User | Dikelompokkan per `bulk_session_id` (batch), export XLSX/DOCX/PDF per batch |
| 🗺️ Roadmap Karir | Daftar roadmap per expander, export TXT/DOCX/PDF |

---

## 5. AI Agent Design

### System Prompts

**Syllabus Org Analyzer:**
Membaca dokumen profil perusahaan → output JSON: `organization_name`, `industry`, `vision`, `mission`, `strategic_priorities`, `core_competencies`, `learning_context`, `recommended_course_types`.

**TLO Generator:**
Input: profil org + tipe course + level range → output JSON array TLO dengan `tlo_number`, `tlo`, `rationale`.

**PCS Generator:**
Input: TLO terpilih → output JSON array PCS dengan `perf_number`, `related_tlo`, `performance_objective`, `condition`, `standard`.

**ELO Generator:**
Input: PCS terpilih → output JSON array ELO dengan `elo_number`, `related_performance`, `elo`, `bloom_level`, `delivery_method`, `duration_minutes`.

**Decomposer:**
Input: ELO dari silabus + panduan microlearning → output JSON array modul mikro dengan `module_number`, `title`, `specific_objective`, `content_summary`, `delivery_format`, `duration_minutes`, `related_elo`.

**Personal Recommender:**
Input: profil peserta lengkap + gap + ELO silabus (opsional) → output JSON array rekomendasi.

**Bulk Recommender:**
Input: profil peserta + gap + ELO silabus (opsional) → output JSON object `{ recommended_level, level_label, modules[] }`.

**Quiz Generator:**
Input: ELO yang delivery_method-nya Quiz → output JSON array soal pilihan ganda dengan `nomor`, `elo_reference`, `pertanyaan`, `pilihan {A,B,C,D}`, `jawaban_benar`, `penjelasan`.

**Career Roadmap:**
Input: posisi awal, target, timeline → output JSON array phases dengan `phase_number`, `phase_name`, `month_range`, `focus`, `modules[]`.

---

## 6. Export Design

Semua export menggunakan `streamlit_app/export_utils.py`.

| Fungsi | Format | Konten |
|---|---|---|
| `combined_to_docx/pdf/text` | DOCX/PDF/TXT | Silabus + Modul Mikro + Timeline + Quiz (opsional) |
| `syllabus_to_docx/pdf/text` | DOCX/PDF/TXT | Silabus saja |
| `decompose_to_docx/pdf/text` | DOCX/PDF/TXT | Modul mikro + timeline |
| `recommend_to_docx/pdf/text` | DOCX/PDF/TXT | Rekomendasi personal |
| `bulk_recommend_to_xlsx/docx/pdf` | XLSX/DOCX/PDF | Hasil bulk (sheet ringkasan + per peserta) |
| `roadmap_to_docx/pdf/text` | DOCX/PDF/TXT | Career roadmap |
| `quiz_to_docx/pdf/xlsx` | DOCX/PDF/XLSX | Soal quiz (pre/post atau single) |

**Branding:** semua DOCX menyertakan logo Telkom di header; semua PDF menyertakan watermark logo Telkom semi-transparan diagonal.

---

## 7. Database Models (SQLAlchemy)

```python
class User:          id, email, hashed_password, full_name, created_at
class Document:      id, user_id, filename, file_type, content, uploaded_at
class DocumentChunk: id, document_id, chunk_text, embedding(Vector 3072), chunk_index
class Syllabus:      id, user_id, topic, level, output_json(JSONB), created_at
class MicroModule:   id, user_id, source_document_id, title, objective, summary,
                     delivery_format, duration_minutes, embedding(Vector 3072), created_at
class Recommendation: id, user_id, participant_name, gap_input,
                      recommended_modules(JSONB), bulk_session_id, created_at
```

`bulk_session_id` pada `Recommendation`:
- `NULL` → rekomendasi personal (FR-03) atau roadmap karir
- non-`NULL` → bagian dari batch bulk (FR-04), semua record dalam satu batch berbagi UUID yang sama

---

## 8. Key Implementation Details

### Upload & Cache Pattern (Dekomposisi)
File panduan microlearning di-cache di session state untuk menghindari re-upload setiap Streamlit rerun:
```python
if st.session_state.get("decompose_guide_filename") != guide_file.name:
    guide_id = _upload_and_get_id(guide_file, token)
    st.session_state["decompose_guide_id"] = guide_id
    st.session_state["decompose_guide_filename"] = guide_file.name
else:
    guide_id = st.session_state.get("decompose_guide_id")
```

### LLM JSON Parsing
```python
def parse_llm_json(raw: str, model: Type[BaseModel]) -> List[dict]:
    # Strip markdown code fences
    # json.loads() → validate each item with Pydantic
    # Retry once with stricter prompt if parsing fails
```

Bulk recommender menggunakan format JSON object (bukan array) untuk memisahkan level peserta dari modul:
```json
{ "recommended_level": 2, "level_label": "Beginner", "modules": [...] }
```

### Table Display
Semua `st.dataframe()` menggunakan fungsi `show_table()` yang menambahkan kolom "nomor" mulai dari 1 (bukan indeks 0-based default Streamlit).

### Button Convention
Semua button eksekusi utama (generate/submit) menggunakan label `"Submit"` dengan `type="primary"`. Pengecualian: button wizard silabus (Generate TLO →, Generate PCS →, dll.) menggunakan label deskriptif karena merupakan bagian dari flow multi-step.

---

*Dokumen ini dibuat sebagai bagian dari TelkomAthon 2025 — Use Case LDD SoDSNP*
