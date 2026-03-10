"""UI utility functions for Streamlit application"""

import streamlit as st
from typing import Callable, Any


def show_error(message: str):
    """Display error message in Indonesian"""
    st.error(f"❌ {message}")


def show_success(message: str):
    """Display success message in Indonesian"""
    st.success(f"✅ {message}")


def show_info(message: str):
    """Display info message in Indonesian"""
    st.info(f"ℹ️ {message}")


def show_warning(message: str):
    """Display warning message in Indonesian"""
    st.warning(f"⚠️ {message}")


def with_spinner(message: str):
    """Context manager for showing spinner with Indonesian message"""
    return st.spinner(f"⏳ {message}")


def confirm_action(message: str, button_text: str = "Konfirmasi") -> bool:
    """Show confirmation dialog and return True if confirmed"""
    return st.button(button_text, help=message)


def safe_execute(func: Callable, error_message: str = "Terjadi kesalahan") -> Any:
    """
    Execute function safely and handle errors with Indonesian messages
    
    Args:
        func: Function to execute
        error_message: Error message to display if function fails
        
    Returns:
        Function result or None if error occurred
    """
    try:
        return func()
    except Exception as e:
        show_error(f"{error_message}: {str(e)}")
        return None
