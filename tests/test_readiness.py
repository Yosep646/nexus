from fastapi.testclient import TestClient
from backend.main import app
from backend.database import storage

def test_readiness_reports_database_and_model_separately(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DB_PATH", tmp_path / "ready.db")
    monkeypatch.setenv("NEXUS_API_KEY", "test-key-12345678901234567890")
    with TestClient(app) as client:
        assert client.get("/api/readiness").status_code == 401
        result = client.get("/api/readiness", headers={"X-API-Key": "test-key-12345678901234567890"})
        assert result.status_code == 200
        assert result.json()["database"] == "ready"
        assert isinstance(result.json()["inference_enabled"], bool)
