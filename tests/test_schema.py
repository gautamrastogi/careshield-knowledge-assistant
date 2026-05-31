import pydantic
import pytest

import careshield.contracts.schemas as schemas


def test_high_confidence_requires_citations() -> None:
    """Verify schema validation blocks unsupported high confidence."""
    with pytest.raises(expected_exception=pydantic.ValidationError):
        schemas.AnswerResponse(
            answer="Looks good.",
            confidence="high",
            citations=[],
            redactions=[],
            eval=schemas.EvalReport(
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
