"""Main Streamlit application entry point"""

import streamlit as st
import uuid
from src.config import get_config
from src.models.entities import WorkflowStep, SessionData
from src.database.service import DatabaseService
from src.services.ai_service import AIService
from src.workflow.orchestrator import WorkflowOrchestrator
from src.ui.pages import (
    render_upload_page,
    render_summary_page,
    render_course_type_page,
    render_tlo_page,
    render_performance_page,
    render_elo_page,
    render_syllabus_page
)

# Page configuration
st.set_page_config(
    page_title="Sistem Generasi Silabus AI",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Indonesian language UI labels
UI_LABELS = {
    "title": "📚 Sistem Generasi Silabus Berbasis AI",
    "subtitle": "Buat silabus kursus secara otomatis dengan bantuan AI",
    "steps": {
        WorkflowStep.UPLOAD: "1. Unggah Profil Organisasi",
        WorkflowStep.SUMMARY: "2. Ringkasan Profil",
        WorkflowStep.COURSE_TYPE: "3. Pilih Jenis Kursus",
        WorkflowStep.TLO_GENERATION: "4. Generasi TLO",
        WorkflowStep.TLO_SELECTION: "5. Pilih TLO",
        WorkflowStep.PERFORMANCE_GENERATION: "6. Generasi Performance",
        WorkflowStep.PERFORMANCE_SELECTION: "7. Pilih Performance",
        WorkflowStep.ELO_GENERATION: "8. Generasi ELO",
        WorkflowStep.ELO_SELECTION: "9. Pilih ELO",
        WorkflowStep.SYLLABUS_GENERATION: "10. Buat Silabus"
    },
    "errors": {
        "config": "❌ Kesalahan konfigurasi: {error}",
        "config_info": "Silakan periksa file .env Anda dan pastikan semua variabel yang diperlukan telah diatur.",
        "general": "❌ Terjadi kesalahan: {error}"
    },
    "success": {
        "config_loaded": "✅ Konfigurasi berhasil dimuat"
    },
    "sidebar": {
        "title": "Langkah-langkah",
        "current_step": "Langkah Saat Ini:",
        "session_id": "ID Sesi:",
        "reset": "Mulai Ulang"
    }
}


def initialize_session_state():
    """Initialize Streamlit session state for workflow management"""
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    
    if "current_step" not in st.session_state:
        st.session_state.current_step = WorkflowStep.UPLOAD
    
    if "organization" not in st.session_state:
        st.session_state.organization = None
    
    if "course_type" not in st.session_state:
        st.session_state.course_type = None
    
    if "tlos" not in st.session_state:
        st.session_state.tlos = []
    
    if "selected_tlo_ids" not in st.session_state:
        st.session_state.selected_tlo_ids = []
    
    if "performances" not in st.session_state:
        st.session_state.performances = []
    
    if "selected_performance_ids" not in st.session_state:
        st.session_state.selected_performance_ids = []
    
    if "elos" not in st.session_state:
        st.session_state.elos = []
    
    if "selected_elo_ids" not in st.session_state:
        st.session_state.selected_elo_ids = []
    
    if "syllabus" not in st.session_state:
        st.session_state.syllabus = None


def get_session_data() -> SessionData:
    """Get current session data from Streamlit session state"""
    return SessionData(
        session_id=st.session_state.session_id,
        current_step=st.session_state.current_step.value,
        organization=st.session_state.organization,
        course_type=st.session_state.course_type,
        tlos=st.session_state.tlos,
        performances=st.session_state.performances,
        elos=st.session_state.elos,
        syllabus=st.session_state.syllabus
    )


def render_sidebar():
    """Render sidebar with workflow steps and navigation"""
    with st.sidebar:
        st.title(UI_LABELS["sidebar"]["title"])
        st.markdown("---")
        
        # Display current step
        st.write(f"**{UI_LABELS['sidebar']['current_step']}**")
        current_step_label = UI_LABELS["steps"][st.session_state.current_step]
        st.info(current_step_label)
        
        st.markdown("---")
        
        # Display all workflow steps with status indicators
        st.write("**Progres:**")
        for step in WorkflowStep:
            step_label = UI_LABELS["steps"][step]
            
            # Determine step status
            if step == st.session_state.current_step:
                st.write(f"▶️ {step_label}")
            elif step.value < st.session_state.current_step.value:
                st.write(f"✅ {step_label}")
            else:
                st.write(f"⭕ {step_label}")
        
        st.markdown("---")
        
        # Display session ID
        st.write(f"**{UI_LABELS['sidebar']['session_id']}**")
        st.code(st.session_state.session_id[:8] + "...")
        
        # Reset button
        if st.button(UI_LABELS["sidebar"]["reset"], type="secondary"):
            # Clear all session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()


def render_main_content(orchestrator: WorkflowOrchestrator):
    """Render main content area based on current workflow step"""
    st.title(UI_LABELS["title"])
    st.caption(UI_LABELS["subtitle"])
    st.markdown("---")
    
    # Route to appropriate page based on current step
    current_step = st.session_state.current_step
    
    if current_step == WorkflowStep.UPLOAD:
        render_upload_page(orchestrator)
    
    elif current_step == WorkflowStep.SUMMARY:
        render_summary_page(orchestrator)
    
    elif current_step == WorkflowStep.COURSE_TYPE:
        render_course_type_page(orchestrator)
    
    elif current_step == WorkflowStep.TLO_GENERATION:
        render_tlo_page(orchestrator)
    
    elif current_step == WorkflowStep.TLO_SELECTION:
        # TLO generation and selection are combined in one page
        render_tlo_page(orchestrator)
    
    elif current_step == WorkflowStep.PERFORMANCE_GENERATION:
        render_performance_page(orchestrator)
    
    elif current_step == WorkflowStep.PERFORMANCE_SELECTION:
        # Performance generation and selection are combined in one page
        render_performance_page(orchestrator)
    
    elif current_step == WorkflowStep.ELO_GENERATION:
        render_elo_page(orchestrator)
    
    elif current_step == WorkflowStep.ELO_SELECTION:
        # ELO generation and selection are combined in one page
        render_elo_page(orchestrator)
    
    elif current_step == WorkflowStep.SYLLABUS_GENERATION:
        render_syllabus_page(orchestrator)


def main():
    """Main application function"""
    # Initialize session state
    initialize_session_state()
    
    # Try to load configuration
    try:
        config = get_config()
        # Configuration loaded successfully (don't show success message to reduce clutter)
    except ValueError as e:
        st.error(UI_LABELS["errors"]["config"].format(error=str(e)))
        st.info(UI_LABELS["errors"]["config_info"])
        return
    
    # Initialize services
    try:
        # Get database connection string from config
        db_connection_string = config.database.get_connection_string()
        db = DatabaseService(db_connection_string)
        # Cari baris ini di app.py
        ai = AIService(config.azure_openai) # Tambahkan .azure_openai
        orchestrator = WorkflowOrchestrator(db, ai)
    except Exception as e:
        st.error(f"❌ Gagal menginisialisasi layanan: {str(e)}")
        st.info("Silakan periksa konfigurasi database dan API Anda.")
        return
    
    # Render sidebar
    render_sidebar()
    
    # Render main content
    render_main_content(orchestrator)


if __name__ == "__main__":
    main()
