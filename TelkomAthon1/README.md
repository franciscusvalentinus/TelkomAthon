# AI-Powered Syllabus Generation System / Sistem Generasi Silabus Berbasis AI

Sistem Generasi Silabus Berbasis AI adalah aplikasi web yang memungkinkan pengguna untuk membuat silabus kursus secara otomatis menggunakan AI. Aplikasi ini menggunakan Microsoft Azure OpenAI GPT-4o untuk menghasilkan Terminal Learning Objectives (TLO), Performance objectives, dan Enabling Learning Objectives (ELO) berdasarkan profil organisasi.

---

## English Instructions

### Project Structure

```
.
├── src/
│   ├── __init__.py
│   ├── config.py              # Configuration management
│   ├── models/                # Data models
│   │   ├── __init__.py
│   │   └── entities.py
│   ├── services/              # AI and business services
│   │   ├── __init__.py
│   │   └── ai_service.py
│   ├── database/              # Database layer
│   │   ├── __init__.py
│   │   ├── schema.sql
│   │   └── service.py
│   ├── processors/            # Document processing
│   │   ├── __init__.py
│   │   ├── document_processor.py
│   │   └── document_generator.py
│   ├── workflow/              # Workflow orchestration
│   │   ├── __init__.py
│   │   └── orchestrator.py
│   └── ui/                    # Streamlit UI components
│       ├── __init__.py
│       ├── pages.py
│       └── utils.py
├── tests/
│   ├── unit/                  # Unit tests
│   ├── property/              # Property-based tests
│   └── integration/           # Integration tests
├── app.py                     # Main Streamlit application
├── requirements.txt           # Python dependencies
├── .env.example              # Example environment variables
├── migrate_db.py             # Database migration script
└── README.md                 # This file
```

### Prerequisites

- Python 3.9 or higher
- PostgreSQL 12 or higher
- Azure OpenAI API access with GPT-4o deployment

### Installation

1. Clone the repository and navigate to the project directory

2. Create a virtual environment:
```bash
python -m venv venv
```

3. Activate the virtual environment:
   - Windows:
     ```cmd
     venv\Scripts\activate
     ```
   - Linux/Mac:
     ```bash
     source venv/bin/activate
     ```

4. Install dependencies:
```bash
pip install -r requirements.txt
```

### Configuration

1. Copy the example environment file:
   - Windows:
     ```cmd
     copy .env.example .env
     ```
   - Linux/Mac:
     ```bash
     cp .env.example .env
     ```

2. Edit `.env` and fill in your configuration:
   - `AZURE_OPENAI_ENDPOINT`: Your Azure OpenAI endpoint URL
   - `AZURE_OPENAI_API_KEY`: Your Azure OpenAI API key
   - `AZURE_OPENAI_DEPLOYMENT_NAME`: Your GPT-4o deployment name
   - `DATABASE_HOST`: PostgreSQL host (default: localhost)
   - `DATABASE_PORT`: PostgreSQL port (default: 5432)
   - `DATABASE_NAME`: Database name (default: syllabus_generator)
   - `DATABASE_USER`: Database username
   - `DATABASE_PASSWORD`: Database password

### Database Setup

#### Option 1: Local PostgreSQL

1. Create a PostgreSQL database:
```sql
CREATE DATABASE syllabus_generator;
```

2. Run the migration script to create the database schema:
```bash
python migrate_db.py
```

This will create all necessary tables and indexes.

#### Option 2: Supabase PostgreSQL (Recommended for Cloud Deployment)

1. Create a free account at [Supabase](https://supabase.com)

2. Create a new project in Supabase dashboard

3. Get your database credentials:
   - Go to Project Settings > Database
   - Find "Connection String" section
   - Copy the connection details:
     - Host: `db.xxxxxxxxxxxxx.supabase.co`
     - Port: `5432`
     - Database: `postgres`
     - User: `postgres`
     - Password: (your project password)

4. Update your `.env` file with Supabase credentials:
```env
DATABASE_HOST=db.xxxxxxxxxxxxx.supabase.co
DATABASE_PORT=5432
DATABASE_NAME=postgres
DATABASE_USER=postgres
DATABASE_PASSWORD=your_supabase_password
```

5. Run the migration script to create the database schema:
```bash
python migrate_db.py
```

Note: Supabase provides a free tier with 500MB database storage, which is sufficient for this application.

### Running the Application

Start the Streamlit application:
```bash
streamlit run app.py
```

The application will open in your default web browser at `http://localhost:8501`

### Using the Application

1. **Upload Organization Profile**: Upload a PDF, DOCX, or TXT file containing your organization's profile
2. **Review Summary**: Review the AI-generated summary of your organization
3. **Select Course Type**: Choose the type of course (B2B, innovation, tech, etc.)
4. **Generate and Select TLOs**: Review generated Terminal Learning Objectives and select the ones you want
5. **Generate and Select Performances**: Review generated performance objectives and select the ones you want
6. **Generate and Select ELOs**: Review generated Enabling Learning Objectives and select the ones you want
7. **Generate Syllabus**: Create and download the complete syllabus document in DOCX format

### Running Tests

Run all tests:
```bash
pytest
```

Run specific test types:
```bash
# Unit tests only
pytest tests/unit/

# Property-based tests only
pytest tests/property/

# Integration tests only
pytest tests/integration/
```

Run tests with coverage:
```bash
pytest --cov=src --cov-report=html
```

---

## Instruksi Bahasa Indonesia

### Struktur Proyek

Lihat struktur proyek di bagian bahasa Inggris di atas.

### Prasyarat

- Python 3.9 atau lebih tinggi
- PostgreSQL 12 atau lebih tinggi
- Akses Azure OpenAI API dengan deployment GPT-4o

### Instalasi

1. Clone repository dan navigasi ke direktori proyek

2. Buat virtual environment:
```bash
python -m venv venv
```

3. Aktifkan virtual environment:
   - Windows:
     ```cmd
     venv\Scripts\activate
     ```
   - Linux/Mac:
     ```bash
     source venv/bin/activate
     ```

4. Install dependencies:
```bash
pip install -r requirements.txt
```

### Konfigurasi

1. Salin file contoh environment:
   - Windows:
     ```cmd
     copy .env.example .env
     ```
   - Linux/Mac:
     ```bash
     cp .env.example .env
     ```

2. Edit file `.env` dan isi konfigurasi Anda:
   - `AZURE_OPENAI_ENDPOINT`: URL endpoint Azure OpenAI Anda
   - `AZURE_OPENAI_API_KEY`: API key Azure OpenAI Anda
   - `AZURE_OPENAI_DEPLOYMENT_NAME`: Nama deployment GPT-4o Anda
   - `DATABASE_HOST`: Host PostgreSQL (default: localhost)
   - `DATABASE_PORT`: Port PostgreSQL (default: 5432)
   - `DATABASE_NAME`: Nama database (default: syllabus_generator)
   - `DATABASE_USER`: Username database
   - `DATABASE_PASSWORD`: Password database

### Setup Database

#### Opsi 1: PostgreSQL Lokal

1. Buat database PostgreSQL:
```sql
CREATE DATABASE syllabus_generator;
```

2. Jalankan script migrasi untuk membuat schema database:
```bash
python migrate_db.py
```

Ini akan membuat semua tabel dan index yang diperlukan.

#### Opsi 2: Supabase PostgreSQL (Direkomendasikan untuk Deployment Cloud)

1. Buat akun gratis di [Supabase](https://supabase.com)

2. Buat project baru di dashboard Supabase

3. Dapatkan kredensial database Anda:
   - Buka Project Settings > Database
   - Cari bagian "Connection String"
   - Salin detail koneksi:
     - Host: `db.xxxxxxxxxxxxx.supabase.co`
     - Port: `5432`
     - Database: `postgres`
     - User: `postgres`
     - Password: (password project Anda)

4. Update file `.env` dengan kredensial Supabase:
```env
DATABASE_HOST=db.xxxxxxxxxxxxx.supabase.co
DATABASE_PORT=5432
DATABASE_NAME=postgres
DATABASE_USER=postgres
DATABASE_PASSWORD=password_supabase_anda
```

5. Jalankan script migrasi untuk membuat schema database:
```bash
python migrate_db.py
```

Catatan: Supabase menyediakan tier gratis dengan storage database 500MB, yang cukup untuk aplikasi ini.

### Menjalankan Aplikasi

Jalankan aplikasi Streamlit:
```bash
streamlit run app.py
```

Aplikasi akan terbuka di browser default Anda di `http://localhost:8501`

### Menggunakan Aplikasi

1. **Unggah Profil Organisasi**: Unggah file PDF, DOCX, atau TXT yang berisi profil organisasi Anda
2. **Tinjau Ringkasan**: Tinjau ringkasan profil organisasi yang dihasilkan AI
3. **Pilih Jenis Kursus**: Pilih jenis kursus (B2B, innovation, tech, dll.)
4. **Generate dan Pilih TLO**: Tinjau Terminal Learning Objectives yang dihasilkan dan pilih yang Anda inginkan
5. **Generate dan Pilih Performance**: Tinjau performance objectives yang dihasilkan dan pilih yang Anda inginkan
6. **Generate dan Pilih ELO**: Tinjau Enabling Learning Objectives yang dihasilkan dan pilih yang Anda inginkan
7. **Generate Silabus**: Buat dan unduh dokumen silabus lengkap dalam format DOCX

### Menjalankan Tests

Jalankan semua tests:
```bash
pytest
```

Jalankan jenis test tertentu:
```bash
# Unit tests saja
pytest tests/unit/

# Property-based tests saja
pytest tests/property/

# Integration tests saja
pytest tests/integration/
```

Jalankan tests dengan coverage:
```bash
pytest --cov=src --cov-report=html
```

---

## Troubleshooting / Pemecahan Masalah

Untuk panduan lengkap troubleshooting, lihat [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

### Quick Fixes / Solusi Cepat

#### Error: "Gagal menginisialisasi layanan: 'AppConfig' object has no attribute 'database_url'"

**Solusi:** File sudah diperbaiki. Pastikan menggunakan versi terbaru dari `app.py`.

#### Database Connection Issues / Masalah Koneksi Database

- Pastikan PostgreSQL berjalan (atau Supabase accessible)
- Periksa kredensial database di file `.env`
- Pastikan database sudah dibuat dan migrasi sudah dijalankan
- Untuk Supabase: lihat [SUPABASE_SETUP.md](SUPABASE_SETUP.md)

#### Azure OpenAI API Issues / Masalah Azure OpenAI API

- Periksa API key dan endpoint di file `.env`
- Pastikan deployment name sesuai dengan deployment Anda
- Periksa quota dan rate limits di Azure portal

#### File Upload Issues / Masalah Upload File

- Pastikan file dalam format yang didukung (PDF, DOCX, TXT)
- Periksa ukuran file (maksimum 200MB)
- Pastikan file tidak corrupt atau kosong

### Testing Before Running / Test Sebelum Menjalankan

Jalankan test startup untuk memverifikasi konfigurasi:
```bash
python test_app_startup.py
```

Jika semua test pass, aplikasi siap dijalankan!

---

## License / Lisensi

Proprietary - All rights reserved
