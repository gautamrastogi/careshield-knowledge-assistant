from __future__ import annotations

from careshield.pii import contains_pii
from careshield.schemas import EvalReport, Evidence


def evaluate_answer(
    answer: str,
    evidence: list[Evidence],
    redactions: list[str],
) -> EvalReport:
    citations_present = bool(evidence) and "Sources:" in answer
    evidence_text = " ".join(item.quote for item in evidence).lower()
    grounded_terms = [
        term
        for term in ["vendor", "redact", "model gateway", "clinical", "billing", "approved"]
        if term in answer.lower() and term in evidence_text
    ]
    grounded = bool(evidence) and bool(grounded_terms)
    pii_redacted = not contains_pii(answer)
    policy_safe = bool(evidence)
    checks = [citations_present, grounded, pii_redacted, policy_safe]
    warnings: list[str] = []
    if not citations_present:
        warnings.append("answer is missing source citations")
    if not grounded:
        warnings.append("answer has weak grounding against retrieved evidence")
    if not pii_redacted:
        warnings.append("answer contains unredacted sensitive data")
    if not policy_safe:
        warnings.append("no authorized evidence was used")
    if redactions:
        warnings.append(f"redacted sensitive fields: {', '.join(redactions)}")
    return EvalReport(
        citations_present=citations_present,
        grounded=grounded,
        pii_redacted=pii_redacted,
        policy_safe=policy_safe,
        score=round((sum(checks) / len(checks)) * 100),
        warnings=warnings,
    )
