import careshield.contracts.schemas as schemas
import careshield.guardrails.evals as evals
import careshield.guardrails.pii as pii
import careshield.pipeline.gateway as gateway
import careshield.pipeline.tracing as tracing
import careshield.retrieval.data as data
import careshield.retrieval.embeddings as embeddings
import careshield.retrieval.ingestion as ingestion
import careshield.retrieval.keyword as keyword
import careshield.retrieval.vector_store as vector_store


class CareShieldAssistant:
    """Application service that orchestrates the governed GenAI flow."""

    def __init__(
        self,
        *,
        model_gateway: gateway.MockModelGateway | None = None,
        embedding_model: embeddings.HashEmbeddingModel | None = None,
    ) -> None:
        """Create the assistant service.

        :param model_gateway: Gateway adapter for model calls.
        :param embedding_model: Embedding adapter for uploaded documents.
        """
        self.model_gateway = model_gateway or gateway.MockModelGateway()
        self.embedding_model = embedding_model or embeddings.HashEmbeddingModel()

    def ask(self, *, request: schemas.AskRequest) -> schemas.AnswerResponse:
        """Answer a question using built-in synthetic policy documents.

        :param request: Validated Q&A request.
        :return: Structured answer with citations, evals, and trace events.
        """
        trace = tracing.Trace()
        trace.add(step="request", status="ok", detail=f"received question for role={request.role}")

        context = schemas.UserContext(
            role=request.role,
            department=request.department,
            purpose="synthetic_healthcare_policy_qa",
        )
        trace.add(step="auth_context", status="ok", detail=f"context role={context.role}")

        # Built-in policy Q&A uses deterministic keyword retrieval. Uploaded
        # documents use the vector path in analyze_document.
        documents = keyword.retrieve(
            question=request.question,
            context=context,
            documents=data.DOCUMENTS,
            max_docs=request.max_docs,
        )
        trace.add(
            step="policy_retrieval",
            status="ok" if documents else "blocked",
            detail=f"retrieved {len(documents)} authorized document(s)",
        )
        return self._answer_from_documents(question=request.question, documents=documents, trace=trace)

    def analyze_document(
        self,
        *,
        content: bytes,
        source_name: str,
        role: schemas.Role,
        question: str,
        sensitivity: schemas.Sensitivity = schemas.Sensitivity.clinical,
        department: str = "care-operations",
        max_docs: int = 3,
    ) -> schemas.DocumentAnalysisResponse:
        """Analyze an uploaded document through the RAG pipeline.

        :param content: Raw uploaded file bytes.
        :param source_name: Original file name.
        :param role: Caller role used by the policy filter.
        :param question: Analysis question.
        :param sensitivity: Sensitivity assigned to uploaded chunks.
        :param department: Caller department.
        :param max_docs: Maximum chunks to retrieve.
        :return: Structured answer plus ingestion metadata.
        """
        trace = tracing.Trace()
        trace.add(step="request", status="ok", detail=f"received document={source_name} role={role}")

        parsed = ingestion.parse_document_bytes(content=content, source_name=source_name)
        trace.add(
            step="document_parse",
            status="ok",
            detail=f"parser={parsed.parser} characters={len(parsed.text)}",
        )

        documents = ingestion.build_documents_from_text(
            text=parsed.text,
            source_name=source_name,
            sensitivity=sensitivity,
        )
        trace.add(step="chunking", status="ok", detail=f"chunks={len(documents)} sensitivity={sensitivity}")

        store = vector_store.InMemoryVectorStore(embedding_model=self.embedding_model)
        store.add_documents(documents=documents)
        trace.add(
            step="vector_index",
            status="ok",
            detail=f"model={self.embedding_model.name} dimensions={self.embedding_model.dimensions}",
        )

        context = schemas.UserContext(
            role=role,
            department=department,
            purpose="synthetic_document_analysis",
        )
        trace.add(step="auth_context", status="ok", detail=f"context role={context.role}")

        retrieved = store.search(query=question, context=context, max_docs=max_docs)
        trace.add(
            step="vector_retrieval",
            status="ok" if retrieved else "blocked",
            detail=f"retrieved {len(retrieved)} authorized chunk(s)",
        )

        ingest_report = schemas.IngestReport(
            source_name=source_name,
            parser=parsed.parser,
            characters=len(parsed.text),
            chunks=len(documents),
            embedding_model=self.embedding_model.name,
            embedding_dimensions=self.embedding_model.dimensions,
            indexed_vectors=store.size,
        )
        answer = self._answer_from_documents(question=question, documents=retrieved, trace=trace)
        return schemas.DocumentAnalysisResponse(**answer.model_dump(mode="python"), ingestion=ingest_report)

    def _answer_from_documents(
        self,
        *,
        question: str,
        documents: list[schemas.Document],
        trace: tracing.Trace,
    ) -> schemas.AnswerResponse:
        """Run redaction, model gateway, validation, and evals.

        :param question: User question.
        :param documents: Authorized documents or chunks.
        :param trace: Mutable trace collector.
        :return: Structured answer response.
        """
        citations: list[schemas.Evidence] = []
        redactions: set[str] = set()

        for document in documents:
            redacted_body = pii.redact_pii(text=document.body)
            redactions.update(redacted_body.redactions)
            quote = _select_relevant_quote(text=redacted_body.text, question=question)
            citations.append(keyword.to_evidence(document=document, quote=quote))

        trace.add(step="pii_redaction", status="ok", detail=f"redactions={sorted(redactions) or ['none']}")

        gateway_result = self.model_gateway.generate(question=question, evidence=citations)
        trace.add(
            step="model_gateway",
            status="ok",
            detail=f"provider={gateway_result.provider} model={gateway_result.model}",
        )

        answer_redaction = pii.redact_pii(text=gateway_result.raw_answer)
        redactions.update(answer_redaction.redactions)
        eval_report = evals.evaluate_answer(
            answer=answer_redaction.text,
            evidence=citations,
            redactions=sorted(redactions),
        )
        trace.add(
            step="evals",
            status="ok" if eval_report.score >= 75 else "warning",
            detail=f"score={eval_report.score}",
        )

        confidence = _confidence_from_score(score=eval_report.score)
        response = schemas.AnswerResponse(
            answer=answer_redaction.text,
            confidence=confidence,
            citations=citations,
            redactions=sorted(redactions),
            eval=eval_report,
            trace=trace.events,
            provider=gateway_result.provider,
            model=gateway_result.model,
        )
        trace.add(step="schema_validation", status="ok", detail="response passed Pydantic validation")
        response.trace = trace.events
        return response


def _confidence_from_score(*, score: int) -> str:
    """Convert evaluation score into response confidence.

    :param score: Evaluation score from 0 to 100.
    :return: Confidence label.
    """
    if score >= 90:
        return "high"
    if score >= 60:
        return "medium"
    return "low"


def _select_relevant_quote(*, text: str, question: str) -> str:
    """Select the sentence with the strongest overlap with the question.

    :param text: Redacted evidence body.
    :param question: User question.
    :return: Short quote to use as citation evidence.
    """
    question_terms = keyword.tokenize(text=question)
    sentences = [sentence.strip() for sentence in text.split(". ") if sentence.strip()]
    if not sentences:
        return text[:240].strip()

    scored = [
        (len(question_terms & keyword.tokenize(text=sentence)), index, sentence)
        for index, sentence in enumerate(sentences)
    ]
    scored.sort(key=lambda item: (item[0], -item[1]), reverse=True)
    return scored[0][2][:240].strip()
