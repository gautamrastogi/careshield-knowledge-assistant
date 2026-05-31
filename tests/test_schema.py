import pytest
from pydantic import ValidationError

from careshield.schemas import AnswerResponse, EvalReport


def test_high_confidence_requires_citations() -> None:
    with pytest.raises(ValidationError):
        AnswerResponse(
            answer="Looks good.",
            confidence="high",
            citations=[],
            redactions=[],
            eval=EvalReport(
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
