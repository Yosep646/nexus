from fastapi.testclient import TestClient
from backend.main import app

def test_model_status(monkeypatch):
    monkeypatch.setenv("NEXUS_API_KEY", "test-key-12345678901234567890")
    result = TestClient(app).get("/api/model/status", headers={"X-API-Key":"test-key-12345678901234567890"})
    assert result.status_code == 200
    assert "ready" in result.json()
