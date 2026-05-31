from careshield.app import CareShieldAssistant
from careshield.schemas import AskRequest, Role


def test_assistant_returns_structured_cited_answer_for_nurse() -> None:
    response = CareShieldAssistant().ask(
        AskRequest(
            role=Role.nurse,
            question="Can I send a patient discharge summary to an external vendor?",
        )
    )
    assert response.provider == "mock"
    assert response.citations
    assert response.eval.citations_present is True
    assert response.eval.pii_redacted is True
    assert "external vendors" in response.answer
    assert "patient-summary-redaction-guide" in {item.doc_id for item in response.citations}


def test_external_vendor_answer_uses_only_public_source() -> None:
    response = CareShieldAssistant().ask(
        AskRequest(
            role=Role.external_vendor,
            question="Can I receive patient summaries?",
        )
    )
    assert {item.doc_id for item in response.citations} == {"vendor-safe-summary"}
    assert all(item.sensitivity.value == "public" for item in response.citations)
