# Quick Start Guide - AI Syllabus Generator

Panduan cepat untuk menjalankan aplikasi dalam 5 menit! ⚡

## Prasyarat

- Python 3.9+ terinstall
- Akun Azure OpenAI dengan deployment GPT-4o
- Database PostgreSQL (lokal atau Supabase)

## Langkah Cepat

### 1️⃣ Install Dependencies (1 menit)

```bash
# Clone/download project
cd ai-syllabus-generator

# Buat virtual environment
python -m venv venv

# Aktifkan virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install packages
pip install -r requirements.txt
```

### 2️⃣ Setup Database (2 menit)

**Pilih salah satu:**

#### Opsi A: Supabase (Recommended - Gratis & Mudah)

1. Daftar di [supabase.com](https://supabase.com)
2. Buat project baru
3. Copy kredensial dari Settings > Database

#### Opsi B: PostgreSQL Lokal

```sql
CREATE DATABASE syllabus_generator;
```

### 3️⃣ Konfigurasi (1 menit)

```bash
# Copy template
copy .env.example .env

# Edit .env dengan kredensial Anda
notepad .env
```

**Isi minimal yang diperlukan:**
```env
# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com/
AZURE_OPENAI_API_KEY=your_api_key
AZURE_OPENAI_DEPLOYMENT_NAME=your-deployment-name

# Database (Supabase)
DATABASE_HOST=db.xxxxx.supabase.co
DATABASE_NAME=postgres
DATABASE_USER=postgres
DATABASE_PASSWORD=your_supabase_password
```

### 4️⃣ Migrasi Database (30 detik)

```bash
python migrate_db.py
```

Harus muncul: ✅ "Migration completed successfully!"

### 5️⃣ Test & Run (30 detik)

```bash
# Test konfigurasi
python test_app_startup.py

# Jika semua pass, jalankan aplikasi
streamlit run app.py
```

Aplikasi akan terbuka di browser: `http://localhost:8501`

## Troubleshooting Cepat

### ❌ Error saat install dependencies

```bash
# Upgrade pip dulu
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### ❌ Error "AppConfig has no attribute database_url"

File sudah diperbaiki. Pull/download versi terbaru.

### ❌ Error koneksi database

**Supabase:**
- Cek HOST di .env (harus `db.xxxxx.supabase.co`)
- Cek PASSWORD (case-sensitive!)
- Cek koneksi internet

**PostgreSQL Lokal:**
- Pastikan PostgreSQL running
- Cek password di .env

### ❌ Error Azure OpenAI

- Cek API_KEY di .env
- Cek DEPLOYMENT_NAME sesuai dengan Azure Portal
- Pastikan endpoint ada trailing slash: `https://xxx.openai.azure.com/`

### ❌ Test startup gagal

Jalankan dengan verbose:
```bash
python test_app_startup.py
```

Lihat test mana yang fail dan ikuti petunjuk troubleshooting.

## Cara Menggunakan Aplikasi

1. **Upload** file profil organisasi (PDF/DOCX/TXT)
2. **Review** ringkasan yang dihasilkan AI
3. **Pilih** jenis kursus
4. **Generate & Pilih** TLO (Terminal Learning Objectives)
5. **Generate & Pilih** Performance objectives
6. **Generate & Pilih** ELO (Enabling Learning Objectives)
7. **Generate** silabus lengkap
8. **Download** file DOCX

## File Penting

- `.env` - Konfigurasi (JANGAN commit ke Git!)
- `README.md` - Dokumentasi lengkap
- `SUPABASE_SETUP.md` - Panduan setup Supabase
- `TROUBLESHOOTING.md` - Solusi masalah lengkap
- `MANUAL_TESTING_GUIDE.md` - Panduan testing manual

## Bantuan Lebih Lanjut

- **Setup Supabase:** Lihat [SUPABASE_SETUP.md](SUPABASE_SETUP.md)
- **Troubleshooting:** Lihat [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- **Testing:** Lihat [MANUAL_TESTING_GUIDE.md](MANUAL_TESTING_GUIDE.md)

## Checklist Setup ✅

- [ ] Python 3.9+ terinstall
- [ ] Virtual environment dibuat dan aktif
- [ ] Dependencies terinstall (`pip install -r requirements.txt`)
- [ ] File `.env` dibuat dan diisi
- [ ] Database setup (Supabase atau lokal)
- [ ] Migrasi database berhasil (`python migrate_db.py`)
- [ ] Test startup pass (`python test_app_startup.py`)
- [ ] Aplikasi berjalan (`streamlit run app.py`)

**Selamat! Aplikasi siap digunakan! 🎉**

---

💡 **Tips:**
- Gunakan Supabase untuk kemudahan (gratis 500MB)
- Jalankan `test_app_startup.py` sebelum `streamlit run app.py`
- Jangan commit file `.env` ke Git
- Backup database secara berkala

🆘 **Butuh bantuan?**
Buka [TROUBLESHOOTING.md](TROUBLESHOOTING.md) untuk solusi lengkap!
