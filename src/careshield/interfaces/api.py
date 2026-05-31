import fastapi

import careshield
import careshield.pipeline.assistant as assistant_service
import careshield.retrieval.ingestion as ingestion
from careshield import contracts

app = fastapi.FastAPI(
    title="CareShield Knowledge Assistant",
    version=careshield.__version__,
    description=(
        "Public-safe synthetic healthcare GenAI/RAG learning app with policy-aware "
        "document ingestion, vector retrieval, PII redaction, structured "
        "outputs, evals, and traces."
    ),
)
assistant = assistant_service.CareShieldAssistant()


@app.get("/health")
def health() -> dict[str, str]:
    """Return service health metadata.

    :return: Health status and application version.
    """
    return {"status": "ok", "version": careshield.__version__}


@app.post("/ask", response_model=contracts.schema.AnswerResponse)
def ask(*, request: contracts.schema.AskRequest) -> contracts.schema.AnswerResponse:
    """Answer a policy question from built-in synthetic documents.

    :param request: Validated JSON request body.
    :return: Structured answer with citations, evals, and trace events.
    """
    return assistant.ask(request=request)


@app.post("/documents/analyze", response_model=contracts.schema.DocumentAnalysisResponse)
async def analyze_document(
    *,
    file: fastapi.UploadFile = fastapi.File(...),
    role: contracts.schema.Role = fastapi.Form(contracts.schema.Role.compliance_officer),
    question: str = fastapi.Form(..., min_length=5, max_length=1_000),
    sensitivity: contracts.schema.Sensitivity = fastapi.Form(contracts.schema.Sensitivity.clinical),
    vector_backend: str = fastapi.Form("chroma", pattern="^(chroma|memory)$"),
    max_docs: int = fastapi.Form(3, ge=1, le=5),
) -> contracts.schema.DocumentAnalysisResponse:
    """Analyze an uploaded report-like document.

    :param file: Uploaded TXT, Markdown, PDF, or DOCX file.
    :param role: Caller role used for policy filtering.
    :param question: Analysis question.
    :param sensitivity: Sensitivity assigned to uploaded chunks.
    :param vector_backend: Vector store backend for uploaded documents.
    :param max_docs: Maximum chunks to retrieve.
    :return: Structured answer plus ingestion metadata.
    """
    content = await file.read()
    try:
        document_assistant = assistant_service.CareShieldAssistant(vector_backend=vector_backend)
        return document_assistant.analyze_document(
            content=content,
            source_name=file.filename or "uploaded-document.txt",
            role=role,
            question=question,
            sensitivity=sensitivity,
            max_docs=max_docs,
        )
    except ingestion.DocumentParseError as exc:
        raise fastapi.HTTPException(status_code=422, detail=str(exc)) from exc
