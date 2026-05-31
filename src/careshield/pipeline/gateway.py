from careshield import contracts


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
