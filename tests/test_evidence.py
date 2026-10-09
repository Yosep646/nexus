import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import storage

def test_evidence_metadata_and_endpoint(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DB_PATH", tmp_path / "evidence.db")
    monkeypatch.setenv("NEXUS_API_KEY", "test-key-12345678901234567890")
    with TestClient(app) as client:
        client.headers.update({"X-API-Key": "test-key-12345678901234567890"})
        camera = storage.add_camera("Río", "http://192.168.1.10:8080/video")
        event = storage.save_detection(camera["id"], "huayco", 0.9)
        digest = "a" * 64
        saved = storage.save_evidence_record(event["id"], "frame.jpg", digest)
        result = client.get("/api/detections/" + event["id"] + "/evidence")
        assert result.status_code == 200
        assert result.json()[0]["id"] == saved["id"]
        assert client.get("/api/detections/missing/evidence").status_code == 404
        with pytest.raises(ValueError):
            storage.save_evidence_record(event["id"], "../unsafe.jpg", digest)
        with pytest.raises(ValueError):
            storage.save_evidence_record(event["id"], "frame.jpg", "not-a-digest")
