"""Core data entities for the application"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from enum import Enum


class WorkflowStep(Enum):
    """Workflow steps in the syllabus generation process"""
    UPLOAD = "upload"
    SUMMARY = "summary"
    COURSE_TYPE = "course_type"
    TLO_GENERATION = "tlo_generation"
    TLO_SELECTION = "tlo_selection"
    PERFORMANCE_GENERATION = "performance_generation"
    PERFORMANCE_SELECTION = "performance_selection"
    ELO_GENERATION = "elo_generation"
    ELO_SELECTION = "elo_selection"
    SYLLABUS_GENERATION = "syllabus_generation"


@dataclass
class OrganizationProfile:
    """Organization profile entity"""
    original_text: str
    summary: str
    context_overview: str
    file_name: str
    file_type: str
    id: Optional[str] = None
    uploaded_at: Optional[datetime] = None


@dataclass
class TLO:
    """Terminal Learning Objective entity"""
    org_id: str
    course_type: str
    text: str
    id: Optional[str] = None
    generated_at: Optional[datetime] = None
    is_selected: bool = False


@dataclass
class Performance:
    """Performance objective entity"""
    tlo_ids: List[str]
    text: str
    id: Optional[str] = None
    generated_at: Optional[datetime] = None
    is_selected: bool = False


@dataclass
class ELO:
    """Enabling Learning Objective entity"""
    performance_ids: List[str]
    text: str
    id: Optional[str] = None
    generated_at: Optional[datetime] = None
    is_selected: bool = False


@dataclass
class Syllabus:
    """Syllabus document entity"""
    session_id: str
    org_id: str
    course_type: str
    selected_tlo_ids: List[str]
    selected_performance_ids: List[str]
    selected_elo_ids: List[str]
    document_content: bytes
    id: Optional[str] = None
    created_at: Optional[datetime] = None


@dataclass
class SessionData:
    """Session data containing all workflow information"""
    session_id: str
    current_step: str
    organization: Optional[OrganizationProfile] = None
    course_type: Optional[str] = None
    tlos: List[TLO] = field(default_factory=list)
    performances: List[Performance] = field(default_factory=list)
    elos: List[ELO] = field(default_factory=list)
    syllabus: Optional[Syllabus] = None


@dataclass
class SyllabusMaterials:
    """Materials for syllabus generation"""
    organization_summary: str
    organization_context: str
    selected_tlos: List[TLO]
    selected_performances: List[Performance]
    selected_elos: List[ELO]
    course_type: str
