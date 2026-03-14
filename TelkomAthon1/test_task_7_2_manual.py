"""
Manual test for task 7.2: Syllabus compilation in orchestrator

This test verifies that the create_syllabus_document method:
1. Retrieves all selected materials from database
2. Calls AI service to format content
3. Generates DOCX document using DocumentGenerator
4. Stores syllabus in database
"""

from unittest.mock import Mock
from src.workflow.orchestrator import WorkflowOrchestrator
from src.models.entities import (
    OrganizationProfile,
    TLO,
    Performance,
    ELO,
    SyllabusMaterials
)


def test_create_syllabus_document():
    """Test the complete syllabus document creation workflow"""
    
    # Create mock dependencies
    mock_db = Mock()
    mock_ai = Mock()
    
    # Create orchestrator
    orchestrator = WorkflowOrchestrator(mock_db, mock_ai)
    
    # Setup test data
    org_profile = OrganizationProfile(
        id="org-123",
        original_text="Test organization",
        summary="Test summary",
        context_overview="Test context",
        file_name="test.pdf",
        file_type=".pdf"
    )
    
    tlos = [
        TLO(
            id="tlo-1",
            org_id="org-123",
            course_type="B2B",
            text="TLO 1: Learn fundamental concepts",
            is_selected=True
        ),
        TLO(
            id="tlo-2",
            org_id="org-123",
            course_type="B2B",
            text="TLO 2: Apply advanced techniques",
            is_selected=True
        )
    ]
    
    performances = [
        Performance(
            id="perf-1",
            tlo_ids=["tlo-1"],
            text="Performance 1: Demonstrate understanding",
            is_selected=True
        ),
        Performance(
            id="perf-2",
            tlo_ids=["tlo-2"],
            text="Performance 2: Execute complex tasks",
            is_selected=True
        )
    ]
    
    elos = [
        ELO(
            id="elo-1",
            performance_ids=["perf-1"],
            text="ELO 1: Identify key components",
            is_selected=True
        ),
        ELO(
            id="elo-2",
            performance_ids=["perf-2"],
            text="ELO 2: Analyze relationships",
            is_selected=True
        )
    ]
    
    # Setup mock returns
    mock_db.get_organization_profile.return_value = org_profile
    mock_db.get_tlos_by_org.return_value = tlos
    mock_db.get_performances_by_tlos.return_value = performances
    mock_db.get_elos_by_performances.return_value = elos
    mock_ai.format_syllabus_content.return_value = "Formatted syllabus content"
    mock_db.save_syllabus.return_value = "syllabus-123"
    
    # Execute
    print("Testing create_syllabus_document...")
    result = orchestrator.create_syllabus_document(
        session_id="test-session",
        org_id="org-123",
        course_type="B2B",
        selected_tlo_ids=["tlo-1", "tlo-2"],
        selected_performance_ids=["perf-1", "perf-2"],
        selected_elo_ids=["elo-1", "elo-2"]
    )
    
    # Verify results
    print("\n✓ Step 1: Retrieve all selected materials from database")
    assert mock_db.get_organization_profile.called, "Should retrieve organization profile"
    assert mock_db.get_tlos_by_org.called, "Should retrieve TLOs"
    assert mock_db.get_performances_by_tlos.called, "Should retrieve performances"
    assert mock_db.get_elos_by_performances.called, "Should retrieve ELOs"
    print("  - Organization profile retrieved")
    print("  - TLOs retrieved")
    print("  - Performances retrieved")
    print("  - ELOs retrieved")
    
    print("\n✓ Step 2: Call AI service to format content")
    assert mock_ai.format_syllabus_content.called, "Should call AI service"
    call_args = mock_ai.format_syllabus_content.call_args[1]
    assert call_args['org_summary'] == "Test summary"
    assert len(call_args['tlos']) == 2
    assert len(call_args['performances']) == 2
    assert len(call_args['elos']) == 2
    print("  - AI service called with correct parameters")
    
    print("\n✓ Step 3: Generate DOCX document using DocumentGenerator")
    assert isinstance(result, bytes), "Should return bytes"
    assert len(result) > 0, "Document should not be empty"
    assert result[:2] == b'PK', "Should be a valid DOCX file (ZIP format)"
    print(f"  - DOCX document generated ({len(result)} bytes)")
    
    print("\n✓ Step 4: Store syllabus in database")
    assert mock_db.save_syllabus.called, "Should save syllabus to database"
    saved_syllabus = mock_db.save_syllabus.call_args[0][0]
    assert saved_syllabus.session_id == "test-session"
    assert saved_syllabus.org_id == "org-123"
    assert saved_syllabus.course_type == "B2B"
    assert saved_syllabus.selected_tlo_ids == ["tlo-1", "tlo-2"]
    assert saved_syllabus.selected_performance_ids == ["perf-1", "perf-2"]
    assert saved_syllabus.selected_elo_ids == ["elo-1", "elo-2"]
    assert isinstance(saved_syllabus.document_content, bytes)
    print("  - Syllabus stored with correct metadata")
    
    print("\n✅ All requirements validated successfully!")
    print("\nTask 7.2 Implementation Summary:")
    print("- ✓ Retrieves all selected materials from database")
    print("- ✓ Calls AI service to format content")
    print("- ✓ Generates DOCX document using DocumentGenerator")
    print("- ✓ Stores syllabus in database")
    print("\nRequirements validated: 10.1, 10.2, 10.3, 10.4, 10.5")


if __name__ == "__main__":
    test_create_syllabus_document()
