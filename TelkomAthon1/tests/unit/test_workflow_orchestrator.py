"""Unit tests for WorkflowOrchestrator"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from src.workflow.orchestrator import WorkflowOrchestrator, WorkflowStateError
from src.models.entities import (
    WorkflowStep,
    OrganizationProfile,
    TLO,
    Performance,
    ELO,
    SessionData
)


@pytest.fixture
def mock_db():
    """Create mock database service"""
    return Mock()


@pytest.fixture
def mock_ai():
    """Create mock AI service"""
    return Mock()


@pytest.fixture
def orchestrator(mock_db, mock_ai):
    """Create workflow orchestrator with mocked dependencies"""
    return WorkflowOrchestrator(mock_db, mock_ai)


@pytest.fixture
def sample_org_profile():
    """Create sample organization profile"""
    return OrganizationProfile(
        id="org-123",
        original_text="Sample organization text",
        summary="Sample organization summary",
        context_overview="Sample context",
        file_name="test.pdf",
        file_type=".pdf"
    )


@pytest.fixture
def sample_tlos():
    """Create sample TLOs"""
    return [
        TLO(
            id="tlo-1",
            org_id="org-123",
            course_type="B2B",
            text="TLO 1 text",
            is_selected=True
        ),
        TLO(
            id="tlo-2",
            org_id="org-123",
            course_type="B2B",
            text="TLO 2 text",
            is_selected=False
        )
    ]


@pytest.fixture
def sample_performances():
    """Create sample performances"""
    return [
        Performance(
            id="perf-1",
            tlo_ids=["tlo-1"],
            text="Performance 1 text",
            is_selected=True
        ),
        Performance(
            id="perf-2",
            tlo_ids=["tlo-1"],
            text="Performance 2 text",
            is_selected=False
        )
    ]


@pytest.fixture
def sample_elos():
    """Create sample ELOs"""
    return [
        ELO(
            id="elo-1",
            performance_ids=["perf-1"],
            text="ELO 1 text",
            is_selected=True
        ),
        ELO(
            id="elo-2",
            performance_ids=["perf-1"],
            text="ELO 2 text",
            is_selected=False
        )
    ]


class TestWorkflowOrchestratorInitialization:
    """Test workflow orchestrator initialization"""
    
    def test_initialization(self, mock_db, mock_ai):
        """Test that orchestrator initializes correctly"""
        orchestrator = WorkflowOrchestrator(mock_db, mock_ai)
        
        assert orchestrator.db == mock_db
        assert orchestrator.ai == mock_ai
        assert orchestrator.current_step == WorkflowStep.UPLOAD
        assert orchestrator.document_processor is not None


class TestCanAdvanceToStep:
    """Test can_advance_to_step validation method"""
    
    def test_can_always_access_upload_step(self, orchestrator):
        """Test that UPLOAD step is always accessible"""
        session_data = SessionData(
            session_id="test-session",
            current_step="upload"
        )
        
        assert orchestrator.can_advance_to_step(WorkflowStep.UPLOAD, session_data)
    
    def test_summary_requires_organization(self, orchestrator, sample_org_profile):
        """Test that SUMMARY step requires organization profile"""
        # Without organization
        session_data = SessionData(
            session_id="test-session",
            current_step="upload"
        )
        assert not orchestrator.can_advance_to_step(WorkflowStep.SUMMARY, session_data)
        
        # With organization
        session_data.organization = sample_org_profile
        assert orchestrator.can_advance_to_step(WorkflowStep.SUMMARY, session_data)
    
    def test_course_type_requires_organization(self, orchestrator, sample_org_profile):
        """Test that COURSE_TYPE step requires organization profile"""
        # Without organization
        session_data = SessionData(
            session_id="test-session",
            current_step="upload"
        )
        assert not orchestrator.can_advance_to_step(WorkflowStep.COURSE_TYPE, session_data)
        
        # With organization
        session_data.organization = sample_org_profile
        assert orchestrator.can_advance_to_step(WorkflowStep.COURSE_TYPE, session_data)
    
    def test_tlo_generation_requires_course_type(self, orchestrator, sample_org_profile):
        """Test that TLO_GENERATION step requires course type"""
        session_data = SessionData(
            session_id="test-session",
            current_step="course_type",
            organization=sample_org_profile
        )
        
        # Without course type
        assert not orchestrator.can_advance_to_step(WorkflowStep.TLO_GENERATION, session_data)
        
        # With course type
        session_data.course_type = "B2B"
        assert orchestrator.can_advance_to_step(WorkflowStep.TLO_GENERATION, session_data)
    
    def test_tlo_selection_requires_generated_tlos(self, orchestrator, sample_org_profile, sample_tlos):
        """Test that TLO_SELECTION step requires generated TLOs"""
        session_data = SessionData(
            session_id="test-session",
            current_step="tlo_generation",
            organization=sample_org_profile,
            course_type="B2B"
        )
        
        # Without TLOs
        assert not orchestrator.can_advance_to_step(WorkflowStep.TLO_SELECTION, session_data)
        
        # With TLOs
        session_data.tlos = sample_tlos
        assert orchestrator.can_advance_to_step(WorkflowStep.TLO_SELECTION, session_data)
    
    def test_performance_generation_requires_selected_tlos(self, orchestrator, sample_tlos):
        """Test that PERFORMANCE_GENERATION step requires at least one selected TLO"""
        session_data = SessionData(
            session_id="test-session",
            current_step="tlo_selection",
            tlos=sample_tlos
        )
        
        # With selected TLO
        assert orchestrator.can_advance_to_step(WorkflowStep.PERFORMANCE_GENERATION, session_data)
        
        # Without selected TLOs
        for tlo in session_data.tlos:
            tlo.is_selected = False
        assert not orchestrator.can_advance_to_step(WorkflowStep.PERFORMANCE_GENERATION, session_data)
    
    def test_performance_selection_requires_generated_performances(
        self, orchestrator, sample_tlos, sample_performances
    ):
        """Test that PERFORMANCE_SELECTION step requires generated performances"""
        session_data = SessionData(
            session_id="test-session",
            current_step="performance_generation",
            tlos=sample_tlos
        )
        
        # Without performances
        assert not orchestrator.can_advance_to_step(WorkflowStep.PERFORMANCE_SELECTION, session_data)
        
        # With performances
        session_data.performances = sample_performances
        assert orchestrator.can_advance_to_step(WorkflowStep.PERFORMANCE_SELECTION, session_data)
    
    def test_elo_generation_requires_selected_performances(self, orchestrator, sample_performances):
        """Test that ELO_GENERATION step requires at least one selected performance"""
        session_data = SessionData(
            session_id="test-session",
            current_step="performance_selection",
            performances=sample_performances
        )
        
        # With selected performance
        assert orchestrator.can_advance_to_step(WorkflowStep.ELO_GENERATION, session_data)
        
        # Without selected performances
        for perf in session_data.performances:
            perf.is_selected = False
        assert not orchestrator.can_advance_to_step(WorkflowStep.ELO_GENERATION, session_data)
    
    def test_elo_selection_requires_generated_elos(
        self, orchestrator, sample_performances, sample_elos
    ):
        """Test that ELO_SELECTION step requires generated ELOs"""
        session_data = SessionData(
            session_id="test-session",
            current_step="elo_generation",
            performances=sample_performances
        )
        
        # Without ELOs
        assert not orchestrator.can_advance_to_step(WorkflowStep.ELO_SELECTION, session_data)
        
        # With ELOs
        session_data.elos = sample_elos
        assert orchestrator.can_advance_to_step(WorkflowStep.ELO_SELECTION, session_data)
    
    def test_syllabus_generation_requires_selected_elos(self, orchestrator, sample_elos):
        """Test that SYLLABUS_GENERATION step requires at least one selected ELO"""
        session_data = SessionData(
            session_id="test-session",
            current_step="elo_selection",
            elos=sample_elos
        )
        
        # With selected ELO
        assert orchestrator.can_advance_to_step(WorkflowStep.SYLLABUS_GENERATION, session_data)
        
        # Without selected ELOs
        for elo in session_data.elos:
            elo.is_selected = False
        assert not orchestrator.can_advance_to_step(WorkflowStep.SYLLABUS_GENERATION, session_data)


class TestProcessOrganizationProfile:
    """Test process_organization_profile method"""
    
    def test_successful_processing(self, orchestrator, mock_db, mock_ai):
        """Test successful organization profile processing"""
        # Setup mocks
        file_content = b"Sample organization profile content with enough text to be valid"
        file_type = ".txt"
        file_name = "org_profile.txt"
        
        mock_ai.summarize_organization_profile.return_value = "Generated summary"
        mock_db.save_organization_profile.return_value = "org-123"
        
        # Execute
        result = orchestrator.process_organization_profile(
            file_content, file_type, file_name
        )
        
        # Verify
        assert result.id == "org-123"
        assert result.summary == "Generated summary"
        assert result.context_overview == "Generated summary"
        assert result.file_name == file_name
        assert result.file_type == file_type
        assert result.original_text == "Sample organization profile content with enough text to be valid"
        assert orchestrator.current_step == WorkflowStep.SUMMARY
        
        # Verify AI service was called with extracted text
        mock_ai.summarize_organization_profile.assert_called_once_with(
            "Sample organization profile content with enough text to be valid"
        )
        
        # Verify database save was called
        mock_db.save_organization_profile.assert_called_once()
        saved_profile = mock_db.save_organization_profile.call_args[0][0]
        assert saved_profile.original_text == "Sample organization profile content with enough text to be valid"
        assert saved_profile.summary == "Generated summary"
        assert saved_profile.file_name == file_name
        assert saved_profile.file_type == file_type
    
    def test_unsupported_format_raises_error(self, orchestrator):
        """Test that unsupported file format raises error"""
        from src.processors.document_processor import UnsupportedFormatError
        
        file_content = b"content"
        file_type = ".jpg"
        file_name = "image.jpg"
        
        with pytest.raises(UnsupportedFormatError):
            orchestrator.process_organization_profile(
                file_content, file_type, file_name
            )
    
    def test_empty_file_raises_error(self, orchestrator):
        """Test that empty file raises error"""
        from src.processors.document_processor import EmptyFileError
        
        file_content = b""
        file_type = ".txt"
        file_name = "empty.txt"
        
        with pytest.raises(EmptyFileError):
            orchestrator.process_organization_profile(
                file_content, file_type, file_name
            )
    
    def test_file_with_insufficient_content_raises_error(self, orchestrator):
        """Test that file with insufficient content raises error"""
        from src.processors.document_processor import EmptyFileError
        
        file_content = b"short"  # Less than 10 characters
        file_type = ".txt"
        file_name = "short.txt"
        
        with pytest.raises(EmptyFileError) as exc_info:
            orchestrator.process_organization_profile(
                file_content, file_type, file_name
            )
        
        assert "tidak mengandung teks yang dapat dibaca" in str(exc_info.value).lower()
    
    def test_document_processor_integration(self, orchestrator, mock_db, mock_ai):
        """Test that document processor correctly extracts text"""
        # Setup mocks
        file_content = b"This is a test organization profile with sufficient content for validation"
        file_type = ".txt"
        file_name = "test.txt"
        
        mock_ai.summarize_organization_profile.return_value = "Test summary"
        mock_db.save_organization_profile.return_value = "org-456"
        
        # Execute
        result = orchestrator.process_organization_profile(
            file_content, file_type, file_name
        )
        
        # Verify text extraction worked
        assert "test organization profile" in result.original_text.lower()
        
    def test_ai_service_integration(self, orchestrator, mock_db, mock_ai):
        """Test that AI service is called with correct parameters"""
        # Setup mocks
        file_content = b"Organization profile text for AI processing with enough content"
        file_type = ".txt"
        file_name = "ai_test.txt"
        
        mock_ai.summarize_organization_profile.return_value = "AI generated summary"
        mock_db.save_organization_profile.return_value = "org-789"
        
        # Execute
        result = orchestrator.process_organization_profile(
            file_content, file_type, file_name
        )
        
        # Verify AI service was called with extracted text
        mock_ai.summarize_organization_profile.assert_called_once()
        call_args = mock_ai.summarize_organization_profile.call_args[0][0]
        assert "Organization profile text" in call_args
        
    def test_database_integration(self, orchestrator, mock_db, mock_ai):
        """Test that database service is called with correct profile data"""
        # Setup mocks
        file_content = b"Database integration test content with sufficient length for validation"
        file_type = ".txt"
        file_name = "db_test.txt"
        
        mock_ai.summarize_organization_profile.return_value = "Database test summary"
        mock_db.save_organization_profile.return_value = "org-db-123"
        
        # Execute
        result = orchestrator.process_organization_profile(
            file_content, file_type, file_name
        )
        
        # Verify database save was called with correct data
        mock_db.save_organization_profile.assert_called_once()
        saved_profile = mock_db.save_organization_profile.call_args[0][0]
        
        assert isinstance(saved_profile, OrganizationProfile)
        assert saved_profile.original_text == "Database integration test content with sufficient length for validation"
        assert saved_profile.summary == "Database test summary"
        assert saved_profile.context_overview == "Database test summary"
        assert saved_profile.file_name == "db_test.txt"
        assert saved_profile.file_type == ".txt"


class TestGenerateTLOs:
    """Test generate_tlos method"""
    
    def test_successful_tlo_generation(self, orchestrator, mock_db, mock_ai, sample_org_profile):
        """Test successful TLO generation"""
        # Setup mocks
        mock_db.get_organization_profile.return_value = sample_org_profile
        mock_ai.generate_tlos.return_value = [
            "TLO 1", "TLO 2", "TLO 3", "TLO 4", "TLO 5"
        ]
        mock_db.save_tlos.return_value = ["tlo-1", "tlo-2", "tlo-3", "tlo-4", "tlo-5"]
        
        # Execute
        result = orchestrator.generate_tlos("org-123", "B2B", count=5)
        
        # Verify
        assert len(result) == 5
        assert all(tlo.org_id == "org-123" for tlo in result)
        assert all(tlo.course_type == "B2B" for tlo in result)
        assert orchestrator.current_step == WorkflowStep.TLO_SELECTION
        
        mock_ai.generate_tlos.assert_called_once_with(
            org_context=sample_org_profile.summary,
            course_type="B2B",
            count=5
        )
        mock_db.save_tlos.assert_called_once()
    
    def test_insufficient_tlos_raises_error(self, orchestrator, mock_db, mock_ai, sample_org_profile):
        """Test that generating fewer than 3 TLOs raises error"""
        # Setup mocks
        mock_db.get_organization_profile.return_value = sample_org_profile
        mock_ai.generate_tlos.return_value = ["TLO 1", "TLO 2"]  # Only 2 TLOs
        
        # Execute and verify
        with pytest.raises(WorkflowStateError) as exc_info:
            orchestrator.generate_tlos("org-123", "B2B")
        
        assert "minimum" in str(exc_info.value).lower()
    
    def test_missing_organization_raises_error(self, orchestrator, mock_db):
        """Test that missing organization profile raises error"""
        mock_db.get_organization_profile.return_value = None
        
        with pytest.raises(WorkflowStateError) as exc_info:
            orchestrator.generate_tlos("org-123", "B2B")
        
        assert "tidak ditemukan" in str(exc_info.value).lower()


class TestGeneratePerformances:
    """Test generate_performances method"""
    
    def test_successful_performance_generation(self, orchestrator, mock_db, mock_ai, sample_tlos):
        """Test successful performance generation"""
        # Setup mocks
        mock_db.get_tlos_by_org.return_value = sample_tlos
        mock_ai.generate_performances.return_value = [
            "Performance 1", "Performance 2", "Performance 3", "Performance 4", "Performance 5"
        ]
        mock_db.save_performances.return_value = ["perf-1", "perf-2", "perf-3", "perf-4", "perf-5"]
        
        # Execute
        result = orchestrator.generate_performances(
            selected_tlo_ids=["tlo-1"],
            org_id="org-123",
            count=5
        )
        
        # Verify
        assert len(result) == 5
        assert all(perf.tlo_ids == ["tlo-1"] for perf in result)
        assert orchestrator.current_step == WorkflowStep.PERFORMANCE_SELECTION
        
        mock_ai.generate_performances.assert_called_once_with(
            tlo_texts=["TLO 1 text"],
            count=5
        )
        mock_db.save_performances.assert_called_once()
    
    def test_empty_tlo_list_raises_error(self, orchestrator):
        """Test that empty TLO list raises error"""
        with pytest.raises(WorkflowStateError) as exc_info:
            orchestrator.generate_performances([], org_id="org-123")
        
        assert "pilih" in str(exc_info.value).lower()
    
    def test_tlos_not_found_raises_error(self, orchestrator, mock_db):
        """Test that missing TLOs raises error"""
        mock_db.get_tlos_by_org.return_value = []
        
        with pytest.raises(WorkflowStateError) as exc_info:
            orchestrator.generate_performances(["tlo-999"], org_id="org-123")
        
        assert "tidak ditemukan" in str(exc_info.value).lower()
    
    def test_multiple_selected_tlos(self, orchestrator, mock_db, mock_ai, sample_tlos):
        """Test performance generation with multiple selected TLOs"""
        # Setup mocks
        mock_db.get_tlos_by_org.return_value = sample_tlos
        mock_ai.generate_performances.return_value = [
            "Performance 1", "Performance 2", "Performance 3"
        ]
        mock_db.save_performances.return_value = ["perf-1", "perf-2", "perf-3"]
        
        # Execute with both TLOs selected
        result = orchestrator.generate_performances(
            selected_tlo_ids=["tlo-1", "tlo-2"],
            org_id="org-123",
            count=3
        )
        
        # Verify
        assert len(result) == 3
        assert all(set(perf.tlo_ids) == {"tlo-1", "tlo-2"} for perf in result)
        
        # Verify AI was called with both TLO texts
        mock_ai.generate_performances.assert_called_once()
        call_args = mock_ai.generate_performances.call_args[1]
        assert len(call_args['tlo_texts']) == 2
        assert "TLO 1 text" in call_args['tlo_texts']
        assert "TLO 2 text" in call_args['tlo_texts']


class TestGenerateELOs:
    """Test generate_elos method"""
    
    def test_successful_elo_generation(self, orchestrator, mock_db, mock_ai, sample_performances):
        """Test successful ELO generation"""
        # Setup mocks
        mock_db.get_performances_by_ids.return_value = sample_performances
        mock_ai.generate_elos.return_value = [
            "ELO 1", "ELO 2", "ELO 3", "ELO 4", "ELO 5"
        ]
        mock_db.save_elos.return_value = ["elo-1", "elo-2", "elo-3", "elo-4", "elo-5"]
        
        # Execute
        result = orchestrator.generate_elos(
            selected_performance_ids=["perf-1"],
            count=5
        )
        
        # Verify
        assert len(result) == 5
        assert all(elo.performance_ids == ["perf-1"] for elo in result)
        assert orchestrator.current_step == WorkflowStep.ELO_SELECTION
        
        mock_ai.generate_elos.assert_called_once_with(
            performance_texts=["Performance 1 text"],
            count=5
        )
        mock_db.save_elos.assert_called_once()
    
    def test_empty_performance_list_raises_error(self, orchestrator):
        """Test that empty performance list raises error"""
        with pytest.raises(WorkflowStateError) as exc_info:
            orchestrator.generate_elos([])
        
        assert "pilih" in str(exc_info.value).lower()
    
    def test_performances_not_found_raises_error(self, orchestrator, mock_db):
        """Test that missing performances raises error"""
        mock_db.get_performances_by_ids.return_value = []
        
        with pytest.raises(WorkflowStateError) as exc_info:
            orchestrator.generate_elos(["perf-999"])
        
        assert "tidak ditemukan" in str(exc_info.value).lower()
    
    def test_insufficient_elos_raises_error(self, orchestrator, mock_db, mock_ai, sample_performances):
        """Test that generating fewer than 3 ELOs raises error"""
        # Setup mocks
        mock_db.get_performances_by_ids.return_value = sample_performances
        mock_ai.generate_elos.return_value = ["ELO 1", "ELO 2"]  # Only 2 ELOs
        
        # Execute and verify
        with pytest.raises(WorkflowStateError) as exc_info:
            orchestrator.generate_elos(["perf-1"])
        
        assert "minimum" in str(exc_info.value).lower()
    
    def test_multiple_selected_performances(self, orchestrator, mock_db, mock_ai, sample_performances):
        """Test ELO generation with multiple selected performances"""
        # Setup mocks
        mock_db.get_performances_by_ids.return_value = sample_performances
        mock_ai.generate_elos.return_value = [
            "ELO 1", "ELO 2", "ELO 3", "ELO 4"
        ]
        mock_db.save_elos.return_value = ["elo-1", "elo-2", "elo-3", "elo-4"]
        
        # Execute with both performances selected
        result = orchestrator.generate_elos(
            selected_performance_ids=["perf-1", "perf-2"],
            count=4
        )
        
        # Verify
        assert len(result) == 4
        assert all(set(elo.performance_ids) == {"perf-1", "perf-2"} for elo in result)
        
        # Verify AI was called with both performance texts
        mock_ai.generate_elos.assert_called_once()
        call_args = mock_ai.generate_elos.call_args[1]
        assert len(call_args['performance_texts']) == 2
        assert "Performance 1 text" in call_args['performance_texts']
        assert "Performance 2 text" in call_args['performance_texts']


class TestCreateSyllabusDocument:
    """Test create_syllabus_document method"""
    
    def test_empty_elo_list_raises_error(self, orchestrator):
        """Test that empty ELO list raises error"""
        with pytest.raises(WorkflowStateError) as exc_info:
            orchestrator.create_syllabus_document(
                session_id="test-session",
                org_id="org-123",
                course_type="B2B",
                selected_tlo_ids=["tlo-1"],
                selected_performance_ids=["perf-1"],
                selected_elo_ids=[]
            )
        
        assert "pilih" in str(exc_info.value).lower()
    
    def test_successful_syllabus_creation(
        self, orchestrator, mock_db, mock_ai,
        sample_org_profile, sample_tlos, sample_performances, sample_elos
    ):
        """Test successful syllabus document creation"""
        # Setup mocks
        mock_db.get_organization_profile.return_value = sample_org_profile
        mock_db.get_tlos_by_org.return_value = sample_tlos
        mock_db.get_performances_by_tlos.return_value = sample_performances
        mock_db.get_elos_by_performances.return_value = sample_elos
        mock_ai.format_syllabus_content.return_value = "Formatted syllabus content"
        mock_db.save_syllabus.return_value = "syllabus-123"
        
        # Execute
        result = orchestrator.create_syllabus_document(
            session_id="test-session",
            org_id="org-123",
            course_type="B2B",
            selected_tlo_ids=["tlo-1"],
            selected_performance_ids=["perf-1"],
            selected_elo_ids=["elo-1"]
        )
        
        # Verify result is bytes (DOCX document)
        assert isinstance(result, bytes)
        assert len(result) > 0
        
        # Verify workflow state updated
        assert orchestrator.current_step == WorkflowStep.SYLLABUS_GENERATION
        
        # Verify database calls
        mock_db.get_organization_profile.assert_called_once_with("org-123")
        mock_db.get_tlos_by_org.assert_called_once_with("org-123")
        mock_db.get_performances_by_tlos.assert_called_once_with(["tlo-1"])
        mock_db.get_elos_by_performances.assert_called_once_with(["perf-1"])
        
        # Verify AI service was called
        mock_ai.format_syllabus_content.assert_called_once()
        
        # Verify syllabus was saved to database
        mock_db.save_syllabus.assert_called_once()
        saved_syllabus = mock_db.save_syllabus.call_args[0][0]
        assert saved_syllabus.session_id == "test-session"
        assert saved_syllabus.org_id == "org-123"
        assert saved_syllabus.course_type == "B2B"
        assert saved_syllabus.selected_tlo_ids == ["tlo-1"]
        assert saved_syllabus.selected_performance_ids == ["perf-1"]
        assert saved_syllabus.selected_elo_ids == ["elo-1"]
    
    def test_missing_organization_raises_error(self, orchestrator, mock_db):
        """Test that missing organization profile raises error"""
        mock_db.get_organization_profile.return_value = None
        
        with pytest.raises(WorkflowStateError) as exc_info:
            orchestrator.create_syllabus_document(
                session_id="test-session",
                org_id="org-123",
                course_type="B2B",
                selected_tlo_ids=["tlo-1"],
                selected_performance_ids=["perf-1"],
                selected_elo_ids=["elo-1"]
            )
        
        assert "tidak ditemukan" in str(exc_info.value).lower()
    
    def test_retrieves_all_selected_materials(
        self, orchestrator, mock_db, mock_ai,
        sample_org_profile, sample_tlos, sample_performances, sample_elos
    ):
        """Test that all selected materials are retrieved from database"""
        # Setup mocks
        mock_db.get_organization_profile.return_value = sample_org_profile
        mock_db.get_tlos_by_org.return_value = sample_tlos
        mock_db.get_performances_by_tlos.return_value = sample_performances
        mock_db.get_elos_by_performances.return_value = sample_elos
        mock_ai.format_syllabus_content.return_value = "Formatted content"
        mock_db.save_syllabus.return_value = "syllabus-456"
        
        # Execute
        orchestrator.create_syllabus_document(
            session_id="test-session",
            org_id="org-123",
            course_type="B2B",
            selected_tlo_ids=["tlo-1", "tlo-2"],
            selected_performance_ids=["perf-1", "perf-2"],
            selected_elo_ids=["elo-1", "elo-2"]
        )
        
        # Verify all retrieval methods were called
        mock_db.get_organization_profile.assert_called_once_with("org-123")
        mock_db.get_tlos_by_org.assert_called_once_with("org-123")
        mock_db.get_performances_by_tlos.assert_called_once_with(["tlo-1", "tlo-2"])
        mock_db.get_elos_by_performances.assert_called_once_with(["perf-1", "perf-2"])
    
    def test_calls_ai_service_to_format_content(
        self, orchestrator, mock_db, mock_ai,
        sample_org_profile, sample_tlos, sample_performances, sample_elos
    ):
        """Test that AI service is called to format syllabus content"""
        # Setup mocks
        mock_db.get_organization_profile.return_value = sample_org_profile
        mock_db.get_tlos_by_org.return_value = sample_tlos
        mock_db.get_performances_by_tlos.return_value = sample_performances
        mock_db.get_elos_by_performances.return_value = sample_elos
        mock_ai.format_syllabus_content.return_value = "AI formatted content"
        mock_db.save_syllabus.return_value = "syllabus-789"
        
        # Execute
        orchestrator.create_syllabus_document(
            session_id="test-session",
            org_id="org-123",
            course_type="B2B",
            selected_tlo_ids=["tlo-1"],
            selected_performance_ids=["perf-1"],
            selected_elo_ids=["elo-1"]
        )
        
        # Verify AI service was called with correct parameters
        mock_ai.format_syllabus_content.assert_called_once_with(
            org_summary=sample_org_profile.summary,
            tlos=["TLO 1 text"],
            performances=["Performance 1 text"],
            elos=["ELO 1 text"]
        )
    
    def test_generates_docx_document(
        self, orchestrator, mock_db, mock_ai,
        sample_org_profile, sample_tlos, sample_performances, sample_elos
    ):
        """Test that DOCX document is generated using DocumentGenerator"""
        # Setup mocks
        mock_db.get_organization_profile.return_value = sample_org_profile
        mock_db.get_tlos_by_org.return_value = sample_tlos
        mock_db.get_performances_by_tlos.return_value = sample_performances
        mock_db.get_elos_by_performances.return_value = sample_elos
        mock_ai.format_syllabus_content.return_value = "Formatted content"
        mock_db.save_syllabus.return_value = "syllabus-docx"
        
        # Execute
        result = orchestrator.create_syllabus_document(
            session_id="test-session",
            org_id="org-123",
            course_type="B2B",
            selected_tlo_ids=["tlo-1"],
            selected_performance_ids=["perf-1"],
            selected_elo_ids=["elo-1"]
        )
        
        # Verify result is bytes (DOCX format)
        assert isinstance(result, bytes)
        
        # Verify document generator was used (result should be DOCX, not plain text)
        # DOCX files start with PK (ZIP signature)
        assert result[:2] == b'PK'
    
    def test_stores_syllabus_in_database(
        self, orchestrator, mock_db, mock_ai,
        sample_org_profile, sample_tlos, sample_performances, sample_elos
    ):
        """Test that syllabus is stored in database"""
        # Setup mocks
        mock_db.get_organization_profile.return_value = sample_org_profile
        mock_db.get_tlos_by_org.return_value = sample_tlos
        mock_db.get_performances_by_tlos.return_value = sample_performances
        mock_db.get_elos_by_performances.return_value = sample_elos
        mock_ai.format_syllabus_content.return_value = "Formatted content"
        mock_db.save_syllabus.return_value = "syllabus-db-123"
        
        # Execute
        orchestrator.create_syllabus_document(
            session_id="test-session-db",
            org_id="org-123",
            course_type="Innovation",
            selected_tlo_ids=["tlo-1"],
            selected_performance_ids=["perf-1"],
            selected_elo_ids=["elo-1"]
        )
        
        # Verify save_syllabus was called
        mock_db.save_syllabus.assert_called_once()
        
        # Verify saved syllabus has correct attributes
        saved_syllabus = mock_db.save_syllabus.call_args[0][0]
        assert saved_syllabus.session_id == "test-session-db"
        assert saved_syllabus.org_id == "org-123"
        assert saved_syllabus.course_type == "Innovation"
        assert saved_syllabus.selected_tlo_ids == ["tlo-1"]
        assert saved_syllabus.selected_performance_ids == ["perf-1"]
        assert saved_syllabus.selected_elo_ids == ["elo-1"]
        assert isinstance(saved_syllabus.document_content, bytes)
        assert len(saved_syllabus.document_content) > 0
