import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import storage

@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DB_PATH", tmp_path / "secure.db")
    monkeypatch.setenv("NEXUS_API_KEY", "test-key-12345678901234567890")
    with TestClient(app) as c:
        yield c

def test_unauthorized(client):
    assert client.get("/api/cameras").status_code == 401

def test_authorized(client):
    assert client.get("/api/cameras", headers={"X-API-Key":"test-key-12345678901234567890"}).status_code == 200

def test_missing_configuration(client, monkeypatch):
    monkeypatch.delenv("NEXUS_API_KEY")
    assert client.get("/api/cameras").status_code == 503
