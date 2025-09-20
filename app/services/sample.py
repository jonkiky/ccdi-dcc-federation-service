"""
Sample service for the CCDI Federation Service.

This module provides business logic for sample operations,
including caching, validation, and coordination between
repositories and API endpoints.
"""

from typing import List, Dict, Any, Optional
from neo4j import AsyncSession

from app.core.config import Settings
from app.core.logging import get_logger
from app.core.cache import CacheService
from app.lib.field_allowlist import FieldAllowlist
from app.models.dto import Sample, SampleResponse, CountResponse, SummaryResponse
from app.models.errors import NotFoundError, ValidationError
from app.repositories.sample import SampleRepository

logger = get_logger(__name__)


class SampleService:
    """Service for sample business logic."""
    
    def __init__(
        self,
        session: AsyncSession,
        allowlist: FieldAllowlist,
        settings: Settings,
        cache_service: Optional[CacheService] = None
    ):
        """Initialize service with dependencies."""
        self.repository = SampleRepository(session, allowlist)
        self.settings = settings
        self.cache_service = cache_service
        
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
        """
        logger.debug(
            "Getting samples",
            filters=filters,
            offset=offset,
            limit=limit
        )
        
        # Validate pagination limits
        if limit > self.settings.pagination.max_per_page:
            limit = self.settings.pagination.max_per_page
            logger.debug(
                "Limiting page size",
                requested=limit,
                max_allowed=self.settings.pagination.max_per_page
            )
        
        # Get data from repository
        samples = await self.repository.get_samples(filters, offset, limit)
        
        logger.info(
            "Retrieved samples",
            count=len(samples),
            offset=offset,
            limit=limit
        )
        
        return samples
    
    async def get_sample_by_identifier(
        self,
        org: str,
        ns: str,
        name: str
    ) -> Sample:
        """
        Get a specific sample by organization, namespace, and name.
        
        Args:
            org: Organization identifier
            ns: Namespace identifier  
            name: Sample name/identifier
            
        Returns:
            Sample object
            
        Raises:
            NotFoundError: If sample is not found
        """
        logger.debug(
            "Getting sample by identifier",
            org=org,
            ns=ns,
            name=name
        )
        
        # Validate parameters
        self._validate_identifier_params(org, ns, name)
        
        # Get from repository
        sample = await self.repository.get_sample_by_identifier(org, ns, name)
        
        if not sample:
            raise NotFoundError(f"Sample not found: {org}.{ns}.{name}")
        
        logger.info(
            "Retrieved sample by identifier",
            org=org,
            ns=ns,
            name=name,
            sample_id=sample.id
        )
        
        return sample
    
    async def count_samples_by_field(
        self,
        field: str,
        filters: Dict[str, Any]
    ) -> CountResponse:
        """
        Count samples grouped by a specific field value.
        
        Args:
            field: Field to group by and count
            filters: Additional filters to apply
            
        Returns:
            CountResponse with field counts
        """
        logger.debug(
            "Counting samples by field",
            field=field,
            filters=filters
        )
        
        # Check cache first
        cache_key = None
        if self.cache_service:
            cache_key = self._build_cache_key("sample_count", field, filters)
            cached_result = await self.cache_service.get(cache_key)
            if cached_result:
                logger.debug("Returning cached sample count", field=field)
                return CountResponse(**cached_result)
        
        # Get counts from repository
        counts = await self.repository.count_samples_by_field(field, filters)
        
        # Build response
        response = CountResponse(
            field=field,
            counts=counts
        )
        
        # Cache result
        if self.cache_service and cache_key:
            await self.cache_service.set(
                cache_key,
                response.dict(),
                ttl=self.settings.cache.count_ttl
            )
        
        logger.info(
            "Completed sample count by field",
            field=field,
            result_count=len(counts)
        )
        
        return response
    
    async def get_samples_summary(
        self,
        filters: Dict[str, Any]
    ) -> SummaryResponse:
        """
        Get summary statistics for samples.
        
        Args:
            filters: Filters to apply
            
        Returns:
            SummaryResponse with summary statistics
        """
        logger.debug("Getting samples summary", filters=filters)
        
        # Check cache first
        cache_key = None
        if self.cache_service:
            cache_key = self._build_cache_key("sample_summary", None, filters)
            cached_result = await self.cache_service.get(cache_key)
            if cached_result:
                logger.debug("Returning cached samples summary")
                return SummaryResponse(**cached_result)
        
        # Get summary from repository
        summary_data = await self.repository.get_samples_summary(filters)
        
        # Build response
        response = SummaryResponse(**summary_data)
        
        # Cache result
        if self.cache_service and cache_key:
            await self.cache_service.set(
                cache_key,
                response.dict(),
                ttl=self.settings.cache.summary_ttl
            )
        
        logger.info(
            "Completed samples summary",
            total_count=response.total_count
        )
        
        return response
    
    def _validate_identifier_params(self, org: str, ns: str, name: str) -> None:
        """
        Validate identifier parameters.
        
        Args:
            org: Organization identifier
            ns: Namespace identifier
            name: Sample name
            
        Raises:
            ValidationError: If parameters are invalid
        """
        if not org or not org.strip():
            raise ValidationError("Organization identifier cannot be empty")
        
        if not ns or not ns.strip():
            raise ValidationError("Namespace identifier cannot be empty")
        
        if not name or not name.strip():
            raise ValidationError("Sample name cannot be empty")
        
        # Check for invalid characters
        for param_name, param_value in [("org", org), ("ns", ns), ("name", name)]:
            if any(char in param_value for char in [".", "/", "\\", " "]):
                raise ValidationError(f"Invalid characters in {param_name}: {param_value}")
    
    def _build_cache_key(
        self,
        operation: str,
        field: Optional[str],
        filters: Dict[str, Any]
    ) -> str:
        """
        Build cache key for caching results.
        
        Args:
            operation: Type of operation (count, summary, etc.)
            field: Field name for count operations
            filters: Applied filters
            
        Returns:
            Cache key string
        """
        # Sort filters for consistent cache keys
        filter_items = sorted(filters.items()) if filters else []
        filter_str = "|".join([f"{k}:{v}" for k, v in filter_items])
        
        if field:
            return f"{operation}:{field}:{filter_str}"
        else:
            return f"{operation}:{filter_str}"
