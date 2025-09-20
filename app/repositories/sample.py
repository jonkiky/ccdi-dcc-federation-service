"""
Sample repository for the CCDI Federation Service.

This module provides data access operations for samples
using Cypher queries to Memgraph.
"""

from typing import List, Dict, Any, Optional, Tuple
from neo4j import AsyncSession

from app.core.logging import get_logger
from app.lib.cypher_builder import CypherQueryBuilder, build_diagnosis_search_clauses
from app.lib.field_allowlist import FieldAllowlist
from app.models.dto import Sample
from app.models.errors import UnsupportedFieldError

logger = get_logger(__name__)


class SampleRepository:
    """Repository for sample data operations."""
    
    def __init__(self, session: AsyncSession, allowlist: FieldAllowlist):
        """Initialize repository with database session and field allowlist."""
        self.session = session
        self.allowlist = allowlist
        
    async def get_samples(
        self,
        filters: Dict[str, Any],
        offset: int = 0,
        limit: int = 20
    ) -> List[Sample]:
        """
        Get paginated list of samples with filtering.
        
        Args:
            filters: Dictionary of field filters
            offset: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of Sample objects
            
        Raises:
            UnsupportedFieldError: If filter field is not allowed
        """
        logger.debug(
            "Fetching samples",
            filters=filters,
            offset=offset,
            limit=limit
        )
        
        # Validate filter fields
        self._validate_filters(filters, "sample")
        
        # Build query
        builder = CypherQueryBuilder()
        
        # Handle diagnosis search
        if "_diagnosis_search" in filters:
            search_term = filters.pop("_diagnosis_search")
            diagnosis_clauses = build_diagnosis_search_clauses(search_term, "sample")
            for clause in diagnosis_clauses:
                builder.add_where(clause["where"], clause["params"])
        
        # Add regular filters
        for field, value in filters.items():
            builder.add_filter("s", field, value, self.allowlist, "sample")
        
        # Build final query
        cypher, params = builder.build_samples_query(offset, limit)
        
        logger.debug(
            "Executing get_samples Cypher query",
            cypher=cypher,
            params=params
        )
        
        # Execute query
        result = await self.session.run(cypher, params)
        records = await result.data()
        
        # Convert to Sample objects
        samples = []
        for record in records:
            sample_data = record.get("s", {})
            samples.append(self._record_to_sample(sample_data))
        
        logger.debug(
            "Found samples",
            count=len(samples),
            filters=filters
        )
        
        return samples
    
    async def get_sample_by_identifier(
        self,
        org: str,
        ns: str,
        name: str
    ) -> Optional[Sample]:
        """
        Get a specific sample by organization, namespace, and name.
        
        Args:
            org: Organization identifier
            ns: Namespace identifier
            name: Sample name/identifier
            
        Returns:
            Sample object or None if not found
        """
        logger.debug(
            "Fetching sample by identifier",
            org=org,
            ns=ns,
            name=name
        )
        
        # Build query to find sample by identifier
        cypher = """
        MATCH (s:Sample)
        WHERE s.identifiers CONTAINS $identifier
        RETURN s
        LIMIT 1
        """
        
        # Build the full identifier
        identifier = f"{org}.{ns}.{name}"
        params = {"identifier": identifier}
        
        logger.debug(
            "Executing get_sample_by_identifier Cypher query",
            cypher=cypher,
            params=params
        )
        
        # Execute query
        result = await self.session.run(cypher, params)
        records = await result.data()
        
        if not records:
            logger.debug("Sample not found", identifier=identifier)
            return None
        
        # Convert to Sample object
        sample_data = records[0].get("s", {})
        sample = self._record_to_sample(sample_data)
        
        logger.debug("Found sample", identifier=identifier, id=sample.id)
        
        return sample
    
    async def count_samples_by_field(
        self,
        field: str,
        filters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Count samples grouped by a specific field value.
        
        Args:
            field: Field to group by and count
            filters: Additional filters to apply
            
        Returns:
            List of dictionaries with value and count
            
        Raises:
            UnsupportedFieldError: If field is not allowed
        """
        logger.debug(
            "Counting samples by field",
            field=field,
            filters=filters
        )
        
        # Validate field
        if not self.allowlist.is_field_allowed("sample", field):
            raise UnsupportedFieldError(f"Field '{field}' is not supported for counting")
        
        # Validate filter fields
        self._validate_filters(filters, "sample")
        
        # Build query
        builder = CypherQueryBuilder()
        
        # Handle diagnosis search
        if "_diagnosis_search" in filters:
            search_term = filters.pop("_diagnosis_search")
            diagnosis_clauses = build_diagnosis_search_clauses(search_term, "sample")
            for clause in diagnosis_clauses:
                builder.add_where(clause["where"], clause["params"])
        
        # Add regular filters
        for filter_field, value in filters.items():
            builder.add_filter("s", filter_field, value, self.allowlist, "sample")
        
        # Build count query
        cypher, params = builder.build_count_by_field_query("sample", field)
        
        logger.debug(
            "Executing count_samples_by_field Cypher query",
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
            "Completed sample count by field",
            field=field,
            results_count=len(counts)
        )
        
        return counts
    
    async def get_samples_summary(
        self,
        filters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get summary statistics for samples.
        
        Args:
            filters: Filters to apply
            
        Returns:
            Dictionary with summary statistics
        """
        logger.debug("Getting samples summary", filters=filters)
        
        # Validate filter fields
        self._validate_filters(filters, "sample")
        
        # Build query
        builder = CypherQueryBuilder()
        
        # Handle diagnosis search
        if "_diagnosis_search" in filters:
            search_term = filters.pop("_diagnosis_search")
            diagnosis_clauses = build_diagnosis_search_clauses(search_term, "sample")
            for clause in diagnosis_clauses:
                builder.add_where(clause["where"], clause["params"])
        
        # Add regular filters
        for field, value in filters.items():
            builder.add_filter("s", field, value, self.allowlist, "sample")
        
        # Build summary query
        cypher, params = builder.build_summary_query("sample")
        
        logger.debug(
            "Executing get_samples_summary Cypher query",
            cypher=cypher,
            params=params
        )
        
        # Execute query
        result = await self.session.run(cypher, params)
        records = await result.data()
        
        if not records:
            return {"total_count": 0}
        
        summary = records[0]
        logger.debug("Completed samples summary", total_count=summary.get("total_count", 0))
        
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
    
    def _record_to_sample(self, record: Dict[str, Any]) -> Sample:
        """
        Convert a database record to a Sample object.
        
        Args:
            record: Database record dictionary
            
        Returns:
            Sample object
        """
        # Extract identifiers
        identifiers = record.get("identifiers", [])
        if isinstance(identifiers, str):
            identifiers = [identifiers]
        
        # Extract anatomical sites (can be a list)
        anatomical_sites = record.get("anatomical_sites", [])
        if isinstance(anatomical_sites, str):
            anatomical_sites = [anatomical_sites]
        
        # Build sample
        return Sample(
            id=record.get("id"),
            identifiers=identifiers,
            disease_phase=record.get("disease_phase"),
            anatomical_sites=anatomical_sites,
            library_selection_method=record.get("library_selection_method"),
            library_strategy=record.get("library_strategy"),
            library_source_material=record.get("library_source_material"),
            preservation_method=record.get("preservation_method"),
            tumor_grade=record.get("tumor_grade"),
            specimen_molecular_analyte_type=record.get("specimen_molecular_analyte_type"),
            tissue_type=record.get("tissue_type"),
            tumor_classification=record.get("tumor_classification"),
            age_at_diagnosis=record.get("age_at_diagnosis"),
            age_at_collection=record.get("age_at_collection"),
            tumor_tissue_morphology=record.get("tumor_tissue_morphology"),
            depositions=record.get("depositions", []),
            diagnosis=record.get("diagnosis"),
            metadata=record.get("metadata", {})
        )
