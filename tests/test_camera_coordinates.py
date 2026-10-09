import os
import tempfile
from pathlib import Path
from fastapi.testclient import TestClient


def test_camera_coordinates_are_persisted_and_validated(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        from backend.database import storage
        monkeypatch.setattr(storage, "DB_PATH", Path(tmp) / "nexus.db")
        storage.init_db()
        camera = storage.add_camera("Estacion Huanuco", "http://192.168.1.20:8080/video", -9.93, -76.24)
        found = storage.get_camera(camera["id"])
        assert found["latitude"] == -9.93
        assert found["longitude"] == -76.24
        assert storage.list_cameras()[0]["id"] == camera["id"]


def test_camera_coordinate_schema_rejects_out_of_range():
    import pytest
    from pydantic import ValidationError
    from backend.api.schemas import CameraCreate
    with pytest.raises(ValidationError):
        CameraCreate(name="Cam", url="http://192.168.1.20/video", latitude=91, longitude=-76)
