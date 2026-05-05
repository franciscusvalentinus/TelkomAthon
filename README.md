# PRIMA — AI-Powered Curriculum Design & Micro-Learning Assistant
TelkomAthon 2025 — Tim LDD SoDSNP

## Deployment ke Streamlit Cloud

1. Push repo ke GitHub
2. Buka [share.streamlit.io](https://share.streamlit.io) → New app
3. Set **Main file path**: `streamlit_app/app.py`
4. Di **Advanced settings → Secrets**, isi semua variabel dari `.env.example`:
   ```toml
   AZURE_OPENAI_ENDPOINT = "https://..."
   AZURE_OPENAI_API_KEY = "..."
   AZURE_OPENAI_API_VERSION = "2024-10-01-preview"
   AZURE_OPENAI_DEPLOYMENT_NAME = "corpu-text-gpt-4o"
   AZURE_OPENAI_EMBEDDING_DEPLOYMENT = "corpu-text-embedding-3-large"
   DATABASE_URL = "postgresql://..."
   JWT_SECRET_KEY = "..."
   JWT_ALGORITHM = "HS256"
   ACCESS_TOKEN_EXPIRE_MINUTES = "480"
   ```
5. Deploy

## Setup Lokal

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Copy dan isi env vars:
   ```bash
   cp .env.example .env
   # Edit .env dengan nilai aktual
   ```

3. Setup database (jalankan sekali di Supabase SQL Editor):
   ```bash
   # Paste isi supabase_setup.sql ke Supabase SQL Editor
   ```

4. Jalankan Streamlit:
   ```bash
   streamlit run streamlit_app/app.py
   ```

5. Buka browser: http://localhost:8501

## Demo Flow
1. Register akun baru → Login
2. Generate Silabus → upload profil perusahaan atau input manual
3. Dekomposisi Modul → pilih silabus + upload panduan microlearning
4. Personalisasi User → input nama peserta + gap kompetensi
5. Personalisasi Multi User → upload Excel peserta
6. Roadmap Karir → input posisi saat ini & target
7. Riwayat & Export → download semua hasil

## Struktur Project

```
prima-ldd-ai/
├── streamlit_app/
│   ├── app.py              # Main Streamlit app (entry point)
│   ├── auth.py             # Auth helpers (JWT + bcrypt)
│   ├── backend.py          # All business logic (replaces FastAPI routers)
│   ├── export_utils.py     # Export functions (DOCX, PDF, XLSX, TXT)
│   ├── db/
│   │   ├── database.py     # SQLAlchemy engine + session
│   │   └── models.py       # ORM models
│   ├── services/
│   │   ├── ai_agent.py     # Azure OpenAI GPT-4o calls
│   │   ├── embedder.py     # Azure OpenAI embeddings
│   │   ├── parser.py       # Document parsing (PDF/PPTX/DOCX/XLSX)
│   │   ├── vector_search.py # pgvector similarity search
│   │   └── config.py       # Secrets reader (st.secrets + os.environ)
│   ├── .streamlit/
│   │   └── secrets.toml    # Local secrets template
│   ├── telkom_logo.png
│   └── template_microlearning.docx
├── supabase_setup.sql      # Database setup script
├── requirements.txt
└── .env.example
```
