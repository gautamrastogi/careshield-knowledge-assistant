from __future__ import annotations

from fastapi import FastAPI

from careshield import __version__
from careshield.app import CareShieldAssistant
from careshield.schemas import AnswerResponse, AskRequest


app = FastAPI(
    title="CareShield Knowledge Assistant",
    version=__version__,
    description=(
        "Public-safe synthetic healthcare GenAI/RAG demo with policy-aware "
        "retrieval, PII redaction, structured outputs, evals, and traces."
    ),
)
assistant = CareShieldAssistant()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "version": __version__}


@app.post("/ask", response_model=AnswerResponse)
def ask(request: AskRequest) -> AnswerResponse:
    return assistant.ask(request)
