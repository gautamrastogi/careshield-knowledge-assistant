from careshield.pii import contains_pii, redact_pii


def test_redacts_synthetic_healthcare_identifiers() -> None:
    text = (
        "Patient Jane Example emailed jane.example@example.invalid from +1-555-0100 "
        "with MRN MRN-000-EXAMPLE and Insurance ID INS-000-EXAMPLE, diagnosis asthma."
    )
    result = redact_pii(text)
    assert "[REDACTED_PATIENT_NAME]" in result.text
    assert "[REDACTED_EMAIL]" in result.text
    assert "[REDACTED_PHONE]" in result.text
    assert "[REDACTED_MEDICAL_RECORD_NUMBER]" in result.text
    assert "[REDACTED_INSURANCE_ID]" in result.text
    assert "[REDACTED_DIAGNOSIS]" in result.text
    assert not contains_pii(result.text)
