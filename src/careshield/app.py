from __future__ import annotations

from careshield.data import DOCUMENTS
from careshield.embeddings import HashEmbeddingModel
from careshield.evals import evaluate_answer
from careshield.gateway import MockModelGateway
from careshield.ingestion import build_documents_from_text, parse_document_bytes
from careshield.pii import redact_pii
from careshield.retrieval import retrieve, to_evidence, tokenize
from careshield.schemas import (
    AnswerResponse,
    AskRequest,
    Document,
    DocumentAnalysisResponse,
    Evidence,
    IngestReport,
    Role,
    Sensitivity,
    UserContext,
)
from careshield.tracing import Trace
from careshield.vector_store import InMemoryVectorStore


class CareShieldAssistant:
    def __init__(
        self,
        gateway: MockModelGateway | None = None,
        embedding_model: HashEmbeddingModel | None = None,
    ) -> None:
        self.gateway = gateway or MockModelGateway()
        self.embedding_model = embedding_model or HashEmbeddingModel()

    def ask(self, request: AskRequest) -> AnswerResponse:
        trace = Trace()
        trace.add("request", "ok", f"received question for role={request.role}")

        context = UserContext(
            role=request.role,
            department=request.department,
            purpose="synthetic_healthcare_policy_qa",
        )
        trace.add("auth_context", "ok", f"context role={context.role}")

        documents = retrieve(
            request.question,
            context,
            DOCUMENTS,
            max_docs=request.max_docs,
        )
        trace.add(
            "policy_retrieval",
            "ok" if documents else "blocked",
            f"retrieved {len(documents)} authorized document(s)",
        )
        return self._answer_from_documents(request.question, documents, trace)

    def analyze_document(
        self,
        content: bytes,
        source_name: str,
        role: Role,
        question: str,
        sensitivity: Sensitivity = Sensitivity.clinical,
        department: str = "care-operations",
        max_docs: int = 3,
    ) -> DocumentAnalysisResponse:
        trace = Trace()
        trace.add("request", "ok", f"received document={source_name} role={role}")

        parsed = parse_document_bytes(content, source_name)
        trace.add("document_parse", "ok", f"parser={parsed.parser} characters={len(parsed.text)}")

        documents = build_documents_from_text(
            parsed.text,
            source_name=source_name,
            sensitivity=sensitivity,
        )
        trace.add("chunking", "ok", f"chunks={len(documents)} sensitivity={sensitivity}")

        vector_store = InMemoryVectorStore(embedding_model=self.embedding_model)
        vector_store.add_documents(documents)
        trace.add(
            "vector_index",
            "ok",
            f"model={self.embedding_model.name} dimensions={self.embedding_model.dimensions}",
        )

        context = UserContext(
            role=role,
            department=department,
            purpose="synthetic_document_analysis",
        )
        trace.add("auth_context", "ok", f"context role={context.role}")

        retrieved = vector_store.search(question, context, max_docs=max_docs)
        trace.add(
            "vector_retrieval",
            "ok" if retrieved else "blocked",
            f"retrieved {len(retrieved)} authorized chunk(s)",
        )

        ingestion = IngestReport(
            source_name=source_name,
            parser=parsed.parser,
            characters=len(parsed.text),
            chunks=len(documents),
            embedding_model=self.embedding_model.name,
            embedding_dimensions=self.embedding_model.dimensions,
            indexed_vectors=vector_store.size,
        )
        answer = self._answer_from_documents(question, retrieved, trace)
        return DocumentAnalysisResponse(**answer.model_dump(mode="python"), ingestion=ingestion)

    def _answer_from_documents(
        self,
        question: str,
        documents: list[Document],
        trace: Trace,
    ) -> AnswerResponse:
        citations: list[Evidence] = []
        redactions: set[str] = set()
        for document in documents:
            redacted_body = redact_pii(document.body)
            redactions.update(redacted_body.redactions)
            quote = _select_relevant_quote(redacted_body.text, question)
            citations.append(to_evidence(document, quote=quote))
        trace.add("pii_redaction", "ok", f"redactions={sorted(redactions) or ['none']}")

        gateway_result = self.gateway.generate(question, citations)
        trace.add(
            "model_gateway",
            "ok",
            f"provider={gateway_result.provider} model={gateway_result.model}",
        )

        answer_redaction = redact_pii(gateway_result.raw_answer)
        redactions.update(answer_redaction.redactions)
        eval_report = evaluate_answer(
            answer=answer_redaction.text,
            evidence=citations,
            redactions=sorted(redactions),
        )
        trace.add("evals", "ok" if eval_report.score >= 75 else "warning", f"score={eval_report.score}")

        confidence = "high" if eval_report.score >= 90 else "medium" if eval_report.score >= 60 else "low"
        response = AnswerResponse(
            answer=answer_redaction.text,
            confidence=confidence,
            citations=citations,
            redactions=sorted(redactions),
            eval=eval_report,
            trace=trace.events,
            provider=gateway_result.provider,
            model=gateway_result.model,
        )
        trace.add("schema_validation", "ok", "response passed Pydantic validation")
        response.trace = trace.events
        return response


def _select_relevant_quote(text: str, question: str) -> str:
    question_terms = tokenize(question)
    sentences = [sentence.strip() for sentence in text.split(". ") if sentence.strip()]
    if not sentences:
        return text[:240].strip()
    scored = [
        (len(question_terms & tokenize(sentence)), index, sentence)
        for index, sentence in enumerate(sentences)
    ]
    scored.sort(key=lambda item: (item[0], -item[1]), reverse=True)
    return scored[0][2][:240].strip()
