"""Database service for managing all data access operations"""

import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import pool
from typing import List, Optional, Dict, Any
from contextlib import contextmanager
from datetime import datetime
import uuid

from src.models.entities import (
    OrganizationProfile,
    TLO,
    Performance,
    ELO,
    Syllabus,
    SessionData
)


class DatabaseError(Exception):
    """Base exception for database errors"""
    pass


class ConnectionError(DatabaseError):
    """Raised when database connection fails"""
    pass


class IntegrityError(DatabaseError):
    """Raised when data integrity constraints are violated"""
    pass


class QueryError(DatabaseError):
    """Raised when a database query fails"""
    pass


class DatabaseService:
    """Service for managing database operations"""

    def __init__(self, connection_string: str, min_connections: int = 1, max_connections: int = 10):
        """
        Initialize database service with connection pooling
        
        Args:
            connection_string: PostgreSQL connection string
            min_connections: Minimum number of connections in pool
            max_connections: Maximum number of connections in pool
        """
        try:
            self.connection_pool = psycopg2.pool.SimpleConnectionPool(
                min_connections,
                max_connections,
                connection_string
            )
            if self.connection_pool is None:
                raise ConnectionError("Gagal membuat connection pool database")
        except psycopg2.Error as e:
            raise ConnectionError(f"Gagal terhubung ke database: {str(e)}")

    @contextmanager
    def get_connection(self):
        """
        Context manager for getting database connections from pool
        
        Yields:
            Database connection with automatic commit/rollback
        """
        conn = None
        try:
            conn = self.connection_pool.getconn()
            if conn is None:
                raise ConnectionError("Gagal mendapatkan koneksi dari pool")
            yield conn
            conn.commit()
        except psycopg2.IntegrityError as e:
            if conn:
                conn.rollback()
            raise IntegrityError(f"Pelanggaran integritas data: {str(e)}")
        except psycopg2.OperationalError as e:
            if conn:
                conn.rollback()
            raise ConnectionError(f"Kesalahan koneksi database: {str(e)}")
        except psycopg2.Error as e:
            if conn:
                conn.rollback()
            raise QueryError(f"Operasi database gagal: {str(e)}")
        finally:
            if conn:
                self.connection_pool.putconn(conn)

    def close(self):
        """Close all connections in the pool"""
        if self.connection_pool:
            self.connection_pool.closeall()

    # Organization Profile Operations

    def save_organization_profile(self, profile: OrganizationProfile) -> str:
        """
        Save organization profile to database
        
        Args:
            profile: OrganizationProfile entity
            
        Returns:
            UUID of saved profile
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                profile_id = str(uuid.uuid4())
                cur.execute(
                    """
                    INSERT INTO organization_profiles 
                    (id, original_text, summary, context_overview, file_name, file_type, uploaded_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (
                        profile_id,
                        profile.original_text,
                        profile.summary,
                        profile.context_overview,
                        profile.file_name,
                        profile.file_type,
                        datetime.now()
                    )
                )
                result = cur.fetchone()
                return str(result[0])

    def get_organization_profile(self, profile_id: str) -> Optional[OrganizationProfile]:
        """
        Retrieve organization profile by ID
        
        Args:
            profile_id: UUID of profile
            
        Returns:
            OrganizationProfile entity or None if not found
        """
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT id, original_text, summary, context_overview, 
                           file_name, file_type, uploaded_at
                    FROM organization_profiles
                    WHERE id = %s
                    """,
                    (profile_id,)
                )
                row = cur.fetchone()
                if row:
                    return OrganizationProfile(
                        id=str(row['id']),
                        original_text=row['original_text'],
                        summary=row['summary'],
                        context_overview=row['context_overview'],
                        file_name=row['file_name'],
                        file_type=row['file_type'],
                        uploaded_at=row['uploaded_at']
                    )
                return None

    # TLO Operations

    def save_tlos(self, tlos: List[TLO], org_id: str, course_type: str) -> List[str]:
        """
        Save multiple TLOs to database
        
        Args:
            tlos: List of TLO entities
            org_id: Organization profile ID
            course_type: Course type
            
        Returns:
            List of TLO UUIDs
        """
        tlo_ids = []
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                for tlo in tlos:
                    tlo_id = str(uuid.uuid4())
                    cur.execute(
                        """
                        INSERT INTO tlos 
                        (id, org_id, course_type, text, generated_at, is_selected)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        RETURNING id
                        """,
                        (
                            tlo_id,
                            org_id,
                            course_type,
                            tlo.text,
                            datetime.now(),
                            tlo.is_selected
                        )
                    )
                    result = cur.fetchone()
                    tlo_ids.append(str(result[0]))
        return tlo_ids

    def get_tlos_by_org(self, org_id: str, course_type: Optional[str] = None) -> List[TLO]:
        """
        Retrieve TLOs for an organization
        
        Args:
            org_id: Organization profile ID
            course_type: Optional course type filter
            
        Returns:
            List of TLO entities
        """
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                if course_type:
                    cur.execute(
                        """
                        SELECT id, org_id, course_type, text, generated_at, is_selected
                        FROM tlos
                        WHERE org_id = %s AND course_type = %s
                        ORDER BY generated_at DESC
                        """,
                        (org_id, course_type)
                    )
                else:
                    cur.execute(
                        """
                        SELECT id, org_id, course_type, text, generated_at, is_selected
                        FROM tlos
                        WHERE org_id = %s
                        ORDER BY generated_at DESC
                        """,
                        (org_id,)
                    )
                rows = cur.fetchall()
                return [
                    TLO(
                        id=str(row['id']),
                        org_id=str(row['org_id']),
                        course_type=row['course_type'],
                        text=row['text'],
                        generated_at=row['generated_at'],
                        is_selected=row['is_selected']
                    )
                    for row in rows
                ]

    def update_tlo_selection(self, tlo_id: str, is_selected: bool) -> None:
        """
        Update TLO selection status
        
        Args:
            tlo_id: TLO UUID
            is_selected: Selection status
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE tlos
                    SET is_selected = %s
                    WHERE id = %s
                    """,
                    (is_selected, tlo_id)
                )

    def get_selected_tlos(self, org_id: str) -> List[TLO]:
        """
        Retrieve selected TLOs for an organization
        
        Args:
            org_id: Organization profile ID
            
        Returns:
            List of selected TLO entities
        """
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT id, org_id, course_type, text, generated_at, is_selected
                    FROM tlos
                    WHERE org_id = %s AND is_selected = TRUE
                    ORDER BY generated_at DESC
                    """,
                    (org_id,)
                )
                rows = cur.fetchall()
                return [
                    TLO(
                        id=str(row['id']),
                        org_id=str(row['org_id']),
                        course_type=row['course_type'],
                        text=row['text'],
                        generated_at=row['generated_at'],
                        is_selected=row['is_selected']
                    )
                    for row in rows
                ]
    
    def update_tlo_selections(self, tlo_ids: List[str], is_selected: bool) -> None:
        """
        Update selection status for multiple TLOs
        
        Args:
            tlo_ids: List of TLO UUIDs
            is_selected: Selection status to set
        """
        if not tlo_ids:
            return
        
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE tlos
                    SET is_selected = %s
                    WHERE id = ANY(%s::uuid[])
                    """,
                    (is_selected, tlo_ids)
                )

    # Performance Operations

    def save_performances(self, performances: List[Performance], tlo_ids: List[str]) -> List[str]:
        """
        Save multiple performances to database with TLO mappings
        
        Args:
            performances: List of Performance entities
            tlo_ids: List of TLO UUIDs to associate with performances
            
        Returns:
            List of Performance UUIDs
        """
        performance_ids = []
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                for performance in performances:
                    performance_id = str(uuid.uuid4())
                    cur.execute(
                        """
                        INSERT INTO performances 
                        (id, text, generated_at, is_selected)
                        VALUES (%s, %s, %s, %s)
                        RETURNING id
                        """,
                        (
                            performance_id,
                            performance.text,
                            datetime.now(),
                            performance.is_selected
                        )
                    )
                    result = cur.fetchone()
                    perf_id = str(result[0])
                    performance_ids.append(perf_id)
                    
                    # Create mappings to TLOs
                    for tlo_id in tlo_ids:
                        cur.execute(
                            """
                            INSERT INTO performance_tlo_mapping (performance_id, tlo_id)
                            VALUES (%s, %s)
                            """,
                            (perf_id, tlo_id)
                        )
        return performance_ids

    def get_performances_by_tlos(self, tlo_ids: List[str]) -> List[Performance]:
        """
        Retrieve performances associated with TLOs
        
        Args:
            tlo_ids: List of TLO UUIDs
            
        Returns:
            List of Performance entities
        """
        if not tlo_ids:
            return []
            
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT DISTINCT p.id, p.text, p.generated_at, p.is_selected
                    FROM performances p
                    JOIN performance_tlo_mapping ptm ON p.id = ptm.performance_id
                    WHERE ptm.tlo_id = ANY(%s::uuid[])
                    ORDER BY p.generated_at DESC
                    """,
                    (tlo_ids,)
                )
                rows = cur.fetchall()
                performances = []
                for row in rows:
                    # Get associated TLO IDs
                    cur.execute(
                        """
                        SELECT tlo_id FROM performance_tlo_mapping
                        WHERE performance_id = %s
                        """,
                        (str(row['id']),)
                    )
                    tlo_rows = cur.fetchall()
                    tlo_id_list = [str(t['tlo_id']) for t in tlo_rows]
                    
                    performances.append(
                        Performance(
                            id=str(row['id']),
                            tlo_ids=tlo_id_list,
                            text=row['text'],
                            generated_at=row['generated_at'],
                            is_selected=row['is_selected']
                        )
                    )
                return performances

    def get_performances_by_ids(self, performance_ids: List[str]) -> List[Performance]:
        """
        Retrieve performances by their IDs
        
        Args:
            performance_ids: List of Performance UUIDs
            
        Returns:
            List of Performance entities
        """
        if not performance_ids:
            return []
            
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT id, text, generated_at, is_selected
                    FROM performances
                    WHERE id = ANY(%s::uuid[])
                    ORDER BY generated_at DESC
                    """,
                    (performance_ids,)
                )
                rows = cur.fetchall()
                performances = []
                for row in rows:
                    # Get associated TLO IDs
                    cur.execute(
                        """
                        SELECT tlo_id FROM performance_tlo_mapping
                        WHERE performance_id = %s
                        """,
                        (str(row['id']),)
                    )
                    tlo_rows = cur.fetchall()
                    tlo_id_list = [str(t['tlo_id']) for t in tlo_rows]
                    
                    performances.append(
                        Performance(
                            id=str(row['id']),
                            tlo_ids=tlo_id_list,
                            text=row['text'],
                            generated_at=row['generated_at'],
                            is_selected=row['is_selected']
                        )
                    )
                return performances

    def update_performance_selection(self, performance_id: str, is_selected: bool) -> None:
        """
        Update performance selection status
        
        Args:
            performance_id: Performance UUID
            is_selected: Selection status
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE performances
                    SET is_selected = %s
                    WHERE id = %s
                    """,
                    (is_selected, performance_id)
                )

    def get_selected_performances(self, tlo_ids: List[str]) -> List[Performance]:
        """
        Retrieve selected performances for TLOs
        
        Args:
            tlo_ids: List of TLO UUIDs
            
        Returns:
            List of selected Performance entities
        """
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT DISTINCT p.id, p.text, p.generated_at, p.is_selected
                    FROM performances p
                    JOIN performance_tlo_mapping ptm ON p.id = ptm.performance_id
                    WHERE ptm.tlo_id = ANY(%s::uuid[]) AND p.is_selected = TRUE
                    ORDER BY p.generated_at DESC
                    """,
                    (tlo_ids,)
                )
                rows = cur.fetchall()
                performances = []
                for row in rows:
                    # Get associated TLO IDs
                    cur.execute(
                        """
                        SELECT tlo_id FROM performance_tlo_mapping
                        WHERE performance_id = %s
                        """,
                        (str(row['id']),)
                    )
                    tlo_rows = cur.fetchall()
                    tlo_id_list = [str(t['tlo_id']) for t in tlo_rows]
                    
                    performances.append(
                        Performance(
                            id=str(row['id']),
                            tlo_ids=tlo_id_list,
                            text=row['text'],
                            generated_at=row['generated_at'],
                            is_selected=row['is_selected']
                        )
                    )
                return performances
    
    def update_performance_selections(self, performance_ids: List[str], is_selected: bool) -> None:
        """
        Update selection status for multiple performances
        
        Args:
            performance_ids: List of Performance UUIDs
            is_selected: Selection status to set
        """
        if not performance_ids:
            return
        
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE performances
                    SET is_selected = %s
                    WHERE id = ANY(%s::uuid[])
                    """,
                    (is_selected, performance_ids)
                )

    # ELO Operations

    def save_elos(self, elos: List[ELO], performance_ids: List[str]) -> List[str]:
        """
        Save multiple ELOs to database with performance mappings
        
        Args:
            elos: List of ELO entities
            performance_ids: List of Performance UUIDs to associate with ELOs
            
        Returns:
            List of ELO UUIDs
        """
        elo_ids = []
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                for elo in elos:
                    elo_id = str(uuid.uuid4())
                    cur.execute(
                        """
                        INSERT INTO elos 
                        (id, text, generated_at, is_selected)
                        VALUES (%s, %s, %s, %s)
                        RETURNING id
                        """,
                        (
                            elo_id,
                            elo.text,
                            datetime.now(),
                            elo.is_selected
                        )
                    )
                    result = cur.fetchone()
                    e_id = str(result[0])
                    elo_ids.append(e_id)
                    
                    # Create mappings to performances
                    for perf_id in performance_ids:
                        cur.execute(
                            """
                            INSERT INTO elo_performance_mapping (elo_id, performance_id)
                            VALUES (%s, %s)
                            """,
                            (e_id, perf_id)
                        )
        return elo_ids

    def get_elos_by_performances(self, performance_ids: List[str]) -> List[ELO]:
        """
        Retrieve ELOs associated with performances
        
        Args:
            performance_ids: List of Performance UUIDs
            
        Returns:
            List of ELO entities
        """
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT DISTINCT e.id, e.text, e.generated_at, e.is_selected
                    FROM elos e
                    JOIN elo_performance_mapping epm ON e.id = epm.elo_id
                    WHERE epm.performance_id = ANY(%s::uuid[])
                    ORDER BY e.generated_at DESC
                    """,
                    (performance_ids,)
                )
                rows = cur.fetchall()
                elos = []
                for row in rows:
                    # Get associated performance IDs
                    cur.execute(
                        """
                        SELECT performance_id FROM elo_performance_mapping
                        WHERE elo_id = %s
                        """,
                        (str(row['id']),)
                    )
                    perf_rows = cur.fetchall()
                    perf_id_list = [str(p['performance_id']) for p in perf_rows]
                    
                    elos.append(
                        ELO(
                            id=str(row['id']),
                            performance_ids=perf_id_list,
                            text=row['text'],
                            generated_at=row['generated_at'],
                            is_selected=row['is_selected']
                        )
                    )
                return elos

    def update_elo_selection(self, elo_id: str, is_selected: bool) -> None:
        """
        Update ELO selection status
        
        Args:
            elo_id: ELO UUID
            is_selected: Selection status
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE elos
                    SET is_selected = %s
                    WHERE id = %s
                    """,
                    (is_selected, elo_id)
                )

    def get_selected_elos(self, performance_ids: List[str]) -> List[ELO]:
        """
        Retrieve selected ELOs for performances
        
        Args:
            performance_ids: List of Performance UUIDs
            
        Returns:
            List of selected ELO entities
        """
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT DISTINCT e.id, e.text, e.generated_at, e.is_selected
                    FROM elos e
                    JOIN elo_performance_mapping epm ON e.id = epm.elo_id
                    WHERE epm.performance_id = ANY(%s::uuid[]) AND e.is_selected = TRUE
                    ORDER BY e.generated_at DESC
                    """,
                    (performance_ids,)
                )
                rows = cur.fetchall()
                elos = []
                for row in rows:
                    # Get associated performance IDs
                    cur.execute(
                        """
                        SELECT performance_id FROM elo_performance_mapping
                        WHERE elo_id = %s
                        """,
                        (str(row['id']),)
                    )
                    perf_rows = cur.fetchall()
                    perf_id_list = [str(p['performance_id']) for p in perf_rows]
                    
                    elos.append(
                        ELO(
                            id=str(row['id']),
                            performance_ids=perf_id_list,
                            text=row['text'],
                            generated_at=row['generated_at'],
                            is_selected=row['is_selected']
                        )
                    )
                return elos
    
    def update_elo_selections(self, elo_ids: List[str], is_selected: bool) -> None:
        """
        Update selection status for multiple ELOs
        
        Args:
            elo_ids: List of ELO UUIDs
            is_selected: Selection status to set
        """
        if not elo_ids:
            return
        
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE elos
                    SET is_selected = %s
                    WHERE id = ANY(%s::uuid[])
                    """,
                    (is_selected, elo_ids)
                )

    # Syllabus Operations

    def save_syllabus(
        self,
        syllabus: Syllabus,
        session_id: str
    ) -> str:
        """
        Save syllabus document to database with all mappings
        
        Args:
            syllabus: Syllabus entity
            session_id: Session identifier
            
        Returns:
            Syllabus UUID
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                syllabus_id = str(uuid.uuid4())
                cur.execute(
                    """
                    INSERT INTO syllabi 
                    (id, session_id, org_id, course_type, document_content, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (
                        syllabus_id,
                        session_id,
                        syllabus.org_id,
                        syllabus.course_type,
                        syllabus.document_content,
                        datetime.now()
                    )
                )
                result = cur.fetchone()
                syl_id = str(result[0])
                
                # Create TLO mappings
                for tlo_id in syllabus.selected_tlo_ids:
                    cur.execute(
                        """
                        INSERT INTO syllabus_tlo_mapping (syllabus_id, tlo_id)
                        VALUES (%s, %s)
                        """,
                        (syl_id, tlo_id)
                    )
                
                # Create performance mappings
                for perf_id in syllabus.selected_performance_ids:
                    cur.execute(
                        """
                        INSERT INTO syllabus_performance_mapping (syllabus_id, performance_id)
                        VALUES (%s, %s)
                        """,
                        (syl_id, perf_id)
                    )
                
                # Create ELO mappings
                for elo_id in syllabus.selected_elo_ids:
                    cur.execute(
                        """
                        INSERT INTO syllabus_elo_mapping (syllabus_id, elo_id)
                        VALUES (%s, %s)
                        """,
                        (syl_id, elo_id)
                    )
                
                return syl_id

    def get_syllabus_by_session(self, session_id: str) -> Optional[Syllabus]:
        """
        Retrieve syllabus by session ID
        
        Args:
            session_id: Session identifier
            
        Returns:
            Syllabus entity or None if not found
        """
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT id, session_id, org_id, course_type, document_content, created_at
                    FROM syllabi
                    WHERE session_id = %s
                    ORDER BY created_at DESC
                    LIMIT 1
                    """,
                    (session_id,)
                )
                row = cur.fetchone()
                if not row:
                    return None
                
                syllabus_id = str(row['id'])
                
                # Get TLO mappings
                cur.execute(
                    """
                    SELECT tlo_id FROM syllabus_tlo_mapping
                    WHERE syllabus_id = %s
                    """,
                    (syllabus_id,)
                )
                tlo_ids = [str(r['tlo_id']) for r in cur.fetchall()]
                
                # Get performance mappings
                cur.execute(
                    """
                    SELECT performance_id FROM syllabus_performance_mapping
                    WHERE syllabus_id = %s
                    """,
                    (syllabus_id,)
                )
                perf_ids = [str(r['performance_id']) for r in cur.fetchall()]
                
                # Get ELO mappings
                cur.execute(
                    """
                    SELECT elo_id FROM syllabus_elo_mapping
                    WHERE syllabus_id = %s
                    """,
                    (syllabus_id,)
                )
                elo_ids = [str(r['elo_id']) for r in cur.fetchall()]
                
                return Syllabus(
                    id=syllabus_id,
                    session_id=row['session_id'],
                    org_id=str(row['org_id']),
                    course_type=row['course_type'],
                    selected_tlo_ids=tlo_ids,
                    selected_performance_ids=perf_ids,
                    selected_elo_ids=elo_ids,
                    document_content=bytes(row['document_content']),
                    created_at=row['created_at']
                )

    # Session Data Operations

    def get_session_data(self, session_id: str, org_id: str) -> SessionData:
        """
        Retrieve all data for a user session
        
        Args:
            session_id: Session identifier
            org_id: Organization profile ID
            
        Returns:
            SessionData entity with all workflow information
        """
        # Get organization profile
        organization = self.get_organization_profile(org_id)
        
        # Get TLOs
        tlos = self.get_tlos_by_org(org_id)
        
        # Get course type from TLOs if available
        course_type = tlos[0].course_type if tlos else None
        
        # Get performances
        selected_tlo_ids = [tlo.id for tlo in tlos if tlo.is_selected and tlo.id]
        performances = self.get_performances_by_tlos(selected_tlo_ids) if selected_tlo_ids else []
        
        # Get ELOs
        selected_perf_ids = [p.id for p in performances if p.is_selected and p.id]
        elos = self.get_elos_by_performances(selected_perf_ids) if selected_perf_ids else []
        
        # Get syllabus
        syllabus = self.get_syllabus_by_session(session_id)
        
        # Determine current step based on data
        current_step = self._determine_current_step(
            organization, course_type, tlos, performances, elos, syllabus
        )
        
        return SessionData(
            session_id=session_id,
            organization=organization,
            course_type=course_type,
            tlos=tlos,
            performances=performances,
            elos=elos,
            syllabus=syllabus,
            current_step=current_step
        )

    def _determine_current_step(
        self,
        organization: Optional[OrganizationProfile],
        course_type: Optional[str],
        tlos: List[TLO],
        performances: List[Performance],
        elos: List[ELO],
        syllabus: Optional[Syllabus]
    ) -> str:
        """Determine current workflow step based on available data"""
        if syllabus:
            return "syllabus_generation"
        if elos:
            return "elo_selection"
        if performances:
            return "performance_selection"
        if tlos:
            return "tlo_selection"
        if course_type:
            return "course_type"
        if organization:
            return "summary"
        return "upload"
