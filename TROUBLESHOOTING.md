# Panduan Troubleshooting - AI Syllabus Generator

Panduan lengkap untuk mengatasi masalah umum yang mungkin terjadi saat menjalankan aplikasi.

## Daftar Isi

1. [Error Konfigurasi](#error-konfigurasi)
2. [Error Database](#error-database)
3. [Error Azure OpenAI](#error-azure-openai)
4. [Error Streamlit](#error-streamlit)
5. [Error File Upload](#error-file-upload)

---

## Error Konfigurasi

### ❌ Error: "Gagal menginisialisasi layanan: 'AppConfig' object has no attribute 'database_url'"

**Penyebab:** 
Kode mencoba mengakses atribut `database_url` yang tidak ada di objek `AppConfig`.

**Solusi:**
File sudah diperbaiki. Pastikan Anda menggunakan versi terbaru:
- `app.py`
- `test_app_startup.py`

Cara yang benar untuk mengakses database connection string:
```python
# ❌ SALAH
db = DatabaseService(config.database_url)

# ✅ BENAR
db_connection_string = config.database.get_connection_string()
db = DatabaseService(db_connection_string)
```

### ❌ Error: "Missing required Azure OpenAI configuration"

**Penyebab:** 
File `.env` tidak ada atau variabel Azure OpenAI tidak lengkap.

**Solusi:**
1. Pastikan file `.env` ada di root project
2. Copy dari `.env.example` jika belum ada:
   ```bash
   copy .env.example .env
   ```
3. Isi semua variabel yang diperlukan:
   ```env
   AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com/
   AZURE_OPENAI_API_KEY=your_api_key_here
   AZURE_OPENAI_API_VERSION=2024-10-01-preview
   AZURE_OPENAI_DEPLOYMENT_NAME=your-deployment-name
   AZURE_OPENAI_EMBEDDING_DEPLOYMENT=your-embedding-deployment
   AZURE_OPENAI_EMBEDDING_DIMENSION=1536
   ```

### ❌ Error: "Missing required database configuration"

**Penyebab:** 
Variabel database di file `.env` tidak lengkap.

**Solusi:**
Pastikan semua variabel database terisi:
```env
DATABASE_HOST=localhost  # atau db.xxxxx.supabase.co untuk Supabase
DATABASE_PORT=5432
DATABASE_NAME=syllabus_generator  # atau postgres untuk Supabase
DATABASE_USER=postgres
DATABASE_PASSWORD=your_password_here
```

---

## Error Database

### ❌ Error: "connection refused" atau "could not connect to server"

**Untuk PostgreSQL Lokal:**

**Penyebab:** PostgreSQL tidak berjalan atau tidak bisa diakses.

**Solusi:**
1. Cek apakah PostgreSQL berjalan:
   ```bash
   # Windows
   sc query postgresql-x64-14
   
   # Atau cek di Services (services.msc)
   ```

2. Start PostgreSQL jika belum berjalan:
   ```bash
   # Windows
   net start postgresql-x64-14
   ```

3. Cek apakah port 5432 terbuka:
   ```bash
   netstat -an | findstr 5432
   ```

**Untuk Supabase:**

**Penyebab:** Koneksi internet bermasalah atau kredensial salah.

**Solusi:**
1. Cek koneksi internet
2. Verifikasi HOST di `.env` sesuai dengan Supabase dashboard
3. Pastikan tidak ada firewall yang memblokir koneksi
4. Coba ping host Supabase:
   ```bash
   ping db.xxxxxxxxxxxxx.supabase.co
   ```

### ❌ Error: "password authentication failed for user"

**Penyebab:** Password database salah.

**Solusi:**

**PostgreSQL Lokal:**
1. Reset password PostgreSQL:
   ```sql
   ALTER USER postgres WITH PASSWORD 'new_password';
   ```
2. Update password di file `.env`

**Supabase:**
1. Buka Supabase dashboard
2. Go to Settings > Database
3. Reset database password
4. Update password di file `.env`

### ❌ Error: "database does not exist"

**Penyebab:** Database belum dibuat.

**Solusi:**

**PostgreSQL Lokal:**
```sql
CREATE DATABASE syllabus_generator;
```

**Supabase:**
Gunakan database `postgres` yang sudah ada:
```env
DATABASE_NAME=postgres
```

### ❌ Error: "relation does not exist" atau "table not found"

**Penyebab:** Tabel database belum dibuat (migrasi belum dijalankan).

**Solusi:**
Jalankan script migrasi:
```bash
python migrate_db.py
```

Output yang benar:
```
Connecting to database...
Connected successfully!
Running migration...
Migration completed successfully!
Tables created:
- organization_profiles
- tlos
- performances
- elos
- syllabi
- tlo_performance_mapping
- performance_elo_mapping
```

### ❌ Error: "SSL connection required"

**Penyebab:** Supabase memerlukan SSL connection.

**Solusi:**
Kode sudah menangani SSL secara otomatis. Jika masih error, pastikan library `psycopg2` atau `psycopg2-binary` terinstall:
```bash
pip install psycopg2-binary
```

---

## Error Azure OpenAI

### ❌ Error: "Invalid API key" atau "Unauthorized"

**Penyebab:** API key salah atau expired.

**Solusi:**
1. Buka Azure Portal
2. Go to your Azure OpenAI resource
3. Keys and Endpoint > Copy key
4. Update di file `.env`:
   ```env
   AZURE_OPENAI_API_KEY=your_new_api_key
   ```

### ❌ Error: "Resource not found" atau "Deployment not found"

**Penyebab:** Deployment name salah atau tidak ada.

**Solusi:**
1. Buka Azure Portal
2. Go to Azure OpenAI Studio
3. Deployments > Lihat nama deployment yang ada
4. Update di file `.env`:
   ```env
   AZURE_OPENAI_DEPLOYMENT_NAME=nama-deployment-yang-benar
   ```

### ❌ Error: "Rate limit exceeded" atau "429 Too Many Requests"

**Penyebab:** Terlalu banyak request ke API dalam waktu singkat.

**Solusi:**
1. Tunggu beberapa menit
2. Kode sudah memiliki retry logic otomatis
3. Cek quota di Azure Portal:
   - Azure OpenAI resource > Quotas

### ❌ Error: "The API deployment for this resource does not exist"

**Penyebab:** Endpoint URL atau deployment name tidak sesuai.

**Solusi:**
Pastikan format endpoint benar:
```env
# ✅ BENAR
AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com/

# ❌ SALAH (tanpa trailing slash)
AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com

# ❌ SALAH (dengan path tambahan)
AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com/openai/deployments/
```

---

## Error Streamlit

### ❌ Error: "ModuleNotFoundError: No module named 'streamlit'"

**Penyebab:** Dependencies belum terinstall.

**Solusi:**
```bash
pip install -r requirements.txt
```

### ❌ Error: "Address already in use" atau "Port 8501 is already in use"

**Penyebab:** Streamlit sudah berjalan di port yang sama.

**Solusi:**

**Opsi 1:** Stop proses yang berjalan
```bash
# Windows
netstat -ano | findstr :8501
taskkill /PID <PID> /F
```

**Opsi 2:** Gunakan port lain
```bash
streamlit run app.py --server.port 8502
```

### ❌ Error: "Session state is empty" atau data hilang saat refresh

**Penyebab:** Streamlit session state direset saat refresh.

**Solusi:**
Ini adalah behavior normal Streamlit. Data disimpan di database, jadi:
1. Jangan refresh browser saat sedang dalam proses workflow
2. Gunakan tombol "Mulai Ulang" di sidebar untuk reset dengan benar

---

## Error File Upload

### ❌ Error: "File format not supported"

**Penyebab:** Format file tidak didukung.

**Solusi:**
Gunakan salah satu format yang didukung:
- PDF (.pdf)
- Word Document (.docx)
- Text File (.txt)

### ❌ Error: "File is empty" atau "Could not extract text"

**Penyebab:** File corrupt atau tidak berisi teks.

**Solusi:**
1. Pastikan file tidak corrupt
2. Untuk PDF: pastikan bukan PDF hasil scan (gunakan OCR dulu)
3. Untuk DOCX: pastikan ada teks, bukan hanya gambar
4. Coba buka file di aplikasi lain untuk verifikasi

### ❌ Error: "File too large"

**Penyebab:** File melebihi batas ukuran.

**Solusi:**
1. Streamlit default limit: 200MB
2. Compress file atau split menjadi beberapa bagian
3. Untuk PDF: reduce quality atau remove images

---

## Cara Menjalankan Test Startup

Sebelum menjalankan aplikasi, jalankan test startup untuk memastikan semua konfigurasi benar:

```bash
python test_app_startup.py
```

Output yang benar:
```
======================================================================
AI-Powered Syllabus Generation System - Startup Tests
======================================================================

🔍 Testing imports...
   ✅ All imports successful

🔍 Testing configuration...
   ✅ Configuration loaded
      - Database URL: postgresql://postgres:***@...
      - Azure OpenAI Endpoint: https://...
      - API Version: 2024-10-01-preview
      - Deployment: corpu-text-gpt-4o

🔍 Testing database connection...
   ✅ Database connection successful

🔍 Testing AI service initialization...
   ✅ AI service initialized
      - Endpoint: https://...
      - Deployment: corpu-text-gpt-4o

🔍 Testing workflow orchestrator...
   ✅ Workflow orchestrator initialized

======================================================================
Test Summary
======================================================================
✅ PASS - Imports
✅ PASS - Configuration
✅ PASS - Database Connection
✅ PASS - AI Service
✅ PASS - Workflow Orchestrator

======================================================================
Results: 5/5 tests passed
======================================================================

✅ All tests passed! Application is ready to start.

Run the application with:
   streamlit run app.py
```

---

## Masih Mengalami Masalah?

Jika masalah masih berlanjut:

1. **Cek log error lengkap:**
   - Streamlit menampilkan error di browser dan terminal
   - Copy full error message untuk debugging

2. **Verifikasi environment:**
   ```bash
   python --version  # Harus 3.9+
   pip list  # Cek installed packages
   ```

3. **Reinstall dependencies:**
   ```bash
   pip uninstall -r requirements.txt -y
   pip install -r requirements.txt
   ```

4. **Cek file .env:**
   ```bash
   type .env  # Windows
   cat .env   # Linux/Mac
   ```

5. **Test koneksi manual:**
   ```python
   # test_connection.py
   import psycopg2
   
   conn = psycopg2.connect(
       host="your_host",
       port=5432,
       database="your_db",
       user="postgres",
       password="your_password"
   )
   print("Connected!")
   conn.close()
   ```

6. **Buat issue baru:**
   Jika semua cara di atas tidak berhasil, buat issue dengan informasi:
   - Error message lengkap
   - Output dari `python test_app_startup.py`
   - Python version
   - OS version
   - Apakah menggunakan PostgreSQL lokal atau Supabase

---

**Happy coding! 🚀**
