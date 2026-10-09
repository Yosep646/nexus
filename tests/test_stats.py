from fastapi.testclient import TestClient
from backend.main import app
from backend.database import storage

def test_stats_count_all_records_and_review_states(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DB_PATH", tmp_path / "stats.db")
    monkeypatch.setenv("NEXUS_API_KEY", "test-key-12345678901234567890")
    with TestClient(app) as client:
        client.headers.update({"X-API-Key": "test-key-12345678901234567890"})
        camera = storage.add_camera("Rio", "http://192.168.1.5:8080/video")
        for _ in range(505):
            storage.save_detection(camera["id"], "huayco", 0.9, "pending_human_review")
        data = client.get("/api/stats").json()
        assert data["detections_total"] == 505
        assert data["pending_review"] == 505
        assert data["by_label"]["huayco"] == 505
