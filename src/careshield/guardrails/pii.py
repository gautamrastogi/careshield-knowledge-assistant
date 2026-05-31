import dataclasses
import re


PII_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("email", re.compile(pattern=r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")),
    ("phone", re.compile(pattern=r"\+?\d[\d\s().-]{7,}\d")),
    ("medical_record_number", re.compile(pattern=r"\bMRN[-\s]?[A-Z0-9-]+\b", flags=re.IGNORECASE)),
    ("insurance_id", re.compile(pattern=r"\bINS[-\s][A-Z0-9-]+\b", flags=re.IGNORECASE)),
    ("patient_name", re.compile(pattern=r"\bPatient\s+[A-Z][a-z]+\s+Example\b")),
    ("diagnosis", re.compile(pattern=r"\bdiagnosis[:\s]+(?!details\b)[^.,;]+", flags=re.IGNORECASE)),
]


@dataclasses.dataclass(frozen=True)
class RedactionResult:
    """Text plus the synthetic sensitive fields that were redacted."""

    text: str
    redactions: list[str]


def redact_pii(*, text: str) -> RedactionResult:
    """Redact deterministic synthetic PII/PHI markers.

    :param text: Text that may contain synthetic sensitive identifiers.
    :return: Redacted text and the labels that were replaced.
    """
    redactions: list[str] = []
    redacted = text

    # Keep redaction deterministic so tests and CI do not depend on a model.
    for label, pattern in PII_PATTERNS:
        if pattern.search(string=redacted):
            redactions.append(label)
            redacted = pattern.sub(repl=f"[REDACTED_{label.upper()}]", string=redacted)

    return RedactionResult(text=redacted, redactions=sorted(set(redactions)))


def contains_pii(*, text: str) -> bool:
    """Check whether text still contains known synthetic sensitive fields.

    :param text: Text to inspect after redaction.
    :return: Whether any configured synthetic PII pattern is still present.
    """
    return any(pattern.search(string=text) for _, pattern in PII_PATTERNS)
