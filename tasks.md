# Implementation Tasks
# AI-Powered Curriculum Design & Personalized Micro-Learning Assistant
# TelkomAthon 2025 — Tim LDD SoDSNP

---

## Task List

- [x] 1. Project Setup & Environment
  - [x] 1.1 Buat struktur folder project sesuai design (`app/routers`, `app/services`, `app/db`, `streamlit_app`)
  - [x] 1.2 Buat `requirements.txt` dengan semua dependency (fastapi, uvicorn, streamlit, openai, PyMuPDF, python-pptx, python-docx, openpyxl, sqlalchemy, psycopg2-binary, supabase, pgvector, python-jose, passlib, python-multipart, pandas, python-dotenv)
  - [x] 1.3 Buat `.env.example` dengan semua env vars (Azure OpenAI, Supabase, JWT)
  - [x] 1.4 Buat `.env` lokal dengan nilai aktual (tidak di-commit ke git), tambahkan `.env` ke `.gitignore`

- [x] 2. Database Setup (Supabase)
  - [x] 2.1 Aktifkan ekstensi `pgvector` di Supabase SQL editor (`CREATE EXTENSION IF NOT EXISTS vector`)
  - [x] 2.2 Buat tabel `users` (id, email, hashed_password, full_name, created_at)
  - [x] 2.3 Buat tabel `documents` (id, user_id FK, filename, file_type, content, uploaded_at)
  - [x] 2.4 Buat tabel `document_chunks` (id, document_id FK, chunk_text, embedding VECTOR(1536), chunk_index)
  - [x] 2.5 Buat tabel `syllabi` (id, user_id FK, topic, level, output_json JSONB, created_at)
  - [x] 2.6 Buat tabel `micro_modules` (id, user_id FK, source_document_id FK, title, objective, summary, delivery_format, duration_minutes, embedding VECTOR(1536), created_at)
  - [x] 2.7 Buat tabel `recommendations` (id, user_id FK, participant_name, gap_input, recommended_modules JSONB, created_at)
  - [x] 2.8 Buat ivfflat index pada `document_chunks.embedding` dan `micro_modules.embedding` untuk performa vector search

- [x] 3. Backend Core (`app/db/` dan `app/services/`)
  - [x] 3.1 Buat `app/db/database.py` — koneksi PostgreSQL via SQLAlchemy menggunakan `DATABASE_URL` dari `.env`
  - [x] 3.2 Buat `app/db/models.py` — SQLAlchemy models untuk semua tabel (User, Document, DocumentChunk, Syllabus, MicroModule, Recommendation)
  - [x] 3.3 Buat `app/services/parser.py` — fungsi `parse_document(file_path, file_type)` yang mendukung PDF (PyMuPDF), PPTX (python-pptx), DOCX (python-docx), XLSX (openpyxl)
  - [x] 3.4 Buat `app/services/parser.py` — fungsi `chunk_text(text, chunk_size=2000, overlap=200)` dengan strategi split pada paragraph boundary
  - [x] 3.5 Buat `app/services/embedder.py` — fungsi `embed_text(text)` dan `embed_chunks(chunks)` menggunakan Azure OpenAI `text-embedding-3-large`
  - [x] 3.6 Buat `app/services/vector_search.py` — fungsi `search_similar_chunks(query, top_k, document_ids)` menggunakan pgvector cosine similarity
  - [x] 3.7 Buat `app/services/ai_agent.py` — fungsi `call_llm(system_prompt, user_message, context_chunks)` menggunakan Azure OpenAI GPT-4o dengan temperature=0.3
  - [x] 3.8 Buat `app/services/ai_agent.py` — fungsi `parse_llm_json(raw, model)` untuk validasi dan parsing JSON output LLM (strip markdown fences, Pydantic validation, retry sekali jika gagal)

- [x] 4. Authentication (`app/routers/auth.py`)
  - [x] 4.1 Buat fungsi `hash_password` dan `verify_password` menggunakan `passlib[bcrypt]`
  - [x] 4.2 Buat fungsi `create_access_token(data)` dan `get_current_user(token)` menggunakan `python-jose` dengan HS256
  - [x] 4.3 Implementasi endpoint `POST /auth/register` — validasi email unik, hash password, INSERT ke tabel `users`, return user info
  - [x] 4.4 Implementasi endpoint `POST /auth/login` — verifikasi password, generate JWT token (expire 8 jam), return `{access_token, token_type}`

- [x] 5. Document Upload & Parsing (`app/routers/upload.py`)
  - [x] 5.1 Implementasi endpoint `POST /upload` (auth required) — terima `List[UploadFile]`, simpan sementara ke `/tmp`
  - [x] 5.2 Panggil `parser.parse_document()` per file, lalu `chunk_text()`, lalu `embedder.embed_chunks()`
  - [x] 5.3 INSERT ke tabel `documents` (dengan `user_id`) dan `document_chunks` (dengan embedding vector)
  - [x] 5.4 Implementasi endpoint `GET /documents` (auth required) — return daftar dokumen milik user yang sedang login

- [x] 6. AI Agent 1 — Syllabus Generator (`app/routers/syllabus.py`)
  - [x] 6.1 Buat Pydantic model `SyllabusItem` (level, topic, subtopics, learning_objectives, delivery_method, duration_hours)
  - [x] 6.2 Implementasi endpoint `POST /syllabus/generate` (auth required) — terima topic, level, document_ids
  - [x] 6.3 Panggil `vector_search.search_similar_chunks(topic, document_ids)` untuk ambil context RAG
  - [x] 6.4 Bangun system prompt Syllabus Generator dan user message template, panggil `ai_agent.call_llm()`
  - [x] 6.5 Parse dan validasi JSON output dengan `parse_llm_json()`, INSERT ke tabel `syllabi` (dengan `user_id`), return result

- [x] 7. AI Agent 2 — Micro-Learning Decomposer (`app/routers/decompose.py`)
  - [x] 7.1 Buat Pydantic model `MicroModuleItem` (module_number, title, specific_objective, content_summary, delivery_format, duration_minutes)
  - [x] 7.2 Implementasi endpoint `POST /decompose` (auth required) — terima document_id dan guide_document_id
  - [x] 7.3 Ambil semua chunks dari dokumen sumber dan panduan microlearning, bangun context
  - [x] 7.4 Bangun system prompt Decomposer, panggil `ai_agent.call_llm()`, parse JSON output
  - [x] 7.5 Embed setiap modul mikro (title + objective), INSERT ke tabel `micro_modules` (dengan `user_id` dan embedding), return result

- [x] 8. AI Agent 3 — Personalized Recommender (`app/routers/recommend.py`)
  - [x] 8.1 Buat Pydantic model `RecommendationItem` (rank, module_title, relevance_reason, priority, estimated_duration_minutes)
  - [x] 8.2 Implementasi endpoint `POST /recommend` (auth required) — terima participant_name, gap_description, top_k
  - [x] 8.3 Panggil `vector_search.search_similar_chunks(gap_description)` pada tabel `micro_modules` milik user
  - [x] 8.4 Ambil context standar kompetensi dari dokumen `STD-Competency_Standards.docx` yang sudah diupload
  - [x] 8.5 Bangun system prompt Recommender, panggil `ai_agent.call_llm()`, parse JSON, INSERT ke `recommendations` (dengan `user_id`), return result

- [x] 9. FastAPI Main App (`app/main.py`)
  - [x] 9.1 Buat `app/main.py` — inisialisasi FastAPI app, daftarkan semua router (auth, upload, syllabus, decompose, recommend)
  - [x] 9.2 Tambahkan CORS middleware untuk mengizinkan request dari Streamlit (localhost)
  - [x] 9.3 Tambahkan endpoint `GET /history` (auth required) — return riwayat syllabi, micro_modules, dan recommendations milik user

- [x] 10. Streamlit Frontend (`streamlit_app/app.py`)
  - [x] 10.1 Setup session state (`token`, `user_email`, `logged_in`) dan logika routing: jika belum login tampilkan halaman auth, jika sudah login tampilkan sidebar navigasi
  - [x] 10.2 Implementasi Page 0 (Login/Register) — dua tab: Login (POST /auth/login, simpan token ke session state, st.rerun()) dan Register (POST /auth/register, auto-login setelah berhasil)
  - [x] 10.3 Implementasi Page 1 (Upload Dokumen) — `st.file_uploader` multi-file, progress bar, POST /upload dengan Bearer token, tampilkan tabel dokumen dari GET /documents
  - [x] 10.4 Implementasi Page 2 (Generate Silabus) — input topik + selectbox level + multiselect dokumen referensi, POST /syllabus/generate, tampilkan `st.dataframe()` + `st.download_button` CSV
  - [x] 10.5 Implementasi Page 3 (Dekomposisi Modul) — selectbox pilih dokumen, POST /decompose, tampilkan `st.dataframe()` + metrics (total modul, total durasi) + download CSV
  - [x] 10.6 Implementasi Page 4 (Rekomendasi Personal) — input nama peserta + text area gap + optional file upload, POST /recommend, tampilkan `st.dataframe()` + total durasi + download CSV
  - [x] 10.7 Implementasi Page 5 (Riwayat & Export) — tiga tabs (Silabus, Modul Mikro, Rekomendasi), ambil data dari GET /history, tampilkan tabel per tab + download per item
  - [x] 10.8 Tambahkan tombol Logout di sidebar yang menghapus session state dan memanggil `st.rerun()`

- [x] 11. Helper Functions & Utilities
  - [x] 11.1 Buat fungsi helper `api_request(method, endpoint, token, **kwargs)` di Streamlit untuk semua HTTP call ke FastAPI dengan header Authorization otomatis
  - [x] 11.2 Buat fungsi `df_to_csv_download(df, filename)` untuk generate download button CSV dari dataframe

- [x] 12. Testing & Validasi End-to-End
  - [x] 12.1 Jalankan FastAPI (`uvicorn app.main:app --reload`) dan verifikasi semua endpoint via Swagger UI (`/docs`)
  - [x] 12.2 Test flow register → login → upload dummy files → generate silabus → decompose → recommend → lihat history → logout
  - [x] 12.3 Verifikasi isolasi data: login dengan dua akun berbeda, pastikan masing-masing hanya melihat data miliknya sendiri
  - [x] 12.4 Test error handling: upload file format tidak didukung, LLM JSON parse error, token expired

---

*Dokumen ini dibuat sebagai bagian dari TelkomAthon 2025 — Use Case LDD SoDSNP*
