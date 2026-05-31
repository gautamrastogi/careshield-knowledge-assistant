import pydantic
import pytest

from careshield import contracts


def test_high_confidence_requires_citations() -> None:
    """Verify schema validation blocks unsupported high confidence."""
    with pytest.raises(expected_exception=pydantic.ValidationError):
        contracts.schema.AnswerResponse(
            answer="Looks good.",
            confidence="high",
            citations=[],
            redactions=[],
            eval=contracts.schema.EvalReport(
                citations_present=False,
                grounded=False,
                pii_redacted=True,
                policy_safe=False,
                score=50,
            ),
            trace=[],
            provider="mock",
            model="mock",
        )
