import asyncio
import numpy as np
from backend.database import storage
from backend.detection import monitor


def test_process_camera_persists_result(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DB_PATH", tmp_path / "monitor.db")
    storage.init_db()
    camera = storage.add_camera("Camera", "http://192.168.1.20:8080/video")

    async def fake_classify(camera_id):
        return {"camera_id": camera_id, "status": "ok",
                "predictions": [{"label": "huayco", "confidence": 0.96}],
                "_frame": np.zeros((10, 10, 3), dtype=np.uint8)}

    saved = []
    monkeypatch.setattr(monitor, "classify_camera", fake_classify)
    monkeypatch.setattr(monitor, "store_frame", lambda detection_id, frame: saved.append(detection_id))
    asyncio.run(monitor.process_camera(camera["id"]))
    detections = storage.list_detections()
    assert len(detections) == 1
    assert detections[0]["label"] == "huayco"
    assert saved == [detections[0]["id"]]
