"""Centralized config reader — works on Streamlit Cloud (st.secrets) and local (.env)."""
import os

# Load .env for local development
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import streamlit as st


def get_secret(key: str, default: str = "") -> str:
    try:
        val = st.secrets.get(key)
        if val is not None:
            return str(val)
    except Exception:
        pass
    return os.getenv(key, default)
