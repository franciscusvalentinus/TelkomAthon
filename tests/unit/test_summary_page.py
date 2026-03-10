"""Unit tests for organization summary display page"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime
from src.models.entities import OrganizationProfile, WorkflowStep


class TestSummaryPageRendering:
    """Test summary page rendering and UI elements"""
    
    @patch('streamlit.session_state')
    @patch('streamlit.header')
    @patch('streamlit.write')
    @patch('streamlit.markdown')
    @patch('streamlit.subheader')
    @patch('streamlit.columns')
    @patch('streamlit.metric')
    @patch('streamlit.expander')
    @patch('streamlit.text_area')
    @patch('streamlit.button')
    @patch('streamlit.info')
    def test_render_summary_page_displays_organization_info(
        self,
        mock_info,
        mock_button,
        mock_text_area,
        mock_expander,
        mock_metric,
        mock_columns,
        mock_subheader,
        mock_markdown,
        mock_write,
        mock_header,
        mock_session_state
    ):
        """Test that summary page renders organization profile information"""
        from src.ui.pages import render_summary_page
        
        # Mock organization profile
        mock_profile = OrganizationProfile(
            id="test-id",
            original_text="Original organization profile text",
            summary="Test organization summary",
            context_overview="Test context overview",
            file_name="test_profile.pdf",
            file_type=".pdf",
            uploaded_at=datetime(2024, 1, 15, 10, 30)
        )
        
        # Mock session state
        mock_session_state.organization = mock_profile
        
        # Mock orchestrator
        mock_orchestrator = Mock()
        
        # Mock columns
        mock_col = Mock()
        mock_col.__enter__ = Mock(return_value=mock_col)
        mock_col.__exit__ = Mock()
        mock_columns.return_value = [mock_col, mock_col, mock_col]
        
        # Mock expander
        mock_expander_ctx = Mock()
        mock_expander_ctx.__enter__ = Mock(return_value=mock_expander_ctx)
        mock_expander_ctx.__exit__ = Mock()
        mock_expander.return_value = mock_expander_ctx
        
        # Mock button to return False
        mock_button.return_value = False
        
        # Render page
        render_summary_page(mock_orchestrator)
        
        # Verify header is displayed
        mock_header.assert_called_once()
        assert "Ringkasan Profil Organisasi" in str(mock_header.call_args)
        
        # Verify subheaders are displayed
        assert mock_subheader.called
        subheader_calls = [str(call) for call in mock_subheader.call_args_list]
        assert any("Informasi File" in call for call in subheader_calls)
        assert any("Ringkasan Profil" in call for call in subheader_calls)
        assert any("Konteks Organisasi" in call for call in subheader_calls)
        
        # Verify metrics are displayed (file info)
        assert mock_metric.called
        metric_calls = [str(call) for call in mock_metric.call_args_list]
        assert any("test_profile.pdf" in call for call in metric_calls)
        assert any("PDF" in call for call in metric_calls)
    
    @patch('streamlit.session_state')
    @patch('streamlit.header')
    @patch('streamlit.write')
    @patch('src.ui.utils.show_error')
    @patch('streamlit.button')
    @patch('streamlit.rerun')
    def test_render_summary_page_handles_missing_organization(
        self,
        mock_rerun,
        mock_button,
        mock_show_error,
        mock_write,
        mock_header,
        mock_session_state
    ):
        """Test that summary page handles missing organization profile"""
        from src.ui.pages import render_summary_page
        
        # Mock session state with no organization
        mock_session_state.organization = None
        
        # Mock orchestrator
        mock_orchestrator = Mock()
        
        # Mock button to return False
        mock_button.return_value = False
        
        # Render page
        render_summary_page(mock_orchestrator)
        
        # Verify error message is shown
        assert mock_show_error.called
        error_message = str(mock_show_error.call_args)
        assert "tidak ditemukan" in error_message.lower() or "unggah dokumen" in error_message.lower()
        
        # Verify back button is displayed
        assert mock_button.called
    
    @patch('streamlit.session_state')
    @patch('streamlit.header')
    @patch('streamlit.write')
    @patch('streamlit.markdown')
    @patch('streamlit.subheader')
    @patch('streamlit.columns')
    @patch('streamlit.metric')
    @patch('streamlit.expander')
    @patch('streamlit.text_area')
    @patch('streamlit.button')
    @patch('streamlit.info')
    def test_render_summary_page_displays_summary_content(
        self,
        mock_info,
        mock_button,
        mock_text_area,
        mock_expander,
        mock_metric,
        mock_columns,
        mock_subheader,
        mock_markdown,
        mock_write,
        mock_header,
        mock_session_state
    ):
        """Test that summary and context overview are displayed"""
        from src.ui.pages import render_summary_page
        
        # Mock organization profile with specific content
        mock_profile = OrganizationProfile(
            id="test-id",
            original_text="Original text",
            summary="This is the organization summary",
            context_overview="This is the context overview",
            file_name="test.pdf",
            file_type=".pdf"
        )
        
        # Mock session state
        mock_session_state.organization = mock_profile
        
        # Mock orchestrator
        mock_orchestrator = Mock()
        
        # Mock columns
        mock_col = Mock()
        mock_col.__enter__ = Mock(return_value=mock_col)
        mock_col.__exit__ = Mock()
        mock_columns.return_value = [mock_col, mock_col, mock_col]
        
        # Mock expander
        mock_expander_ctx = Mock()
        mock_expander_ctx.__enter__ = Mock(return_value=mock_expander_ctx)
        mock_expander_ctx.__exit__ = Mock()
        mock_expander.return_value = mock_expander_ctx
        
        # Mock button to return False
        mock_button.return_value = False
        
        # Render page
        render_summary_page(mock_orchestrator)
        
        # Verify markdown is called with summary and context
        markdown_calls = [str(call) for call in mock_markdown.call_args_list]
        assert any("organization summary" in call.lower() for call in markdown_calls)
        assert any("context overview" in call.lower() for call in markdown_calls)


class TestSummaryPageNavigation:
    """Test navigation buttons on summary page"""
    
    @patch('streamlit.session_state')
    @patch('streamlit.header')
    @patch('streamlit.write')
    @patch('streamlit.markdown')
    @patch('streamlit.subheader')
    @patch('streamlit.columns')
    @patch('streamlit.metric')
    @patch('streamlit.expander')
    @patch('streamlit.text_area')
    @patch('streamlit.button')
    @patch('streamlit.info')
    @patch('streamlit.rerun')
    def test_back_button_navigates_to_upload(
        self,
        mock_rerun,
        mock_info,
        mock_button,
        mock_text_area,
        mock_expander,
        mock_metric,
        mock_columns,
        mock_subheader,
        mock_markdown,
        mock_write,
        mock_header,
        mock_session_state
    ):
        """Test that back button navigates to upload page"""
        from src.ui.pages import render_summary_page
        
        # Mock organization profile
        mock_profile = OrganizationProfile(
            id="test-id",
            original_text="Original text",
            summary="Summary",
            context_overview="Context",
            file_name="test.pdf",
            file_type=".pdf"
        )
        
        # Mock session state
        mock_session_state.organization = mock_profile
        mock_session_state.current_step = WorkflowStep.SUMMARY
        
        # Mock orchestrator
        mock_orchestrator = Mock()
        
        # Mock columns
        mock_col = Mock()
        mock_col.__enter__ = Mock(return_value=mock_col)
        mock_col.__exit__ = Mock()
        mock_columns.return_value = [mock_col, mock_col, mock_col]
        
        # Mock expander
        mock_expander_ctx = Mock()
        mock_expander_ctx.__enter__ = Mock(return_value=mock_expander_ctx)
        mock_expander_ctx.__exit__ = Mock()
        mock_expander.return_value = mock_expander_ctx
        
        # Mock button - first call (back button) returns True
        mock_button.side_effect = [True, False]
        
        # Render page
        render_summary_page(mock_orchestrator)
        
        # Verify current step was changed to UPLOAD
        assert mock_session_state.current_step == WorkflowStep.UPLOAD
        
        # Verify rerun was called
        assert mock_rerun.called
    
    @patch('streamlit.session_state')
    @patch('streamlit.header')
    @patch('streamlit.write')
    @patch('streamlit.markdown')
    @patch('streamlit.subheader')
    @patch('streamlit.columns')
    @patch('streamlit.metric')
    @patch('streamlit.expander')
    @patch('streamlit.text_area')
    @patch('streamlit.button')
    @patch('streamlit.info')
    @patch('streamlit.rerun')
    def test_continue_button_navigates_to_course_type(
        self,
        mock_rerun,
        mock_info,
        mock_button,
        mock_text_area,
        mock_expander,
        mock_metric,
        mock_columns,
        mock_subheader,
        mock_markdown,
        mock_write,
        mock_header,
        mock_session_state
    ):
        """Test that continue button navigates to course type selection"""
        from src.ui.pages import render_summary_page
        
        # Mock organization profile
        mock_profile = OrganizationProfile(
            id="test-id",
            original_text="Original text",
            summary="Summary",
            context_overview="Context",
            file_name="test.pdf",
            file_type=".pdf"
        )
        
        # Mock session state
        mock_session_state.organization = mock_profile
        mock_session_state.current_step = WorkflowStep.SUMMARY
        
        # Mock orchestrator
        mock_orchestrator = Mock()
        
        # Mock columns
        mock_col = Mock()
        mock_col.__enter__ = Mock(return_value=mock_col)
        mock_col.__exit__ = Mock()
        mock_columns.return_value = [mock_col, mock_col, mock_col]
        
        # Mock expander
        mock_expander_ctx = Mock()
        mock_expander_ctx.__enter__ = Mock(return_value=mock_expander_ctx)
        mock_expander_ctx.__exit__ = Mock()
        mock_expander.return_value = mock_expander_ctx
        
        # Mock button - second call (continue button) returns True
        mock_button.side_effect = [False, True]
        
        # Render page
        render_summary_page(mock_orchestrator)
        
        # Verify current step was changed to COURSE_TYPE
        assert mock_session_state.current_step == WorkflowStep.COURSE_TYPE
        
        # Verify rerun was called
        assert mock_rerun.called


class TestIndonesianLanguage:
    """Test that summary page uses Indonesian language"""
    
    def test_summary_page_uses_indonesian_labels(self):
        """Test that summary page contains Indonesian text"""
        from src.ui import pages
        import inspect
        
        # Get source code of render_summary_page
        source = inspect.getsource(pages.render_summary_page)
        
        # Check for Indonesian keywords
        indonesian_keywords = [
            "Ringkasan Profil Organisasi",
            "Informasi File",
            "Konteks Organisasi",
            "Lanjutkan",
            "Kembali",
            "Nama File",
            "Tipe File"
        ]
        
        # All keywords should be present
        found_keywords = [kw for kw in indonesian_keywords if kw in source]
        assert len(found_keywords) >= 5, f"Summary page should use Indonesian labels. Found: {found_keywords}"
    
    def test_summary_page_error_messages_indonesian(self):
        """Test that error messages are in Indonesian"""
        from src.ui import pages
        import inspect
        
        # Get source code
        source = inspect.getsource(pages.render_summary_page)
        
        # Check for Indonesian error message keywords
        error_keywords = [
            "tidak ditemukan",
            "Silakan",
            "unggah dokumen"
        ]
        
        # At least some error keywords should be present
        found_keywords = [kw for kw in error_keywords if kw in source]
        assert len(found_keywords) >= 2, f"Error messages should be in Indonesian. Found: {found_keywords}"


class TestRequirementsValidation:
    """Test that summary page meets requirements"""
    
    @patch('streamlit.session_state')
    @patch('streamlit.header')
    @patch('streamlit.write')
    @patch('streamlit.markdown')
    @patch('streamlit.subheader')
    @patch('streamlit.columns')
    @patch('streamlit.metric')
    @patch('streamlit.expander')
    @patch('streamlit.text_area')
    @patch('streamlit.button')
    @patch('streamlit.info')
    def test_displays_organization_profile_summary(
        self,
        mock_info,
        mock_button,
        mock_text_area,
        mock_expander,
        mock_metric,
        mock_columns,
        mock_subheader,
        mock_markdown,
        mock_write,
        mock_header,
        mock_session_state
    ):
        """Test requirement 2.2: Display organization profile summary"""
        from src.ui.pages import render_summary_page
        
        # Mock organization profile
        mock_profile = OrganizationProfile(
            id="test-id",
            original_text="Original text",
            summary="Organization profile summary",
            context_overview="Context overview",
            file_name="test.pdf",
            file_type=".pdf"
        )
        
        # Mock session state
        mock_session_state.organization = mock_profile
        
        # Mock orchestrator
        mock_orchestrator = Mock()
        
        # Mock columns
        mock_col = Mock()
        mock_col.__enter__ = Mock(return_value=mock_col)
        mock_col.__exit__ = Mock()
        mock_columns.return_value = [mock_col, mock_col, mock_col]
        
        # Mock expander
        mock_expander_ctx = Mock()
        mock_expander_ctx.__enter__ = Mock(return_value=mock_expander_ctx)
        mock_expander_ctx.__exit__ = Mock()
        mock_expander.return_value = mock_expander_ctx
        
        # Mock button to return False
        mock_button.return_value = False
        
        # Render page
        render_summary_page(mock_orchestrator)
        
        # Verify summary is displayed in markdown
        markdown_calls = [str(call) for call in mock_markdown.call_args_list]
        assert any("Organization profile summary" in call for call in markdown_calls)
    
    @patch('streamlit.session_state')
    @patch('streamlit.header')
    @patch('streamlit.write')
    @patch('streamlit.markdown')
    @patch('streamlit.subheader')
    @patch('streamlit.columns')
    @patch('streamlit.metric')
    @patch('streamlit.expander')
    @patch('streamlit.text_area')
    @patch('streamlit.button')
    @patch('streamlit.info')
    def test_displays_context_overview(
        self,
        mock_info,
        mock_button,
        mock_text_area,
        mock_expander,
        mock_metric,
        mock_columns,
        mock_subheader,
        mock_markdown,
        mock_write,
        mock_header,
        mock_session_state
    ):
        """Test requirement 2.3: Display context overview"""
        from src.ui.pages import render_summary_page
        
        # Mock organization profile
        mock_profile = OrganizationProfile(
            id="test-id",
            original_text="Original text",
            summary="Summary",
            context_overview="Organization context overview",
            file_name="test.pdf",
            file_type=".pdf"
        )
        
        # Mock session state
        mock_session_state.organization = mock_profile
        
        # Mock orchestrator
        mock_orchestrator = Mock()
        
        # Mock columns
        mock_col = Mock()
        mock_col.__enter__ = Mock(return_value=mock_col)
        mock_col.__exit__ = Mock()
        mock_columns.return_value = [mock_col, mock_col, mock_col]
        
        # Mock expander
        mock_expander_ctx = Mock()
        mock_expander_ctx.__enter__ = Mock(return_value=mock_expander_ctx)
        mock_expander_ctx.__exit__ = Mock()
        mock_expander.return_value = mock_expander_ctx
        
        # Mock button to return False
        mock_button.return_value = False
        
        # Render page
        render_summary_page(mock_orchestrator)
        
        # Verify context overview is displayed in markdown
        markdown_calls = [str(call) for call in mock_markdown.call_args_list]
        assert any("Organization context overview" in call for call in markdown_calls)
    
    @patch('streamlit.session_state')
    @patch('streamlit.header')
    @patch('streamlit.write')
    @patch('streamlit.markdown')
    @patch('streamlit.subheader')
    @patch('streamlit.columns')
    @patch('streamlit.metric')
    @patch('streamlit.expander')
    @patch('streamlit.text_area')
    @patch('streamlit.button')
    @patch('streamlit.info')
    def test_has_continue_button(
        self,
        mock_info,
        mock_button,
        mock_text_area,
        mock_expander,
        mock_metric,
        mock_columns,
        mock_subheader,
        mock_markdown,
        mock_write,
        mock_header,
        mock_session_state
    ):
        """Test requirement 13.4: Add continue button to next step"""
        from src.ui.pages import render_summary_page
        
        # Mock organization profile
        mock_profile = OrganizationProfile(
            id="test-id",
            original_text="Original text",
            summary="Summary",
            context_overview="Context",
            file_name="test.pdf",
            file_type=".pdf"
        )
        
        # Mock session state
        mock_session_state.organization = mock_profile
        
        # Mock orchestrator
        mock_orchestrator = Mock()
        
        # Mock columns
        mock_col = Mock()
        mock_col.__enter__ = Mock(return_value=mock_col)
        mock_col.__exit__ = Mock()
        mock_columns.return_value = [mock_col, mock_col, mock_col]
        
        # Mock expander
        mock_expander_ctx = Mock()
        mock_expander_ctx.__enter__ = Mock(return_value=mock_expander_ctx)
        mock_expander_ctx.__exit__ = Mock()
        mock_expander.return_value = mock_expander_ctx
        
        # Mock button to return False
        mock_button.return_value = False
        
        # Render page
        render_summary_page(mock_orchestrator)
        
        # Verify button is called (should have back and continue buttons)
        assert mock_button.call_count >= 2
        
        # Check button labels
        button_calls = [str(call) for call in mock_button.call_args_list]
        assert any("Lanjutkan" in call or "Lanjut" in call for call in button_calls)
