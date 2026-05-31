from fastapi.testclient import TestClient

from careshield.api import app


def test_health_endpoint() -> None:
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_ask_endpoint() -> None:
    client = TestClient(app)
    response = client.post(
        "/ask",
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
