import numpy as np
import pytest
from backend.database import storage
from backend.evidence import service


def test_evidence_roundtrip_and_tampering(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DB_PATH", tmp_path / "nexus.db")
    monkeypatch.setenv("NEXUS_EVIDENCE_DIR", str(tmp_path / "evidence"))
    storage.init_db()
    camera = storage.add_camera("Test", "http://192.168.1.10:8080/video")
    event = storage.save_detection(camera["id"], "normal", 0.95)
    frame = np.zeros((32, 32, 3), dtype=np.uint8)
    record = service.store_frame(event["id"], frame)
    data = service.load_evidence(event["id"], record["id"])
    assert data.startswith(b"\xff\xd8")
    assert len(storage.list_evidence(event["id"])) == 1
    path = service.evidence_root() / event["id"] / record["filename"]
    path.write_bytes(b"tampered")
    with pytest.raises(ValueError, match="checksum"):
        service.load_evidence(event["id"], record["id"])
