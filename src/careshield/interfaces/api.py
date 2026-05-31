import fastapi

import careshield
import careshield.contracts.schemas as schemas
import careshield.pipeline.assistant as assistant_service
import careshield.retrieval.ingestion as ingestion


app = fastapi.FastAPI(
    title="CareShield Knowledge Assistant",
    version=careshield.__version__,
    description=(
        "Public-safe synthetic healthcare GenAI/RAG demo with policy-aware "
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


@app.post("/ask", response_model=schemas.AnswerResponse)
def ask(*, request: schemas.AskRequest) -> schemas.AnswerResponse:
    """Answer a policy question from built-in synthetic documents.

    :param request: Validated JSON request body.
    :return: Structured answer with citations, evals, and trace events.
    """
    return assistant.ask(request=request)


@app.post("/documents/analyze", response_model=schemas.DocumentAnalysisResponse)
async def analyze_document(
    *,
    file: fastapi.UploadFile = fastapi.File(...),
    role: schemas.Role = fastapi.Form(schemas.Role.compliance_officer),
    question: str = fastapi.Form(..., min_length=5, max_length=1_000),
    sensitivity: schemas.Sensitivity = fastapi.Form(schemas.Sensitivity.clinical),
    max_docs: int = fastapi.Form(3, ge=1, le=5),
) -> schemas.DocumentAnalysisResponse:
    """Analyze an uploaded report-like document.

    :param file: Uploaded TXT, Markdown, PDF, or DOCX file.
    :param role: Caller role used for policy filtering.
    :param question: Analysis question.
    :param sensitivity: Sensitivity assigned to uploaded chunks.
    :param max_docs: Maximum chunks to retrieve.
    :return: Structured answer plus ingestion metadata.
    """
    content = await file.read()
    try:
        return assistant.analyze_document(
            content=content,
            source_name=file.filename or "uploaded-document.txt",
            role=role,
            question=question,
            sensitivity=sensitivity,
            max_docs=max_docs,
        )
    except ingestion.DocumentParseError as exc:
        raise fastapi.HTTPException(status_code=422, detail=str(exc)) from exc
