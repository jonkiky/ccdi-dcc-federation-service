"""
Namespace API routes for the CCDI Federation Service.

This module provides REST endpoints for namespace operations
including listing namespaces and getting individual namespace details.
"""

from typing import List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Request
from neo4j import AsyncSession

from app.api.v1.deps import (
    get_database_session,
    get_app_settings,
    check_rate_limit
)
from app.core.config import Settings
from app.core.logging import get_logger
from app.models.dto import Namespace, Organization

logger = get_logger(__name__)

router = APIRouter(prefix="/namespace", tags=["namespaces"])


# ============================================================================
# Namespace Services
# ============================================================================

class NamespaceService:
    """Service for namespace operations."""
    
    def __init__(self, session: AsyncSession, settings: Settings):
        """Initialize service with dependencies."""
        self.session = session
        self.settings = settings
    
    async def get_namespaces(self) -> List[Namespace]:
        """
        Get all available namespaces.
        
        Returns:
            List of Namespace objects
        """
        logger.debug("Getting all namespaces")
        
        # Query to get distinct organizations and namespaces
        cypher = """
        MATCH (n)
        WHERE n.identifiers IS NOT NULL
        WITH n.identifiers AS identifiers
        UNWIND identifiers AS identifier
        WITH split(identifier, '.') AS parts
        WHERE size(parts) >= 3
        WITH parts[0] AS org, parts[1] AS ns
        RETURN DISTINCT org, ns
        ORDER BY org, ns
        """
        
        # Execute query
        result = await self.session.run(cypher)
        records = await result.data()
        
        # Group by organization
        org_namespaces: Dict[str, List[str]] = {}
        for record in records:
            org = record.get("org")
            ns = record.get("ns")
            if org and ns:
                if org not in org_namespaces:
                    org_namespaces[org] = []
                org_namespaces[org].append(ns)
        
        # Build namespace objects
        namespaces = []
        for org, ns_list in org_namespaces.items():
            for ns in ns_list:
                namespaces.append(Namespace(
                    organization=org,
                    name=ns
                ))
        
        logger.info("Retrieved namespaces", count=len(namespaces))
        
        return namespaces
    
    async def get_namespace_detail(self, org: str, ns: str) -> Namespace:
        """
        Get details for a specific namespace.
        
        Args:
            org: Organization identifier
            ns: Namespace identifier
            
        Returns:
            Namespace object with details
            
        Raises:
            NotFoundError: If namespace is not found
        """
        logger.debug("Getting namespace detail", org=org, ns=ns)
        
        # Query to check if namespace exists and get some statistics
        cypher = """
        MATCH (n)
        WHERE n.identifiers IS NOT NULL
        WITH n.identifiers AS identifiers
        UNWIND identifiers AS identifier
        WITH split(identifier, '.') AS parts, n
        WHERE size(parts) >= 3 AND parts[0] = $org AND parts[1] = $ns
        RETURN COUNT(n) AS entity_count, COLLECT(DISTINCT labels(n)) AS entity_types
        """
        
        params = {"org": org, "ns": ns}
        
        # Execute query
        result = await self.session.run(cypher, params)
        records = await result.data()
        
        if not records or records[0]["entity_count"] == 0:
            from app.models.errors import NotFoundError
            raise NotFoundError(f"Namespace not found: {org}.{ns}")
        
        # Build namespace with details
        record = records[0]
        namespace = Namespace(
            organization=org,
            name=ns,
            description=f"Namespace {ns} in organization {org}",
            entity_count=record["entity_count"],
            entity_types=[label for labels in record["entity_types"] for label in labels]
        )
        
        logger.info(
            "Retrieved namespace detail",
            org=org,
            ns=ns,
            entity_count=namespace.entity_count
        )
        
        return namespace


# ============================================================================
# List All Namespaces
# ============================================================================

@router.get(
    "",
    response_model=List[Namespace],
    summary="List namespaces",
    description="Get all available namespaces"
)
async def list_namespaces(
    request: Request,
    session: AsyncSession = Depends(get_database_session),
    settings: Settings = Depends(get_app_settings),
    _rate_limit: None = Depends(check_rate_limit)
):
    """List all available namespaces."""
    logger.info(
        "List namespaces request",
        path=request.url.path
    )
    
    try:
        # Create service
        service = NamespaceService(session, settings)
        
        # Get namespaces
        namespaces = await service.get_namespaces()
        
        logger.info(
            "List namespaces response",
            namespace_count=len(namespaces)
        )
        
        return namespaces
        
    except Exception as e:
        logger.error("Error listing namespaces", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================================================
# Get Specific Namespace
# ============================================================================

@router.get(
    "/{organization}/{namespace}",
    response_model=Namespace,
    summary="Get namespace details",
    description="Get details for a specific namespace"
)
async def get_namespace(
    organization: str,
    namespace: str,
    request: Request,
    session: AsyncSession = Depends(get_database_session),
    settings: Settings = Depends(get_app_settings),
    _rate_limit: None = Depends(check_rate_limit)
):
    """Get details for a specific namespace."""
    logger.info(
        "Get namespace request",
        organization=organization,
        namespace=namespace,
        path=request.url.path
    )
    
    try:
        # Create service
        service = NamespaceService(session, settings)
        
        # Get namespace
        result = await service.get_namespace_detail(organization, namespace)
        
        logger.info(
            "Get namespace response",
            organization=organization,
            namespace=namespace,
            entity_count=result.entity_count
        )
        
        return result
        
    except Exception as e:
        logger.error("Error getting namespace", error=str(e), exc_info=True)
        if hasattr(e, 'to_http_exception'):
            raise e.to_http_exception()
        elif "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")
