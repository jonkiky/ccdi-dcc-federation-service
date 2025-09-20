"""
Subject API routes for the CCDI Federation Service.

This module provides REST endpoints for subject operations
including listing, individual retrieval, counting, and summaries.
"""

from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from neo4j import AsyncSession

from app.api.v1.deps import (
    get_database_session,
    get_app_settings,
    get_allowlist,
    get_pagination_params,
    get_subject_filters,
    get_subject_diagnosis_filters,
    check_rate_limit
)
from app.core.config import Settings
from app.core.pagination import PaginationParams, PaginationInfo, build_link_header
from app.core.cache import get_cache_service
from app.core.logging import get_logger
from app.lib.field_allowlist import FieldAllowlist
from app.models.dto import (
    Subject,
    SubjectResponse,
    CountResponse,
    SummaryResponse
)
from app.models.errors import NotFoundError
from app.services.subject import SubjectService

logger = get_logger(__name__)

router = APIRouter(prefix="/subject", tags=["subjects"])


# ============================================================================
# Subject Listing
# ============================================================================

@router.get(
    "",
    response_model=SubjectResponse,
    summary="List subjects",
    description="Get a paginated list of subjects with optional filtering"
)
async def list_subjects(
    request: Request,
    response: Response,
    filters: Dict[str, Any] = Depends(get_subject_filters),
    pagination: PaginationParams = Depends(get_pagination_params),
    session: AsyncSession = Depends(get_database_session),
    settings: Settings = Depends(get_app_settings),
    allowlist: FieldAllowlist = Depends(get_allowlist),
    _rate_limit: None = Depends(check_rate_limit)
):
    """List subjects with pagination and filtering."""
    logger.info(
        "List subjects request",
        filters=filters,
        page=pagination.page,
        per_page=pagination.per_page,
        path=request.url.path
    )
    
    try:
        # Create service
        cache_service = get_cache_service()
        service = SubjectService(session, allowlist, settings, cache_service)
        
        # Get subjects
        subjects = await service.get_subjects(
            filters=filters,
            offset=pagination.offset,
            limit=pagination.per_page
        )
        
        # Build pagination info (we'd need total count for complete pagination)
        # For now, we'll provide basic pagination info
        pagination_info = PaginationInfo(
            page=pagination.page,
            per_page=pagination.per_page,
            total_pages=None,  # Would require additional count query
            total_count=None   # Would require additional count query
        )
        
        # Add Link header for pagination
        base_url = str(request.url.replace(query=""))
        link_header = build_link_header(
            base_url=base_url,
            query_params=dict(request.query_params),
            pagination_info=pagination_info
        )
        
        if link_header:
            response.headers["Link"] = link_header
        
        # Build response
        result = SubjectResponse(
            subjects=subjects,
            pagination=pagination_info
        )
        
        logger.info(
            "List subjects response",
            subject_count=len(subjects),
            page=pagination.page
        )
        
        return result
        
    except Exception as e:
        logger.error("Error listing subjects", error=str(e), exc_info=True)
        if hasattr(e, 'to_http_exception'):
            raise e.to_http_exception()
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================================================
# Individual Subject Retrieval
# ============================================================================

@router.get(
    "/{org}/{ns}/{name}",
    response_model=Subject,
    summary="Get subject by identifier",
    description="Get a specific subject by organization, namespace, and name"
)
async def get_subject(
    org: str,
    ns: str,
    name: str,
    request: Request,
    session: AsyncSession = Depends(get_database_session),
    settings: Settings = Depends(get_app_settings),
    allowlist: FieldAllowlist = Depends(get_allowlist),
    _rate_limit: None = Depends(check_rate_limit)
):
    """Get a specific subject by identifier."""
    logger.info(
        "Get subject request",
        org=org,
        ns=ns,
        name=name,
        path=request.url.path
    )
    
    try:
        # Create service
        cache_service = get_cache_service()
        service = SubjectService(session, allowlist, settings, cache_service)
        
        # Get subject
        subject = await service.get_subject_by_identifier(org, ns, name)
        
        logger.info(
            "Get subject response",
            org=org,
            ns=ns,
            name=name,
            subject_id=subject.id
        )
        
        return subject
        
    except NotFoundError as e:
        logger.warning("Subject not found", org=org, ns=ns, name=name)
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("Error getting subject", error=str(e), exc_info=True)
        if hasattr(e, 'to_http_exception'):
            raise e.to_http_exception()
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================================================
# Subject Counting by Field
# ============================================================================

@router.get(
    "/by/{field}/count",
    response_model=CountResponse,
    summary="Count subjects by field",
    description="Get counts of subjects grouped by a specific field value"
)
async def count_subjects_by_field(
    field: str,
    request: Request,
    filters: Dict[str, Any] = Depends(get_subject_filters),
    session: AsyncSession = Depends(get_database_session),
    settings: Settings = Depends(get_app_settings),
    allowlist: FieldAllowlist = Depends(get_allowlist),
    _rate_limit: None = Depends(check_rate_limit)
):
    """Count subjects grouped by a specific field."""
    logger.info(
        "Count subjects by field request",
        field=field,
        filters=filters,
        path=request.url.path
    )
    
    try:
        # Create service
        cache_service = get_cache_service()
        service = SubjectService(session, allowlist, settings, cache_service)
        
        # Get counts
        result = await service.count_subjects_by_field(field, filters)
        
        logger.info(
            "Count subjects by field response",
            field=field,
            count_items=len(result.counts)
        )
        
        return result
        
    except Exception as e:
        logger.error("Error counting subjects by field", error=str(e), exc_info=True)
        if hasattr(e, 'to_http_exception'):
            raise e.to_http_exception()
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================================================
# Subject Summary
# ============================================================================

@router.get(
    "/summary",
    response_model=SummaryResponse,
    summary="Get subjects summary",
    description="Get summary statistics for subjects"
)
async def get_subjects_summary(
    request: Request,
    filters: Dict[str, Any] = Depends(get_subject_filters),
    session: AsyncSession = Depends(get_database_session),
    settings: Settings = Depends(get_app_settings),
    allowlist: FieldAllowlist = Depends(get_allowlist),
    _rate_limit: None = Depends(check_rate_limit)
):
    """Get summary statistics for subjects."""
    logger.info(
        "Get subjects summary request",
        filters=filters,
        path=request.url.path
    )
    
    try:
        # Create service
        cache_service = get_cache_service()
        service = SubjectService(session, allowlist, settings, cache_service)
        
        # Get summary
        result = await service.get_subjects_summary(filters)
        
        logger.info(
            "Get subjects summary response",
            total_count=result.total_count
        )
        
        return result
        
    except Exception as e:
        logger.error("Error getting subjects summary", error=str(e), exc_info=True)
        if hasattr(e, 'to_http_exception'):
            raise e.to_http_exception()
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================================================
# Subject Diagnosis Search Endpoints
# ============================================================================

@router.get(
    "/diagnosis/search",
    response_model=SubjectResponse,
    summary="Search subjects by diagnosis",
    description="Search subjects with diagnosis filtering"
)
async def search_subjects_by_diagnosis(
    request: Request,
    response: Response,
    filters: Dict[str, Any] = Depends(get_subject_diagnosis_filters),
    pagination: PaginationParams = Depends(get_pagination_params),
    session: AsyncSession = Depends(get_database_session),
    settings: Settings = Depends(get_app_settings),
    allowlist: FieldAllowlist = Depends(get_allowlist),
    _rate_limit: None = Depends(check_rate_limit)
):
    """Search subjects with diagnosis filtering."""
    logger.info(
        "Search subjects by diagnosis request",
        filters=filters,
        page=pagination.page,
        per_page=pagination.per_page,
        path=request.url.path
    )
    
    try:
        # Create service
        cache_service = get_cache_service()
        service = SubjectService(session, allowlist, settings, cache_service)
        
        # Get subjects
        subjects = await service.get_subjects(
            filters=filters,
            offset=pagination.offset,
            limit=pagination.per_page
        )
        
        # Build pagination info
        pagination_info = PaginationInfo(
            page=pagination.page,
            per_page=pagination.per_page,
            total_pages=None,
            total_count=None
        )
        
        # Add Link header
        base_url = str(request.url.replace(query=""))
        link_header = build_link_header(
            base_url=base_url,
            query_params=dict(request.query_params),
            pagination_info=pagination_info
        )
        
        if link_header:
            response.headers["Link"] = link_header
        
        # Build response
        result = SubjectResponse(
            subjects=subjects,
            pagination=pagination_info
        )
        
        logger.info(
            "Search subjects by diagnosis response",
            subject_count=len(subjects),
            page=pagination.page
        )
        
        return result
        
    except Exception as e:
        logger.error("Error searching subjects by diagnosis", error=str(e), exc_info=True)
        if hasattr(e, 'to_http_exception'):
            raise e.to_http_exception()
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/diagnosis/by/{field}/count",
    response_model=CountResponse,
    summary="Count subjects by field with diagnosis search",
    description="Count subjects by field with diagnosis filtering"
)
async def count_subjects_by_field_with_diagnosis(
    field: str,
    request: Request,
    filters: Dict[str, Any] = Depends(get_subject_diagnosis_filters),
    session: AsyncSession = Depends(get_database_session),
    settings: Settings = Depends(get_app_settings),
    allowlist: FieldAllowlist = Depends(get_allowlist),
    _rate_limit: None = Depends(check_rate_limit)
):
    """Count subjects by field with diagnosis filtering."""
    logger.info(
        "Count subjects by field with diagnosis request",
        field=field,
        filters=filters,
        path=request.url.path
    )
    
    try:
        # Create service
        cache_service = get_cache_service()
        service = SubjectService(session, allowlist, settings, cache_service)
        
        # Get counts
        result = await service.count_subjects_by_field(field, filters)
        
        logger.info(
            "Count subjects by field with diagnosis response",
            field=field,
            count_items=len(result.counts)
        )
        
        return result
        
    except Exception as e:
        logger.error("Error counting subjects by field with diagnosis", error=str(e), exc_info=True)
        if hasattr(e, 'to_http_exception'):
            raise e.to_http_exception()
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/diagnosis/summary",
    response_model=SummaryResponse,
    summary="Get subjects summary with diagnosis search",
    description="Get summary statistics for subjects with diagnosis filtering"
)
async def get_subjects_summary_with_diagnosis(
    request: Request,
    filters: Dict[str, Any] = Depends(get_subject_diagnosis_filters),
    session: AsyncSession = Depends(get_database_session),
    settings: Settings = Depends(get_app_settings),
    allowlist: FieldAllowlist = Depends(get_allowlist),
    _rate_limit: None = Depends(check_rate_limit)
):
    """Get summary statistics for subjects with diagnosis filtering."""
    logger.info(
        "Get subjects summary with diagnosis request",
        filters=filters,
        path=request.url.path
    )
    
    try:
        # Create service
        cache_service = get_cache_service()
        service = SubjectService(session, allowlist, settings, cache_service)
        
        # Get summary
        result = await service.get_subjects_summary(filters)
        
        logger.info(
            "Get subjects summary with diagnosis response",
            total_count=result.total_count
        )
        
        return result
        
    except Exception as e:
        logger.error("Error getting subjects summary with diagnosis", error=str(e), exc_info=True)
        if hasattr(e, 'to_http_exception'):
            raise e.to_http_exception()
        raise HTTPException(status_code=500, detail="Internal server error")
