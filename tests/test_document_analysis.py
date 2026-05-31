from careshield.app import CareShieldAssistant
from careshield.ingestion import build_documents_from_text
from careshield.schemas import Role, Sensitivity, UserContext
from careshield.vector_store import InMemoryVectorStore


REPORT_TEXT = """
Care coordination report. External sharing requires approved de-identification.
Patient names, phone numbers, email addresses, medical record numbers, insurance
identifiers, and diagnosis details must be redacted before vendor sharing.
The approved model gateway must validate structured responses and keep audit traces.
"""


def test_vector_store_filters_by_policy_before_similarity_ranking() -> None:
    documents = build_documents_from_text(
        REPORT_TEXT,
        source_name="care-report.md",
        sensitivity=Sensitivity.clinical,
        max_words=35,
        overlap_words=5,
    )
    store = InMemoryVectorStore()
    store.add_documents(documents)

    nurse_docs = store.search(
        "What must be redacted before vendor sharing?",
        UserContext(role=Role.nurse),
    )
    vendor_docs = store.search(
        "What must be redacted before vendor sharing?",
        UserContext(role=Role.external_vendor),
    )

    assert nurse_docs
    assert vendor_docs == []


def test_document_analysis_runs_ingest_embed_retrieve_eval_flow() -> None:
    response = CareShieldAssistant().analyze_document(
        content=REPORT_TEXT.encode("utf-8"),
        source_name="care-report.md",
        role=Role.nurse,
        question="What must be redacted before vendor sharing?",
        sensitivity=Sensitivity.clinical,
    )

    assert response.ingestion.parser == "utf8-text"
    assert response.ingestion.indexed_vectors == response.ingestion.chunks
    assert response.citations
    assert response.eval.citations_present is True
    assert response.eval.pii_redacted is True
    assert "document_parse" in {event.step for event in response.trace}
    assert "vector_index" in {event.step for event in response.trace}
    assert "vector_retrieval" in {event.step for event in response.trace}
