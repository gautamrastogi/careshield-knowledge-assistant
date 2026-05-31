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

    model_config = pydantic.ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "role": "nurse",
                    "department": "care-operations",
                    "purpose": "synthetic_document_analysis",
                }
            ]
        }
    )

    role: Role
    department: str = pydantic.Field(default="care-operations", min_length=2)
    purpose: str = pydantic.Field(default="knowledge_assistance", min_length=2)


class Document(pydantic.BaseModel):
    """Knowledge document or document chunk available for retrieval."""

    model_config = pydantic.ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "id": "synthetic-care-report-chunk-1",
                    "title": "synthetic-care-report section 1",
                    "body": "Vendor sharing requires de-identification and approval.",
                    "sensitivity": "clinical",
                    "allowed_roles": ["doctor", "nurse", "compliance_officer"],
                    "tags": ["uploaded-report", "md"],
                }
            ]
        }
    )

    id: str = pydantic.Field(min_length=1)
    title: str = pydantic.Field(min_length=1)
    body: str = pydantic.Field(min_length=1)
    sensitivity: Sensitivity
    allowed_roles: list[Role] = pydantic.Field(min_length=1)
    tags: list[str] = pydantic.Field(default_factory=list)


class Evidence(pydantic.BaseModel):
    """Cited evidence returned with the final answer."""

    model_config = pydantic.ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "doc_id": "vendor-safe-summary",
                    "title": "Vendor Safe Summary",
                    "quote": "External vendors may receive only approved de-identified summaries.",
                    "sensitivity": "public",
                }
            ]
        }
    )

    doc_id: str = pydantic.Field(min_length=1)
    title: str = pydantic.Field(min_length=1)
    quote: str = pydantic.Field(min_length=1)
    sensitivity: Sensitivity


class IngestReport(pydantic.BaseModel):
    """Metadata proving what happened during document ingestion."""

    model_config = pydantic.ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "source_name": "synthetic-care-report.md",
                    "parser": "utf8-text",
                    "characters": 1022,
                    "chunks": 2,
                    "embedding_model": "local-hash-embedding-v1",
                    "embedding_dimensions": 64,
                    "indexed_vectors": 2,
                }
            ]
        }
    )

    source_name: str = pydantic.Field(min_length=1)
    parser: str = pydantic.Field(min_length=1)
    characters: int = pydantic.Field(ge=0)
    chunks: int = pydantic.Field(ge=0)
    embedding_model: str = pydantic.Field(min_length=1)
    embedding_dimensions: int = pydantic.Field(gt=0)
    indexed_vectors: int = pydantic.Field(ge=0)


class AskRequest(pydantic.BaseModel):
    """JSON request body for policy Q&A."""

    model_config = pydantic.ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "role": "nurse",
                    "question": "Can I send a patient discharge summary to an external vendor?",
                    "department": "care-operations",
                    "max_docs": 3,
                }
            ]
        }
    )

    role: Role
    question: str = pydantic.Field(min_length=5, max_length=1_000)
    department: str = pydantic.Field(default="care-operations", min_length=2)
    max_docs: int = pydantic.Field(default=3, ge=1, le=5)


class GatewayResult(pydantic.BaseModel):
    """Raw model gateway output before application-level validation."""

    provider: str = pydantic.Field(min_length=1)
    model: str = pydantic.Field(min_length=1)
    raw_answer: str = pydantic.Field(min_length=1)


class BedrockGatewayConfig(pydantic.BaseModel):
    """Configuration for the AWS Bedrock Converse gateway adapter."""

    model_config = pydantic.ConfigDict(
        frozen=True,
        json_schema_extra={
            "examples": [
                {
                    "region_name": "eu-central-1",
                    "model_id": "anthropic.claude-3-5-sonnet-20241022-v2:0",
                    "guardrail_identifier": "care-guardrail",
                    "guardrail_version": "1",
                    "max_tokens": 400,
                    "temperature": 0.0,
                }
            ]
        },
    )

    region_name: str = pydantic.Field(default="eu-central-1", min_length=3)
    model_id: str = pydantic.Field(min_length=3)
    guardrail_identifier: str | None = pydantic.Field(default=None, min_length=1)
    guardrail_version: str | None = pydantic.Field(default=None, min_length=1)
    max_tokens: int = pydantic.Field(default=400, ge=1, le=4_096)
    temperature: float = pydantic.Field(default=0.0, ge=0.0, le=1.0)

    @pydantic.model_validator(mode="after")
    def guardrail_requires_version(self) -> typing.Self:
        """Require guardrail identifier and version to be configured together.

        :return: The validated Bedrock gateway config.
        """
        if bool(self.guardrail_identifier) != bool(self.guardrail_version):
            raise ValueError("guardrail_identifier and guardrail_version must be set together")
        return self


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

    step: str = pydantic.Field(min_length=1)
    status: typing.Literal["ok", "blocked", "warning", "error"]
    detail: str = pydantic.Field(min_length=1)


class AnswerResponse(pydantic.BaseModel):
    """Validated response returned by Q&A and document analysis."""

    model_config = pydantic.ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "answer": (
                        "Only approved de-identified summaries may be shared. Sources: Vendor Safe Summary."
                    ),
                    "confidence": "high",
                    "citations": [
                        {
                            "doc_id": "vendor-safe-summary",
                            "title": "Vendor Safe Summary",
                            "quote": "External vendors may receive only approved de-identified summaries.",
                            "sensitivity": "public",
                        }
                    ],
                    "redactions": ["email"],
                    "eval": {
                        "citations_present": True,
                        "grounded": True,
                        "pii_redacted": True,
                        "policy_safe": True,
                        "score": 100,
                        "warnings": [],
                    },
                    "trace": [],
                    "provider": "mock",
                    "model": "deterministic-care-gateway-v1",
                }
            ]
        }
    )

    answer: str = pydantic.Field(min_length=1)
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
