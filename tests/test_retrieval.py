from careshield.data import DOCUMENTS
from careshield.retrieval import retrieve
from careshield.schemas import Role, UserContext


def test_retrieval_prefilters_by_role_before_scoring() -> None:
    context = UserContext(role=Role.external_vendor)
    docs = retrieve("Can I receive a patient discharge summary?", context, DOCUMENTS)
    assert [doc.id for doc in docs] == ["vendor-safe-summary"]


def test_nurse_vendor_question_retrieves_redaction_guidance() -> None:
    context = UserContext(role=Role.nurse)
    docs = retrieve("Can I send a patient discharge summary to an external vendor?", context, DOCUMENTS)
    ids = {doc.id for doc in docs}
    assert "patient-summary-redaction-guide" in ids
    assert "clinical-access-policy" in ids
