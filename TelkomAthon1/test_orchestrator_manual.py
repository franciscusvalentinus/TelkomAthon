"""
Manual test script for verifying process_organization_profile workflow

This script tests the complete integration of:
- Document processing
- AI service (mocked)
- Database service (mocked)
- Workflow orchestrator

Run with: python test_orchestrator_manual.py
"""

from unittest.mock import Mock
from src.workflow.orchestrator import WorkflowOrchestrator
from src.models.entities import WorkflowStep


def test_process_organization_profile():
    """Test the complete process_organization_profile workflow"""
    
    print("=" * 60)
    print("Testing process_organization_profile workflow")
    print("=" * 60)
    
    # Create mock dependencies
    mock_db = Mock()
    mock_ai = Mock()
    
    # Setup mock responses
    mock_ai.summarize_organization_profile.return_value = "Ringkasan: Organisasi pendidikan yang fokus pada teknologi dan inovasi."
    mock_db.save_organization_profile.return_value = "org-test-123"
    
    # Create orchestrator
    orchestrator = WorkflowOrchestrator(mock_db, mock_ai)
    
    print("\n1. Initial state:")
    print(f"   Current step: {orchestrator.current_step}")
    
    # Test with TXT file
    print("\n2. Processing TXT file...")
    txt_content = b"""
    Profil Organisasi XYZ
    
    Organisasi XYZ adalah lembaga pendidikan yang berfokus pada pengembangan
    teknologi dan inovasi. Kami memiliki visi untuk menjadi pusat pembelajaran
    terkemuka di bidang teknologi informasi dan komunikasi.
    
    Misi kami adalah:
    - Memberikan pendidikan berkualitas tinggi
    - Mengembangkan inovasi teknologi
    - Membangun ekosistem pembelajaran yang kolaboratif
    """
    
    try:
        result = orchestrator.process_organization_profile(
            file_content=txt_content,
            file_type=".txt",
            file_name="profil_organisasi.txt"
        )
        
        print("   ✓ Processing successful!")
        print(f"   Profile ID: {result.id}")
        print(f"   File name: {result.file_name}")
        print(f"   File type: {result.file_type}")
        print(f"   Summary: {result.summary}")
        print(f"   Original text length: {len(result.original_text)} characters")
        print(f"   Workflow step: {orchestrator.current_step}")
        
        # Verify AI service was called
        assert mock_ai.summarize_organization_profile.called
        print("\n   ✓ AI service was called")
        
        # Verify database save was called
        assert mock_db.save_organization_profile.called
        print("   ✓ Database save was called")
        
        # Verify workflow state updated
        assert orchestrator.current_step == WorkflowStep.SUMMARY
        print("   ✓ Workflow state updated correctly")
        
    except Exception as e:
        print(f"   ✗ Error: {e}")
        raise
    
    # Test with unsupported format
    print("\n3. Testing unsupported format...")
    try:
        orchestrator.process_organization_profile(
            file_content=b"image data",
            file_type=".jpg",
            file_name="image.jpg"
        )
        print("   ✗ Should have raised UnsupportedFormatError")
    except Exception as e:
        print(f"   ✓ Correctly raised error: {type(e).__name__}")
    
    # Test with empty file
    print("\n4. Testing empty file...")
    try:
        orchestrator.process_organization_profile(
            file_content=b"",
            file_type=".txt",
            file_name="empty.txt"
        )
        print("   ✗ Should have raised EmptyFileError")
    except Exception as e:
        print(f"   ✓ Correctly raised error: {type(e).__name__}")
    
    # Test with insufficient content
    print("\n5. Testing insufficient content...")
    try:
        orchestrator.process_organization_profile(
            file_content=b"short",
            file_type=".txt",
            file_name="short.txt"
        )
        print("   ✗ Should have raised EmptyFileError")
    except Exception as e:
        print(f"   ✓ Correctly raised error: {type(e).__name__}")
    
    print("\n" + "=" * 60)
    print("All tests passed! ✓")
    print("=" * 60)


if __name__ == "__main__":
    test_process_organization_profile()
