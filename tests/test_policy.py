from careshield.data import DOCUMENTS
from careshield.policy import filter_allowed_documents
from careshield.schemas import Role, UserContext


def test_external_vendor_can_only_retrieve_public_documents() -> None:
    context = UserContext(role=Role.external_vendor)
    docs = filter_allowed_documents(context, DOCUMENTS)
    assert {doc.sensitivity.value for doc in docs} == {"public"}
    assert {doc.id for doc in docs} == {"vendor-safe-summary"}


def test_nurse_cannot_access_billing_policy() -> None:
    context = UserContext(role=Role.nurse)
    docs = filter_allowed_documents(context, DOCUMENTS)
    assert "billing-data-policy" not in {doc.id for doc in docs}
