from backend.database import storage

def test_camera_and_event_persistence(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DB_PATH", tmp_path / "nexus.db")
    storage.init_db()
    camera = storage.add_camera("Huanuco", "http://192.168.1.15:8080/video")
    assert storage.get_camera(camera["id"])["name"] == "Huanuco"
    assert len(storage.list_cameras()) == 1
    event = storage.save_detection(camera["id"], "normal", 0.93)
    assert storage.list_detections()[0]["id"] == event["id"]
    assert storage.remove_camera(camera["id"])
    assert storage.get_camera(camera["id"]) is None
