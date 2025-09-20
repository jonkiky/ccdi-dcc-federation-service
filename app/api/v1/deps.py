"""
FastAPI dependencies for the CCDI Federation Service.

This module provides dependency injection for common resources like
database sessions, configuration, and pagination parameters.
"""

from typing import Optional, Dict, Any

from fastapi import Depends, Query, HTTPException, Request
from neo4j import AsyncSession

from app.core.config import Settings, get_settings
from app.core.pagination import PaginationParams, parse_pagination_params
from app.core.logging import get_logger
from app.db.memgraph import get_session
from app.lib.field_allowlist import get_field_allowlist, FieldAllowlist
from app.models.errors import create_pagination_error, InvalidParametersError

logger = get_logger(__name__)


# ============================================================================
# Core Dependencies
# ============================================================================

async def get_database_session() -> AsyncSession:
    """Get database session dependency."""
    async for session in get_session():
        yield session


def get_app_settings() -> Settings:
    """Get application settings dependency."""
    return get_settings()


def get_allowlist() -> FieldAllowlist:
    """Get field allowlist dependency."""
    return get_field_allowlist()


# ============================================================================
# Pagination Dependencies
# ============================================================================

def get_pagination_params(
    page: Optional[int] = Query(
        default=1,
        ge=1,
        description="Page number (1-based)"
    ),
    per_page: Optional[int] = Query(
        default=None,
        ge=1,
        description="Items per page"
    )
) -> PaginationParams:
    """
    Get and validate pagination parameters.
    
    Raises:
        HTTPException: If pagination parameters are invalid
    """
    try:
        return parse_pagination_params(page, per_page)
    except ValueError as e:
        error = create_pagination_error(page, per_page)
        raise error.to_http_exception()


# ============================================================================
# Filter Dependencies  
# ============================================================================

def get_subject_filters(
    sex: Optional[str] = Query(None, description="Filter by sex"),
    race: Optional[str] = Query(None, description="Filter by race"),
    ethnicity: Optional[str] = Query(None, description="Filter by ethnicity"),
    identifiers: Optional[str] = Query(None, description="Filter by identifiers"),
    vital_status: Optional[str] = Query(None, description="Filter by vital status"),
    age_at_vital_status: Optional[str] = Query(None, description="Filter by age at vital status"),
    depositions: Optional[str] = Query(None, description="Filter by depositions"),
    request: Request = None
) -> Dict[str, Any]:
    """Get subject filter parameters."""
    filters = {}
    
    # Add non-null filters
    if sex is not None:
        filters["sex"] = sex
    if race is not None:
        filters["race"] = race
    if ethnicity is not None:
        filters["ethnicity"] = ethnicity
    if identifiers is not None:
        filters["identifiers"] = identifiers
    if vital_status is not None:
        filters["vital_status"] = vital_status
    if age_at_vital_status is not None:
        filters["age_at_vital_status"] = age_at_vital_status
    if depositions is not None:
        filters["depositions"] = depositions
    
    # Handle unharmonized fields from query parameters
    if request:
        for key, value in request.query_params.items():
            if key.startswith("metadata.unharmonized."):
                filters[key] = value
    
    return filters


def get_sample_filters(
    disease_phase: Optional[str] = Query(None, description="Filter by disease phase"),
    anatomical_sites: Optional[str] = Query(None, description="Filter by anatomical sites"),
    library_selection_method: Optional[str] = Query(None, description="Filter by library selection method"),
    library_strategy: Optional[str] = Query(None, description="Filter by library strategy"),
    library_source_material: Optional[str] = Query(None, description="Filter by library source material"),
    preservation_method: Optional[str] = Query(None, description="Filter by preservation method"),
    tumor_grade: Optional[str] = Query(None, description="Filter by tumor grade"),
    specimen_molecular_analyte_type: Optional[str] = Query(None, description="Filter by specimen molecular analyte type"),
    tissue_type: Optional[str] = Query(None, description="Filter by tissue type"),
    tumor_classification: Optional[str] = Query(None, description="Filter by tumor classification"),
    age_at_diagnosis: Optional[str] = Query(None, description="Filter by age at diagnosis"),
    age_at_collection: Optional[str] = Query(None, description="Filter by age at collection"),
    tumor_tissue_morphology: Optional[str] = Query(None, description="Filter by tumor tissue morphology"),
    depositions: Optional[str] = Query(None, description="Filter by depositions"),
    diagnosis: Optional[str] = Query(None, description="Filter by diagnosis"),
    request: Request = None
) -> Dict[str, Any]:
    """Get sample filter parameters."""
    filters = {}
    
    # Add non-null filters
    if disease_phase is not None:
        filters["disease_phase"] = disease_phase
    if anatomical_sites is not None:
        filters["anatomical_sites"] = anatomical_sites
    if library_selection_method is not None:
        filters["library_selection_method"] = library_selection_method
    if library_strategy is not None:
        filters["library_strategy"] = library_strategy
    if library_source_material is not None:
        filters["library_source_material"] = library_source_material
    if preservation_method is not None:
        filters["preservation_method"] = preservation_method
    if tumor_grade is not None:
        filters["tumor_grade"] = tumor_grade
    if specimen_molecular_analyte_type is not None:
        filters["specimen_molecular_analyte_type"] = specimen_molecular_analyte_type
    if tissue_type is not None:
        filters["tissue_type"] = tissue_type
    if tumor_classification is not None:
        filters["tumor_classification"] = tumor_classification
    if age_at_diagnosis is not None:
        filters["age_at_diagnosis"] = age_at_diagnosis
    if age_at_collection is not None:
        filters["age_at_collection"] = age_at_collection
    if tumor_tissue_morphology is not None:
        filters["tumor_tissue_morphology"] = tumor_tissue_morphology
    if depositions is not None:
        filters["depositions"] = depositions
    if diagnosis is not None:
        filters["diagnosis"] = diagnosis
    
    # Handle unharmonized fields from query parameters
    if request:
        for key, value in request.query_params.items():
            if key.startswith("metadata.unharmonized."):
                filters[key] = value
    
    return filters


def get_file_filters(
    type: Optional[str] = Query(None, description="Filter by file type", alias="type"),
    size: Optional[str] = Query(None, description="Filter by file size"),
    checksums: Optional[str] = Query(None, description="Filter by checksums"),
    description: Optional[str] = Query(None, description="Filter by description"),
    depositions: Optional[str] = Query(None, description="Filter by depositions"),
    request: Request = None
) -> Dict[str, Any]:
    """Get file filter parameters."""
    filters = {}
    
    # Add non-null filters
    if type is not None:
        filters["type"] = type
    if size is not None:
        filters["size"] = size
    if checksums is not None:
        filters["checksums"] = checksums
    if description is not None:
        filters["description"] = description
    if depositions is not None:
        filters["depositions"] = depositions
    
    # Handle unharmonized fields from query parameters
    if request:
        for key, value in request.query_params.items():
            if key.startswith("metadata.unharmonized."):
                filters[key] = value
    
    return filters


# ============================================================================
# Diagnosis Search Dependencies
# ============================================================================

def get_diagnosis_search_params(
    search: Optional[str] = Query(None, description="Diagnosis search term")
) -> Optional[str]:
    """Get diagnosis search parameters."""
    return search


def get_subject_diagnosis_filters(
    search: Optional[str] = Query(None, description="Diagnosis search term"),
    sex: Optional[str] = Query(None, description="Filter by sex"),
    race: Optional[str] = Query(None, description="Filter by race"),
    ethnicity: Optional[str] = Query(None, description="Filter by ethnicity"),
    identifiers: Optional[str] = Query(None, description="Filter by identifiers"),
    vital_status: Optional[str] = Query(None, description="Filter by vital status"),
    age_at_vital_status: Optional[str] = Query(None, description="Filter by age at vital status"),
    depositions: Optional[str] = Query(None, description="Filter by depositions"),
    request: Request = None
) -> Dict[str, Any]:
    """Get subject diagnosis search filters."""
    filters = get_subject_filters(
        sex=sex,
        race=race,
        ethnicity=ethnicity,
        identifiers=identifiers,
        vital_status=vital_status,
        age_at_vital_status=age_at_vital_status,
        depositions=depositions,
        request=request
    )
    
    if search:
        filters["_diagnosis_search"] = search
    
    return filters


def get_sample_diagnosis_filters(
    search: Optional[str] = Query(None, description="Diagnosis search term"),
    disease_phase: Optional[str] = Query(None, description="Filter by disease phase"),
    anatomical_sites: Optional[str] = Query(None, description="Filter by anatomical sites"),
    library_selection_method: Optional[str] = Query(None, description="Filter by library selection method"),
    library_strategy: Optional[str] = Query(None, description="Filter by library strategy"),
    library_source_material: Optional[str] = Query(None, description="Filter by library source material"),
    preservation_method: Optional[str] = Query(None, description="Filter by preservation method"),
    specimen_molecular_analyte_type: Optional[str] = Query(None, description="Filter by specimen molecular analyte type"),
    tissue_type: Optional[str] = Query(None, description="Filter by tissue type"),
    tumor_classification: Optional[str] = Query(None, description="Filter by tumor classification"),
    age_at_diagnosis: Optional[str] = Query(None, description="Filter by age at diagnosis"),
    age_at_collection: Optional[str] = Query(None, description="Filter by age at collection"),
    tumor_tissue_morphology: Optional[str] = Query(None, description="Filter by tumor tissue morphology"),
    depositions: Optional[str] = Query(None, description="Filter by depositions"),
    diagnosis: Optional[str] = Query(None, description="Filter by diagnosis"),
    request: Request = None
) -> Dict[str, Any]:
    """Get sample diagnosis search filters."""
    filters = get_sample_filters(
        disease_phase=disease_phase,
        anatomical_sites=anatomical_sites,
        library_selection_method=library_selection_method,
        library_strategy=library_strategy,
        library_source_material=library_source_material,
        preservation_method=preservation_method,
        specimen_molecular_analyte_type=specimen_molecular_analyte_type,
        tissue_type=tissue_type,
        tumor_classification=tumor_classification,
        age_at_diagnosis=age_at_diagnosis,
        age_at_collection=age_at_collection,
        tumor_tissue_morphology=tumor_tissue_morphology,
        depositions=depositions,
        diagnosis=diagnosis,
        request=request
    )
    
    if search:
        filters["_diagnosis_search"] = search
    
    return filters


# ============================================================================
# Rate Limiting Dependencies
# ============================================================================

async def check_rate_limit(
    request: Request,
    settings: Settings = Depends(get_app_settings)
) -> None:
    """Check rate limiting (placeholder for slowapi integration)."""
    # This would be implemented with slowapi rate limiting
    # For now, we'll just log the request
    logger.debug(
        "Request received",
        path=request.url.path,
        method=request.method,
        client_ip=request.client.host if request.client else None
    )
