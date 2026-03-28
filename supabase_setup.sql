-- ============================================================
-- TelkomAthon 2025 — LDD AI Assistant
-- Jalankan script ini di Supabase SQL Editor (satu kali)
-- ============================================================

-- 1. Enable pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Users
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    full_name TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 3. Documents
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    filename TEXT NOT NULL,
    file_type TEXT,
    content TEXT,
    uploaded_at TIMESTAMP DEFAULT NOW()
);

-- 4. Document Chunks (for RAG)
CREATE TABLE IF NOT EXISTS document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    chunk_text TEXT NOT NULL,
    embedding VECTOR(3072),
    chunk_index INT
);

-- 5. Syllabi
CREATE TABLE IF NOT EXISTS syllabi (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    topic TEXT,
    level TEXT,
    output_json JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 6. Micro Modules
CREATE TABLE IF NOT EXISTS micro_modules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    source_document_id UUID REFERENCES documents(id) ON DELETE SET NULL,
    title TEXT,
    objective TEXT,
    summary TEXT,
    delivery_format TEXT,
    duration_minutes INT,
    embedding VECTOR(3072),
    created_at TIMESTAMP DEFAULT NOW()
);

-- 7. Recommendations
CREATE TABLE IF NOT EXISTS recommendations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    participant_name TEXT,
    gap_input TEXT,
    recommended_modules JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 8. Vector indexes skipped — Supabase pgvector limits indexes to <=2000 dims.
-- Cosine similarity queries work via sequential scan (sufficient for this scale).
