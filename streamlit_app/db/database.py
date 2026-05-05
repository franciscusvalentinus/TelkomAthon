import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Load .env for local development
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def _get_secret(key: str, default: str = "") -> str:
    """Read from st.secrets (Streamlit Cloud) or os.environ (local)."""
    try:
        import streamlit as st
        val = st.secrets.get(key)
        if val is not None:
            return str(val)
    except Exception:
        pass
    return os.getenv(key, default)


def build_database_url() -> str:
    url = _get_secret("DATABASE_URL")
    if url:
        return url
    host = _get_secret("DATABASE_HOST")
    port = _get_secret("DATABASE_PORT", "5432")
    name = _get_secret("DATABASE_NAME", "postgres")
    user = _get_secret("DATABASE_USER")
    password = _get_secret("DATABASE_PASSWORD")
    return f"postgresql://{user}:{password}@{host}:{port}/{name}"


Base = declarative_base()

_engine = None
_SessionLocal = None


def _get_engine():
    global _engine
    if _engine is None:
        _engine = create_engine(build_database_url(), pool_pre_ping=True)
    return _engine


def _get_session_factory():
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_get_engine())
    return _SessionLocal


def get_db():
    db = _get_session_factory()()
    try:
        yield db
    finally:
        db.close()


def get_db_session():
    """Return a plain session for direct use."""
    return _get_session_factory()()
