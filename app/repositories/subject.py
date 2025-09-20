"""
Subject repository for the CCDI Federation Service.

This module provides data access operations for subjects
using Cypher queries to Memgraph.
"""

from typing import List, Dict, Any, Optional, Tuple
from neo4j import AsyncSession

from app.core.logging import get_logger
from app.lib.cypher_builder import CypherQueryBuilder, build_diagnosis_search_clauses
from app.lib.field_allowlist import FieldAllowlist
from app.models.dto import Subject
from app.models.errors import UnsupportedFieldError

logger = get_logger(__name__)


class SubjectRepository:
    """Repository for subject data operations."""
    
    def __init__(self, session: AsyncSession, allowlist: FieldAllowlist):
        """Initialize repository with database session and field allowlist."""
        self.session = session
        self.allowlist = allowlist
        
    async def get_subjects(
        self,
        filters: Dict[str, Any],
        offset: int = 0,
        limit: int = 20
    ) -> List[Subject]:
        """
        Get paginated list of subjects with filtering.
        
        Args:
            filters: Dictionary of field filters
            offset: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of Subject objects
            
        Raises:
            UnsupportedFieldError: If filter field is not allowed
        """
        logger.debug(
            "Fetching subjects",
            filters=filters,
            offset=offset,
            limit=limit
        )
        
        # Validate filter fields
        self._validate_filters(filters, "subject")
        
        # Build query
        builder = CypherQueryBuilder()
        
        # Handle diagnosis search
        if "_diagnosis_search" in filters:
            search_term = filters.pop("_diagnosis_search")
            diagnosis_clauses = build_diagnosis_search_clauses(search_term, "subject")
            for clause in diagnosis_clauses:
                builder.add_where(clause["where"], clause["params"])
        
        # Add regular filters
        for field, value in filters.items():
            builder.add_filter("s", field, value, self.allowlist, "subject")
        
        # Build final query
        cypher, params = builder.build_subjects_query(offset, limit)
        
        # Execute query
        result = await self.session.run(cypher, params)
        records = await result.data()
        
        # Convert to Subject objects
        subjects = []
        for record in records:
            subject_data = record.get("s", {})
            subjects.append(self._record_to_subject(subject_data))
        
        logger.debug(
            "Found subjects",
            count=len(subjects),
            filters=filters
        )
        
        return subjects
    
    async def get_subject_by_identifier(
        self,
        org: str,
        ns: str,
        name: str
    ) -> Optional[Subject]:
        """
        Get a specific subject by organization, namespace, and name.
        
        Args:
            org: Organization identifier
            ns: Namespace identifier
            name: Subject name/identifier
            
        Returns:
            Subject object or None if not found
        """
        logger.debug(
            "Fetching subject by identifier",
            org=org,
            ns=ns,
            name=name
        )
        
        # Build query to find subject by identifier
        cypher = """
        MATCH (s:Subject)
        WHERE s.identifiers CONTAINS $identifier
        RETURN s
        LIMIT 1
        """
        
        # Build the full identifier
        identifier = f"{org}.{ns}.{name}"
        params = {"identifier": identifier}
        
        # Execute query
        result = await self.session.run(cypher, params)
        records = await result.data()
        
        if not records:
            logger.debug("Subject not found", identifier=identifier)
            return None
        
        # Convert to Subject object
        subject_data = records[0].get("s", {})
        subject = self._record_to_subject(subject_data)
        
        logger.debug("Found subject", identifier=identifier, id=subject.id)
        
        return subject
    
    async def count_subjects_by_field(
        self,
        field: str,
        filters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Count subjects grouped by a specific field value.
        
        Args:
            field: Field to group by and count
            filters: Additional filters to apply
            
        Returns:
            List of dictionaries with value and count
            
        Raises:
            UnsupportedFieldError: If field is not allowed
        """
        logger.debug(
            "Counting subjects by field",
            field=field,
            filters=filters
        )
        
        # Validate field
        if not self.allowlist.is_field_allowed("subject", field):
            raise UnsupportedFieldError(f"Field '{field}' is not supported for counting")
        
        # Validate filter fields
        self._validate_filters(filters, "subject")
        
        # Build query
        builder = CypherQueryBuilder()
        
        # Handle diagnosis search
        if "_diagnosis_search" in filters:
            search_term = filters.pop("_diagnosis_search")
            diagnosis_clauses = build_diagnosis_search_clauses(search_term, "subject")
            for clause in diagnosis_clauses:
                builder.add_where(clause["where"], clause["params"])
        
        # Add regular filters
        for filter_field, value in filters.items():
            builder.add_filter("s", filter_field, value, self.allowlist, "subject")
        
        # Build count query
        cypher, params = builder.build_count_by_field_query("subject", field)
        
        # Execute query
        result = await self.session.run(cypher, params)
        records = await result.data()
        
        # Format results
        counts = []
        for record in records:
            counts.append({
                "value": record.get("value"),
                "count": record.get("count", 0)
            })
        
        logger.debug(
            "Completed subject count by field",
            field=field,
            results_count=len(counts)
        )
        
        return counts
    
    async def get_subjects_summary(
        self,
        filters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get summary statistics for subjects.
        
        Args:
            filters: Filters to apply
            
        Returns:
            Dictionary with summary statistics
        """
        logger.debug("Getting subjects summary", filters=filters)
        
        # Validate filter fields
        self._validate_filters(filters, "subject")
        
        # Build query
        builder = CypherQueryBuilder()
        
        # Handle diagnosis search
        if "_diagnosis_search" in filters:
            search_term = filters.pop("_diagnosis_search")
            diagnosis_clauses = build_diagnosis_search_clauses(search_term, "subject")
            for clause in diagnosis_clauses:
                builder.add_where(clause["where"], clause["params"])
        
        # Add regular filters
        for field, value in filters.items():
            builder.add_filter("s", field, value, self.allowlist, "subject")
        
        # Build summary query
        cypher, params = builder.build_summary_query("subject")
        
        # Execute query
        result = await self.session.run(cypher, params)
        records = await result.data()
        
        if not records:
            return {"total_count": 0}
        
        summary = records[0]
        logger.debug("Completed subjects summary", total_count=summary.get("total_count", 0))
        
        return summary
    
    def _validate_filters(self, filters: Dict[str, Any], entity_type: str) -> None:
        """
        Validate that all filter fields are allowed.
        
        Args:
            filters: Dictionary of filters to validate
            entity_type: Type of entity for allowlist checking
            
        Raises:
            UnsupportedFieldError: If any field is not allowed
        """
        for field in filters.keys():
            # Skip special fields
            if field.startswith("_"):
                continue
                
            if not self.allowlist.is_field_allowed(entity_type, field):
                raise UnsupportedFieldError(f"Field '{field}' is not supported for {entity_type} filtering")
    
    def _record_to_subject(self, record: Dict[str, Any]) -> Subject:
        """
        Convert a database record to a Subject object.
        
        Args:
            record: Database record dictionary
            
        Returns:
            Subject object
        """
        # Extract identifiers
        identifiers = record.get("identifiers", [])
        if isinstance(identifiers, str):
            identifiers = [identifiers]
        
        # Build subject
        return Subject(
            id=record.get("id"),
            identifiers=identifiers,
            sex=record.get("sex"),
            race=record.get("race"),
            ethnicity=record.get("ethnicity"),
            vital_status=record.get("vital_status"),
            age_at_vital_status=record.get("age_at_vital_status"),
            depositions=record.get("depositions", []),
            metadata=record.get("metadata", {})
        )
