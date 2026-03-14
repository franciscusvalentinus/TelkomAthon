# Design Document
# AI-Powered Curriculum Design & Personalized Micro-Learning Assistant
# TelkomAthon 2025 — Tim LDD SoDSNP

---

## 1. High-Level Architecture

Sistem terdiri dari tiga lapisan utama: Streamlit frontend, FastAPI backend, dan Supabase (PostgreSQL + pgvector) sebagai persistent storage. Azure OpenAI menyediakan kemampuan LLM (GPT-4o) dan embedding (text-embedding-3-large).

```
┌──────────────────────────────────────────────────────────────────┐
│                        STREAMLIT FRONTEND                        │
│                                                                  │
│  Page 1: Upload & Manage Docs                                    │
│  Page 2: Generate Syllabus (AI Agent 1)                          │
│  Page 3: Decompose to Micro-Modules (AI Agent 2)                 │
│  Page 4: Personalized Recommendation (AI Agent 3)               │
│  Page 5: Export & History                                        │
└────────────────────────┬─────────────────────────────────────────┘
                         │ HTTP/REST (localhost:8000)
┌────────────────────────▼─────────────────────────────────────────┐
│                        FASTAPI BACKEND                           │
│                                                                  │
│  POST /auth/register       → create user account                 │
│  POST /auth/login          → return JWT token                    │
│  POST /upload              → parser + embedder (auth required)   │
│  POST /syllabus/generate   → RAG + GPT-4o (auth required)        │
│  POST /decompose           → RAG + GPT-4o (auth required)        │
│  POST /recommend           → vector search + GPT-4o (auth req)  │
│  GET  /documents           → list user's docs (auth required)    │
│  GET  /history             → user's past sessions (auth req)     │
└──────────┬──────────────────────────────────┬────────────────────┘
           │                                  │
┌──────────▼──────────┐           ┌───────────▼──────────────────┐
│   AZURE OPENAI      │           │   SUPABASE (PostgreSQL)      │
│                     │           │                              │
│  GPT-4o             │           │  documents                   │
│  (chat completion)  │           │  document_chunks + VECTOR    │
│                     │           │  syllabi                     │
│  text-embedding-    │           │  micro_modules + VECTOR      │
│  3-large            │           │  recommendations             │
└─────────────────────┘           └──────────────────────────────┘
```

---

## 2. Authentication Design

### 2.1 Auth Flow

```
Register:
  User → POST /auth/register {email, password, full_name}
       → hash password (bcrypt)
       → INSERT INTO users
       → return {user_id, email}

Login:
  User → POST /auth/login {email, password}
       → verify password hash
       → generate JWT (payload: user_id, email, exp)
       → return {access_token, token_type: "bearer"}

Protected Endpoint:
  Client → Header: Authorization: Bearer <token>
         → FastAPI dependency get_current_user()
         → decode JWT → user_id
         → inject user_id ke semua query DB
```

### 2.2 JWT Configuration

```python
SECRET_KEY = os.getenv("JWT_SECRET_KEY")   # random 32-byte string
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 8       # 8 jam
```

### 2.3 FastAPI Auth Dependency

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return {"user_id": user_id}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

Semua endpoint yang membutuhkan auth menggunakan:
```python
current_user: dict = Depends(get_current_user)
```
Dan menyertakan `user_id = current_user["user_id"]` di setiap query DB.

### 2.4 Password Hashing

```python
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)
```

### 2.5 Auth Router (`app/routers/auth.py`)

```python
POST /auth/register
  Body: {email, password, full_name}
  → validate email unique
  → hash password
  → INSERT users
  → return {user_id, email, full_name}

POST /auth/login
  Body: OAuth2PasswordRequestForm (email as username, password)
  → fetch user by email
  → verify_password()
  → create_access_token({"sub": user_id})
  → return {access_token, token_type: "bearer"}
```

---

## 3. Component Design

### 3.1 Document Parser (`app/services/parser.py`)

Bertanggung jawab mengekstrak teks mentah dari berbagai format file.

```python
def parse_document(file_path: str, file_type: str) -> str:
    """
    Returns raw extracted text from the document.
    Supported: pdf, pptx, docx, xlsx
    """
```

| Format | Library | Strategi Ekstraksi |
|---|---|---|
| PDF | PyMuPDF (`fitz`) | Iterasi per halaman, `page.get_text()` |
| PPTX | python-pptx | Iterasi per slide, kumpulkan semua `shape.text` |
| DOCX | python-docx | Iterasi per paragraph, `para.text` |
| XLSX | openpyxl | Iterasi per sheet dan row, join cell values |

Setelah teks diekstrak, teks dipecah menjadi chunks dengan strategi:
- Ukuran chunk: 500 token (~2000 karakter)
- Overlap antar chunk: 50 token
- Pemisah: paragraph break (`\n\n`) diutamakan

### 3.2 Embedder (`app/services/embedder.py`)

Mengubah teks chunk menjadi vector embedding menggunakan Azure OpenAI.

```python
def embed_text(text: str) -> List[float]:
    """
    Returns 1536-dimensional embedding vector.
    Uses: corpu-text-embedding-3-large
    """

def embed_chunks(chunks: List[str]) -> List[List[float]]:
    """Batch embed multiple chunks."""
```

Embedding disimpan ke tabel `document_chunks` kolom `embedding VECTOR(1536)`.

### 3.3 Vector Search (`app/services/vector_search.py`)

Melakukan similarity search menggunakan pgvector untuk RAG (Retrieval-Augmented Generation).

```python
def search_similar_chunks(
    query: str,
    top_k: int = 5,
    document_ids: Optional[List[str]] = None
) -> List[dict]:
    """
    Embeds query, then finds top_k most similar chunks.
    Returns: [{"chunk_text": str, "similarity": float, "document_id": str}]
    """
```

Query SQL yang digunakan (cosine similarity via pgvector):
```sql
SELECT chunk_text, document_id,
       1 - (embedding <=> $1::vector) AS similarity
FROM document_chunks
WHERE document_id = ANY($2)
ORDER BY embedding <=> $1::vector
LIMIT $3;
```

### 3.4 AI Agent (`app/services/ai_agent.py`)

Wrapper untuk Azure OpenAI GPT-4o chat completion. Setiap agent menggunakan system prompt yang berbeda.

```python
def call_llm(
    system_prompt: str,
    user_message: str,
    context_chunks: List[str] = []
) -> str:
    """
    Calls Azure OpenAI GPT-4o with RAG context injected.
    Returns: raw text response from LLM.
    """
```

Struktur pesan ke LLM:
```
[system]  → role + instruksi format output
[user]    → "Context:\n{joined_chunks}\n\nTask:\n{user_message}"
```

---

## 3. AI Agent Design

### Agent 1 — Syllabus Generator

**Trigger:** User memilih topik + level, klik "Generate Syllabus"

**RAG Sources:** `BUS-Profile_CorpU_Context.pdf`, `STD-Competency_Standards.docx`, `CAT-Training_Catalog.pptx`

**System Prompt:**
```
Kamu adalah Learning Design Expert untuk Telkom Indonesia.
Tugasmu adalah membuat draft silabus pelatihan yang terstruktur dan berjenjang.
Silabus harus selaras dengan konteks bisnis Telkom dan standar kompetensi internal.

Format output WAJIB dalam JSON array dengan struktur berikut:
[
  {
    "level": "Beginner|Intermediate|Advanced|Mastery",
    "topic": "nama topik utama",
    "subtopics": ["subtopik 1", "subtopik 2"],
    "learning_objectives": ["peserta mampu...", "peserta dapat..."],
    "delivery_method": "Video|Workshop|Hands-on|Self-paced|Blended",
    "duration_hours": <angka>
  }
]
Hasilkan untuk SEMUA level dari Beginner hingga Mastery dengan kedalaman yang berbeda.
```

**User Message Template:**
```
Topik Pelatihan: {topic}
Target Level: {level}

Konteks Bisnis & Standar Kompetensi:
{rag_context}

Buatkan draft silabus berjenjang untuk topik ini.
```

**Output:** JSON → diparse → ditampilkan sebagai `st.dataframe()` di Streamlit

---

### Agent 2 — Micro-Learning Decomposer

**Trigger:** User memilih dokumen modul, klik "Decompose"

**RAG Sources:** Dokumen modul yang dipilih + `GUIDE-Microlearning_Design.docx`

**System Prompt:**
```
Kamu adalah Instructional Designer spesialis microlearning.
Tugasmu adalah memecah modul pelatihan besar menjadi modul mikro yang mandiri.

Setiap modul mikro harus:
- Berdiri sendiri (standalone), tidak bergantung pada modul lain
- Fokus pada SATU tujuan pembelajaran spesifik
- Dapat diselesaikan dalam 5–15 menit

Format output WAJIB dalam JSON array:
[
  {
    "module_number": <int>,
    "title": "judul modul mikro",
    "specific_objective": "setelah menyelesaikan modul ini, peserta dapat...",
    "content_summary": "ringkasan konten dalam 2-3 kalimat",
    "delivery_format": "Video|Infographic|Quiz|Case Study|Simulation",
    "duration_minutes": <5-15>
  }
]
```

**User Message Template:**
```
Konten Modul Pelatihan:
{rag_context}

Panduan Microlearning:
{microlearning_guide_context}

Pecah materi di atas menjadi modul mikro yang mandiri.
```

**Output:** JSON → `st.dataframe()` + download CSV

---

### Agent 3 — Personalized Recommender

**Trigger:** User menginput gap kompetensi + (opsional) upload gap assessment file

**RAG Sources:** `micro_modules` table (vector search), `STD-Competency_Standards.docx`

**System Prompt:**
```
Kamu adalah Learning Advisor untuk Telkom Indonesia.
Tugasmu adalah merekomendasikan modul mikro yang paling relevan berdasarkan gap kompetensi peserta.

Urutkan rekomendasi dari modul yang paling fundamental ke yang paling advanced.
Jelaskan mengapa setiap modul relevan dengan gap yang ada.

Format output WAJIB dalam JSON array:
[
  {
    "rank": <int>,
    "module_title": "judul modul mikro",
    "relevance_reason": "alasan relevansi dengan gap peserta",
    "priority": "High|Medium|Low",
    "estimated_duration_minutes": <int>
  }
]
```

**User Message Template:**
```
Profil Peserta: {participant_name}
Gap Kompetensi: {gap_description}

Modul Mikro yang Tersedia:
{similar_modules_context}

Standar Kompetensi:
{competency_standards_context}

Rekomendasikan learning path yang paling relevan untuk peserta ini.
```

**Output:** JSON → `st.dataframe()` + total durasi estimasi

---

## 4. FastAPI Endpoint Design

### POST `/auth/register`
```python
# Request body:
{"email": "user@telkom.co.id", "password": "...", "full_name": "..."}
# Response:
{"user_id": "uuid", "email": "...", "full_name": "..."}
```

### POST `/auth/login`
```python
# Request: OAuth2PasswordRequestForm (form-data: username=email, password)
# Response:
{"access_token": "eyJ...", "token_type": "bearer"}
```

---

### POST `/upload`
```python
# Auth: Bearer token required
# Request: multipart/form-data
# Body: files: List[UploadFile]
# Response:
{
  "uploaded": [
    {"document_id": "uuid", "filename": "...", "chunks_created": 12}
  ]
}
```

Flow:
1. `get_current_user()` → `user_id`
2. Terima file → simpan sementara
3. `parser.parse_document()` → raw text
4. Chunking → list of strings
5. `embedder.embed_chunks()` → list of vectors
6. Simpan ke `documents` (dengan `user_id`) + `document_chunks`
7. Return response

---

### POST `/syllabus/generate`
```python
# Auth: Bearer token required
# Request body:
{
  "topic": "Workflow Optimization",
  "level": "Intermediate",
  "document_ids": ["uuid1", "uuid2"]
}
# Response:
{
  "syllabus_id": "uuid",
  "result": [ ...syllabus JSON array... ]
}
```

Flow:
1. `get_current_user()` → `user_id`
2. `vector_search.search_similar_chunks(topic, document_ids)` → context
3. `ai_agent.call_llm(system_prompt, user_message)` → raw JSON string
4. Parse JSON → validasi struktur
5. Simpan ke tabel `syllabi` (dengan `user_id`)
6. Return result

---

### POST `/decompose`
```python
# Auth: Bearer token required
# Request body:
{
  "document_id": "uuid",
  "guide_document_id": "uuid"
}
# Response:
{
  "modules": [ ...micro_modules JSON array... ]
}
```

Flow:
1. `get_current_user()` → `user_id`
2. Ambil semua chunks dari `document_id`
3. Ambil chunks panduan dari `guide_document_id`
4. `ai_agent.call_llm()` → JSON modul mikro
5. Embed setiap modul mikro
6. Simpan ke `micro_modules` (dengan `user_id`)
7. Return result

---

### POST `/recommend`
```python
# Auth: Bearer token required
# Request body:
{
  "participant_name": "...",
  "gap_description": "...",
  "top_k": 5
}
# Response:
{
  "recommendation_id": "uuid",
  "recommendations": [ ...recommendation JSON array... ]
}
```

Flow:
1. `get_current_user()` → `user_id`
2. `vector_search.search_similar_chunks(gap_description)` pada `micro_modules` milik user
3. Ambil standar kompetensi dari `STD-Competency_Standards.docx`
4. `ai_agent.call_llm()` → JSON rekomendasi
5. Simpan ke `recommendations` (dengan `user_id`)
6. Return result

---

## 5. Streamlit UI Design

### Session State untuk Auth
```python
# Streamlit session state keys:
st.session_state["token"]      # JWT access token
st.session_state["user_email"] # email user yang login
st.session_state["logged_in"]  # bool
```

Setiap kali app dimuat, cek `st.session_state["logged_in"]`. Jika `False`, tampilkan halaman Auth saja. Jika `True`, tampilkan sidebar navigasi penuh.

### Navigasi
Sidebar dengan 5 halaman menggunakan `st.sidebar.radio()`:

```
🔐 Login / Register   ← hanya tampil jika belum login
---
📁 Upload Dokumen
📋 Generate Silabus
🔬 Dekomposisi Modul
🎯 Rekomendasi Personal
📥 Export & Riwayat
---
👤 {user_email}  [Logout]
```

### Page 0 — Login / Register
```
st.title("🔐 AI Learning Assistant — Telkom")

tab1, tab2 = st.tabs(["Login", "Register"])

# Tab Login:
  st.text_input("Email")
  st.text_input("Password", type="password")
  → Tombol "Login"
  → POST /auth/login
  → Simpan token ke st.session_state["token"]
  → st.rerun() untuk refresh ke halaman utama

# Tab Register:
  st.text_input("Nama Lengkap")
  st.text_input("Email")
  st.text_input("Password", type="password")
  st.text_input("Konfirmasi Password", type="password")
  → Tombol "Daftar"
  → POST /auth/register
  → Auto-login setelah register berhasil
```

### Page 1 — Upload Dokumen
```
st.title("Upload Dokumen Referensi")
st.file_uploader(accept_multiple_files=True, type=["pdf","pptx","docx","xlsx"])
→ Tombol "Upload & Proses"
→ Progress bar saat parsing + embedding
→ Tabel daftar dokumen yang sudah diupload (dari GET /documents)
```

### Page 2 — Generate Silabus
```
st.title("Generate Draft Silabus")
st.text_input("Topik Pelatihan")
st.selectbox("Target Level", ["Beginner","Intermediate","Advanced","Mastery","All Levels"])
st.multiselect("Dokumen Referensi", [list of uploaded docs])
→ Tombol "Generate Silabus"
→ st.spinner("AI sedang menyusun silabus...")
→ st.dataframe(hasil silabus)
→ st.download_button("Download CSV")
```

### Page 3 — Dekomposisi Modul
```
st.title("Dekomposisi Modul Mikro")
st.selectbox("Pilih Modul Pelatihan", [list of uploaded docs])
→ Tombol "Decompose"
→ st.spinner("AI sedang memecah materi...")
→ st.dataframe(daftar modul mikro)
→ st.metric("Total Modul", n) + st.metric("Total Durasi", "X menit")
→ st.download_button("Download CSV")
```

### Page 4 — Rekomendasi Personal
```
st.title("Rekomendasi Learning Path Personal")
st.text_input("Nama Peserta")
st.text_area("Deskripsi Gap Kompetensi")
st.file_uploader("Upload Gap Assessment (opsional)", type=["pdf","xlsx"])
→ Tombol "Generate Rekomendasi"
→ st.spinner("AI sedang menganalisis gap...")
→ st.dataframe(rekomendasi modul)
→ st.download_button("Download CSV")
```

### Page 5 — Export & Riwayat
```
st.title("Riwayat & Export")
→ Tabs: [Silabus] [Modul Mikro] [Rekomendasi]
→ Setiap tab: tabel riwayat MILIK USER YANG LOGIN + tombol download per item
→ Data difilter by user_id dari JWT token
```

---

## 6. Data Flow Diagram

### Flow 1: Document Upload & Embedding
```
User uploads file
      │
      ▼
FastAPI /upload
      │
      ├─► parser.parse_document()  ──► raw_text
      │
      ├─► chunk_text(raw_text)     ──► chunks[]
      │
      ├─► embedder.embed_chunks()  ──► vectors[]
      │
      └─► Supabase INSERT
              documents (id, filename, content)
              document_chunks (chunk_text, embedding)
```

### Flow 2: Syllabus Generation (RAG)
```
User: topic + level + doc_ids
      │
      ▼
FastAPI /syllabus/generate
      │
      ├─► embed(topic)  ──► query_vector
      │
      ├─► pgvector similarity search  ──► top_k chunks (context)
      │
      ├─► build prompt (system + context + user_task)
      │
      ├─► Azure OpenAI GPT-4o  ──► JSON string
      │
      ├─► parse + validate JSON
      │
      └─► Supabase INSERT syllabi
              │
              ▼
          Return to Streamlit → st.dataframe()
```

### Flow 3: Micro-Module Decomposition
```
User: document_id
      │
      ▼
FastAPI /decompose
      │
      ├─► fetch all chunks of document
      │
      ├─► fetch microlearning guide chunks
      │
      ├─► Azure OpenAI GPT-4o  ──► JSON micro_modules[]
      │
      ├─► embed each module title+objective
      │
      └─► Supabase INSERT micro_modules (with embeddings)
              │
              ▼
          Return to Streamlit → st.dataframe()
```

### Flow 4: Personalized Recommendation
```
User: participant_name + gap_description
      │
      ▼
FastAPI /recommend
      │
      ├─► embed(gap_description)  ──► query_vector
      │
      ├─► pgvector search on micro_modules  ──► top_k relevant modules
      │
      ├─► fetch competency standards context
      │
      ├─► Azure OpenAI GPT-4o  ──► JSON recommendations[]
      │
      └─► Supabase INSERT recommendations
              │
              ▼
          Return to Streamlit → st.dataframe()
```

---

## 7. Key Implementation Details

### Chunking Strategy
```python
def chunk_text(text: str, chunk_size: int = 2000, overlap: int = 200) -> List[str]:
    """
    Split text into overlapping chunks.
    Prefer splitting on paragraph boundaries (\n\n).
    """
    paragraphs = text.split("\n\n")
    chunks = []
    current = ""
    for para in paragraphs:
        if len(current) + len(para) <= chunk_size:
            current += para + "\n\n"
        else:
            if current:
                chunks.append(current.strip())
            current = current[-overlap:] + para + "\n\n"  # overlap
    if current:
        chunks.append(current.strip())
    return chunks
```

### JSON Output Validation
Setiap response LLM divalidasi sebelum disimpan:
```python
import json
from pydantic import BaseModel

class SyllabusItem(BaseModel):
    level: str
    topic: str
    subtopics: List[str]
    learning_objectives: List[str]
    delivery_method: str
    duration_hours: float

def parse_llm_json(raw: str, model: type) -> List[dict]:
    """Extract JSON from LLM response, validate with Pydantic model."""
    # Strip markdown code fences if present
    raw = raw.strip().removeprefix("```json").removesuffix("```").strip()
    data = json.loads(raw)
    return [model(**item).dict() for item in data]
```

### Error Handling
- LLM JSON parse error → retry sekali dengan prompt "Return ONLY valid JSON, no explanation"
- Embedding API error → exponential backoff, max 3 retries
- File parse error → return partial text dengan warning ke user

---

## 8. Supabase Setup Checklist

```sql
-- 1. Enable pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Create all tables (lihat requirements.md section 8)

-- 3. Create index untuk vector search (performance)
CREATE INDEX ON document_chunks
  USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 100);

CREATE INDEX ON micro_modules
  USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 100);
```

---

## 9. File: `app/services/ai_agent.py` (Skeleton)

```python
import os
from openai import AzureOpenAI
from typing import List

client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
)

def call_llm(system_prompt: str, user_message: str, context_chunks: List[str] = []) -> str:
    context = "\n\n---\n\n".join(context_chunks)
    full_user_msg = f"Context:\n{context}\n\nTask:\n{user_message}" if context else user_message

    response = client.chat.completions.create(
        model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": full_user_msg},
        ],
        temperature=0.3,
        max_tokens=4096,
    )
    return response.choices[0].message.content
```

---

## 10. File: `app/services/embedder.py` (Skeleton)

```python
import os
from openai import AzureOpenAI
from typing import List

client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
)

def embed_text(text: str) -> List[float]:
    response = client.embeddings.create(
        input=text,
        model=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT"),
    )
    return response.data[0].embedding

def embed_chunks(chunks: List[str]) -> List[List[float]]:
    return [embed_text(chunk) for chunk in chunks]
```

---

*Dokumen ini dibuat sebagai bagian dari TelkomAthon 2025 — Use Case LDD SoDSNP*
