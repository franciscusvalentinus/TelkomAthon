# Requirements Specification
# AI-Powered Curriculum Design & Personalized Micro-Learning Assistant
# TelkomAthon 2025 — Tim LDD SoDSNP

---

## 1. Project Overview

**Use Case Title:** AI-Powered Curriculum Design & Personalized Micro-Learning Assistant

**Background:**
Proses pengembangan materi pelatihan di Telkom masih dilakukan secara manual oleh Tim Learning Design & Development (LDD). Penyusunan silabus multi-level (Beginner–Mastery) membutuhkan waktu lama, sulit menjaga konsistensi kedalaman antar jenjang, dan materi yang tersedia bersifat *one-size-fits-all* tanpa personalisasi terhadap gap kompetensi peserta.

**Objective:**
Membangun AI-powered assistant untuk mendukung proses end-to-end pengembangan materi pelatihan — mulai dari penyusunan silabus berjenjang yang selaras dengan kebutuhan bisnis Telkom, hingga dekomposisi materi menjadi modul mikro adaptif berdasarkan gap kompetensi peserta.

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
| Embedding | Azure OpenAI (text-embedding-3-large) |
| Vector Search | pgvector (Supabase extension) |
| Document Parsing | PyMuPDF, python-pptx, openpyxl, python-docx |
| Environment | Jupyter Notebook (AI Space Telkom) / Ubuntu |

---

## 3. Azure OpenAI Configuration

```python
AZURE_ENDPOINT = "https://openaitcuc.openai.azure.com/"
API_VERSION = "2024-10-01-preview"
DEPLOYMENT_NAME = "corpu-text-gpt-4o"
AZURE_OPENAI_EMBEDDING_DEPLOYMENT = "corpu-text-embedding-3-large"
EMBEDDING_DIMENSION = 1536
```

> Catatan: API Key disimpan di file `.env`, tidak di-hardcode di source code.

---

## 4. Dummy Reference Files

File-file berikut disediakan panitia sebagai contoh input dokumen nyata yang akan diproses oleh sistem:

| File | Tipe | Fungsi dalam Sistem |
|---|---|---|
| `[Dummy] BUS-Profile_CorpU_Context.pdf` | PDF | Profil bisnis & konteks organisasi Telkom CorpU — referensi alignment silabus dengan kebutuhan bisnis |
| `[Dummy] CAT-Training_Catalog.pptx` | PPTX | Katalog pelatihan SoDSNP — referensi topik dan program pelatihan yang tersedia |
| `[Dummy] Document index.xlsx` | XLSX | Indeks dokumen referensi — metadata seluruh dokumen sumber |
| `[Dummy] GUIDE-Microlearning_Design.docx` | DOCX | Panduan desain microlearning — standar dan prinsip pemecahan materi menjadi modul mikro |
| `[Dummy] LEARNING DESIGN - Intermediate Level Consultative Selling for AMEX Enterprise Regional.pptx` | PPTX | Contoh modul pelatihan lengkap — input untuk dekomposisi modul mikro |
| `[Dummy] MOD-Training_Module_Workflow_Optimization.pdf` | PDF | Modul pelatihan internal — contoh materi besar yang akan dipecah menjadi modul mikro |
| `[Dummy] Microlearning content inventory.xlsx` | XLSX | Inventori konten microlearning — referensi modul mikro yang sudah ada |
| `[Dummy] Participant Roster.xlsx` | XLSX | Daftar peserta pelatihan — data profil peserta untuk personalisasi |
| `[Dummy] Roleplay scores.xlsx` | XLSX | Skor roleplay peserta — data performa untuk analisis gap kompetensi |
| `[Dummy] STD-Competency_Standards.docx` | DOCX | Standar kompetensi internal Telkom — acuan level Beginner hingga Mastery |
| `[Dummy] TPL-Gap_Assessment_Template.pdf` | PDF | Template gap assessment — format input gap kompetensi peserta |

---

## 5. Functional Requirements

### FR-00: User Authentication
- User dapat mendaftar akun baru dengan email dan password
- User dapat login menggunakan email dan password yang terdaftar
- Sesi login disimpan menggunakan session token (JWT)
- Setiap data (dokumen, silabus, modul mikro, rekomendasi) terikat ke akun user masing-masing
- User hanya dapat melihat dan mengakses data miliknya sendiri
- User dapat logout dari sistem

### FR-01: Document Upload & Parsing
- User dapat mengunggah dokumen referensi (PDF, PPTX, DOCX, XLSX)
- Sistem mem-parsing teks dari setiap format dokumen
- Teks hasil parsing disimpan ke database dan di-embed menggunakan Azure OpenAI Embedding
- Mendukung multi-file upload dalam satu sesi

### FR-02: Syllabus Generation (AI Agent 1)
- User memilih topik pelatihan dan target level (Beginner / Intermediate / Advanced / Mastery)
- AI Agent membaca dokumen referensi yang relevan via vector search (RAG)
- AI Agent menghasilkan draft silabus berjenjang berisi:
  - Level pelatihan
  - Topik utama dan sub-topik
  - Learning objectives per topik
  - Rekomendasi metode penyampaian (video, workshop, hands-on, dll)
  - Estimasi durasi
- Output ditampilkan dalam format tabel terstruktur dan dapat diunduh (CSV/JSON)

### FR-03: Micro-Learning Decomposition (AI Agent 2)
- User mengunggah atau memilih modul pelatihan besar yang sudah ada
- AI Agent memecah materi menjadi modul mikro mandiri, masing-masing berisi:
  - Judul modul mikro
  - Tujuan spesifik (specific learning objective)
  - Ringkasan konten
  - Rekomendasi format penyampaian
  - Estimasi durasi (5–15 menit per modul)
- Output ditampilkan dalam format tabel dan dapat diunduh

### FR-04: Competency Gap Input & Personalized Recommendation (AI Agent 3)
- User menginput gap kompetensi peserta (manual atau upload file gap assessment)
- Sistem membaca profil peserta dari Participant Roster
- AI Agent mencocokkan gap dengan modul mikro yang tersedia
- AI Agent menghasilkan rekomendasi learning path personal berisi daftar modul mikro yang relevan dengan urutan belajar yang disarankan

### FR-05: Structured Output & Export
- Semua output AI tersedia dalam tampilan tabel di UI Streamlit
- User dapat mengunduh output dalam format CSV atau JSON
- Riwayat sesi tersimpan di database Supabase

---

## 6. Non-Functional Requirements

| ID | Requirement |
|---|---|
| NFR-01 | Sistem berjalan di Ubuntu (AI Space Telkom / Jupyter environment) |
| NFR-02 | Response AI Agent ≤ 30 detik untuk dokumen ≤ 10MB |
| NFR-03 | API key dan credentials tidak di-hardcode di source code (gunakan `.env`) |
| NFR-04 | Output AI bersifat draft dan harus direview oleh user sebelum digunakan |
| NFR-05 | Sistem mendukung dokumen berbahasa Indonesia dan Inggris |
| NFR-06 | Password disimpan dalam bentuk hashed (bcrypt), tidak pernah plaintext |
| NFR-07 | Setiap API endpoint yang membutuhkan data user wajib terautentikasi via JWT |
| NFR-06 | Password disimpan dalam bentuk hashed (bcrypt), tidak pernah plaintext |
| NFR-07 | Setiap API endpoint yang membutuhkan data user wajib terautentikasi via JWT |

---

## 7. System Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Streamlit Frontend                  │
│  [Upload Docs] [Select Level] [Input Gap] [Output]  │
└──────────────────────┬──────────────────────────────┘
                       │ HTTP
┌──────────────────────▼──────────────────────────────┐
│                   FastAPI Backend                    │
│  /upload  /generate-syllabus  /decompose  /recommend│
└──────┬───────────────────────────────────┬──────────┘
       │                                   │
┌──────▼──────────┐              ┌─────────▼──────────┐
│  Azure OpenAI   │              │  Supabase (PG)     │
│  GPT-4o (LLM)  │              │  - documents       │
│  Embedding 3L   │              │  - embeddings      │
└─────────────────┘              │  - sessions        │
                                 │  - outputs         │
                                 └────────────────────┘
```

---

## 8. Database Schema (Supabase / PostgreSQL)

```sql
-- Enable pgvector extension (run once in Supabase SQL editor)
CREATE EXTENSION IF NOT EXISTS vector;

-- User accounts
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    full_name TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Dokumen yang diupload
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    filename TEXT NOT NULL,
    file_type TEXT,           -- pdf, pptx, docx, xlsx
    content TEXT,             -- raw parsed text
    uploaded_at TIMESTAMP DEFAULT NOW()
);

-- Chunks teks untuk vector search (RAG)
CREATE TABLE document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    chunk_text TEXT NOT NULL,
    embedding VECTOR(1536),   -- pgvector
    chunk_index INT
);

-- Hasil generate silabus
CREATE TABLE syllabi (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    topic TEXT,
    level TEXT,
    output_json JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Modul mikro hasil dekomposisi
CREATE TABLE micro_modules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    source_document_id UUID REFERENCES documents(id),
    title TEXT,
    objective TEXT,
    summary TEXT,
    delivery_format TEXT,
    duration_minutes INT,
    embedding VECTOR(1536),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Rekomendasi personal per peserta
CREATE TABLE recommendations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    participant_name TEXT,
    gap_input TEXT,
    recommended_modules JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 9. Project Structure

```
telkoathlon-ldd-ai/
├── app/
│   ├── main.py                  # FastAPI entry point
│   ├── routers/
│   │   ├── auth.py              # FR-00: register & login
│   │   ├── upload.py            # FR-01: document upload & parsing
│   │   ├── syllabus.py          # FR-02: syllabus generation
│   │   ├── decompose.py         # FR-03: micro-learning decomposition
│   │   └── recommend.py         # FR-04: gap-based recommendation
│   ├── services/
│   │   ├── parser.py            # PDF/PPTX/DOCX/XLSX text extraction
│   │   ├── embedder.py          # Azure OpenAI embedding
│   │   ├── vector_search.py     # pgvector similarity search
│   │   └── ai_agent.py          # Azure OpenAI GPT-4o calls
│   └── db/
│       ├── database.py          # Supabase/PostgreSQL connection
│       └── models.py            # SQLAlchemy models
├── streamlit_app/
│   └── app.py                   # Streamlit UI (semua halaman)
├── dummy/                       # Dummy files dari panitia (referensi)
│   └── ... (copy dari folder Dummy panitia)
├── .env                         # Credentials (tidak di-commit ke git)
├── .env.example                 # Template env vars
├── requirements.txt
└── README.md
```

---

## 10. Environment Variables (.env.example)

```env
# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://openaitcuc.openai.azure.com/
AZURE_OPENAI_API_KEY=your_api_key_here
AZURE_OPENAI_API_VERSION=2024-10-01-preview
AZURE_OPENAI_DEPLOYMENT_NAME=corpu-text-gpt-4o
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=corpu-text-embedding-3-large
EMBEDDING_DIMENSION=1536

# Supabase / PostgreSQL
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key
DATABASE_URL=postgresql://user:password@host:5432/dbname

# Auth
JWT_SECRET_KEY=your_random_32byte_secret_here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=480

# App
FASTAPI_HOST=0.0.0.0
FASTAPI_PORT=8000
```

---

## 11. Python Dependencies (requirements.txt)

```
# Core
fastapi==0.111.0
uvicorn==0.29.0
streamlit==1.35.0
python-dotenv==1.0.1
pydantic==2.7.1

# Auth
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.9

# Azure OpenAI
openai==1.30.1

# Document Parsing
PyMuPDF==1.24.3
python-pptx==0.6.23
python-docx==1.1.2
openpyxl==3.1.2

# Database
sqlalchemy==2.0.30
psycopg2-binary==2.9.9
supabase==2.4.6
pgvector==0.2.5

# Utilities
pandas==2.2.2
numpy==1.26.4
httpx==0.27.0
```

---

## 12. Demo Scenario (MVP Flow)

```
Step 1 — Upload Dokumen
  User mengunggah file dari folder Dummy:
  → BUS-Profile_CorpU_Context.pdf       (konteks bisnis)
  → STD-Competency_Standards.docx       (standar kompetensi)
  → CAT-Training_Catalog.pptx           (katalog pelatihan)
  → MOD-Training_Module_Workflow_Optimization.pdf  (modul sumber)

Step 2 — Generate Silabus
  User memilih: Topik = "Workflow Optimization", Level = "Intermediate"
  → AI Agent 1 menghasilkan draft silabus berjenjang (tabel: level, topik,
    objektif, metode, durasi)

Step 3 — Dekomposisi Modul Mikro
  User memilih modul: MOD-Training_Module_Workflow_Optimization.pdf
  → AI Agent 2 memecah menjadi modul mikro (5–15 menit per modul)

Step 4 — Input Gap Kompetensi
  User mengunggah: TPL-Gap_Assessment_Template.pdf + Roleplay scores.xlsx
  → AI Agent 3 menghasilkan rekomendasi modul mikro personal per peserta

Step 5 — Export Output
  User mengunduh hasil dalam format CSV atau JSON
```

---

## 13. MVP Success Indicators

1. AI Agent mampu menghasilkan struktur silabus yang logis dan berbeda kedalaman di tiap level
2. AI Agent mampu memecah materi besar menjadi modul mikro yang relevan dan mandiri
3. AI Agent mampu merekomendasikan modul berdasarkan gap kompetensi peserta
4. Alur end-to-end (upload → generate → decompose → recommend → export) berjalan tanpa error kritis

---

## 14. Known Limitations

1. Akurasi konten bergantung pada kualitas dan kelengkapan dokumen sumber yang diupload
2. Semua output bersifat draft dan wajib direview oleh Learning Designer sebelum digunakan
3. Parsing dokumen PPTX dengan banyak gambar/diagram mungkin kehilangan sebagian konteks visual
4. Sistem mendukung multi-user dengan isolasi data per akun

---

*Dokumen ini dibuat sebagai bagian dari TelkomAthon 2025 — Use Case LDD SoDSNP*
