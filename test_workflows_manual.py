"""Manual test script for workflow orchestrator TLO, Performance, and ELO generation"""

import os
from unittest.mock import Mock, MagicMock
from src.workflow.orchestrator import WorkflowOrchestrator
from src.models.entities import OrganizationProfile, TLO, Performance, ELO


def test_tlo_generation_workflow():
    """Test TLO generation workflow (Task 6.3)"""
    print("\n=== Testing TLO Generation Workflow (Task 6.3) ===")
    
    # Create mocks
    mock_db = Mock()
    mock_ai = Mock()
    
    # Setup mock organization profile
    org_profile = OrganizationProfile(
        id="org-123",
        original_text="Sample organization profile",
        summary="Organization focused on B2B training",
        context_overview="B2B training context",
        file_name="org.pdf",
        file_type=".pdf"
    )
    
    # Setup mock responses
    mock_db.get_organization_profile.return_value = org_profile
    mock_ai.generate_tlos.return_value = [
        "Peserta mampu menganalisis kebutuhan pelatihan B2B",
        "Peserta mampu merancang program pelatihan yang efektif",
        "Peserta mampu mengevaluasi hasil pelatihan",
        "Peserta mampu mengimplementasikan strategi pembelajaran",
        "Peserta mampu mengembangkan materi pelatihan"
    ]
    mock_db.save_tlos.return_value = ["tlo-1", "tlo-2", "tlo-3", "tlo-4", "tlo-5"]
    
    # Create orchestrator
    orchestrator = WorkflowOrchestrator(mock_db, mock_ai)
    
    # Execute TLO generation
    try:
        tlos = orchestrator.generate_tlos(
            org_id="org-123",
            course_type="B2B",
            count=5
        )
        
        print(f"✓ Generated {len(tlos)} TLOs")
        print(f"✓ All TLOs have org_id: {all(tlo.org_id == 'org-123' for tlo in tlos)}")
        print(f"✓ All TLOs have course_type: {all(tlo.course_type == 'B2B' for tlo in tlos)}")
        print(f"✓ All TLOs have IDs: {all(tlo.id is not None for tlo in tlos)}")
        print(f"✓ Workflow state updated: {orchestrator.current_step.value}")
        
        # Verify AI service was called correctly
        mock_ai.generate_tlos.assert_called_once_with(
            org_context=org_profile.summary,
            course_type="B2B",
            count=5
        )
        print("✓ AI service called with correct parameters")
        
        # Verify database save was called
        mock_db.save_tlos.assert_called_once()
        print("✓ Database save called")
        
        print("\n✅ Task 6.3 (TLO Generation) - PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ Task 6.3 (TLO Generation) - FAILED: {e}")
        return False


def test_performance_generation_workflow():
    """Test Performance generation workflow (Task 6.4)"""
    print("\n=== Testing Performance Generation Workflow (Task 6.4) ===")
    
    # Create mocks
    mock_db = Mock()
    mock_ai = Mock()
    
    # Setup mock TLOs
    sample_tlos = [
        TLO(
            id="tlo-1",
            org_id="org-123",
            course_type="B2B",
            text="Peserta mampu menganalisis kebutuhan pelatihan B2B",
            is_selected=True
        ),
        TLO(
            id="tlo-2",
            org_id="org-123",
            course_type="B2B",
            text="Peserta mampu merancang program pelatihan yang efektif",
            is_selected=False
        )
    ]
    
    # Setup mock responses
    mock_db.get_tlos_by_org.return_value = sample_tlos
    mock_ai.generate_performances.return_value = [
        "Melakukan analisis kebutuhan dengan metode survei",
        "Mengidentifikasi gap kompetensi dalam organisasi",
        "Menyusun laporan analisis kebutuhan pelatihan",
        "Mempresentasikan hasil analisis kepada stakeholder",
        "Merekomendasikan solusi pelatihan yang tepat"
    ]
    mock_db.save_performances.return_value = ["perf-1", "perf-2", "perf-3", "perf-4", "perf-5"]
    
    # Create orchestrator
    orchestrator = WorkflowOrchestrator(mock_db, mock_ai)
    
    # Execute Performance generation
    try:
        performances = orchestrator.generate_performances(
            selected_tlo_ids=["tlo-1"],
            org_id="org-123",
            count=5
        )
        
        print(f"✓ Generated {len(performances)} performances")
        print(f"✓ All performances linked to TLO: {all('tlo-1' in perf.tlo_ids for perf in performances)}")
        print(f"✓ All performances have IDs: {all(perf.id is not None for perf in performances)}")
        print(f"✓ Workflow state updated: {orchestrator.current_step.value}")
        
        # Verify AI service was called correctly
        mock_ai.generate_performances.assert_called_once()
        call_args = mock_ai.generate_performances.call_args[1]
        assert len(call_args['tlo_texts']) == 1
        assert "menganalisis kebutuhan pelatihan" in call_args['tlo_texts'][0].lower()
        print("✓ AI service called with correct TLO texts")
        
        # Verify database operations
        mock_db.get_tlos_by_org.assert_called_once_with("org-123")
        mock_db.save_performances.assert_called_once()
        print("✓ Database operations completed")
        
        print("\n✅ Task 6.4 (Performance Generation) - PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ Task 6.4 (Performance Generation) - FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_elo_generation_workflow():
    """Test ELO generation workflow (Task 6.5)"""
    print("\n=== Testing ELO Generation Workflow (Task 6.5) ===")
    
    # Create mocks
    mock_db = Mock()
    mock_ai = Mock()
    
    # Setup mock performances
    sample_performances = [
        Performance(
            id="perf-1",
            tlo_ids=["tlo-1"],
            text="Melakukan analisis kebutuhan dengan metode survei",
            is_selected=True
        ),
        Performance(
            id="perf-2",
            tlo_ids=["tlo-1"],
            text="Mengidentifikasi gap kompetensi dalam organisasi",
            is_selected=False
        )
    ]
    
    # Setup mock responses
    mock_db.get_performances_by_ids.return_value = [sample_performances[0]]
    mock_ai.generate_elos.return_value = [
        "Menyusun kuesioner survei kebutuhan pelatihan",
        "Melakukan wawancara dengan stakeholder kunci",
        "Menganalisis data survei menggunakan statistik deskriptif",
        "Membuat visualisasi hasil survei",
        "Menyimpulkan temuan dari survei"
    ]
    mock_db.save_elos.return_value = ["elo-1", "elo-2", "elo-3", "elo-4", "elo-5"]
    
    # Create orchestrator
    orchestrator = WorkflowOrchestrator(mock_db, mock_ai)
    
    # Execute ELO generation
    try:
        elos = orchestrator.generate_elos(
            selected_performance_ids=["perf-1"],
            count=5
        )
        
        print(f"✓ Generated {len(elos)} ELOs")
        print(f"✓ All ELOs linked to performance: {all('perf-1' in elo.performance_ids for elo in elos)}")
        print(f"✓ All ELOs have IDs: {all(elo.id is not None for elo in elos)}")
        print(f"✓ Workflow state updated: {orchestrator.current_step.value}")
        
        # Verify AI service was called correctly
        mock_ai.generate_elos.assert_called_once()
        call_args = mock_ai.generate_elos.call_args[1]
        assert len(call_args['performance_texts']) == 1
        assert "analisis kebutuhan" in call_args['performance_texts'][0].lower()
        print("✓ AI service called with correct performance texts")
        
        # Verify database operations
        mock_db.get_performances_by_ids.assert_called_once_with(["perf-1"])
        mock_db.save_elos.assert_called_once()
        print("✓ Database operations completed")
        
        print("\n✅ Task 6.5 (ELO Generation) - PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ Task 6.5 (ELO Generation) - FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_error_handling():
    """Test error handling for all three workflows"""
    print("\n=== Testing Error Handling ===")
    
    mock_db = Mock()
    mock_ai = Mock()
    orchestrator = WorkflowOrchestrator(mock_db, mock_ai)
    
    errors_caught = 0
    
    # Test 1: TLO generation with missing organization
    try:
        mock_db.get_organization_profile.return_value = None
        orchestrator.generate_tlos("org-999", "B2B")
        print("❌ Should have raised error for missing organization")
    except Exception as e:
        if "tidak ditemukan" in str(e).lower():
            print("✓ Correctly raised error for missing organization")
            errors_caught += 1
    
    # Test 2: TLO generation with insufficient count
    try:
        org_profile = OrganizationProfile(
            id="org-123",
            original_text="Test",
            summary="Test summary",
            context_overview="Test",
            file_name="test.pdf",
            file_type=".pdf"
        )
        mock_db.get_organization_profile.return_value = org_profile
        mock_ai.generate_tlos.return_value = ["TLO 1", "TLO 2"]  # Only 2
        orchestrator.generate_tlos("org-123", "B2B")
        print("❌ Should have raised error for insufficient TLOs")
    except Exception as e:
        if "minimum" in str(e).lower():
            print("✓ Correctly raised error for insufficient TLOs")
            errors_caught += 1
    
    # Test 3: Performance generation with empty TLO list
    try:
        orchestrator.generate_performances([], "org-123")
        print("❌ Should have raised error for empty TLO list")
    except Exception as e:
        if "pilih" in str(e).lower():
            print("✓ Correctly raised error for empty TLO list")
            errors_caught += 1
    
    # Test 4: ELO generation with empty performance list
    try:
        orchestrator.generate_elos([])
        print("❌ Should have raised error for empty performance list")
    except Exception as e:
        if "pilih" in str(e).lower():
            print("✓ Correctly raised error for empty performance list")
            errors_caught += 1
    
    # Test 5: ELO generation with insufficient count
    try:
        mock_db.get_performances_by_ids.return_value = [
            Performance(
                id="perf-1",
                tlo_ids=["tlo-1"],
                text="Test performance",
                is_selected=True
            )
        ]
        mock_ai.generate_elos.return_value = ["ELO 1", "ELO 2"]  # Only 2
        orchestrator.generate_elos(["perf-1"])
        print("❌ Should have raised error for insufficient ELOs")
    except Exception as e:
        if "minimum" in str(e).lower():
            print("✓ Correctly raised error for insufficient ELOs")
            errors_caught += 1
    
    print(f"\n✅ Error Handling - {errors_caught}/5 tests passed")
    return errors_caught == 5


if __name__ == "__main__":
    print("=" * 70)
    print("WORKFLOW ORCHESTRATOR MANUAL TESTS")
    print("Testing Tasks 6.3, 6.4, and 6.5")
    print("=" * 70)
    
    results = []
    
    # Run all tests
    results.append(("Task 6.3 - TLO Generation", test_tlo_generation_workflow()))
    results.append(("Task 6.4 - Performance Generation", test_performance_generation_workflow()))
    results.append(("Task 6.5 - ELO Generation", test_elo_generation_workflow()))
    results.append(("Error Handling", test_error_handling()))
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Tasks 6.3, 6.4, and 6.5 are working correctly.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the output above.")
