from fastapi.testclient import TestClient
from backend.main import app
from backend.database import storage

def test_review_audit_is_atomic_and_readable(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DB_PATH", tmp_path / "audit.db")
    monkeypatch.setenv("NEXUS_API_KEY", "test-key-12345678901234567890")
    with TestClient(app) as client:
        client.headers.update({"X-API-Key": "test-key-12345678901234567890"})
        camera = storage.add_camera("Cámara", "http://192.168.1.12:8080/video")
        event = storage.save_detection(camera["id"], "huayco", 0.94, "pending_human_review")
        assert client.get("/api/audit").json() == []
        result = client.patch("/api/detections/" + event["id"] + "/review",
                              json={"decision": "confirmed", "notes": "Verificado"})
        assert result.status_code == 200
        audit = client.get("/api/audit").json()
        assert len(audit) == 1
        assert audit[0]["entity_id"] == event["id"]
        assert audit[0]["details"] == "confirmed"
        assert client.patch("/api/detections/" + event["id"] + "/review",
                            json={"decision": "dismissed"}).status_code == 409
        assert len(client.get("/api/audit").json()) == 1
