"""Manual test script for upload page functionality"""

import sys
from unittest.mock import Mock, MagicMock
from io import BytesIO

# Mock streamlit before importing
sys.modules['streamlit'] = MagicMock()

from src.ui.pages import render_upload_page, process_uploaded_document
from src.models.entities import OrganizationProfile, WorkflowStep
from src.processors.document_processor import UnsupportedFormatError, EmptyFileError


def test_upload_page_rendering():
    """Test that upload page can be rendered"""
    print("Testing upload page rendering...")
    
    # Mock orchestrator
    mock_orchestrator = Mock()
    
    try:
        # This will call streamlit functions, but they're mocked
        render_upload_page(mock_orchestrator)
        print("✅ Upload page rendering successful")
        return True
    except Exception as e:
        print(f"❌ Upload page rendering failed: {e}")
        return False


def test_document_processing_success():
    """Test successful document processing"""
    print("\nTesting successful document processing...")
    
    # Mock orchestrator
    mock_orchestrator = Mock()
    mock_profile = OrganizationProfile(
        id="test-id",
        original_text="Test organization profile text",
        summary="Test summary of the organization",
        context_overview="Test context overview",
        file_name="test.pdf",
        file_type=".pdf"
    )
    mock_orchestrator.process_organization_profile.return_value = mock_profile
    
    # Mock uploaded file
    mock_file = Mock()
    mock_file.name = "test_profile.pdf"
    mock_file.read.return_value = b"test content"
    
    try:
        # Mock session state
        import streamlit as st
        st.session_state = {}
        
        process_uploaded_document(mock_orchestrator, mock_file)
        
        # Verify orchestrator was called
        assert mock_orchestrator.process_organization_profile.called
        call_args = mock_orchestrator.process_organization_profile.call_args
        assert call_args[1]['file_content'] == b"test content"
        assert call_args[1]['file_type'] == ".pdf"
        assert call_args[1]['file_name'] == "test_profile.pdf"
        
        # Verify session state was updated
        assert st.session_state['organization'] == mock_profile
        assert st.session_state['current_step'] == WorkflowStep.SUMMARY
        
        print("✅ Document processing success test passed")
        return True
    except Exception as e:
        print(f"❌ Document processing success test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_unsupported_format_error():
    """Test handling of unsupported format error"""
    print("\nTesting unsupported format error handling...")
    
    # Mock orchestrator to raise error
    mock_orchestrator = Mock()
    mock_orchestrator.process_organization_profile.side_effect = UnsupportedFormatError(
        "Unsupported format"
    )
    
    # Mock uploaded file
    mock_file = Mock()
    mock_file.name = "test.xyz"
    mock_file.read.return_value = b"test content"
    
    try:
        import streamlit as st
        st.session_state = {}
        
        # This should handle the error gracefully
        process_uploaded_document(mock_orchestrator, mock_file)
        
        print("✅ Unsupported format error handling test passed")
        return True
    except Exception as e:
        print(f"❌ Unsupported format error handling test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_empty_file_error():
    """Test handling of empty file error"""
    print("\nTesting empty file error handling...")
    
    # Mock orchestrator to raise error
    mock_orchestrator = Mock()
    mock_orchestrator.process_organization_profile.side_effect = EmptyFileError(
        "File is empty"
    )
    
    # Mock uploaded file
    mock_file = Mock()
    mock_file.name = "empty.pdf"
    mock_file.read.return_value = b""
    
    try:
        import streamlit as st
        st.session_state = {}
        
        # This should handle the error gracefully
        process_uploaded_document(mock_orchestrator, mock_file)
        
        print("✅ Empty file error handling test passed")
        return True
    except Exception as e:
        print(f"❌ Empty file error handling test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_indonesian_messages():
    """Test that Indonesian messages are present"""
    print("\nTesting Indonesian language messages...")
    
    try:
        # Read the pages module source
        with open('src/ui/pages.py', 'r', encoding='utf-8') as f:
            source = f.read()
        
        # Check for Indonesian keywords
        indonesian_keywords = [
            "Unggah",
            "Profil",
            "Organisasi",
            "Proses",
            "Dokumen",
            "Format file tidak didukung",
            "File kosong",
            "Terjadi kesalahan",
            "Silakan"
        ]
        
        found_keywords = [kw for kw in indonesian_keywords if kw in source]
        
        print(f"Found {len(found_keywords)}/{len(indonesian_keywords)} Indonesian keywords:")
        for kw in found_keywords:
            print(f"  ✓ {kw}")
        
        if len(found_keywords) >= 6:
            print("✅ Indonesian language messages test passed")
            return True
        else:
            print("❌ Not enough Indonesian keywords found")
            return False
    except Exception as e:
        print(f"❌ Indonesian messages test failed: {e}")
        return False


def main():
    """Run all manual tests"""
    print("=" * 60)
    print("MANUAL TEST: Organization Profile Upload Page")
    print("=" * 60)
    
    results = []
    
    results.append(test_upload_page_rendering())
    results.append(test_document_processing_success())
    results.append(test_unsupported_format_error())
    results.append(test_empty_file_error())
    results.append(test_indonesian_messages())
    
    print("\n" + "=" * 60)
    print(f"RESULTS: {sum(results)}/{len(results)} tests passed")
    print("=" * 60)
    
    if all(results):
        print("✅ All tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
