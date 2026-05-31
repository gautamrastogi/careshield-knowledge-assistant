from __future__ import annotations

from fastapi import FastAPI, File, Form, HTTPException, UploadFile

from careshield import __version__
from careshield.app import CareShieldAssistant
from careshield.ingestion import DocumentParseError
from careshield.schemas import AnswerResponse, AskRequest, DocumentAnalysisResponse, Role, Sensitivity


app = FastAPI(
    title="CareShield Knowledge Assistant",
    version=__version__,
    description=(
        "Public-safe synthetic healthcare GenAI/RAG demo with policy-aware "
        "document ingestion, vector retrieval, PII redaction, structured "
        "outputs, evals, and traces."
    ),
)
assistant = CareShieldAssistant()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "version": __version__}


@app.post("/ask", response_model=AnswerResponse)
def ask(request: AskRequest) -> AnswerResponse:
    return assistant.ask(request)


@app.post("/documents/analyze", response_model=DocumentAnalysisResponse)
async def analyze_document(
    file: UploadFile = File(...),
    role: Role = Form(Role.compliance_officer),
    question: str = Form(..., min_length=5, max_length=1_000),
    sensitivity: Sensitivity = Form(Sensitivity.clinical),
    max_docs: int = Form(3, ge=1, le=5),
) -> DocumentAnalysisResponse:
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
    except DocumentParseError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
