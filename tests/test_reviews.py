from fastapi.testclient import TestClient
from backend.main import app
from backend.database import storage

KEY = "test-key-12345678901234567890"

def test_human_review_lifecycle(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DB_PATH", tmp_path / "review.db")
    monkeypatch.setenv("NEXUS_API_KEY", KEY)
    with TestClient(app) as client:
        client.headers.update({"X-API-Key": KEY})
        camera = client.post("/api/cameras", json={
            "name": "Test", "url": "http://192.168.1.25:8080/video"
        }).json()
        detection = storage.save_detection(camera["id"], "huayco", 0.92, "pending_human_review")
        path = f'/api/detections/{detection["id"]}/review'
        response = client.patch(path, json={"decision": "confirmed", "notes": "Reviewed by operator"})
        assert response.status_code == 200
        assert response.json()["review_status"] == "confirmed"
        assert response.json()["reviewed_at"] is not None
        assert client.patch(path, json={"decision": "dismissed"}).status_code == 409
        assert client.patch(path, json={"decision": "invalid"}).status_code == 422
        assert client.get("/api/detections").json()[0]["review_status"] == "confirmed"
        assert client.delete(f'/api/cameras/{camera["id"]}').status_code == 200
        assert client.get("/api/detections").json()[0]["id"] == detection["id"]

def test_review_requires_authentication(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DB_PATH", tmp_path / "review.db")
    monkeypatch.setenv("NEXUS_API_KEY", KEY)
    with TestClient(app) as client:
        assert client.patch("/api/detections/any/review",
                            json={"decision": "confirmed"}).status_code == 401
