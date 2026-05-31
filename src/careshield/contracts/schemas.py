import enum
import typing

import pydantic


class Role(enum.StrEnum):
    """Supported synthetic user roles."""

    doctor = "doctor"
    nurse = "nurse"
    billing_analyst = "billing_analyst"
    vendor_manager = "vendor_manager"
    external_vendor = "external_vendor"
    compliance_officer = "compliance_officer"


class Sensitivity(enum.StrEnum):
    """Document sensitivity labels used by the policy layer."""

    public = "public"
    internal = "internal"
    clinical = "clinical"
    billing = "billing"
    restricted = "restricted"


class UserContext(pydantic.BaseModel):
    """Request context derived from the caller."""

    role: Role
    department: str = "care-operations"
    purpose: str = "knowledge_assistance"


class Document(pydantic.BaseModel):
    """Knowledge document or document chunk available for retrieval."""

    id: str
    title: str
    body: str
    sensitivity: Sensitivity
    allowed_roles: list[Role]
    tags: list[str] = pydantic.Field(default_factory=list)


class Evidence(pydantic.BaseModel):
    """Cited evidence returned with the final answer."""

    doc_id: str
    title: str
    quote: str
    sensitivity: Sensitivity


class IngestReport(pydantic.BaseModel):
    """Metadata proving what happened during document ingestion."""

    source_name: str
    parser: str
    characters: int = pydantic.Field(ge=0)
    chunks: int = pydantic.Field(ge=0)
    embedding_model: str
    embedding_dimensions: int = pydantic.Field(gt=0)
    indexed_vectors: int = pydantic.Field(ge=0)


class AskRequest(pydantic.BaseModel):
    """JSON request body for policy Q&A."""

    role: Role
    question: str = pydantic.Field(min_length=5, max_length=1_000)
    department: str = "care-operations"
    max_docs: int = pydantic.Field(default=3, ge=1, le=5)


class GatewayResult(pydantic.BaseModel):
    """Raw model gateway output before application-level validation."""

    provider: str
    model: str
    raw_answer: str


class EvalReport(pydantic.BaseModel):
    """Deterministic quality and safety checks for an answer."""

    citations_present: bool
    grounded: bool
    pii_redacted: bool
    policy_safe: bool
    score: int = pydantic.Field(ge=0, le=100)
    warnings: list[str] = pydantic.Field(default_factory=list)


class TraceEvent(pydantic.BaseModel):
    """Single audit/debug event from the request pipeline."""

    step: str
    status: typing.Literal["ok", "blocked", "warning", "error"]
    detail: str


class AnswerResponse(pydantic.BaseModel):
    """Validated response returned by Q&A and document analysis."""

    answer: str
    confidence: typing.Literal["low", "medium", "high"]
    citations: list[Evidence]
    redactions: list[str]
    eval: EvalReport
    trace: list[TraceEvent]
    provider: str
    model: str

    @pydantic.model_validator(mode="after")
    def high_confidence_requires_evidence(self) -> typing.Self:
        """Ensure high-confidence answers cannot be uncited.

        :return: The validated response model.
        """
        if self.confidence == "high" and not self.citations:
            raise ValueError("high confidence answers require at least one citation")
        return self


class DocumentAnalysisResponse(AnswerResponse):
    """Response returned by the upload/document analysis endpoint."""

    ingestion: IngestReport
