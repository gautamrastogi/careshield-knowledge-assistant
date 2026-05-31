import json
import pathlib
import typing

import pytest

from careshield import contracts, pipeline

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATASET_PATH = ROOT / "evals" / "golden_dataset.json"


class GoldenCase(typing.TypedDict):
    """Golden eval case loaded from JSON."""

    id: str
    mode: str
    role: str
    question: str
    expected_citation_ids: list[str]
    expected_answer_terms: list[str]
    min_score: int
    must_redact: list[str]
    source_path: typing.NotRequired[str]
    sensitivity: typing.NotRequired[str]


def load_golden_cases() -> list[GoldenCase]:
    """Load the golden eval dataset.

    :return: Golden eval cases.
    """
    payload = json.loads(DATASET_PATH.read_text(encoding="utf-8"))
    return typing.cast(list[GoldenCase], payload["cases"])


@pytest.mark.parametrize("case", load_golden_cases(), ids=lambda case: case["id"])
def test_golden_eval_case(case: GoldenCase) -> None:
    """Verify golden answers keep citations, redactions, and eval scores stable."""
    assistant = pipeline.assistant.CareShieldAssistant()
    response = _run_case(assistant=assistant, case=case)
    citation_ids = {citation.doc_id for citation in response.citations}

    assert set(case["expected_citation_ids"]).issubset(citation_ids)
    assert response.eval.score >= case["min_score"]
    assert response.eval.pii_redacted is True

    for term in case["expected_answer_terms"]:
        assert term.lower() in response.answer.lower()
    for redaction in case["must_redact"]:
        assert redaction in response.redactions


def _run_case(
    *,
    assistant: pipeline.assistant.CareShieldAssistant,
    case: GoldenCase,
) -> contracts.schema.AnswerResponse:
    """Run one golden eval case.

    :param assistant: Assistant service under test.
    :param case: Golden eval case.
    :return: Assistant response.
    """
    role = contracts.schema.Role(case["role"])
    if case["mode"] == "ask":
        return assistant.ask(
            request=contracts.schema.AskRequest(
                role=role,
                question=case["question"],
            )
        )
    if case["mode"] == "document":
        source_path = ROOT / case["source_path"]
        return assistant.analyze_document(
            content=source_path.read_bytes(),
            source_name=source_path.name,
            role=role,
            question=case["question"],
            sensitivity=contracts.schema.Sensitivity(case["sensitivity"]),
        )
    raise ValueError(f"unsupported golden eval mode: {case['mode']}")
