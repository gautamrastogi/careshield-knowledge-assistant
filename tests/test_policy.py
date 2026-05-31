import careshield.contracts.schemas as schemas
import careshield.guardrails.policy as policy
import careshield.retrieval.data as data


def test_external_vendor_can_only_retrieve_public_documents() -> None:
    """Verify external vendors only receive public documents."""
    context = schemas.UserContext(role=schemas.Role.external_vendor)
    docs = policy.filter_allowed_documents(context=context, documents=data.DOCUMENTS)
    assert {doc.sensitivity.value for doc in docs} == {"public"}
    assert {doc.id for doc in docs} == {"vendor-safe-summary"}


def test_nurse_cannot_access_billing_policy() -> None:
    """Verify clinical roles do not receive billing-only policy."""
    context = schemas.UserContext(role=schemas.Role.nurse)
    docs = policy.filter_allowed_documents(context=context, documents=data.DOCUMENTS)
    assert "billing-data-policy" not in {doc.id for doc in docs}
