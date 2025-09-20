"""
Data Transfer Objects (DTOs) for the CCDI Federation Service.

This module contains Pydantic models for request/response serialization
based on the OpenAPI specification.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict


# ============================================================================
# Base Models
# ============================================================================

class BaseIdentifier(BaseModel):
    """Base identifier model."""
    organization: str = Field(..., description="Organization identifier")
    name: str = Field(..., description="Name")


class NamespaceIdentifier(BaseIdentifier):
    """Namespace identifier model."""
    pass


class OrganizationIdentifier(BaseModel):
    """Organization identifier model."""
    model_config = ConfigDict(extra="forbid")
    
    identifier: str = Field(..., description="Organization identifier")


# ============================================================================
# Metadata Field Models
# ============================================================================

class FieldDetails(BaseModel):
    """Details regarding the harmonization process."""
    method: Optional[str] = None
    harmonizer: Optional[str] = None
    url: Optional[str] = None


class UnharmonizedField(BaseModel):
    """Unharmonized metadata field."""
    value: Any = Field(..., description="Field value")
    ancestors: Optional[List[str]] = None
    details: Optional[FieldDetails] = None
    comment: Optional[str] = None


class HarmonizedStandard(BaseModel):
    """Standard to which a field is harmonized."""
    name: str = Field(..., description="Standard name")
    url: str = Field(..., description="Standard URL")


class HarmonizedFieldDescription(BaseModel):
    """Harmonized metadata field description."""
    harmonized: bool = Field(True, description="Always true for harmonized fields")
    path: str = Field(..., description="Dot-delimited path to field location")
    wiki_url: str = Field(..., description="Wiki URL for field documentation")
    standard: Optional[HarmonizedStandard] = None


class UnharmonizedFieldDescription(BaseModel):
    """Unharmonized metadata field description."""
    harmonized: bool = Field(False, description="Always false for unharmonized fields")
    name: Optional[str] = None
    description: Optional[str] = None
    path: str = Field(..., description="Dot-delimited path to field location")
    standard: Optional[str] = None
    url: Optional[str] = None


FieldDescription = Union[HarmonizedFieldDescription, UnharmonizedFieldDescription]


# ============================================================================
# Gateway Models
# ============================================================================

class GatewayKind(str, Enum):
    """Gateway access kinds."""
    OPEN = "Open"
    REGISTERED = "Registered"
    CONTROLLED = "Controlled"
    CLOSED = "Closed"


class LinkKind(str, Enum):
    """Link types."""
    DIRECT = "Direct"
    APPROXIMATE = "Approximate"
    INFORMATIONAL = "Informational"
    MAILTO = "MailTo"


class DirectLink(BaseModel):
    """Direct link to resource."""
    url: str = Field(..., description="Resource URL")
    kind: LinkKind = Field(LinkKind.DIRECT)


class ApproximateLink(BaseModel):
    """Approximate link with instructions."""
    url: str = Field(..., description="Approximate resource URL")
    instructions: str = Field(..., description="Manual instructions")
    kind: LinkKind = Field(LinkKind.APPROXIMATE)


class InformationalLink(BaseModel):
    """Informational link about access."""
    url: str = Field(..., description="Information URL")
    kind: LinkKind = Field(LinkKind.INFORMATIONAL)


class MailToLink(BaseModel):
    """Email link for access requests."""
    url: str = Field(..., description="Email URL")
    instructions: str = Field(..., description="Email instructions")
    kind: LinkKind = Field(LinkKind.MAILTO)


GatewayLink = Union[DirectLink, ApproximateLink, InformationalLink, MailToLink]


class ClosedStatus(str, Enum):
    """Closed gateway status."""
    INDEFINITELY_CLOSED = "IndefinitelyClosed"
    AWAITING_PUBLICATION = "AwaitingPublication"
    EMBARGOED = "Embargoed"


class IndefinitelyClosedGateway(BaseModel):
    """Indefinitely closed gateway."""
    status: ClosedStatus = Field(ClosedStatus.INDEFINITELY_CLOSED)
    description: str = Field(..., description="Gateway description")
    kind: GatewayKind = Field(GatewayKind.CLOSED)


class AwaitingPublicationGateway(BaseModel):
    """Gateway awaiting publication."""
    status: ClosedStatus = Field(ClosedStatus.AWAITING_PUBLICATION)
    available_at: Optional[datetime] = None
    description: str = Field(..., description="Gateway description")
    kind: GatewayKind = Field(GatewayKind.CLOSED)


class EmbargoedGateway(BaseModel):
    """Embargoed gateway."""
    status: ClosedStatus = Field(ClosedStatus.EMBARGOED)
    available_at: datetime = Field(..., description="Embargo end date")
    description: str = Field(..., description="Gateway description")
    kind: GatewayKind = Field(GatewayKind.CLOSED)


class OpenGateway(BaseModel):
    """Open access gateway."""
    link: GatewayLink = Field(..., description="Gateway link")
    kind: GatewayKind = Field(GatewayKind.OPEN)


class RegisteredGateway(BaseModel):
    """Registered access gateway."""
    link: GatewayLink = Field(..., description="Gateway link")
    kind: GatewayKind = Field(GatewayKind.REGISTERED)


class ControlledGateway(BaseModel):
    """Controlled access gateway."""
    link: GatewayLink = Field(..., description="Gateway link")
    kind: GatewayKind = Field(GatewayKind.CONTROLLED)


Gateway = Union[
    OpenGateway,
    RegisteredGateway, 
    ControlledGateway,
    IndefinitelyClosedGateway,
    AwaitingPublicationGateway,
    EmbargoedGateway
]


class AnonymousGateway(BaseModel):
    """Anonymous gateway embedded in response."""
    gateway: Gateway = Field(..., description="Gateway details")
    kind: str = Field("Anonymous")


class GatewayReference(BaseModel):
    """Reference to a named gateway."""
    gateway: str = Field(..., description="Gateway name reference")
    kind: str = Field("Reference")


GatewayOrReference = Union[AnonymousGateway, GatewayReference]


class NamedGateway(BaseModel):
    """Named gateway for response gateways collection."""
    name: str = Field(..., description="Gateway name")
    # Include all gateway fields inline
    link: Optional[GatewayLink] = None
    status: Optional[ClosedStatus] = None
    available_at: Optional[datetime] = None
    description: Optional[str] = None
    kind: GatewayKind = Field(..., description="Gateway kind")


# ============================================================================
# Common Metadata Models
# ============================================================================

class DepositionAccession(BaseModel):
    """Deposition accession model."""
    kind: str = Field(..., description="Repository type")
    value: str = Field(..., description="Accession value")


class CommonMetadata(BaseModel):
    """Common metadata shared across entities."""
    depositions: Optional[List[DepositionAccession]] = Field(
        None, 
        description="Public repository depositions"
    )


# ============================================================================
# Entity-Specific Models
# ============================================================================

class SubjectKind(str, Enum):
    """Subject kinds."""
    HOMO_SAPIENS = "Homo sapiens"


class SubjectIdentifier(BaseModel):
    """Subject identifier model."""
    namespace: NamespaceIdentifier = Field(..., description="Namespace identifier")
    name: str = Field(..., description="Subject name", examples=["SubjectName001"])


class SubjectMetadata(CommonMetadata):
    """Subject metadata model."""
    sex: Optional[UnharmonizedField] = None
    race: Optional[UnharmonizedField] = None
    ethnicity: Optional[UnharmonizedField] = None
    identifiers: Optional[List[UnharmonizedField]] = None
    vital_status: Optional[UnharmonizedField] = None
    age_at_vital_status: Optional[UnharmonizedField] = None
    associated_diagnoses: Optional[UnharmonizedField] = None
    unharmonized: Optional[Dict[str, UnharmonizedField]] = Field(
        None,
        description="Unharmonized metadata fields"
    )


class SampleIdentifier(BaseModel):
    """Sample identifier model."""
    namespace: NamespaceIdentifier = Field(..., description="Namespace identifier")
    name: str = Field(..., description="Sample name", examples=["SampleName001"])


class SampleMetadata(CommonMetadata):
    """Sample metadata model."""
    disease_phase: Optional[UnharmonizedField] = None
    anatomical_sites: Optional[UnharmonizedField] = None
    library_selection_method: Optional[UnharmonizedField] = None
    library_strategy: Optional[UnharmonizedField] = None
    library_source_material: Optional[UnharmonizedField] = None
    preservation_method: Optional[UnharmonizedField] = None
    tumor_grade: Optional[UnharmonizedField] = None
    specimen_molecular_analyte_type: Optional[UnharmonizedField] = None
    tissue_type: Optional[UnharmonizedField] = None
    tumor_classification: Optional[UnharmonizedField] = None
    age_at_diagnosis: Optional[UnharmonizedField] = None
    age_at_collection: Optional[UnharmonizedField] = None
    tumor_tissue_morphology: Optional[UnharmonizedField] = None
    diagnosis: Optional[UnharmonizedField] = None
    identifiers: Optional[List[UnharmonizedField]] = None
    unharmonized: Optional[Dict[str, UnharmonizedField]] = Field(
        None,
        description="Unharmonized metadata fields"
    )


class FileIdentifier(BaseModel):
    """File identifier model."""
    namespace: NamespaceIdentifier = Field(..., description="Namespace identifier")
    name: str = Field(..., description="File name", examples=["File001.txt"])


class FileChecksums(BaseModel):
    """File checksums model."""
    md5: Optional[str] = None


class FileMetadata(CommonMetadata):
    """File metadata model."""
    type: Optional[UnharmonizedField] = None
    size: Optional[UnharmonizedField] = None
    checksums: Optional[UnharmonizedField] = None
    description: Optional[UnharmonizedField] = None
    unharmonized: Optional[Dict[str, UnharmonizedField]] = Field(
        None,
        description="Unharmonized metadata fields"
    )


# ============================================================================
# Entity Models
# ============================================================================

class Subject(BaseModel):
    """Subject model."""
    id: SubjectIdentifier = Field(..., description="Subject identifier")
    kind: SubjectKind = Field(..., description="Subject kind")
    gateways: Optional[List[GatewayOrReference]] = None
    metadata: Optional[SubjectMetadata] = None


class Sample(BaseModel):
    """Sample model."""
    id: SampleIdentifier = Field(..., description="Sample identifier")
    subject: SubjectIdentifier = Field(..., description="Associated subject identifier")
    gateways: Optional[List[GatewayOrReference]] = None
    metadata: Optional[SampleMetadata] = None


class File(BaseModel):
    """File model."""
    id: FileIdentifier = Field(..., description="File identifier")
    samples: List[SampleIdentifier] = Field(
        ..., 
        description="Associated sample identifiers"
    )
    gateways: Optional[List[GatewayOrReference]] = None
    metadata: Optional[FileMetadata] = None


class Organization(BaseModel):
    """Organization model."""
    identifier: str = Field(..., description="Organization identifier")
    name: str = Field(..., description="Organization name")
    metadata: Optional[Dict[str, Any]] = None


class NamespaceMetadata(CommonMetadata):
    """Namespace metadata model."""
    study_short_title: Optional[UnharmonizedField] = None
    study_name: Optional[UnharmonizedField] = None
    study_funding_id: Optional[List[UnharmonizedField]] = None
    study_id: Optional[UnharmonizedField] = None
    unharmonized: Optional[Dict[str, UnharmonizedField]] = Field(
        None,
        description="Unharmonized metadata fields"
    )


class Namespace(BaseModel):
    """Namespace model."""
    id: NamespaceIdentifier = Field(..., description="Namespace identifier")
    description: str = Field(..., description="Namespace description")
    contact_email: str = Field(..., description="Support email address")
    metadata: Optional[NamespaceMetadata] = None


# ============================================================================
# Response Models
# ============================================================================

class Summary(BaseModel):
    """Summary response model."""
    # TODO: Define summary fields based on requirements
    total_count: int = Field(..., description="Total entity count")
    # Add more summary fields as needed


class CountResult(BaseModel):
    """Count result for by-field counting."""
    value: str = Field(..., description="Field value")
    count: int = Field(..., description="Count for this value")


class CountResponse(BaseModel):
    """Generic count response for field counting."""
    field: str = Field(..., description="Field name that was counted")
    counts: List[CountResult] = Field(..., description="Count results for field values")


class SummaryResponse(BaseModel):
    """Generic summary response model."""
    total_count: int = Field(..., description="Total entity count")
    # Add other summary fields as needed based on the summary data structure


class SubjectsResponse(BaseModel):
    """Subjects list response."""
    subjects: List[Subject] = Field(..., description="List of subjects")
    gateways: Optional[Dict[str, NamedGateway]] = Field(
        None,
        description="Named gateways referenced by subjects"
    )


class SamplesResponse(BaseModel):
    """Samples list response."""
    samples: List[Sample] = Field(..., description="List of samples")
    gateways: Optional[Dict[str, NamedGateway]] = Field(
        None,
        description="Named gateways referenced by samples"
    )


class FilesResponse(BaseModel):
    """Files list response."""
    files: List[File] = Field(..., description="List of files")
    gateways: Optional[Dict[str, NamedGateway]] = Field(
        None,
        description="Named gateways referenced by files"
    )


class SubjectResponse(BaseModel):
    """Single subject response."""
    subject: Subject = Field(..., description="Subject details")
    gateways: Optional[Dict[str, NamedGateway]] = Field(
        None,
        description="Named gateways referenced by subject"
    )


class SampleResponse(BaseModel):
    """Single sample response."""
    sample: Sample = Field(..., description="Sample details")
    gateways: Optional[Dict[str, NamedGateway]] = Field(
        None,
        description="Named gateways referenced by sample"
    )


class FileResponse(BaseModel):
    """Single file response."""
    file: File = Field(..., description="File details")
    gateways: Optional[Dict[str, NamedGateway]] = Field(
        None,
        description="Named gateways referenced by file"
    )


class SubjectCountResponse(BaseModel):
    """Subject count by field response."""
    results: List[CountResult] = Field(..., description="Count results")


class SampleCountResponse(BaseModel):
    """Sample count by field response."""
    results: List[CountResult] = Field(..., description="Count results")


class FileCountResponse(BaseModel):
    """File count by field response."""
    results: List[CountResult] = Field(..., description="Count results")


class FieldDescriptionsResponse(BaseModel):
    """Field descriptions response."""
    fields: Dict[str, FieldDescription] = Field(
        ...,
        description="Available metadata fields"
    )


class MetadataFieldsResponse(BaseModel):
    """Metadata fields response."""
    harmonized: List[str] = Field(..., description="List of harmonized field names")
    unharmonized: List[str] = Field(..., description="List of unharmonized field names")


class NamespacesResponse(BaseModel):
    """Namespaces list response."""
    namespaces: List[Namespace] = Field(..., description="List of namespaces")


class NamespaceResponse(BaseModel):
    """Single namespace response."""
    namespace: Namespace = Field(..., description="Namespace details")


class OrganizationsResponse(BaseModel):
    """Organizations list response."""
    organizations: List[Organization] = Field(..., description="List of organizations")


class OrganizationResponse(BaseModel):
    """Single organization response."""
    organization: Organization = Field(..., description="Organization details")


class Information(BaseModel):
    """Server information model."""
    name: str = Field(..., description="Server name")
    version: str = Field(..., description="Server version")
    description: Optional[str] = None
    contact_email: str = Field(..., description="Contact email")


class InformationResponse(BaseModel):
    """Information response."""
    information: Information = Field(..., description="Server information")
