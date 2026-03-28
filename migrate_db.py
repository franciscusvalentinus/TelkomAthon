"""
migrate_db.py — Database migration script for TelkomAthon LDD AI Assistant
Run once to set up all tables and indexes in Supabase/PostgreSQL.

Usage:
    python migrate_db.py
"""

import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError, ProgrammingError

load_dotenv()


def build_database_url() -> str:
    url = os.getenv("DATABASE_URL")
    if url:
        return url
    host = os.getenv("DATABASE_HOST")
    port = os.getenv("DATABASE_PORT", "5432")
    name = os.getenv("DATABASE_NAME", "postgres")
    user = os.getenv("DATABASE_USER")
    password = os.getenv("DATABASE_PASSWORD")
    if not all([host, user, password]):
        print("ERROR: Database credentials not found in .env")
        print("Required: DATABASE_URL  OR  DATABASE_HOST + DATABASE_USER + DATABASE_PASSWORD")
        sys.exit(1)
    return f"postgresql://{user}:{password}@{host}:{port}/{name}"


MIGRATION_SQL = """
-- 1. Enable pgvector extension
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

-- 4. Document Chunks (for RAG / vector search)
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
"""

STEPS = [
    ("Enable pgvector extension",       "CREATE EXTENSION IF NOT EXISTS vector"),
    ("Create table: users",             "CREATE TABLE IF NOT EXISTS users"),
    ("Create table: documents",         "CREATE TABLE IF NOT EXISTS documents"),
    ("Create table: document_chunks",   "CREATE TABLE IF NOT EXISTS document_chunks"),
    ("Create table: syllabi",           "CREATE TABLE IF NOT EXISTS syllabi"),
    ("Create table: micro_modules",     "CREATE TABLE IF NOT EXISTS micro_modules"),
    ("Create table: recommendations",   "CREATE TABLE IF NOT EXISTS recommendations"),
]


def run_migration():
    db_url = build_database_url()
    print(f"Connecting to database...")

    try:
        engine = create_engine(db_url)
        with engine.connect() as conn:
            print("Connected.\n")
            print("Running migration...\n")

            # Execute the full migration as a single transaction
            conn.execute(text(MIGRATION_SQL))
            conn.commit()

            # Print step-by-step confirmation
            for label, _ in STEPS:
                print(f"  ✓ {label}")

            print("\nMigration completed successfully.")

    except OperationalError as e:
        print(f"\nERROR: Could not connect to database.\n{e}")
        sys.exit(1)
    except ProgrammingError as e:
        print(f"\nERROR: SQL error during migration.\n{e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    run_migration()
