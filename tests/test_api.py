import fastapi.testclient

import careshield.interfaces.api as api


def test_health_endpoint() -> None:
    """Verify the API health endpoint."""
    client = fastapi.testclient.TestClient(app=api.app)
    response = client.get(url="/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_ask_endpoint() -> None:
    """Verify built-in policy Q&A through FastAPI."""
    client = fastapi.testclient.TestClient(app=api.app)
    response = client.post(
        url="/ask",
        json={
            "role": "vendor_manager",
            "question": "What should be redacted before sharing data with a vendor?",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["provider"] == "mock"
    assert payload["citations"]
    assert payload["eval"]["pii_redacted"] is True


def test_document_analyze_endpoint() -> None:
    """Verify upload analysis through FastAPI."""
    client = fastapi.testclient.TestClient(app=api.app)
    content = (
        "External sharing requires approved de-identification. Patient Jane Example, "
        "MRN MRN-000-EXAMPLE, and diagnosis Type 2 diabetes must be redacted before "
        "vendor sharing. Use the approved model gateway and keep audit traces."
    )
    response = client.post(
        url="/documents/analyze",
        data={
            "role": "nurse",
            "question": "What must be redacted before vendor sharing?",
            "sensitivity": "clinical",
        },
        files={"file": ("care-report.md", content, "text/markdown")},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["ingestion"]["parser"] == "utf8-text"
    assert payload["ingestion"]["indexed_vectors"] >= 1
    assert payload["citations"]
    assert payload["eval"]["pii_redacted"] is True
    assert "medical_record_number" in payload["redactions"]


def test_document_analyze_rejects_unsupported_file_type() -> None:
    """Verify unsupported uploads return a clear validation error."""
    client = fastapi.testclient.TestClient(app=api.app)
    response = client.post(
        url="/documents/analyze",
        data={
            "role": "nurse",
            "question": "Can this file be analyzed?",
            "sensitivity": "clinical",
        },
        files={"file": ("care-report.csv", "not supported", "text/csv")},
    )

    assert response.status_code == 422
    assert "unsupported document type" in response.json()["detail"]
