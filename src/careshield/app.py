from __future__ import annotations

from careshield.data import DOCUMENTS
from careshield.evals import evaluate_answer
from careshield.gateway import MockModelGateway
from careshield.pii import redact_pii
from careshield.retrieval import retrieve, to_evidence
from careshield.schemas import AnswerResponse, AskRequest, Evidence, UserContext
from careshield.tracing import Trace


class CareShieldAssistant:
    def __init__(self, gateway: MockModelGateway | None = None) -> None:
        self.gateway = gateway or MockModelGateway()

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

        citations: list[Evidence] = []
        redactions: set[str] = set()
        for document in documents:
            redacted_body = redact_pii(document.body)
            redactions.update(redacted_body.redactions)
            quote = redacted_body.text.split(". ")[0].strip()
            citations.append(to_evidence(document, quote=quote))
        trace.add("pii_redaction", "ok", f"redactions={sorted(redactions) or ['none']}")

        gateway_result = self.gateway.generate(request.question, citations)
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
