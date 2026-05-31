import careshield.contracts.schemas as schemas
import careshield.pipeline.assistant as assistant_service
import careshield.retrieval.ingestion as ingestion
import careshield.retrieval.vector_store as vector_store


REPORT_TEXT = """
Care coordination report. External sharing requires approved de-identification.
Patient names, phone numbers, email addresses, medical record numbers, insurance
identifiers, and diagnosis details must be redacted before vendor sharing.
The approved model gateway must validate structured responses and keep audit traces.
"""


def test_vector_store_filters_by_policy_before_similarity_ranking() -> None:
    """Verify unauthorized chunks are filtered before vector ranking."""
    documents = ingestion.build_documents_from_text(
        text=REPORT_TEXT,
        source_name="care-report.md",
        sensitivity=schemas.Sensitivity.clinical,
        max_words=35,
        overlap_words=5,
    )
    store = vector_store.InMemoryVectorStore()
    store.add_documents(documents=documents)

    nurse_docs = store.search(
        query="What must be redacted before vendor sharing?",
        context=schemas.UserContext(role=schemas.Role.nurse),
    )
    vendor_docs = store.search(
        query="What must be redacted before vendor sharing?",
        context=schemas.UserContext(role=schemas.Role.external_vendor),
    )

    assert nurse_docs
    assert vendor_docs == []


def test_document_analysis_runs_ingest_embed_retrieve_eval_flow() -> None:
    """Verify the full upload analysis pipeline."""
    response = assistant_service.CareShieldAssistant().analyze_document(
        content=REPORT_TEXT.encode("utf-8"),
        source_name="care-report.md",
        role=schemas.Role.nurse,
        question="What must be redacted before vendor sharing?",
        sensitivity=schemas.Sensitivity.clinical,
    )

    assert response.ingestion.parser == "utf8-text"
    assert response.ingestion.indexed_vectors == response.ingestion.chunks
    assert response.citations
    assert response.eval.citations_present is True
    assert response.eval.pii_redacted is True
    assert "document_parse" in {event.step for event in response.trace}
    assert "vector_index" in {event.step for event in response.trace}
    assert "vector_retrieval" in {event.step for event in response.trace}
