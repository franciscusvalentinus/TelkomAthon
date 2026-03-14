"""
Example demonstrating Streamlit session state management

This example shows how the session state is initialized and managed
in the AI Syllabus Generator application.

Run with: streamlit run examples/streamlit_session_example.py
"""

import streamlit as st
import uuid
from src.models.entities import WorkflowStep, SessionData

st.set_page_config(
    page_title="Session State Example",
    page_icon="📚",
    layout="wide"
)

st.title("Session State Management Example")
st.markdown("---")

# Initialize session state (similar to app.py)
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

# Display current session state
st.subheader("Current Session State")

col1, col2 = st.columns(2)

with col1:
    st.write("**Session ID:**")
    st.code(st.session_state.session_id)
    
    st.write("**Current Step:**")
    st.info(st.session_state.current_step.value)
    
    st.write("**Organization:**")
    st.write(st.session_state.organization if st.session_state.organization else "None")

with col2:
    st.write("**Course Type:**")
    st.write(st.session_state.course_type if st.session_state.course_type else "None")
    
    st.write("**TLOs Count:**")
    st.write(len(st.session_state.tlos))
    
    st.write("**Selected TLO IDs:**")
    st.write(st.session_state.selected_tlo_ids if st.session_state.selected_tlo_ids else "None")

st.markdown("---")

# Demonstrate workflow step navigation
st.subheader("Workflow Step Navigation")

st.write("**All Workflow Steps:**")
for i, step in enumerate(WorkflowStep, 1):
    status = "✅" if step.value < st.session_state.current_step.value else "⭕"
    if step == st.session_state.current_step:
        status = "▶️"
    st.write(f"{status} {i}. {step.value}")

st.markdown("---")

# Simulate step advancement
st.subheader("Simulate Step Advancement")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("Next Step"):
        # Get all steps as a list
        all_steps = list(WorkflowStep)
        current_index = all_steps.index(st.session_state.current_step)
        
        # Advance to next step if not at the end
        if current_index < len(all_steps) - 1:
            st.session_state.current_step = all_steps[current_index + 1]
            st.rerun()

with col2:
    if st.button("Previous Step"):
        # Get all steps as a list
        all_steps = list(WorkflowStep)
        current_index = all_steps.index(st.session_state.current_step)
        
        # Go back to previous step if not at the beginning
        if current_index > 0:
            st.session_state.current_step = all_steps[current_index - 1]
            st.rerun()

with col3:
    if st.button("Reset"):
        # Clear all session state
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

st.markdown("---")

# Demonstrate SessionData creation
st.subheader("SessionData Object")

session_data = SessionData(
    session_id=st.session_state.session_id,
    current_step=st.session_state.current_step.value,
    organization=st.session_state.organization,
    course_type=st.session_state.course_type,
    tlos=st.session_state.tlos,
    performances=[],
    elos=[],
    syllabus=None
)

st.write("**SessionData object created from session state:**")
st.json({
    "session_id": session_data.session_id,
    "current_step": session_data.current_step,
    "organization": str(session_data.organization),
    "course_type": str(session_data.course_type),
    "tlos_count": len(session_data.tlos),
    "performances_count": len(session_data.performances),
    "elos_count": len(session_data.elos),
    "syllabus": str(session_data.syllabus)
})

st.markdown("---")
st.caption("This example demonstrates the session state management used in the main application.")
