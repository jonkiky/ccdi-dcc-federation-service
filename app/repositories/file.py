"""
File repository for the CCDI Federation Service.

This module provides data access operations for files
using Cypher queries to Memgraph.
"""

from typing import List, Dict, Any, Optional, Tuple
from neo4j import AsyncSession

from app.core.logging import get_logger
from app.lib.cypher_builder import CypherQueryBuilder
from app.lib.field_allowlist import FieldAllowlist
from app.models.dto import File
from app.models.errors import UnsupportedFieldError

logger = get_logger(__name__)


class FileRepository:
    """Repository for file data operations."""
    
    def __init__(self, session: AsyncSession, allowlist: FieldAllowlist):
        """Initialize repository with database session and field allowlist."""
        self.session = session
        self.allowlist = allowlist
        
    async def get_files(
        self,
        filters: Dict[str, Any],
        offset: int = 0,
        limit: int = 20
    ) -> List[File]:
        """
        Get paginated list of files with filtering.
        
        Args:
            filters: Dictionary of field filters
            offset: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of File objects
            
        Raises:
            UnsupportedFieldError: If filter field is not allowed
        """
        logger.debug(
            "Fetching files",
            filters=filters,
            offset=offset,
            limit=limit
        )
        
        # Validate filter fields
        self._validate_filters(filters, "file")
        
        # Build query
        builder = CypherQueryBuilder()
        
        # Add regular filters
        for field, value in filters.items():
            builder.add_filter("f", field, value, self.allowlist, "file")
        
        # Build final query
        cypher, params = builder.build_files_query(offset, limit)
        
        logger.info(
            "Executing get_files Cypher query",
            cypher=cypher,
            params=params
        )
        
        # Execute query
        result = await self.session.run(cypher, params)
        records = await result.data()
        
        # Convert to File objects
        files = []
        for record in records:
            file_data = record.get("f", {})
            files.append(self._record_to_file(file_data))
        
        logger.debug(
            "Found files",
            count=len(files),
            filters=filters
        )
        
        return files
    
    async def get_file_by_identifier(
        self,
        org: str,
        ns: str,
        name: str
    ) -> Optional[File]:
        """
        Get a specific file by organization, namespace, and name.
        
        Args:
            org: Organization identifier
            ns: Namespace identifier
            name: File name/identifier
            
        Returns:
            File object or None if not found
        """
        logger.debug(
            "Fetching file by identifier",
            org=org,
            ns=ns,
            name=name
        )
        
        # Build query to find file by identifier
        cypher = """
        MATCH (f:File)
        WHERE f.identifiers CONTAINS $identifier
        RETURN f
        LIMIT 1
        """
        
        # Build the full identifier
        identifier = f"{org}.{ns}.{name}"
        params = {"identifier": identifier}
        
        logger.info(
            "Executing get_file_by_identifier Cypher query",
            cypher=cypher,
            params=params
        )
        
        # Execute query
        result = await self.session.run(cypher, params)
        records = await result.data()
        
        if not records:
            logger.debug("File not found", identifier=identifier)
            return None
        
        # Convert to File object
        file_data = records[0].get("f", {})
        file = self._record_to_file(file_data)
        
        logger.debug("Found file", identifier=identifier, id=file.id)
        
        return file
    
    async def count_files_by_field(
        self,
        field: str,
        filters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Count files grouped by a specific field value.
        
        Args:
            field: Field to group by and count
            filters: Additional filters to apply
            
        Returns:
            List of dictionaries with value and count
            
        Raises:
            UnsupportedFieldError: If field is not allowed
        """
        logger.debug(
            "Counting files by field",
            field=field,
            filters=filters
        )
        
        # Validate field
        if not self.allowlist.is_field_allowed("file", field):
            raise UnsupportedFieldError(f"Field '{field}' is not supported for counting")
        
        # Validate filter fields
        self._validate_filters(filters, "file")
        
        # Build query
        builder = CypherQueryBuilder()
        
        # Add regular filters
        for filter_field, value in filters.items():
            builder.add_filter("f", filter_field, value, self.allowlist, "file")
        
        # Build count query
        cypher, params = builder.build_count_by_field_query("file", field)
        
        logger.info(
            "Executing count_files_by_field Cypher query",
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
            "Completed file count by field",
            field=field,
            results_count=len(counts)
        )
        
        return counts
    
    async def get_files_summary(
        self,
        filters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get summary statistics for files.
        
        Args:
            filters: Filters to apply
            
        Returns:
            Dictionary with summary statistics
        """
        logger.debug("Getting files summary", filters=filters)
        
        # Validate filter fields
        self._validate_filters(filters, "file")
        
        # Build query
        builder = CypherQueryBuilder()
        
        # Add regular filters
        for field, value in filters.items():
            builder.add_filter("f", field, value, self.allowlist, "file")
        
        # Build summary query
        cypher, params = builder.build_summary_query("file")
        
        logger.info(
            "Executing get_files_summary Cypher query",
            cypher=cypher,
            params=params
        )
        
        # Execute query
        result = await self.session.run(cypher, params)
        records = await result.data()
        
        if not records:
            return {"total_count": 0}
        
        summary = records[0]
        logger.debug("Completed files summary", total_count=summary.get("total_count", 0))
        
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
    
    def _record_to_file(self, record: Dict[str, Any]) -> File:
        """
        Convert a database record to a File object.
        
        Args:
            record: Database record dictionary
            
        Returns:
            File object
        """
        # Extract identifiers
        identifiers = record.get("identifiers", [])
        if isinstance(identifiers, str):
            identifiers = [identifiers]
        
        # Build file
        return File(
            id=record.get("id"),
            identifiers=identifiers,
            type=record.get("type"),
            size=record.get("size"),
            checksums=record.get("checksums", {}),
            description=record.get("description"),
            depositions=record.get("depositions", []),
            metadata=record.get("metadata", {})
        )
