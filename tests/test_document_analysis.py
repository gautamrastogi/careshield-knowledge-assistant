import careshield.pipeline.assistant as assistant_service
import careshield.retrieval.embeddings as embeddings
import careshield.retrieval.ingestion as ingestion
import careshield.retrieval.vector_store as vector_store
from careshield import contracts

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
        sensitivity=contracts.schema.Sensitivity.clinical,
        max_words=35,
        overlap_words=5,
    )
    store = vector_store.InMemoryVectorStore()
    store.add_documents(documents=documents)

    nurse_docs = store.search(
        query="What must be redacted before vendor sharing?",
        context=contracts.schema.UserContext(role=contracts.schema.Role.nurse),
    )
    vendor_docs = store.search(
        query="What must be redacted before vendor sharing?",
        context=contracts.schema.UserContext(role=contracts.schema.Role.external_vendor),
    )

    assert nurse_docs
    assert vendor_docs == []


def test_chroma_vector_store_filters_by_role_and_sensitivity() -> None:
    """Verify Chroma metadata filters still respect the policy layer."""
    documents = ingestion.build_documents_from_text(
        text=REPORT_TEXT,
        source_name="care-report.md",
        sensitivity=contracts.schema.Sensitivity.clinical,
        max_words=35,
        overlap_words=5,
    )
    store = vector_store.build_vector_store(
        backend="chroma",
        embedding_model=embeddings.HashEmbeddingModel(),
    )
    store.add_documents(documents=documents)

    vendor_docs = store.search(
        query="What must be redacted before vendor sharing?",
        context=contracts.schema.UserContext(role=contracts.schema.Role.external_vendor),
    )

    assert vendor_docs == []


def test_document_analysis_runs_ingest_embed_retrieve_eval_flow() -> None:
    """Verify the full upload analysis pipeline."""
    response = assistant_service.CareShieldAssistant().analyze_document(
        content=REPORT_TEXT.encode("utf-8"),
        source_name="care-report.md",
        role=contracts.schema.Role.nurse,
        question="What must be redacted before vendor sharing?",
        sensitivity=contracts.schema.Sensitivity.clinical,
    )

    assert response.ingestion.parser == "utf8-text"
    assert response.ingestion.indexed_vectors == response.ingestion.chunks
    assert response.citations
    assert response.eval.citations_present is True
    assert response.eval.pii_redacted is True
    assert "document_parse" in {event.step for event in response.trace}
    assert "vector_index" in {event.step for event in response.trace}
    assert "vector_retrieval" in {event.step for event in response.trace}
