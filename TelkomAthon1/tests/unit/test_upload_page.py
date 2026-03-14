"""Unit tests for organization profile upload page"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from io import BytesIO
from src.models.entities import OrganizationProfile, WorkflowStep
from src.processors.document_processor import UnsupportedFormatError, EmptyFileError


class TestUploadPageRendering:
    """Test upload page rendering and UI elements"""
    
    @patch('streamlit.header')
    @patch('streamlit.write')
    @patch('streamlit.info')
    @patch('streamlit.file_uploader')
    @patch('streamlit.markdown')
    def test_render_upload_page_displays_ui_elements(
        self,
        mock_markdown,
        mock_uploader,
        mock_info,
        mock_write,
        mock_header
    ):
        """Test that upload page renders all required UI elements"""
        from src.ui.pages import render_upload_page
        
        # Mock orchestrator
        mock_orchestrator = Mock()
        
        # Mock file uploader to return None (no file uploaded)
        mock_uploader.return_value = None
        
        # Render page
        render_upload_page(mock_orchestrator)
        
        # Verify header is displayed
        mock_header.assert_called_once()
        assert "Unggah Profil Organisasi" in str(mock_header.call_args)
        
        # Verify file uploader is created
        mock_uploader.assert_called_once()
        call_kwargs = mock_uploader.call_args[1]
        assert 'pdf' in call_kwargs['type']
        assert 'docx' in call_kwargs['type']
        assert 'txt' in call_kwargs['type']
        
        # Verify info message about supported formats is shown
        assert mock_info.called
    
    @patch('streamlit.header')
    @patch('streamlit.write')
    @patch('streamlit.info')
    @patch('streamlit.file_uploader')
    @patch('streamlit.success')
    @patch('streamlit.button')
    @patch('streamlit.columns')
    @patch('streamlit.markdown')
    def test_render_upload_page_shows_file_info_when_uploaded(
        self,
        mock_markdown,
        mock_columns,
        mock_button,
        mock_success,
        mock_uploader,
        mock_info,
        mock_write,
        mock_header
    ):
        """Test that file info is displayed when a file is uploaded"""
        from src.ui.pages import render_upload_page
        
        # Mock orchestrator
        mock_orchestrator = Mock()
        
        # Mock uploaded file
        mock_file = Mock()
        mock_file.name = "test_profile.pdf"
        mock_file.size = 1024 * 100  # 100 KB
        mock_file.type = "application/pdf"
        mock_uploader.return_value = mock_file
        
        # Mock columns to return mock column objects
        mock_col = Mock()
        mock_columns.return_value = [mock_col, mock_col, mock_col]
        
        # Mock button to return False (not clicked)
        mock_button.return_value = False
        
        # Render page
        render_upload_page(mock_orchestrator)
        
        # Verify file info is displayed
        assert mock_success.called
        success_message = str(mock_success.call_args)
        assert "test_profile.pdf" in success_message
        
        # Verify button is created
        mock_button.assert_called_once()


class TestDocumentProcessing:
    """Test document processing functionality"""
    
    @patch('streamlit.session_state', {})
    @patch('streamlit.spinner')
    @patch('streamlit.success')
    @patch('streamlit.balloons')
    @patch('streamlit.markdown')
    @patch('streamlit.subheader')
    @patch('streamlit.expander')
    @patch('streamlit.write')
    @patch('streamlit.columns')
    @patch('streamlit.button')
    @patch('streamlit.rerun')
    def test_process_uploaded_document_success(
        self,
        mock_rerun,
        mock_button,
        mock_columns,
        mock_write,
        mock_expander,
        mock_subheader,
        mock_markdown,
        mock_balloons,
        mock_success,
        mock_spinner
    ):
        """Test successful document processing"""
        from src.ui.pages import process_uploaded_document
        import streamlit as st
        
        # Mock orchestrator
        mock_orchestrator = Mock()
        mock_profile = OrganizationProfile(
            id="test-id",
            original_text="Test organization profile text",
            summary="Test summary",
            context_overview="Test context",
            file_name="test.pdf",
            file_type=".pdf"
        )
        mock_orchestrator.process_organization_profile.return_value = mock_profile
        
        # Mock uploaded file
        mock_file = Mock()
        mock_file.name = "test_profile.pdf"
        mock_file.read.return_value = b"test content"
        
        # Mock spinner context manager
        mock_spinner.return_value.__enter__ = Mock()
        mock_spinner.return_value.__exit__ = Mock()
        
        # Mock expander context manager
        mock_expander_ctx = Mock()
        mock_expander_ctx.__enter__ = Mock(return_value=mock_expander_ctx)
        mock_expander_ctx.__exit__ = Mock()
        mock_expander.return_value = mock_expander_ctx
        
        # Mock columns
        mock_col = Mock()
        mock_col.__enter__ = Mock(return_value=mock_col)
        mock_col.__exit__ = Mock()
        mock_columns.return_value = [mock_col, mock_col, mock_col]
        
        # Mock button to return False
        mock_button.return_value = False
        
        # Process document
        process_uploaded_document(mock_orchestrator, mock_file)
        
        # Verify orchestrator was called
        mock_orchestrator.process_organization_profile.assert_called_once_with(
            file_content=b"test content",
            file_type=".pdf",
            file_name="test_profile.pdf"
        )
        
        # Verify session state was updated
        assert st.session_state.organization == mock_profile
        assert st.session_state.current_step == WorkflowStep.SUMMARY
        
        # Verify success indicators
        assert mock_balloons.called
    
    @patch('streamlit.session_state', {})
    @patch('streamlit.spinner')
    @patch('src.ui.utils.show_error')
    @patch('streamlit.info')
    def test_process_uploaded_document_unsupported_format(
        self,
        mock_info,
        mock_show_error,
        mock_spinner
    ):
        """Test handling of unsupported file format"""
        from src.ui.pages import process_uploaded_document
        
        # Mock orchestrator to raise UnsupportedFormatError
        mock_orchestrator = Mock()
        mock_orchestrator.process_organization_profile.side_effect = UnsupportedFormatError(
            "Unsupported format"
        )
        
        # Mock uploaded file
        mock_file = Mock()
        mock_file.name = "test_profile.xyz"
        mock_file.read.return_value = b"test content"
        
        # Mock spinner context manager
        mock_spinner.return_value.__enter__ = Mock()
        mock_spinner.return_value.__exit__ = Mock(return_value=False)
        
        # Process document
        process_uploaded_document(mock_orchestrator, mock_file)
        
        # Verify error message was shown
        assert mock_show_error.called
        error_message = str(mock_show_error.call_args)
        assert "Format file tidak didukung" in error_message or "tidak didukung" in error_message.lower()
    
    @patch('streamlit.session_state', {})
    @patch('streamlit.spinner')
    @patch('src.ui.utils.show_error')
    @patch('streamlit.info')
    def test_process_uploaded_document_empty_file(
        self,
        mock_info,
        mock_show_error,
        mock_spinner
    ):
        """Test handling of empty file"""
        from src.ui.pages import process_uploaded_document
        
        # Mock orchestrator to raise EmptyFileError
        mock_orchestrator = Mock()
        mock_orchestrator.process_organization_profile.side_effect = EmptyFileError(
            "File is empty"
        )
        
        # Mock uploaded file
        mock_file = Mock()
        mock_file.name = "empty.pdf"
        mock_file.read.return_value = b""
        
        # Mock spinner context manager
        mock_spinner.return_value.__enter__ = Mock()
        mock_spinner.return_value.__exit__ = Mock(return_value=False)
        
        # Process document
        process_uploaded_document(mock_orchestrator, mock_file)
        
        # Verify error message was shown
        assert mock_show_error.called
        error_message = str(mock_show_error.call_args)
        assert "kosong" in error_message.lower() or "tidak dapat dibaca" in error_message.lower()
    
    @patch('streamlit.session_state', {})
    @patch('streamlit.spinner')
    @patch('src.ui.utils.show_error')
    @patch('streamlit.info')
    @patch('streamlit.exception')
    def test_process_uploaded_document_general_error(
        self,
        mock_exception,
        mock_info,
        mock_show_error,
        mock_spinner
    ):
        """Test handling of general errors"""
        from src.ui.pages import process_uploaded_document
        
        # Mock orchestrator to raise general exception
        mock_orchestrator = Mock()
        mock_orchestrator.process_organization_profile.side_effect = Exception(
            "Unexpected error"
        )
        
        # Mock uploaded file
        mock_file = Mock()
        mock_file.name = "test.pdf"
        mock_file.read.return_value = b"test content"
        
        # Mock spinner context manager
        mock_spinner.return_value.__enter__ = Mock()
        mock_spinner.return_value.__exit__ = Mock(return_value=False)
        
        # Process document
        process_uploaded_document(mock_orchestrator, mock_file)
        
        # Verify error message was shown
        assert mock_show_error.called
        error_message = str(mock_show_error.call_args)
        assert "kesalahan" in error_message.lower()


class TestFileSizeValidation:
    """Test file size validation"""
    
    @patch('streamlit.header')
    @patch('streamlit.write')
    @patch('streamlit.info')
    @patch('streamlit.file_uploader')
    @patch('streamlit.success')
    @patch('src.ui.utils.show_error')
    @patch('streamlit.markdown')
    def test_file_size_limit_exceeded(
        self,
        mock_markdown,
        mock_show_error,
        mock_success,
        mock_uploader,
        mock_info,
        mock_write,
        mock_header
    ):
        """Test that files exceeding size limit are rejected"""
        from src.ui.pages import render_upload_page
        
        # Mock orchestrator
        mock_orchestrator = Mock()
        
        # Mock uploaded file with size > 10 MB
        mock_file = Mock()
        mock_file.name = "large_file.pdf"
        mock_file.size = 11 * 1024 * 1024  # 11 MB
        mock_file.type = "application/pdf"
        mock_uploader.return_value = mock_file
        
        # Render page
        render_upload_page(mock_orchestrator)
        
        # Verify error message was shown
        assert mock_show_error.called
        error_message = str(mock_show_error.call_args)
        assert "terlalu besar" in error_message.lower() or "maksimum" in error_message.lower()


class TestIndonesianErrorMessages:
    """Test that all error messages are in Indonesian"""
    
    def test_error_messages_are_indonesian(self):
        """Test that error messages contain Indonesian text"""
        # Import the pages module to check error messages
        from src.ui import pages
        import inspect
        
        # Get source code of the module
        source = inspect.getsource(pages)
        
        # Check for Indonesian error message keywords
        indonesian_keywords = [
            "tidak didukung",
            "kosong",
            "kesalahan",
            "Silakan",
            "Format file",
            "Ukuran file",
            "terlalu besar"
        ]
        
        # At least some Indonesian keywords should be present in error messages
        found_keywords = [kw for kw in indonesian_keywords if kw in source]
        assert len(found_keywords) >= 3, f"Error messages should be in Indonesian. Found: {found_keywords}"
