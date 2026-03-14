"""Unit tests for Streamlit application structure"""

import pytest
from unittest.mock import Mock, patch
from src.models.entities import WorkflowStep, SessionData


class TestSessionStateManagement:
    """Test session state initialization and management"""
    
    def test_ui_labels_contain_all_workflow_steps(self):
        """Test that UI labels are defined for all workflow steps"""
        # Import here to avoid Streamlit initialization issues
        import sys
        from io import StringIO
        
        # Capture any Streamlit warnings
        old_stderr = sys.stderr
        sys.stderr = StringIO()
        
        try:
            # Import the UI_LABELS from app.py
            import importlib.util
            spec = importlib.util.spec_from_file_location("app", "app.py")
            app_module = importlib.util.module_from_spec(spec)
            
            # Mock streamlit before loading
            sys.modules['streamlit'] = Mock()
            spec.loader.exec_module(app_module)
            
            UI_LABELS = app_module.UI_LABELS
            
            # Verify all workflow steps have labels
            for step in WorkflowStep:
                assert step in UI_LABELS["steps"], f"Missing label for {step}"
                assert isinstance(UI_LABELS["steps"][step], str)
                assert len(UI_LABELS["steps"][step]) > 0
        finally:
            sys.stderr = old_stderr
    
    def test_ui_labels_are_in_indonesian(self):
        """Test that UI labels contain Indonesian text"""
        import sys
        from io import StringIO
        
        old_stderr = sys.stderr
        sys.stderr = StringIO()
        
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("app", "app.py")
            app_module = importlib.util.module_from_spec(spec)
            
            sys.modules['streamlit'] = Mock()
            spec.loader.exec_module(app_module)
            
            UI_LABELS = app_module.UI_LABELS
            
            # Check for common Indonesian words in labels
            indonesian_indicators = [
                "Sistem", "Silabus", "Profil", "Organisasi", 
                "Pilih", "Jenis", "Kursus", "Buat"
            ]
            
            # Convert all labels to a single string
            all_labels = str(UI_LABELS)
            
            # At least some Indonesian words should be present
            found_indonesian = any(word in all_labels for word in indonesian_indicators)
            assert found_indonesian, "UI labels should contain Indonesian text"
        finally:
            sys.stderr = old_stderr
    
    def test_session_data_structure(self):
        """Test that SessionData can be created with required fields"""
        session_data = SessionData(
            session_id="test-123",
            current_step=WorkflowStep.UPLOAD.value,
            organization=None,
            course_type=None,
            tlos=[],
            performances=[],
            elos=[],
            syllabus=None
        )
        
        assert session_data.session_id == "test-123"
        assert session_data.current_step == WorkflowStep.UPLOAD.value
        assert session_data.organization is None
        assert session_data.course_type is None
        assert len(session_data.tlos) == 0
        assert len(session_data.performances) == 0
        assert len(session_data.elos) == 0
        assert session_data.syllabus is None


class TestWorkflowStepRouting:
    """Test workflow step routing logic"""
    
    def test_all_workflow_steps_defined(self):
        """Test that all workflow steps are defined in WorkflowStep enum"""
        expected_steps = [
            "UPLOAD",
            "SUMMARY",
            "COURSE_TYPE",
            "TLO_GENERATION",
            "TLO_SELECTION",
            "PERFORMANCE_GENERATION",
            "PERFORMANCE_SELECTION",
            "ELO_GENERATION",
            "ELO_SELECTION",
            "SYLLABUS_GENERATION"
        ]
        
        actual_steps = [step.name for step in WorkflowStep]
        
        for expected in expected_steps:
            assert expected in actual_steps, f"Missing workflow step: {expected}"
    
    def test_workflow_step_values(self):
        """Test that workflow steps have correct string values"""
        assert WorkflowStep.UPLOAD.value == "upload"
        assert WorkflowStep.SUMMARY.value == "summary"
        assert WorkflowStep.COURSE_TYPE.value == "course_type"
        assert WorkflowStep.TLO_GENERATION.value == "tlo_generation"
        assert WorkflowStep.TLO_SELECTION.value == "tlo_selection"
        assert WorkflowStep.PERFORMANCE_GENERATION.value == "performance_generation"
        assert WorkflowStep.PERFORMANCE_SELECTION.value == "performance_selection"
        assert WorkflowStep.ELO_GENERATION.value == "elo_generation"
        assert WorkflowStep.ELO_SELECTION.value == "elo_selection"
        assert WorkflowStep.SYLLABUS_GENERATION.value == "syllabus_generation"


class TestUIUtilities:
    """Test UI utility functions"""
    
    def test_ui_utils_imports(self):
        """Test that UI utilities can be imported"""
        from src.ui import (
            show_error,
            show_success,
            show_info,
            show_warning,
            with_spinner,
            confirm_action,
            safe_execute
        )
        
        # Verify all functions are callable
        assert callable(show_error)
        assert callable(show_success)
        assert callable(show_info)
        assert callable(show_warning)
        assert callable(with_spinner)
        assert callable(confirm_action)
        assert callable(safe_execute)
    
    @patch('streamlit.error')
    def test_safe_execute_handles_errors(self, mock_error):
        """Test that safe_execute handles errors gracefully"""
        from src.ui import safe_execute
        
        def failing_function():
            raise ValueError("Test error")
        
        result = safe_execute(failing_function, "Operasi gagal")
        
        assert result is None
        # Verify error was displayed (mock was called)
        assert mock_error.called
    
    @patch('streamlit.error')
    def test_safe_execute_returns_result(self, mock_error):
        """Test that safe_execute returns function result on success"""
        from src.ui import safe_execute
        
        def successful_function():
            return "success"
        
        result = safe_execute(successful_function)
        
        assert result == "success"
        # Verify no error was displayed
        assert not mock_error.called
