"""
Subject repository for the CCDI Federation Service.

This module provides data access operations for subjects
using Cypher queries to Memgraph.
"""

from typing import List, Dict, Any, Optional, Tuple
from neo4j import AsyncSession

from app.core.logging import get_logger
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
        
        # Build WHERE conditions and parameters
        where_conditions = []
        params = {"offset": offset, "limit": limit}
        param_counter = 0
        
        # Handle diagnosis search
        if "_diagnosis_search" in filters:
            search_term = filters.pop("_diagnosis_search")
            where_conditions.append("""(
                ANY(diag IN s.associated_diagnoses WHERE toLower(toString(diag)) CONTAINS toLower($diagnosis_search_term))
                OR ANY(key IN keys(s.metadata.unharmonized) 
                       WHERE toLower(key) CONTAINS 'diagnos' 
                       AND toLower(toString(s.metadata.unharmonized[key])) CONTAINS toLower($diagnosis_search_term))
            )""")
            params["diagnosis_search_term"] = search_term
        
        # Add regular filters
        for field, value in filters.items():
            param_counter += 1
            param_name = f"param_{param_counter}"
            
            if isinstance(value, list):
                where_conditions.append(f"s.{field} IN ${param_name}")
            else:
                where_conditions.append(f"s.{field} = ${param_name}")
            params[param_name] = value
        
        # Build final query
        where_clause = ""
        if where_conditions:
            where_clause = "WHERE " + " AND ".join(where_conditions)
        
        cypher = f"""
        MATCH (s:participant)
        {where_clause}
        RETURN s
        SKIP $offset
        LIMIT $limit
        """.strip()
        
        logger.info(
            "Executing get_subjects Cypher query",
            cypher=cypher,
            params=params
        )
        
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
        MATCH (s:participant)
        RETURN s
        LIMIT 1
        """
        
        # Build the full identifier
        identifier = f"{org}.{ns}.{name}"
        params = {"identifier": identifier}
        
        logger.info(
            "Executing get_subject_by_identifier Cypher query",
            cypher=cypher,
            params=params
        )

        # Execute query
        result = await self.session.run(cypher, params)
        records = await result.data()
        
        if not records:
            logger.debug("Subject not found", identifier=identifier)
            return None
        
        # Convert to Subject object
        subject_data = records[0].get("s", {})
        subject = self._record_to_subject(subject_data)
        
        logger.debug("Found subject", identifier=identifier, subject_data=getattr(subject, 'id', str(subject)[:50]))
        
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
        
        # Build WHERE conditions and parameters
        where_conditions = [f"s.{field} IS NOT NULL"]
        params = {}
        param_counter = 0
        
        # Handle diagnosis search
        if "_diagnosis_search" in filters:
            search_term = filters.pop("_diagnosis_search")
            where_conditions.append("""(
                ANY(diag IN s.associated_diagnoses WHERE toLower(toString(diag)) CONTAINS toLower($diagnosis_search_term))
                OR ANY(key IN keys(s.metadata.unharmonized) 
                       WHERE toLower(key) CONTAINS 'diagnos' 
                       AND toLower(toString(s.metadata.unharmonized[key])) CONTAINS toLower($diagnosis_search_term))
            )""")
            params["diagnosis_search_term"] = search_term
        
        # Add regular filters
        for filter_field, value in filters.items():
            param_counter += 1
            param_name = f"param_{param_counter}"
            
            if isinstance(value, list):
                where_conditions.append(f"s.{filter_field} IN ${param_name}")
            else:
                where_conditions.append(f"s.{filter_field} = ${param_name}")
            params[param_name] = value
        
        # Build final query
        where_clause = "WHERE " + " AND ".join(where_conditions)
        
        cypher = f"""
        MATCH (s:participant)
        {where_clause}
        WITH s, 
             CASE 
               WHEN s.{field} IS NULL THEN []
               WHEN NOT apoc.meta.type(s.{field}) = 'LIST' THEN [s.{field}]
               ELSE s.{field}
             END as field_values
        UNWIND field_values as value
        RETURN toString(value) as value, count(*) as count
        ORDER BY count DESC, value ASC
        """.strip()

        logger.info(
            "Executing count_subjects_by_field Cypher query",
            cypher=cypher,
            params=params
        )
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
        
        # Build WHERE conditions and parameters
        where_conditions = []
        params = {}
        param_counter = 0
        
        # Handle diagnosis search
        if "_diagnosis_search" in filters:
            search_term = filters.pop("_diagnosis_search")
            where_conditions.append("""(
                ANY(diag IN s.associated_diagnoses WHERE toLower(toString(diag)) CONTAINS toLower($diagnosis_search_term))
                OR ANY(key IN keys(s.metadata.unharmonized) 
                       WHERE toLower(key) CONTAINS 'diagnos' 
                       AND toLower(toString(s.metadata.unharmonized[key])) CONTAINS toLower($diagnosis_search_term))
            )""")
            params["diagnosis_search_term"] = search_term
        
        # Add regular filters
        for field, value in filters.items():
            param_counter += 1
            param_name = f"param_{param_counter}"
            
            if isinstance(value, list):
                where_conditions.append(f"s.{field} IN ${param_name}")
            else:
                where_conditions.append(f"s.{field} = ${param_name}")
            params[param_name] = value
        
        # Build final query
        where_clause = ""
        if where_conditions:
            where_clause = "WHERE " + " AND ".join(where_conditions)
        
        cypher = f"""
        MATCH (s:participant)
        {where_clause}
        RETURN count(s) as total_count
        """.strip()
        
        logger.info(
            "Executing get_subjects_summary Cypher query",
            cypher=cypher,
            params=params
        )
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
        Convert a database record to a flexible Subject object.
        
        Args:
            record: Database record dictionary
            
        Returns:
            Subject object with flexible structure
        """
        # Create a Subject object with all fields from the record
        # This allows for any field structure to be returned
        return Subject(**record)
