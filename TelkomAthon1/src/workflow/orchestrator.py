"""Workflow orchestrator for managing the syllabus generation process"""

from typing import List, Optional
from src.models.entities import (
    WorkflowStep,
    OrganizationProfile,
    TLO,
    Performance,
    ELO,
    Syllabus,
    SessionData,
    SyllabusMaterials
)
from src.database.service import DatabaseService
from src.services.ai_service import AIService
from src.processors.document_processor import DocumentProcessor
from src.processors.document_generator import DocumentGenerator


class WorkflowStateError(Exception):
    """Raised when workflow state is invalid or transition is not allowed"""
    pass


class WorkflowOrchestrator:
    """
    Orchestrates the multi-step workflow for syllabus generation.
    
    Manages state transitions, validates prerequisites, and coordinates
    between document processing, AI generation, and database persistence.
    """
    
    def __init__(self, db: DatabaseService, ai: AIService):
        """
        Initialize workflow orchestrator
        
        Args:
            db: Database service for data persistence
            ai: AI service for content generation
        """
        self.db = db
        self.ai = ai
        self.document_processor = DocumentProcessor()
        self.document_generator = DocumentGenerator()
        self.current_step = WorkflowStep.UPLOAD
    
    def can_advance_to_step(
        self,
        target_step: WorkflowStep,
        session_data: SessionData
    ) -> bool:
        """
        Validate if user can advance to target workflow step.
        
        Checks that all prerequisites for the target step are met based on
        the current session data.
        
        Args:
            target_step: The workflow step to advance to
            session_data: Current session data with workflow state
            
        Returns:
            True if advancement is allowed, False otherwise
        """
        # UPLOAD step is always accessible
        if target_step == WorkflowStep.UPLOAD:
            return True
        
        # SUMMARY step requires organization profile
        if target_step == WorkflowStep.SUMMARY:
            return session_data.organization is not None
        
        # COURSE_TYPE step requires organization profile
        if target_step == WorkflowStep.COURSE_TYPE:
            return session_data.organization is not None
        
        # TLO_GENERATION step requires course type selection
        if target_step == WorkflowStep.TLO_GENERATION:
            return (
                session_data.organization is not None and
                session_data.course_type is not None
            )
        
        # TLO_SELECTION step requires generated TLOs
        if target_step == WorkflowStep.TLO_SELECTION:
            return (
                session_data.organization is not None and
                session_data.course_type is not None and
                len(session_data.tlos) > 0
            )
        
        # PERFORMANCE_GENERATION step requires at least one selected TLO
        if target_step == WorkflowStep.PERFORMANCE_GENERATION:
            return any(tlo.is_selected for tlo in session_data.tlos)
        
        # PERFORMANCE_SELECTION step requires generated performances
        if target_step == WorkflowStep.PERFORMANCE_SELECTION:
            return (
                any(tlo.is_selected for tlo in session_data.tlos) and
                len(session_data.performances) > 0
            )
        
        # ELO_GENERATION step requires at least one selected performance
        if target_step == WorkflowStep.ELO_GENERATION:
            return any(perf.is_selected for perf in session_data.performances)
        
        # ELO_SELECTION step requires generated ELOs
        if target_step == WorkflowStep.ELO_SELECTION:
            return (
                any(perf.is_selected for perf in session_data.performances) and
                len(session_data.elos) > 0
            )
        
        # SYLLABUS_GENERATION step requires at least one selected ELO
        if target_step == WorkflowStep.SYLLABUS_GENERATION:
            return any(elo.is_selected for elo in session_data.elos)
        
        return False
    
    def process_organization_profile(
        self,
        file_content: bytes,
        file_type: str,
        file_name: str
    ) -> OrganizationProfile:
        """
        Process uploaded organization profile document.
        
        Extracts text from the document, generates AI summary, and stores
        the profile in the database.
        
        Args:
            file_content: Document file content as bytes
            file_type: File extension (e.g., '.pdf', '.docx', '.txt')
            file_name: Original file name
            
        Returns:
            OrganizationProfile entity with generated summary
            
        Raises:
            UnsupportedFormatError: If file format is not supported
            EmptyFileError: If file is empty or unreadable
            AIServiceError: If AI summary generation fails
            DatabaseError: If database operation fails
        """
        # Extract text from document
        original_text = self.document_processor.process_document(
            file_content,
            file_type
        )
        
        # Validate extracted content
        if not self.document_processor.validate_document_content(original_text):
            from src.processors.document_processor import EmptyFileError
            raise EmptyFileError("Dokumen tidak mengandung teks yang dapat dibaca")
        
        # Generate AI summary
        summary = self.ai.summarize_organization_profile(original_text)
        
        # Create organization profile entity
        profile = OrganizationProfile(
            original_text=original_text,
            summary=summary,
            context_overview=summary,  # Using summary as context overview
            file_name=file_name,
            file_type=file_type
        )
        
        # Save to database
        profile_id = self.db.save_organization_profile(profile)
        profile.id = profile_id
        
        # Update workflow state
        self.current_step = WorkflowStep.SUMMARY
        
        return profile
    
    def generate_tlos(
        self,
        org_id: str,
        course_type: str,
        count: int = 5
    ) -> List[TLO]:
        """
        Generate Terminal Learning Objectives.
        
        Uses organization context and course type to generate TLOs via AI,
        then stores them in the database.
        
        Args:
            org_id: Organization profile ID
            course_type: Selected course type
            count: Number of TLOs to generate (default: 5)
            
        Returns:
            List of generated TLO entities
            
        Raises:
            AIServiceError: If AI generation fails
            DatabaseError: If database operation fails
        """
        # Get organization profile for context
        org_profile = self.db.get_organization_profile(org_id)
        if not org_profile:
            raise WorkflowStateError(
                "Profil organisasi tidak ditemukan. Silakan unggah profil terlebih dahulu."
            )
        
        # Generate TLOs using AI
        tlo_texts = self.ai.generate_tlos(
            org_context=org_profile.summary,
            course_type=course_type,
            count=count
        )
        
        # Ensure minimum count
        if len(tlo_texts) < 3:
            raise WorkflowStateError(
                f"Gagal menghasilkan jumlah TLO minimum (3). Hanya {len(tlo_texts)} yang dihasilkan."
            )
        
        # Create TLO entities
        tlos = [
            TLO(
                org_id=org_id,
                course_type=course_type,
                text=text,
                is_selected=False
            )
            for text in tlo_texts
        ]
        
        # Save to database
        tlo_ids = self.db.save_tlos(tlos, org_id, course_type)
        
        # Update TLO IDs
        for tlo, tlo_id in zip(tlos, tlo_ids):
            tlo.id = tlo_id
        
        # Update workflow state
        self.current_step = WorkflowStep.TLO_SELECTION
        
        return tlos
    
    def generate_performances(
        self,
        selected_tlo_ids: List[str],
        org_id: str,
        count: int = 5
    ) -> List[Performance]:
        """
        Generate performance objectives from selected TLOs.
        
        Uses selected TLO texts as context to generate performance objectives
        via AI, then stores them in the database.
        
        Args:
            selected_tlo_ids: List of selected TLO IDs
            org_id: Organization profile ID (needed to retrieve TLOs)
            count: Number of performances to generate (default: 5)
            
        Returns:
            List of generated Performance entities
            
        Raises:
            WorkflowStateError: If no TLOs are selected
            AIServiceError: If AI generation fails
            DatabaseError: If database operation fails
        """
        if not selected_tlo_ids:
            raise WorkflowStateError(
                "Silakan pilih setidaknya satu TLO terlebih dahulu."
            )
        
        # Get all TLOs for the organization
        all_tlos = self.db.get_tlos_by_org(org_id)
        
        # Filter to get only selected TLOs
        selected_tlos = [tlo for tlo in all_tlos if tlo.id in selected_tlo_ids]
        
        if not selected_tlos:
            raise WorkflowStateError(
                "TLO yang dipilih tidak ditemukan."
            )
        
        # Extract TLO texts
        tlo_texts = [tlo.text for tlo in selected_tlos]
        
        # Generate performances using AI
        performance_texts = self.ai.generate_performances(
            tlo_texts=tlo_texts,
            count=count
        )
        
        # Create Performance entities
        performances = [
            Performance(
                tlo_ids=selected_tlo_ids,
                text=text,
                is_selected=False
            )
            for text in performance_texts
        ]
        
        # Save to database
        performance_ids = self.db.save_performances(performances, selected_tlo_ids)
        
        # Update performance IDs
        for perf, perf_id in zip(performances, performance_ids):
            perf.id = perf_id
        
        # Update workflow state
        self.current_step = WorkflowStep.PERFORMANCE_SELECTION
        
        return performances
    
    def generate_elos(
        self,
        selected_performance_ids: List[str],
        count: int = 3
    ) -> List[ELO]:
        """
        Generate Enabling Learning Objectives from selected performances.
        
        Uses selected performance texts as context to generate ELOs via AI,
        then stores them in the database.
        
        Args:
            selected_performance_ids: List of selected performance IDs
            count: Number of ELOs to generate per performance (default: 3)
            
        Returns:
            List of generated ELO entities
            
        Raises:
            WorkflowStateError: If no performances are selected
            AIServiceError: If AI generation fails
            DatabaseError: If database operation fails
        """
        if not selected_performance_ids:
            raise WorkflowStateError(
                "Silakan pilih setidaknya satu performance terlebih dahulu."
            )
        
        # Get selected performances by their IDs
        selected_performances = self.db.get_performances_by_ids(selected_performance_ids)
        
        if not selected_performances:
            raise WorkflowStateError(
                "Performance yang dipilih tidak ditemukan."
            )
        
        # Extract performance texts
        performance_texts = [p.text for p in selected_performances]
        
        # Generate ELOs using AI
        elo_texts = self.ai.generate_elos(
            performance_texts=performance_texts,
            count=count
        )
        
        # Ensure minimum count
        if len(elo_texts) < 3:
            raise WorkflowStateError(
                f"Gagal menghasilkan jumlah ELO minimum (3). Hanya {len(elo_texts)} yang dihasilkan."
            )
        
        # Create ELO entities
        elos = [
            ELO(
                performance_ids=selected_performance_ids,
                text=text,
                is_selected=False
            )
            for text in elo_texts
        ]
        
        # Save to database
        elo_ids = self.db.save_elos(elos, selected_performance_ids)
        
        # Update ELO IDs
        for elo, elo_id in zip(elos, elo_ids):
            elo.id = elo_id
        
        # Update workflow state
        self.current_step = WorkflowStep.ELO_SELECTION
        
        return elos
    
    def create_syllabus_document(
        self,
        session_id: str,
        org_id: str,
        course_type: str,
        selected_tlo_ids: List[str],
        selected_performance_ids: List[str],
        selected_elo_ids: List[str]
    ) -> bytes:
        """
        Compile all selections into final syllabus document.
        
        Retrieves all selected materials from database, calls AI service to format
        content, and generates a DOCX document using DocumentGenerator.
        
        Args:
            session_id: Session identifier
            org_id: Organization profile ID
            course_type: Selected course type
            selected_tlo_ids: List of selected TLO IDs
            selected_performance_ids: List of selected performance IDs
            selected_elo_ids: List of selected ELO IDs
            
        Returns:
            DOCX document content as bytes
            
        Raises:
            WorkflowStateError: If required selections are missing
            AIServiceError: If AI formatting fails
            DatabaseError: If database operation fails
        """
        if not selected_elo_ids:
            raise WorkflowStateError(
                "Silakan pilih setidaknya satu ELO terlebih dahulu."
            )
        
        # Retrieve all selected materials from database
        
        # Get organization profile
        org_profile = self.db.get_organization_profile(org_id)
        if not org_profile:
            raise WorkflowStateError("Profil organisasi tidak ditemukan.")
        
        # Get selected TLOs
        all_tlos = self.db.get_tlos_by_org(org_id)
        selected_tlos = [t for t in all_tlos if t.id in selected_tlo_ids]
        
        # Get selected performances
        all_performances = self.db.get_performances_by_tlos(selected_tlo_ids)
        selected_performances = [
            p for p in all_performances
            if p.id in selected_performance_ids
        ]
        
        # Get selected ELOs
        all_elos = self.db.get_elos_by_performances(selected_performance_ids)
        selected_elos = [e for e in all_elos if e.id in selected_elo_ids]
        
        # Create syllabus materials
        materials = SyllabusMaterials(
            organization_summary=org_profile.summary,
            organization_context=org_profile.context_overview,
            selected_tlos=selected_tlos,
            selected_performances=selected_performances,
            selected_elos=selected_elos,
            course_type=course_type
        )
        
        # Call AI service to format content (optional enhancement)
        # This can be used to add AI-generated introductions or transitions
        formatted_content = self.ai.format_syllabus_content(
            org_summary=materials.organization_summary,
            tlos=[t.text for t in materials.selected_tlos],
            performances=[p.text for p in materials.selected_performances],
            elos=[e.text for e in materials.selected_elos]
        )
        
        # Generate DOCX document using DocumentGenerator
        document_content = self.document_generator.create_syllabus_document(materials)
        
        # Create syllabus entity
        syllabus = Syllabus(
            session_id=session_id,
            org_id=org_id,
            course_type=course_type,
            selected_tlo_ids=selected_tlo_ids,
            selected_performance_ids=selected_performance_ids,
            selected_elo_ids=selected_elo_ids,
            document_content=document_content
        )
        
        # Store syllabus in database
        syllabus_id = self.db.save_syllabus(syllabus, session_id)
        syllabus.id = syllabus_id
        
        # Update workflow state
        self.current_step = WorkflowStep.SYLLABUS_GENERATION
        
        return document_content
