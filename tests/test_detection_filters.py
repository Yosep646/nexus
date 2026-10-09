from fastapi.testclient import TestClient
from backend.main import app
from backend.database import storage

def test_detection_history_filters(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DB_PATH", tmp_path / "filters.db")
    monkeypatch.setenv("NEXUS_API_KEY", "test-key-12345678901234567890")
    with TestClient(app) as client:
        client.headers.update({"X-API-Key": "test-key-12345678901234567890"})
        a = storage.add_camera("A", "http://192.168.1.10:8080/video")
        b = storage.add_camera("B", "http://192.168.1.11:8080/video")
        storage.save_detection(a["id"], "huayco", 0.91, "pending_human_review")
        storage.save_detection(b["id"], "normal", 0.95)
        assert len(client.get("/api/detections").json()) == 2
        assert len(client.get("/api/detections", params={"camera_id": a["id"]}).json()) == 1
        assert len(client.get("/api/detections", params={"label": "normal"}).json()) == 1
        assert len(client.get("/api/detections", params={"review_status": "pending_human_review"}).json()) == 1
        assert client.get("/api/detections", params={"review_status": "invalid"}).status_code == 422
