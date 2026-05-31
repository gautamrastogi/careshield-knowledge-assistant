import typing

import boto3

from careshield import contracts


class ModelGateway(typing.Protocol):
    """Common interface for model provider adapters."""

    def generate(
        self,
        *,
        question: str,
        evidence: list[contracts.schema.Evidence],
    ) -> contracts.schema.GatewayResult:
        """Generate an answer from redacted evidence.

        :param question: User question.
        :param evidence: Redacted citations selected for the prompt.
        :return: Raw gateway result before downstream validation.
        """
        raise NotImplementedError


class MockModelGateway:
    """Deterministic stand-in for a real LLM provider."""

    provider = "mock"
    model = "deterministic-care-gateway-v1"

    def generate(
        self,
        *,
        question: str,
        evidence: list[contracts.schema.Evidence],
    ) -> contracts.schema.GatewayResult:
        """Generate a deterministic answer from cited evidence.

        :param question: User question.
        :param evidence: Redacted citations selected for the prompt.
        :return: Raw gateway result before downstream validation.
        """
        lowered = question.lower()
        titles = ", ".join(item.title for item in evidence) or "no authorized documents"

        # The branchy mock keeps tests stable while still showing where a real
        # OpenAI, Bedrock, Hugging Face, or local model adapter would sit.
        if not evidence:
            answer = (
                "I could not find authorized evidence for this role. Ask a compliance "
                "officer or request access through the approved workflow."
            )
        elif "public model" in lowered or "public api" in lowered:
            answer = (
                "Protected health information and internal healthcare documents should not "
                "be sent to public model APIs. Use the approved model gateway with policy "
                f"checks, redaction, audit logging, and validation. Sources: {titles}."
            )
        elif "external vendor" in lowered or "vendor" in lowered or "send" in lowered:
            answer = (
                "Only approved, de-identified, minimum-necessary summaries may be shared "
                "with external vendors. Patient identifiers, contact details, medical record "
                "numbers, insurance identifiers, and diagnosis details must be redacted. "
                f"Sources: {titles}."
            )
        elif "billing" in lowered or "insurance" in lowered:
            answer = (
                "Billing access should be limited to payment operations and insurance or "
                "claim status fields. Full clinical notes require explicit compliance "
                f"approval. Sources: {titles}."
            )
        else:
            answer = (
                "The approved path is to use role-based access, retrieve only authorized "
                "policy evidence, redact sensitive identifiers, validate the response, "
                f"and keep an audit trace. Sources: {titles}."
            )

        return contracts.schema.GatewayResult(provider=self.provider, model=self.model, raw_answer=answer)


class BedrockConverseGateway:
    """AWS Bedrock Runtime adapter using the Converse API."""

    provider = "aws-bedrock"

    def __init__(
        self,
        *,
        config: contracts.schema.BedrockGatewayConfig,
        client: typing.Any | None = None,
    ) -> None:
        """Create a Bedrock gateway adapter.

        :param config: Bedrock model and guardrail configuration.
        :param client: Optional mocked or preconfigured Bedrock Runtime client.
        """
        self.config = config
        self.model = config.model_id
        self._client = client or boto3.client(
            service_name="bedrock-runtime",
            region_name=config.region_name,
        )

    def generate(
        self,
        *,
        question: str,
        evidence: list[contracts.schema.Evidence],
    ) -> contracts.schema.GatewayResult:
        """Generate an answer with Bedrock Converse.

        :param question: User question.
        :param evidence: Redacted citations selected for the prompt.
        :return: Raw gateway result before downstream validation.
        """
        request = self._build_request(question=question, evidence=evidence)
        response = self._client.converse(**request)
        return contracts.schema.GatewayResult(
            provider=self.provider,
            model=self.model,
            raw_answer=_extract_converse_text(response=response),
        )

    def _build_request(
        self,
        *,
        question: str,
        evidence: list[contracts.schema.Evidence],
    ) -> dict[str, object]:
        """Build a Bedrock Converse request.

        :param question: User question.
        :param evidence: Redacted citations selected for the prompt.
        :return: Bedrock Runtime Converse request payload.
        """
        prompt = _build_grounded_prompt(question=question, evidence=evidence)

        # Bedrock Converse has a provider-neutral message shape, which makes it
        # a good AWS-side match for the app's internal gateway contract.
        request: dict[str, object] = {
            "modelId": self.config.model_id,
            "messages": [
                {
                    "role": "user",
                    "content": [{"text": prompt}],
                }
            ],
            "inferenceConfig": {
                "maxTokens": self.config.max_tokens,
                "temperature": self.config.temperature,
            },
        }

        # Guardrails stay at the provider boundary, while app-level policy and
        # redaction still run before this request is created.
        if self.config.guardrail_identifier and self.config.guardrail_version:
            request["guardrailConfig"] = {
                "guardrailIdentifier": self.config.guardrail_identifier,
                "guardrailVersion": self.config.guardrail_version,
                "trace": "enabled",
            }
        return request


def _build_grounded_prompt(*, question: str, evidence: list[contracts.schema.Evidence]) -> str:
    """Create a compact grounded-answer prompt.

    :param question: User question.
    :param evidence: Redacted citations selected for the prompt.
    :return: Prompt text for a model provider.
    """
    evidence_lines = [
        f"- {item.title} ({item.doc_id}, {item.sensitivity.value}): {item.quote}" for item in evidence
    ]
    return (
        "Answer using only the authorized evidence below. "
        "If the evidence is insufficient, say so. Include a 'Sources:' sentence.\n\n"
        f"Question: {question}\n\n"
        "Authorized evidence:\n"
        + ("\n".join(evidence_lines) if evidence_lines else "- No authorized evidence.")
    )


def _extract_converse_text(*, response: dict[str, typing.Any]) -> str:
    """Extract assistant text from a Bedrock Converse response.

    :param response: Bedrock Runtime Converse response.
    :return: Concatenated text output.
    """
    content_blocks = response.get("output", {}).get("message", {}).get("content", [])
    text_parts = [block.get("text", "") for block in content_blocks if isinstance(block, dict)]
    answer = " ".join(part.strip() for part in text_parts if part.strip())
    if not answer:
        raise ValueError("bedrock response did not contain text output")
    return answer
