# AI-Powered Curriculum Design & Micro-Learning Assistant
TelkomAthon 2025 — Tim LDD SoDSNP

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Copy dan isi env vars:
   ```bash
   cp .env.example .env
   # Edit .env dengan nilai aktual
   ```

3. Setup database — jalankan `supabase_setup.sql` di Supabase SQL Editor.

4. Jalankan FastAPI backend:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

5. Jalankan Streamlit frontend (terminal terpisah):
   ```bash
   streamlit run streamlit_app/app.py
   ```

6. Buka browser: http://localhost:8501

## Demo Flow
1. Register akun baru → Login
2. Upload dummy files dari folder `dummy/`
3. Generate Silabus → pilih topik + level
4. Dekomposisi Modul → pilih dokumen modul
5. Rekomendasi Personal → input nama peserta + gap kompetensi
6. Lihat Riwayat & Export CSV
