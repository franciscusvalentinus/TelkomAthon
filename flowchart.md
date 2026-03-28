# Flowchart Alur Aplikasi PRIMA
# TelkomAthon 2025 — Tim LDD SoDSNP

> Render menggunakan Mermaid. Buka di VS Code (extension: Markdown Preview Mermaid Support), GitHub, atau paste ke https://mermaid.live

---

## 0. Alur Autentikasi

```mermaid
flowchart TD
    A([Buka Aplikasi]) --> B{Sudah Login?}
    B -- Tidak --> C[Halaman Login / Register]
    C --> D{Pilih Tab}
    D -- Login --> E[Input Email & Password]
    D -- Register --> F[Input Nama, Email, Password]
    E --> I{Berhasil?}
    F --> I
    I -- Ya --> J[Simpan JWT Token\nke Session State]
    I -- Tidak --> K[Tampilkan Error]
    K --> C
    J --> L([Masuk ke Aplikasi])
    B -- Ya --> L
    L --> M[Tampilkan Sidebar Navigasi]
```

---

## 1. Generate Silabus (Wizard 6 Langkah)

```mermaid
flowchart TD
    A([Buka Generate Silabus]) --> B[Tampilkan Progress Bar\nStep 1–6]

    B --> S1[STEP 1 — Profil Perusahaan]
    S1 --> S1A{Sumber Profil?}
    S1A -- Upload Dokumen --> S1B[Upload PDF/DOCX/PPTX/XLSX]
    S1A -- Input Manual --> S1C[Input Nama Perusahaan\n& Industri]
    S1B --> S1G[AI Hasilkan Profil Terstruktur]
    S1C --> S1G
    S1G --> S1H[Simpan ke Session State]
    S1H --> S2

    S2[STEP 2 — Tipe Course & Level]
    S2 --> S2A[Tampilkan Ringkasan Profil]
    S2A --> S2B[Pilih Tipe Course]
    S2B --> S2C[Pilih Level Awal Peserta\nLevel 1–5]
    S2C --> S2D[Simpan Pilihan]
    S2D --> S3

    S3[STEP 3 — Terminal Learning Objectives]
    S3 --> S3B[AI Generate TLO]
    S3B --> S3C[Tampilkan Checkbox TLO]
    S3C --> S3D[User Pilih TLO Relevan]
    S3D --> S4

    S4[STEP 4 — Performance & Condition Standards]
    S4 --> S4B[AI Generate PCS\nberdasarkan TLO terpilih]
    S4B --> S4C[Tampilkan Checkbox PCS]
    S4C --> S4D[User Pilih PCS Relevan]
    S4D --> S5

    S5[STEP 5 — Enabling Learning Objectives]
    S5 --> S5B[AI Generate ELO\nberdasarkan PCS terpilih]
    S5B --> S5C[Tampilkan Checkbox ELO]
    S5C --> S5D[User Pilih ELO Relevan]
    S5D --> S6

    S6[STEP 6 — Finalisasi Silabus]
    S6 --> S6B[Simpan Silabus ke Database]
    S6B --> S6C[Tampilkan Silabus Lengkap]
    S6C --> S6D[Export TXT / DOCX / PDF]
    S6D --> S6E{Buat Silabus Baru?}
    S6E -- Ya --> S6F[Reset Session State]
    S6F --> B
    S6E -- Tidak --> Z([Selesai])
```

---

## 2. Dekomposisi Modul Mikro

```mermaid
flowchart TD
    A([Buka Dekomposisi Modul]) --> B[Upload Panduan Microlearning\nPDF/DOCX/PPTX/XLSX\nOpsional]
    B --> C{File Baru?}
    C -- Ya --> D[Upload & Simpan ID Panduan\nke Session State]
    C -- Tidak --> E[Ambil ID Panduan dari Session State]
    D --> F
    E --> F

    F[Pilih Silabus dari Daftar] --> G[Tampilkan Ringkasan Silabus\nTLO / PCS / ELO]

    G --> H{Generate Soal Quiz?}
    H -- Ya --> I[Pilih Tipe Quiz\nPre-test & Post-test / Quiz Tunggal]
    I --> J[Input Jumlah Soal]
    J --> K[Tampilkan Penjelasan Jumlah Soal]
    K --> L
    H -- Tidak --> L

    L[Klik Submit] --> N[AI Pecah ELO menjadi\nModul Mikro Mandiri]
    N --> O[Simpan Modul Mikro ke Database]

    O --> P{Generate Quiz Dipilih?}
    P -- Ya --> R{Ada ELO dengan\nMetode Quiz?}
    R -- Ya --> S[AI Generate Soal\nPilihan Ganda]
    R -- Tidak --> T[Tandai: Tidak Ada ELO Quiz]
    S --> U
    T --> U
    P -- Tidak --> U

    U[Tampilkan Hasil]
    U --> U1[Daftar Modul Mikro]
    U --> U2[Timeline Penyelesaian\nVersi Singkat & Lama]
    U --> U3{Ada Quiz?}
    U3 -- Ya --> U4[Tampilkan Soal Quiz\nTab Pre-test / Post-test / Single]
    U3 -- Tidak / Tidak Ada ELO Quiz --> U5[Tampilkan Pesan Info]

    U1 & U2 & U4 & U5 --> V[Export DOCX / PDF / TXT\nSilabus + Modul + Timeline + Quiz]
    V --> Z([Selesai])
```

---

## 3. Personalisasi User (Individual)

```mermaid
flowchart TD
    A([Buka Personalisasi User]) --> B[Input Nama Peserta]
    B --> C[Input Gap Kompetensi]
    C --> D[Expander: Informasi Profil Tambahan\nOpsional]
    D --> D1[Jabatan]
    D --> D2[Lama Bekerja]
    D --> D3[Departemen]
    D --> D4[Pendidikan Terakhir]
    D --> D5[Preferensi Belajar]
    D --> D6[Waktu Belajar per Minggu]

    D1 & D2 & D3 & D4 & D5 & D6 --> E[Slider Jumlah Rekomendasi\n3–10]
    E --> F[Pilih Konteks Silabus\nOpsional]
    F --> G{Silabus Dipilih?}
    G -- Ya --> H[AI Gunakan ELO Silabus\nsebagai Katalog Modul]
    G -- Tidak --> I[AI Generate Modul\nBerdasarkan Gap]
    H & I --> J[Klik Submit]

    J --> L[AI Analisis Gap & Profil]
    L --> M[AI Hasilkan Rekomendasi\nLearning Path Personal]
    M --> N[Simpan ke Database]

    N --> O[Tampilkan Hasil]
    O --> O1[Daftar Modul Rekomendasi\ndengan Prioritas High/Med/Low]
    O --> O2[Estimasi Total Durasi]
    O1 & O2 --> P[Export TXT / DOCX / PDF]
    P --> Z([Selesai])
```

---

## 4. Personalisasi Multi User (Bulk)

```mermaid
flowchart TD
    A([Buka Personalisasi Multi User]) --> B{Perlu Template?}
    B -- Ya --> C[Download Template Excel\nberisi 5 Data Dummy]
    B -- Tidak --> D
    C --> D

    D[Upload File Excel Peserta .xlsx] --> E[Validasi Kolom Wajib\nnama + gap_kompetensi]
    E --> F{Kolom Valid?}
    F -- Tidak --> G[Tampilkan Error\nKolom Tidak Ditemukan]
    G --> D
    F -- Ya --> H[Drop Baris Kosong\nTampilkan Preview Tabel]

    H --> I[Pilih Konteks Silabus\nOpsional]
    I --> J[Slider Jumlah Rekomendasi\nper Peserta 3–10]
    J --> K[Klik Submit]

    K --> L[Generate ID Sesi Batch]
    L --> M[Loop per Peserta]

    M --> N[Susun Profil Peserta\nnama + gap + data opsional\n+ konteks silabus]
    N --> O[AI Analisis & Generate\nRekomendasi]
    O --> P[Hasil: Level Peserta\n+ Daftar Modul]
    P --> Q[Simpan ke Database\ndengan ID Sesi yang sama]
    Q --> R{Masih Ada\nPeserta?}
    R -- Ya --> M
    R -- Tidak --> S

    S[Tampilkan Hasil per Peserta]
    S --> S1[Nama + Jabatan + Departemen]
    S --> S2[Recommended Level\nLevel 1–5 dengan ikon warna]
    S --> S3[Daftar Modul Rekomendasi]
    S1 & S2 & S3 --> T[Export Semua Hasil\nXLSX / DOCX / PDF]
    T --> Z([Selesai])
```

---

## 5. Roadmap Karir

```mermaid
flowchart TD
    A([Buka Roadmap Karir]) --> B[Input Nama Peserta]
    B --> C[Input Posisi Saat Ini]
    C --> D[Input Target Posisi]
    D --> E[Pilih Timeline\n3 / 6 / 9 / 12 / 18 / 24 bulan]
    E --> F[Input Konteks Tambahan\nOpsional]
    F --> G[Pilih Konteks Silabus\nOpsional]
    G --> H[Klik Submit]

    H --> J[AI Analisis Gap Posisi\n& Timeline]
    J --> K[AI Susun Roadmap\nMulti-Phase]
    K --> L[Simpan ke Database]

    L --> M[Tampilkan Hasil]
    M --> M1[Metrik: Total Phase\nTotal Durasi, Timeline]
    M --> M2[Detail per Phase\nNama Phase + Rentang Bulan + Fokus]
    M --> M3[Modul per Phase\ndengan Urgensi Critical/Important/Nice-to-have]
    M1 & M2 & M3 --> N[Export TXT / DOCX / PDF]
    N --> Z([Selesai])
```

---

## 6. Riwayat & Export

```mermaid
flowchart TD
    A([Buka Riwayat & Export]) --> B[Ambil Semua Data Milik User]
    B --> C[Tampilkan 5 Tab]

    C --> T1[📋 Silabus]
    C --> T2[🔬 Modul Mikro]
    C --> T3[🎯 Personalisasi User]
    C --> T4[👥 Personalisasi Multi User]
    C --> T5[🗺️ Roadmap Karir]

    T1 --> T1A[Daftar Silabus per Expander\nTampilkan TLO / PCS / ELO]
    T1A --> T1B[Export TXT / DOCX / PDF]

    T2 --> T2A[Dikelompokkan per\nDokumen Sumber + Tanggal]
    T2A --> T2B[Tampilkan Modul Mikro]
    T2B --> T2C[Export TXT / DOCX / PDF]

    T3 --> T3A[Daftar Rekomendasi Personal]
    T3A --> T3B[Tampilkan Modul per Peserta]
    T3B --> T3C[Export TXT / DOCX / PDF]

    T4 --> T4A[Dikelompokkan per Sesi Batch]
    T4A --> T4B[Tampilkan Semua Peserta\ndalam 1 Group]
    T4B --> T4C[Export XLSX / DOCX / PDF\nper Batch]

    T5 --> T5A[Daftar Roadmap per Expander\nTampilkan Phase & Modul]
    T5A --> T5B[Export TXT / DOCX / PDF]
```

---

## 7. Alur End-to-End (Overview)

```mermaid
flowchart LR
    AUTH([Login / Register]) --> SYL

    SYL[📋 Generate Silabus\nWizard 6 Langkah\nOutput: silabus tersimpan di DB]
    SYL --> DEC
    SYL --> REC
    SYL --> BULK
    SYL --> ROAD

    DEC[🔬 Dekomposisi Modul\nInput: silabus + panduan\nOutput: modul mikro + timeline + quiz]
    REC[🎯 Personalisasi User\nInput: nama + gap + profil\nOutput: learning path personal]
    BULK[👥 Personalisasi Multi User\nInput: Excel peserta\nOutput: rekomendasi per peserta + level]
    ROAD[🗺️ Roadmap Karir\nInput: posisi awal → target\nOutput: roadmap multi-phase]

    DEC --> HIST
    REC --> HIST
    BULK --> HIST
    ROAD --> HIST

    HIST[📥 Riwayat & Export\nSemua hasil tersimpan\nExport DOCX / PDF / XLSX / TXT]
```
