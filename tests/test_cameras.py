from fastapi.testclient import TestClient
from backend.main import app
from backend.cameras.registry import _cameras

client = TestClient(app)

def test_camera_lifecycle():
    _cameras.clear()
    created = client.post("/api/cameras", json={"name": "Test", "url": "http://192.168.1.20:8080/video"})
    assert created.status_code == 201
    camera_id = created.json()["id"]
    assert len(client.get("/api/cameras").json()) == 1
    assert client.delete(f"/api/cameras/{camera_id}").status_code == 200
    assert client.get(f"/api/cameras/{camera_id}/stream").status_code == 404

def test_reject_public_ip():
    result = client.post("/api/cameras", json={"name": "Invalid", "url": "http://8.8.8.8/video"})
    assert result.status_code == 422
