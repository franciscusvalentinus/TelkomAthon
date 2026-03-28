# Requirements Specification
# PRIMA — Personalized Responsive Intelligent Micro-Learning Assistant
# TelkomAthon 2025 — Tim LDD SoDSNP

---

## 1. Project Overview

**Use Case Title:** PRIMA — AI-Powered Curriculum Design & Personalized Micro-Learning Assistant

**Background:**
Proses pengembangan materi pelatihan di Telkom masih dilakukan secara manual oleh Tim Learning Design & Development (LDD). Penyusunan silabus multi-level membutuhkan waktu lama, sulit menjaga konsistensi kedalaman antar jenjang, dan materi yang tersedia bersifat *one-size-fits-all* tanpa personalisasi terhadap gap kompetensi peserta.

**Objective:**
Membangun AI-powered assistant untuk mendukung proses end-to-end pengembangan materi pelatihan — mulai dari penyusunan silabus berjenjang, dekomposisi modul mikro, generate soal quiz, hingga personalisasi learning path per peserta (individual maupun massal).

**Target User:** Learning Designer, Curriculum Developer, Learning Developer, Learning Analyst (Tim LDD SoDSNP)

---

## 2. Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.11+ |
| Frontend | Streamlit |
| Backend / API | FastAPI |
| Database | PostgreSQL via Supabase |
| AI / LLM | Azure OpenAI (GPT-4o) |
| Embedding | Azure OpenAI (text-embedding-3-large, 3072 dim) |
| Vector Search | pgvector (Supabase extension) |
| Document Parsing | PyMuPDF, python-pptx, openpyxl, python-docx |
| Export | python-docx, reportlab, openpyxl, pandas |

---

## 3. Azure OpenAI Configuration

```python
AZURE_ENDPOINT = "https://openaitcuc.openai.azure.com/"
API_VERSION = "2024-10-01-preview"
DEPLOYMENT_NAME = "corpu-text-gpt-4o"
AZURE_OPENAI_EMBEDDING_DEPLOYMENT = "corpu-text-embedding-3-large"
EMBEDDING_DIMENSION = 3072
```

> API Key disimpan di file `.env`, tidak di-hardcode di source code.

---

## 4. Functional Requirements

### FR-00: User Authentication
- User dapat mendaftar akun baru dengan email dan password
- User dapat login menggunakan email dan password yang terdaftar
- Sesi login disimpan menggunakan JWT token
- Setiap data terikat ke akun user masing-masing (isolasi data per user)
- User dapat logout dari sistem

### FR-01: Generate Silabus (Wizard 6 Langkah)
- **Step 1 — Profil Perusahaan:** User upload dokumen profil perusahaan (PDF/DOCX/PPTX/XLSX) atau input manual nama perusahaan & industri. AI menganalisis dan menghasilkan profil terstruktur.
- **Step 2 — Tipe Course & Level:** User memilih tipe course dan level awal peserta (Level 1–5). Silabus mencakup dari level yang dipilih hingga Level 5 (Mastery).
- **Step 3 — TLO:** AI generate Terminal Learning Objectives; user memilih yang relevan.
- **Step 4 — PCS:** AI generate Performance & Condition Standards; user memilih yang relevan.
- **Step 5 — ELO:** AI generate Enabling Learning Objectives; user memilih yang relevan.
- **Step 6 — Finalisasi:** Tampilkan silabus lengkap; user dapat export ke TXT, DOCX, atau PDF.

### FR-02: Dekomposisi Modul Mikro
- Sumber materi wajib dari silabus yang sudah dibuat (FR-01)
- User upload dokumen panduan microlearning sebagai acuan format (opsional, tersedia template)
- AI memecah ELO dari silabus menjadi modul mikro mandiri (5–15 menit per modul)
- Setiap modul berisi: judul, tujuan spesifik, ringkasan konten, format delivery, durasi, referensi ELO
- Hasil dilengkapi timeline penyelesaian modul (versi singkat 2 modul/minggu & versi lama 1 modul/minggu)
- **Generate Soal Quiz (opsional):** User dapat memilih generate Pre-test & Post-test atau Quiz tunggal dengan jumlah soal yang ditentukan. Sistem otomatis mendeteksi ELO yang delivery method-nya Quiz. Jika tidak ada, ditampilkan pesan informatif.
- Export: DOCX, PDF, TXT — silabus + modul mikro + timeline + quiz (jika ada) dalam satu dokumen

### FR-03: Personalisasi User (Individual)
- Input wajib: nama peserta, deskripsi gap kompetensi
- Input opsional: jabatan, lama bekerja, departemen, pendidikan terakhir, preferensi belajar, waktu belajar per minggu
- Konteks silabus opsional: user dapat memilih silabus yang sudah dibuat sebagai kerangka rekomendasi
- AI menghasilkan rekomendasi learning path personal berisi modul mikro yang relevan dengan urutan belajar
- Export: TXT, DOCX, PDF

### FR-04: Personalisasi Multi User (Bulk)
- User upload file Excel (.xlsx) berisi data peserta
- Kolom wajib: `nama`, `gap_kompetensi`
- Kolom opsional: `jabatan`, `lama_bekerja`, `departemen`, `pendidikan_terakhir`, `preferensi_belajar`, `waktu_belajar_per_minggu`
- Template Excel dengan 5 data dummy tersedia untuk didownload
- Konteks silabus opsional
- AI memproses semua peserta dalam satu batch; setiap peserta mendapat rekomendasi personal + recommended level (Level 1–5)
- Hasil dikelompokkan per sesi generate (1 batch = 1 group)
- Export per batch: XLSX (sheet ringkasan + sheet per peserta), DOCX, PDF

### FR-05: Roadmap Karir
- Input: nama peserta, posisi saat ini, target posisi, timeline (3–24 bulan), konteks tambahan (opsional)
- Konteks silabus opsional
- AI menghasilkan roadmap karir bertahap (multi-phase) dengan modul per phase
- Export: TXT, DOCX, PDF

### FR-06: Riwayat & Export
- Tab terpisah untuk: Silabus, Modul Mikro, Personalisasi User, Personalisasi Multi User, Roadmap Karir
- Personalisasi Multi User dikelompokkan per sesi generate (batch)
- Semua hasil dapat didownload ulang dalam berbagai format

---

## 5. Non-Functional Requirements

| ID | Requirement |
|---|---|
| NFR-01 | Sistem berjalan di Ubuntu (AI Space Telkom / Jupyter environment) |
| NFR-02 | Response AI Agent ≤ 60 detik untuk operasi single; bulk processing proporsional dengan jumlah peserta |
| NFR-03 | API key dan credentials tidak di-hardcode di source code (gunakan `.env`) |
| NFR-04 | Output AI bersifat draft dan harus direview oleh user sebelum digunakan |
| NFR-05 | Sistem mendukung dokumen berbahasa Indonesia dan Inggris |
| NFR-06 | Password disimpan dalam bentuk hashed (bcrypt), tidak pernah plaintext |
| NFR-07 | Setiap API endpoint yang membutuhkan data user wajib terautentikasi via JWT |
| NFR-08 | Semua tabel yang ditampilkan menggunakan penomoran mulai dari 1 (kolom "nomor") |
| NFR-09 | Semua export dokumen menyertakan logo Telkom sebagai watermark/header |

---

## 6. Database Schema

```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    full_name TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    filename TEXT NOT NULL,
    file_type TEXT,
    content TEXT,
    uploaded_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    chunk_text TEXT NOT NULL,
    embedding VECTOR(3072),
    chunk_index INT
);

CREATE TABLE syllabi (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    topic TEXT,
    level TEXT,
    output_json JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE micro_modules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    source_document_id UUID REFERENCES documents(id) ON DELETE SET NULL,
    title TEXT,
    objective TEXT,
    summary TEXT,
    delivery_format TEXT,
    duration_minutes INT,
    embedding VECTOR(3072),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE recommendations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    participant_name TEXT,
    gap_input TEXT,
    recommended_modules JSONB,
    bulk_session_id TEXT,        -- NULL = personal, non-NULL = bulk batch group
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 7. Project Structure

```
prima-ldd-ai/
├── app/
│   ├── main.py                  # FastAPI entry point + /history endpoint
│   ├── routers/
│   │   ├── auth.py              # Register & login
│   │   ├── upload.py            # Document upload & parsing
│   │   ├── syllabus.py          # Syllabus generation wizard (5 endpoints)
│   │   ├── decompose.py         # Micro-module decomposition
│   │   ├── recommend.py         # Personal recommendation
│   │   ├── bulk_recommend.py    # Bulk recommendation (multi-user)
│   │   ├── career_roadmap.py    # Career roadmap generation
│   │   └── quiz.py              # Quiz generation (pre/post-test or single)
│   ├── services/
│   │   ├── parser.py            # PDF/PPTX/DOCX/XLSX text extraction
│   │   ├── embedder.py          # Azure OpenAI embedding
│   │   ├── vector_search.py     # pgvector similarity search
│   │   └── ai_agent.py          # Azure OpenAI GPT-4o calls + JSON parser
│   └── db/
│       ├── database.py          # PostgreSQL connection
│       └── models.py            # SQLAlchemy models
├── streamlit_app/
│   ├── app.py                   # Streamlit UI (semua halaman)
│   ├── export_utils.py          # Export functions (DOCX, PDF, XLSX, TXT)
│   ├── telkom_logo.png          # Logo untuk watermark/header
│   └── template_microlearning.docx  # Template panduan microlearning
├── migrate_db.py                # Database migration script
├── .env                         # Credentials (tidak di-commit)
├── .env.example
├── requirements.txt
└── README.md
```

---

## 8. Environment Variables

```env
AZURE_OPENAI_ENDPOINT=https://openaitcuc.openai.azure.com/
AZURE_OPENAI_API_KEY=your_api_key_here
AZURE_OPENAI_API_VERSION=2024-10-01-preview
AZURE_OPENAI_DEPLOYMENT_NAME=corpu-text-gpt-4o
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=corpu-text-embedding-3-large

DATABASE_URL=postgresql://user:password@host:5432/dbname

JWT_SECRET_KEY=your_random_32byte_secret_here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=480
```

---

*Dokumen ini dibuat sebagai bagian dari TelkomAthon 2025 — Use Case LDD SoDSNP*
