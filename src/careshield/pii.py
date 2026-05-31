from __future__ import annotations

import re
from dataclasses import dataclass


PII_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("email", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")),
    ("phone", re.compile(r"\+?\d[\d\s().-]{7,}\d")),
    ("medical_record_number", re.compile(r"\bMRN[-\s]?[A-Z0-9-]+\b", re.IGNORECASE)),
    ("insurance_id", re.compile(r"\bINS[-\s][A-Z0-9-]+\b", re.IGNORECASE)),
    ("patient_name", re.compile(r"\bPatient\s+[A-Z][a-z]+\s+Example\b")),
    ("diagnosis", re.compile(r"\bdiagnosis[:\s]+(?!details\b)[^.,;]+", re.IGNORECASE)),
]


@dataclass(frozen=True)
class RedactionResult:
    text: str
    redactions: list[str]


def redact_pii(text: str) -> RedactionResult:
    redactions: list[str] = []
    redacted = text
    for label, pattern in PII_PATTERNS:
        if pattern.search(redacted):
            redactions.append(label)
            redacted = pattern.sub(f"[REDACTED_{label.upper()}]", redacted)
    return RedactionResult(text=redacted, redactions=sorted(set(redactions)))


def contains_pii(text: str) -> bool:
    return any(pattern.search(text) for _, pattern in PII_PATTERNS)
