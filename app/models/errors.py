"""
Error handling and exception classes for the CCDI Federation Service.

This module provides custom exceptions and error responses according to
the OpenAPI specification.
"""

from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status
from pydantic import BaseModel


class ErrorKind:
    """Error kinds as defined in the OpenAPI specification."""
    INVALID_PARAMETERS = "InvalidParameters"
    UNSUPPORTED_FIELD = "UnsupportedField"
    NOT_FOUND = "NotFound"
    UNSHAREABLE_DATA = "UnshareableData"
    INTERNAL_SERVER_ERROR = "InternalServerError"


class ErrorDetail(BaseModel):
    """Individual error detail model."""
    kind: str
    message: str
    parameters: Optional[List[str]] = None
    field: Optional[str] = None
    entity: Optional[str] = None
    reason: Optional[str] = None


class ErrorsResponse(BaseModel):
    """Error response model matching OpenAPI specification."""
    errors: List[ErrorDetail]


class CCDIException(Exception):
    """Base exception for CCDI Federation Service."""
    
    def __init__(
        self, 
        message: str, 
        kind: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        parameters: Optional[List[str]] = None,
        field: Optional[str] = None,
        entity: Optional[str] = None,
        reason: Optional[str] = None
    ):
        """Initialize CCDI exception."""
        super().__init__(message)
        self.message = message
        self.kind = kind
        self.status_code = status_code
        self.parameters = parameters or []
        self.field = field
        self.entity = entity
        self.reason = reason
    
    def to_error_detail(self) -> ErrorDetail:
        """Convert exception to error detail."""
        return ErrorDetail(
            kind=self.kind,
            message=self.message,
            parameters=self.parameters if self.parameters else None,
            field=self.field,
            entity=self.entity,
            reason=self.reason
        )
    
    def to_http_exception(self) -> HTTPException:
        """Convert to FastAPI HTTPException."""
        return HTTPException(
            status_code=self.status_code,
            detail=ErrorsResponse(errors=[self.to_error_detail()]).model_dump()
        )


class InvalidParametersError(CCDIException):
    """Invalid query or path parameters error."""
    
    def __init__(
        self, 
        parameters: List[str], 
        reason: str,
        message: Optional[str] = None
    ):
        if not message:
            param_list = "', '".join(parameters)
            message = f"Invalid value for parameter{'s' if len(parameters) > 1 else ''} '{param_list}': {reason}"
        
        super().__init__(
            message=message,
            kind=ErrorKind.INVALID_PARAMETERS,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            parameters=parameters,
            reason=reason
        )


class UnsupportedFieldError(CCDIException):
    """Unsupported field error for count/filter operations."""
    
    def __init__(
        self, 
        field: str, 
        entity_type: str,
        operation: str = "filtering"
    ):
        reason = f"This field is not present for {entity_type.lower()}s."
        message = f"Field '{field}' is not supported: {reason}"
        
        super().__init__(
            message=message,
            kind=ErrorKind.UNSUPPORTED_FIELD,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            field=field,
            reason=reason
        )


class ValidationError(CCDIException):
    """General validation error for invalid input parameters."""
    
    def __init__(self, message: str):
        super().__init__(
            message=message,
            kind=ErrorKind.INVALID_PARAMETERS,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
        )


class NotFoundError(CCDIException):
    """Entity not found error."""
    
    def __init__(
        self, 
        entity: str,
        message: Optional[str] = None
    ):
        if not message:
            message = f"{entity} not found."
        
        super().__init__(
            message=message,
            kind=ErrorKind.NOT_FOUND,
            status_code=status.HTTP_404_NOT_FOUND,
            entity=entity
        )


class UnshareableDataError(CCDIException):
    """Data cannot be shared error."""
    
    def __init__(
        self, 
        entity: str,
        reason: str = "Our agreement with data providers prohibits us from sharing line-level data."
    ):
        message = f"Unable to share data for {entity.lower()}: {reason}"
        
        super().__init__(
            message=message,
            kind=ErrorKind.UNSHAREABLE_DATA,
            status_code=status.HTTP_404_NOT_FOUND,
            entity=entity,
            reason=reason
        )


class InternalServerError(CCDIException):
    """Internal server error."""
    
    def __init__(
        self, 
        message: str = "An internal error occurred.",
        reason: Optional[str] = None
    ):
        super().__init__(
            message=message,
            kind=ErrorKind.INTERNAL_SERVER_ERROR,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            reason=reason
        )


# Utility functions for common error scenarios

def create_pagination_error(page: Optional[int] = None, per_page: Optional[int] = None) -> InvalidParametersError:
    """Create a pagination parameter error."""
    parameters = []
    if page is not None and page < 1:
        parameters.append("page")
    if per_page is not None and per_page < 1:
        parameters.append("per_page")
    
    return InvalidParametersError(
        parameters=parameters or ["page", "per_page"],
        reason="Unable to calculate offset."
    )


def create_unsupported_field_error(field: str, entity_type: str) -> UnsupportedFieldError:
    """Create an unsupported field error."""
    return UnsupportedFieldError(field, entity_type)


def create_entity_not_found_error(
    entity_type: str, 
    organization: Optional[str] = None,
    namespace: Optional[str] = None, 
    name: Optional[str] = None
) -> NotFoundError:
    """Create an entity not found error."""
    if organization and namespace and name:
        entity = f"{entity_type} with namespace '{namespace}' and name '{name}'"
    else:
        entity = entity_type.title() + "s"
    
    return NotFoundError(entity)


def create_unshareable_data_error(entity_type: str) -> UnshareableDataError:
    """Create an unshareable data error."""
    return UnshareableDataError(entity_type.title() + "s")
