from careshield import contracts, pipeline


class FakeBedrockClient:
    """Small fake for the Bedrock Runtime Converse API."""

    def __init__(self) -> None:
        """Create an empty fake Bedrock client."""
        self.request: dict[str, object] | None = None

    def converse(self, **request: object) -> dict[str, object]:
        """Capture the request and return a provider-shaped response.

        :param request: Bedrock Converse request payload.
        :return: Minimal Converse response payload.
        """
        self.request = request
        return {
            "output": {
                "message": {
                    "content": [
                        {
                            "text": (
                                "Only approved de-identified summaries may be shared. "
                                "Sources: Vendor Safe Summary."
                            )
                        }
                    ]
                }
            }
        }


def test_bedrock_converse_gateway_builds_guarded_request() -> None:
    """Verify Bedrock adapter calls Converse with evidence and guardrails."""
    fake_client = FakeBedrockClient()
    gateway = pipeline.gateway.BedrockConverseGateway(
        config=contracts.schema.BedrockGatewayConfig(
            model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
            guardrail_identifier="care-guardrail",
            guardrail_version="1",
        ),
        client=fake_client,
    )
    evidence = [
        contracts.schema.Evidence(
            doc_id="vendor-safe-summary",
            title="Vendor Safe Summary",
            quote="External vendors may receive only approved de-identified summaries.",
            sensitivity=contracts.schema.Sensitivity.public,
        )
    ]

    result = gateway.generate(question="Can vendors receive summaries?", evidence=evidence)

    assert result.provider == "aws-bedrock"
    assert result.model == "anthropic.claude-3-5-sonnet-20241022-v2:0"
    assert "Sources:" in result.raw_answer
    assert fake_client.request is not None
    assert fake_client.request["modelId"] == "anthropic.claude-3-5-sonnet-20241022-v2:0"
    assert fake_client.request["guardrailConfig"] == {
        "guardrailIdentifier": "care-guardrail",
        "guardrailVersion": "1",
        "trace": "enabled",
    }
