# Streamlit Application Structure

## Overview

The main Streamlit application (`app.py`) provides the foundation for the AI-Powered Syllabus Generation System. It implements:

1. **Session State Management** - Persistent state across page interactions
2. **Page Routing** - Navigation between workflow steps
3. **Indonesian Language UI** - All labels and messages in Indonesian

## Architecture

### Session State Management

The application uses Streamlit's session state to maintain workflow data across user interactions:

```python
# Core session state variables
- session_id: Unique identifier for the user session
- current_step: Current workflow step (WorkflowStep enum)
- organization: Organization profile data
- course_type: Selected course type
- tlos: List of generated TLOs
- selected_tlo_ids: IDs of selected TLOs
- performances: List of generated performances
- selected_performance_ids: IDs of selected performances
- elos: List of generated ELOs
- selected_elo_ids: IDs of selected ELOs
- syllabus: Generated syllabus document
```

### Workflow Steps

The application supports 10 workflow steps defined in `WorkflowStep` enum:

1. **UPLOAD** - Upload organization profile document
2. **SUMMARY** - View organization profile summary
3. **COURSE_TYPE** - Select course type
4. **TLO_GENERATION** - Generate Terminal Learning Objectives
5. **TLO_SELECTION** - Select TLOs
6. **PERFORMANCE_GENERATION** - Generate performance objectives
7. **PERFORMANCE_SELECTION** - Select performances
8. **ELO_GENERATION** - Generate Enabling Learning Objectives
9. **ELO_SELECTION** - Select ELOs
10. **SYLLABUS_GENERATION** - Generate final syllabus document

### Page Routing

The `render_main_content()` function routes to the appropriate page based on `current_step`:

```python
def render_main_content():
    current_step = st.session_state.current_step
    
    if current_step == WorkflowStep.UPLOAD:
        # Render upload page
    elif current_step == WorkflowStep.SUMMARY:
        # Render summary page
    # ... etc
```

### Sidebar Navigation

The sidebar displays:
- Current workflow step indicator
- Progress through all steps (✅ completed, ▶️ current, ⭕ pending)
- Session ID (truncated)
- Reset button to start over

## Indonesian Language UI

All UI labels are defined in the `UI_LABELS` dictionary:

```python
UI_LABELS = {
    "title": "📚 Sistem Generasi Silabus Berbasis AI",
    "subtitle": "Buat silabus kursus secara otomatis dengan bantuan AI",
    "steps": {
        WorkflowStep.UPLOAD: "1. Unggah Profil Organisasi",
        # ... etc
    },
    "errors": {
        "config": "❌ Kesalahan konfigurasi: {error}",
        # ... etc
    },
    # ... etc
}
```

## UI Utilities

The `src/ui/utils.py` module provides helper functions:

- `show_error(message)` - Display error message
- `show_success(message)` - Display success message
- `show_info(message)` - Display info message
- `show_warning(message)` - Display warning message
- `with_spinner(message)` - Show loading spinner
- `confirm_action(message, button_text)` - Confirmation dialog
- `safe_execute(func, error_message)` - Execute function with error handling

## Usage

### Running the Application

```bash
streamlit run app.py
```

### Running the Example

```bash
streamlit run examples/streamlit_session_example.py
```

### Testing

```bash
pytest tests/unit/test_streamlit_app.py -v
```

## Implementation Status

✅ **Completed (Task 9.1):**
- Session state initialization and management
- Workflow step routing structure
- Indonesian language UI labels
- Sidebar with progress indicators
- UI utility functions
- Unit tests for core functionality

🚧 **Pending (Tasks 9.2-9.8):**
- Individual page implementations for each workflow step
- Integration with WorkflowOrchestrator
- File upload and processing
- AI content generation UI
- Selection interfaces
- Document download

## Next Steps

The following tasks will implement the individual pages:

- **Task 9.2** - Organization profile upload page
- **Task 9.3** - Organization summary display page
- **Task 9.4** - Course type selection page
- **Task 9.5** - TLO generation and selection page
- **Task 9.6** - Performance generation and selection page
- **Task 9.7** - ELO generation and selection page
- **Task 9.8** - Syllabus generation and download page

## Requirements Validation

This implementation satisfies:

- **Requirement 13.1** - Uses Streamlit for web interface ✅
- **Requirement 13.5** - All content displayed in Indonesian language ✅

Additional requirements will be satisfied as individual pages are implemented in subsequent tasks.
