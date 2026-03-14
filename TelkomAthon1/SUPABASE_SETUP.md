# Panduan Setup Supabase untuk AI Syllabus Generator

Panduan lengkap untuk menggunakan Supabase sebagai database PostgreSQL untuk aplikasi AI Syllabus Generator.

## Mengapa Supabase?

- ✅ PostgreSQL gratis dengan 500MB storage
- ✅ Tidak perlu install PostgreSQL lokal
- ✅ Akses dari mana saja (cloud-based)
- ✅ Dashboard untuk monitoring database
- ✅ Backup otomatis
- ✅ SSL connection secara default

## Langkah-langkah Setup

### 1. Buat Akun Supabase

1. Kunjungi [https://supabase.com](https://supabase.com)
2. Klik "Start your project" atau "Sign Up"
3. Daftar menggunakan GitHub, Google, atau email

### 2. Buat Project Baru

1. Setelah login, klik "New Project"
2. Isi detail project:
   - **Name**: `ai-syllabus-generator` (atau nama lain yang Anda inginkan)
   - **Database Password**: Buat password yang kuat dan SIMPAN password ini!
   - **Region**: Pilih region terdekat (misalnya: Southeast Asia - Singapore)
   - **Pricing Plan**: Pilih "Free" (cukup untuk development)
3. Klik "Create new project"
4. Tunggu beberapa menit sampai project selesai dibuat

### 3. Dapatkan Kredensial Database

1. Di dashboard project Anda, klik ikon "Settings" (gear icon) di sidebar kiri
2. Pilih "Database" dari menu settings
3. Scroll ke bawah ke bagian "Connection string"
4. Pilih tab "URI" atau "Connection parameters"

Anda akan melihat informasi seperti ini:

```
Host: db.xxxxxxxxxxxxx.supabase.co
Database name: postgres
Port: 5432
User: postgres
Password: [your-password]
```

**PENTING**: Ganti `xxxxxxxxxxxxx` dengan project reference ID Anda yang sebenarnya.

### 4. Update File .env

1. Buka file `.env` di project Anda (jika belum ada, copy dari `.env.example`)

2. Update bagian database configuration dengan kredensial Supabase:

```env
# Database Configuration - Supabase
DATABASE_HOST=db.xxxxxxxxxxxxx.supabase.co
DATABASE_PORT=5432
DATABASE_NAME=postgres
DATABASE_USER=postgres
DATABASE_PASSWORD=password_yang_anda_buat_tadi
```

**Contoh lengkap file .env:**

```env
# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT=https://openaitcuc.openai.azure.com/
AZURE_OPENAI_API_KEY=your_api_key_here
AZURE_OPENAI_API_VERSION=2024-10-01-preview
AZURE_OPENAI_DEPLOYMENT_NAME=corpu-text-gpt-4o
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=corpu-text-embedding-3-large
AZURE_OPENAI_EMBEDDING_DIMENSION=1536

# Database Configuration - Supabase
DATABASE_HOST=db.abcdefghijklmnop.supabase.co
DATABASE_PORT=5432
DATABASE_NAME=postgres
DATABASE_USER=postgres
DATABASE_PASSWORD=MyStr0ngP@ssw0rd123
```

### 5. Jalankan Migrasi Database

Setelah konfigurasi selesai, jalankan script migrasi untuk membuat tabel-tabel yang diperlukan:

```bash
python migrate_db.py
```

Anda akan melihat output seperti ini:

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

### 6. Verifikasi Setup

#### Cara 1: Melalui Dashboard Supabase

1. Kembali ke dashboard Supabase
2. Klik "Table Editor" di sidebar kiri
3. Anda akan melihat tabel-tabel yang baru dibuat:
   - `organization_profiles`
   - `tlos`
   - `performances`
   - `elos`
   - `syllabi`
   - `tlo_performance_mapping`
   - `performance_elo_mapping`

#### Cara 2: Jalankan Aplikasi

```bash
streamlit run app.py
```

Jika aplikasi berjalan tanpa error koneksi database, berarti setup berhasil!

## Tips dan Troubleshooting

### Error: "Gagal menginisialisasi layanan: 'AppConfig' object has no attribute 'database_url'"

**Penyebab:** Kode lama yang belum diupdate untuk menggunakan struktur config yang baru.

**Solusi:**
Error ini sudah diperbaiki. Pastikan Anda menggunakan versi terbaru dari file `app.py` dan `test_app_startup.py`.

Jika masih terjadi, periksa apakah ada file lain yang menggunakan `config.database_url` dan ganti dengan:
```python
db_connection_string = config.database.get_connection_string()
db = DatabaseService(db_connection_string)
```

### Error: "connection refused" atau "could not connect"

**Solusi:**
1. Pastikan HOST sudah benar (cek lagi di Supabase dashboard)
2. Pastikan PASSWORD sudah benar
3. Cek koneksi internet Anda
4. Pastikan tidak ada firewall yang memblokir koneksi ke Supabase

### Error: "password authentication failed"

**Solusi:**
1. Pastikan password di `.env` sama dengan password yang Anda buat saat membuat project
2. Jika lupa password, Anda bisa reset di Supabase dashboard:
   - Settings > Database > Database password > Reset password

### Error: "SSL connection required"

**Solusi:**
Supabase memerlukan SSL connection. Jika Anda mengalami error ini, update connection string di `src/database/service.py` untuk menambahkan parameter SSL (sudah dihandle di kode).

### Melihat Data di Database

Anda bisa melihat dan mengedit data langsung di Supabase dashboard:

1. Klik "Table Editor" di sidebar
2. Pilih tabel yang ingin dilihat
3. Anda bisa melihat, menambah, edit, atau hapus data langsung dari sini

### Monitoring Database

Supabase menyediakan monitoring gratis:

1. Klik "Database" di sidebar
2. Lihat metrics seperti:
   - Database size
   - Number of connections
   - Query performance

### Backup Database

Supabase melakukan backup otomatis, tapi Anda juga bisa:

1. Export data: Settings > Database > Database backups
2. Download SQL dump untuk backup manual

## Batasan Free Tier Supabase

- **Database size**: 500 MB
- **Bandwidth**: 5 GB per bulan
- **File storage**: 1 GB
- **Monthly active users**: Unlimited

Untuk aplikasi AI Syllabus Generator, free tier ini lebih dari cukup untuk development dan testing.

## Migrasi dari Local ke Supabase

Jika Anda sudah punya data di PostgreSQL lokal dan ingin migrasi ke Supabase:

1. Export data dari PostgreSQL lokal:
```bash
pg_dump -U postgres syllabus_generator > backup.sql
```

2. Import ke Supabase melalui SQL Editor:
   - Buka Supabase dashboard
   - Klik "SQL Editor"
   - Paste isi file backup.sql
   - Klik "Run"

## Keamanan

⚠️ **PENTING**: 
- Jangan commit file `.env` ke Git
- Jangan share password database Anda
- Gunakan environment variables untuk production
- Aktifkan Row Level Security (RLS) di Supabase untuk production

## Support

Jika mengalami masalah:
- Dokumentasi Supabase: [https://supabase.com/docs](https://supabase.com/docs)
- Community Discord: [https://discord.supabase.com](https://discord.supabase.com)
- GitHub Issues: Laporkan bug di repository ini

---

**Selamat! Anda sudah berhasil setup Supabase untuk AI Syllabus Generator! 🎉**
