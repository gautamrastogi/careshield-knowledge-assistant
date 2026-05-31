from careshield import guardrails


def test_redacts_synthetic_healthcare_identifiers() -> None:
    """Verify deterministic synthetic healthcare redaction."""
    text = (
        "Patient Jane Example emailed jane.example@example.invalid from +1-555-0100 "
        "with MRN MRN-000-EXAMPLE and Insurance ID INS-000-EXAMPLE, diagnosis asthma."
    )
    result = guardrails.pii.redact_pii(text=text)
    assert "[REDACTED_PATIENT_NAME]" in result.text
    assert "[REDACTED_EMAIL]" in result.text
    assert "[REDACTED_PHONE]" in result.text
    assert "[REDACTED_MEDICAL_RECORD_NUMBER]" in result.text
    assert "[REDACTED_INSURANCE_ID]" in result.text
    assert "[REDACTED_DIAGNOSIS]" in result.text
    assert not guardrails.pii.contains_pii(text=result.text)
