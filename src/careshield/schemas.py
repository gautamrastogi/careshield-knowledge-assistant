from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class Role(StrEnum):
    doctor = "doctor"
    nurse = "nurse"
    billing_analyst = "billing_analyst"
    vendor_manager = "vendor_manager"
    external_vendor = "external_vendor"
    compliance_officer = "compliance_officer"


class Sensitivity(StrEnum):
    public = "public"
    internal = "internal"
    clinical = "clinical"
    billing = "billing"
    restricted = "restricted"


class UserContext(BaseModel):
    role: Role
    department: str = "care-operations"
    purpose: str = "knowledge_assistance"


class Document(BaseModel):
    id: str
    title: str
    body: str
    sensitivity: Sensitivity
    allowed_roles: list[Role]
    tags: list[str] = Field(default_factory=list)


class Evidence(BaseModel):
    doc_id: str
    title: str
    quote: str
    sensitivity: Sensitivity


class AskRequest(BaseModel):
    role: Role
    question: str = Field(min_length=5, max_length=1_000)
    department: str = "care-operations"
    max_docs: int = Field(default=3, ge=1, le=5)


class GatewayResult(BaseModel):
    provider: str
    model: str
    raw_answer: str


class EvalReport(BaseModel):
    citations_present: bool
    grounded: bool
    pii_redacted: bool
    policy_safe: bool
    score: int = Field(ge=0, le=100)
    warnings: list[str] = Field(default_factory=list)


class TraceEvent(BaseModel):
    step: str
    status: Literal["ok", "blocked", "warning", "error"]
    detail: str


class AnswerResponse(BaseModel):
    answer: str
    confidence: Literal["low", "medium", "high"]
    citations: list[Evidence]
    redactions: list[str]
    eval: EvalReport
    trace: list[TraceEvent]
    provider: str
    model: str

    @model_validator(mode="after")
    def high_confidence_requires_evidence(self) -> "AnswerResponse":
        if self.confidence == "high" and not self.citations:
            raise ValueError("high confidence answers require at least one citation")
        return self
