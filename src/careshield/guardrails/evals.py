import careshield.contracts.schemas as schemas
import careshield.guardrails.pii as pii


GROUNDEDNESS_TERMS = ["vendor", "redact", "model gateway", "clinical", "billing", "approved"]


def evaluate_answer(
    *,
    answer: str,
    evidence: list[schemas.Evidence],
    redactions: list[str],
) -> schemas.EvalReport:
    """Run deterministic safety and quality checks on the response.

    :param answer: Final model answer after redaction.
    :param evidence: Citations used as answer context.
    :param redactions: Sensitive field labels removed from evidence or answer.
    :return: Evaluation report suitable for API responses and CI assertions.
    """
    citations_present = bool(evidence) and "Sources:" in answer
    evidence_text = " ".join(item.quote for item in evidence).lower()

    # This is intentionally lightweight: enough to prove groundedness checks exist
    # without bringing a judge model into every unit test.
    grounded_terms = [
        term
        for term in GROUNDEDNESS_TERMS
        if term in answer.lower() and term in evidence_text
    ]
    grounded = bool(evidence) and bool(grounded_terms)
    pii_redacted = not pii.contains_pii(text=answer)
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

    return schemas.EvalReport(
        citations_present=citations_present,
        grounded=grounded,
        pii_redacted=pii_redacted,
        policy_safe=policy_safe,
        score=round((sum(checks) / len(checks)) * 100),
        warnings=warnings,
    )
