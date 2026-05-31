import careshield.contracts.schemas as schemas
import careshield.guardrails.evals as evals


def test_eval_flags_missing_citations_and_weak_grounding() -> None:
    """Verify evals fail uncited answers."""
    report = evals.evaluate_answer(
        answer="This answer has no sources.",
        evidence=[],
        redactions=[],
    )
    assert report.citations_present is False
    assert report.policy_safe is False
    assert report.score < 75


def test_eval_passes_grounded_redacted_answer() -> None:
    """Verify evals pass cited and redacted answers."""
    evidence = [
        schemas.Evidence(
            doc_id="vendor-safe-summary",
            title="Vendor Safe Summary",
            quote="External vendors may receive only approved de-identified summaries.",
            sensitivity=schemas.Sensitivity.public,
        )
    ]
    report = evals.evaluate_answer(
        answer=(
            "Only approved de-identified summaries may be shared with vendors. "
            "Sources: Vendor Safe Summary."
        ),
        evidence=evidence,
        redactions=["email"],
    )
    assert report.citations_present is True
    assert report.pii_redacted is True
    assert report.policy_safe is True
