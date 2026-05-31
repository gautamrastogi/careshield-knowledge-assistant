import careshield.retrieval.data as data
import careshield.retrieval.keyword as keyword
from careshield import contracts


def test_retrieval_prefilters_by_role_before_scoring() -> None:
    """Verify policy filtering runs before keyword ranking."""
    context = contracts.schema.UserContext(role=contracts.schema.Role.external_vendor)
    docs = keyword.retrieve(
        question="Can I receive a patient discharge summary?",
        context=context,
        documents=data.DOCUMENTS,
    )
    assert [doc.id for doc in docs] == ["vendor-safe-summary"]


def test_nurse_vendor_question_retrieves_redaction_guidance() -> None:
    """Verify a nurse retrieves clinical and redaction guidance."""
    context = contracts.schema.UserContext(role=contracts.schema.Role.nurse)
    docs = keyword.retrieve(
        question="Can I send a patient discharge summary to an external vendor?",
        context=context,
        documents=data.DOCUMENTS,
    )
    ids = {doc.id for doc in docs}
    assert "patient-summary-redaction-guide" in ids
    assert "clinical-access-policy" in ids
