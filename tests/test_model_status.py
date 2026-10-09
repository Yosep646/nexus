from fastapi.testclient import TestClient
from backend.main import app

def test_model_status():
    result = TestClient(app).get("/api/model/status")
    assert result.status_code == 200
    assert "ready" in result.json()
