"""Manual test script for summary page implementation"""

import sys
from datetime import datetime
from unittest.mock import Mock, MagicMock
from src.models.entities import OrganizationProfile, WorkflowStep

# Mock streamlit before importing pages
sys.modules['streamlit'] = MagicMock()

from src.ui.pages import render_summary_page


def test_summary_page_with_valid_profile():
    """Test summary page with valid organization profile"""
    print("Testing summary page with valid organization profile...")
    
    # Create mock organization profile
    mock_profile = OrganizationProfile(
        id="test-123",
        original_text="This is the original organization profile document text. " * 10,
        summary="PT Example Indonesia adalah perusahaan teknologi yang berfokus pada "
                "pengembangan solusi digital untuk industri pendidikan. Dengan pengalaman "
                "lebih dari 10 tahun, perusahaan ini telah melayani lebih dari 500 institusi "
                "pendidikan di seluruh Indonesia.",
        context_overview="Perusahaan bergerak di bidang teknologi pendidikan (EdTech) dengan "
                        "fokus pada pengembangan platform pembelajaran online, sistem manajemen "
                        "pembelajaran (LMS), dan solusi AI untuk personalisasi pembelajaran. "
                        "Target pasar utama adalah universitas, sekolah menengah, dan lembaga "
                        "pelatihan profesional.",
        file_name="profil_organisasi.pdf",
        file_type=".pdf",
        uploaded_at=datetime(2024, 1, 15, 10, 30, 45)
    )
    
    # Mock streamlit session state
    import streamlit as st
    st.session_state = Mock()
    st.session_state.organization = mock_profile
    st.session_state.current_step = WorkflowStep.SUMMARY
    
    # Mock orchestrator
    mock_orchestrator = Mock()
    
    # Mock streamlit functions
    st.header = Mock()
    st.write = Mock()
    st.markdown = Mock()
    st.subheader = Mock()
    st.columns = Mock(return_value=[Mock(), Mock(), Mock()])
    st.metric = Mock()
    st.expander = Mock(return_value=MagicMock())
    st.text_area = Mock()
    st.button = Mock(return_value=False)
    st.info = Mock()
    st.rerun = Mock()
    
    # Mock column context manager
    for col in st.columns.return_value:
        col.__enter__ = Mock(return_value=col)
        col.__exit__ = Mock()
    
    # Mock expander context manager
    st.expander.return_value.__enter__ = Mock(return_value=st.expander.return_value)
    st.expander.return_value.__exit__ = Mock()
    
    # Call render_summary_page
    try:
        render_summary_page(mock_orchestrator)
        print("✅ Summary page rendered successfully")
        
        # Verify key elements were called
        assert st.header.called, "Header should be displayed"
        print("✅ Header displayed")
        
        assert st.subheader.called, "Subheaders should be displayed"
        print("✅ Subheaders displayed")
        
        assert st.markdown.called, "Markdown content should be displayed"
        print("✅ Markdown content displayed")
        
        assert st.metric.called, "Metrics should be displayed"
        print("✅ Metrics displayed")
        
        assert st.button.called, "Buttons should be displayed"
        print("✅ Buttons displayed")
        
        # Check that summary and context are in markdown calls
        markdown_calls = [str(call) for call in st.markdown.call_args_list]
        summary_found = any("PT Example Indonesia" in call for call in markdown_calls)
        context_found = any("teknologi pendidikan" in call for call in markdown_calls)
        
        assert summary_found, "Summary should be displayed in markdown"
        print("✅ Summary content displayed")
        
        assert context_found, "Context overview should be displayed in markdown"
        print("✅ Context overview displayed")
        
        print("\n✅ All tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_summary_page_without_profile():
    """Test summary page when organization profile is missing"""
    print("\nTesting summary page without organization profile...")
    
    # Mock streamlit session state with no organization
    import streamlit as st
    st.session_state = Mock()
    st.session_state.organization = None
    st.session_state.current_step = WorkflowStep.SUMMARY
    
    # Mock orchestrator
    mock_orchestrator = Mock()
    
    # Mock streamlit functions
    st.header = Mock()
    st.write = Mock()
    st.button = Mock(return_value=False)
    st.rerun = Mock()
    
    # Mock show_error from utils
    from src.ui import utils
    utils.show_error = Mock()
    
    # Call render_summary_page
    try:
        render_summary_page(mock_orchestrator)
        print("✅ Summary page handled missing profile")
        
        # Verify error was shown
        assert utils.show_error.called, "Error message should be displayed"
        error_message = str(utils.show_error.call_args)
        assert "tidak ditemukan" in error_message.lower() or "unggah" in error_message.lower()
        print("✅ Error message displayed in Indonesian")
        
        # Verify back button was shown
        assert st.button.called, "Back button should be displayed"
        print("✅ Back button displayed")
        
        print("\n✅ All tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_navigation_buttons():
    """Test navigation button functionality"""
    print("\nTesting navigation buttons...")
    
    # Create mock organization profile
    mock_profile = OrganizationProfile(
        id="test-123",
        original_text="Original text",
        summary="Summary text",
        context_overview="Context text",
        file_name="test.pdf",
        file_type=".pdf"
    )
    
    # Test back button
    print("Testing back button...")
    import streamlit as st
    st.session_state = Mock()
    st.session_state.organization = mock_profile
    st.session_state.current_step = WorkflowStep.SUMMARY
    
    mock_orchestrator = Mock()
    
    # Mock streamlit functions
    st.header = Mock()
    st.write = Mock()
    st.markdown = Mock()
    st.subheader = Mock()
    st.columns = Mock(return_value=[Mock(), Mock(), Mock()])
    st.metric = Mock()
    st.expander = Mock(return_value=MagicMock())
    st.text_area = Mock()
    st.button = Mock(side_effect=[True, False])  # First button (back) clicked
    st.info = Mock()
    st.rerun = Mock()
    
    # Mock column context manager
    for col in st.columns.return_value:
        col.__enter__ = Mock(return_value=col)
        col.__exit__ = Mock()
    
    # Mock expander context manager
    st.expander.return_value.__enter__ = Mock(return_value=st.expander.return_value)
    st.expander.return_value.__exit__ = Mock()
    
    try:
        render_summary_page(mock_orchestrator)
        assert st.session_state.current_step == WorkflowStep.UPLOAD
        print("✅ Back button navigates to UPLOAD")
    except Exception as e:
        print(f"❌ Back button test failed: {e}")
        return False
    
    # Test continue button
    print("Testing continue button...")
    st.session_state.current_step = WorkflowStep.SUMMARY
    st.button = Mock(side_effect=[False, True])  # Second button (continue) clicked
    st.rerun = Mock()
    
    try:
        render_summary_page(mock_orchestrator)
        assert st.session_state.current_step == WorkflowStep.COURSE_TYPE
        print("✅ Continue button navigates to COURSE_TYPE")
    except Exception as e:
        print(f"❌ Continue button test failed: {e}")
        return False
    
    print("\n✅ All navigation tests passed!")
    return True


def test_indonesian_language():
    """Test that all text is in Indonesian"""
    print("\nTesting Indonesian language usage...")
    
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
        "tidak ditemukan",
        "Silakan"
    ]
    
    found_keywords = []
    for keyword in indonesian_keywords:
        if keyword in source:
            found_keywords.append(keyword)
            print(f"✅ Found: '{keyword}'")
    
    if len(found_keywords) >= 6:
        print(f"\n✅ Indonesian language test passed ({len(found_keywords)}/{len(indonesian_keywords)} keywords found)")
        return True
    else:
        print(f"\n❌ Indonesian language test failed (only {len(found_keywords)}/{len(indonesian_keywords)} keywords found)")
        return False


def main():
    """Run all manual tests"""
    print("=" * 60)
    print("MANUAL TEST: Organization Summary Display Page (Task 9.3)")
    print("=" * 60)
    
    results = []
    
    # Run tests
    results.append(("Valid Profile Test", test_summary_page_with_valid_profile()))
    results.append(("Missing Profile Test", test_summary_page_without_profile()))
    results.append(("Navigation Test", test_navigation_buttons()))
    results.append(("Indonesian Language Test", test_indonesian_language()))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Task 9.3 implementation is complete.")
        return 0
    else:
        print(f"\n⚠️ {total - passed} test(s) failed. Please review the implementation.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
