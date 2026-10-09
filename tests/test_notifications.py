from backend.database import storage


def test_confirmed_alert_outbox(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DB_PATH", tmp_path / "alerts.db")
    storage.init_db()
    camera = storage.add_camera("Huanuco", "http://192.168.1.30:8080/video")
    first = storage.save_detection(camera["id"], "huayco", 0.99, "pending_human_review")
    second = storage.save_detection(camera["id"], "normal", 0.98, "pending_human_review")
    assert storage.list_notifications() == []
    storage.review_detection(first["id"], "confirmed", "Verified")
    storage.review_detection(second["id"], "dismissed", "False positive")
    assert len(storage.list_notifications()) == 1
    assert storage.list_notifications()[0]["detection_id"] == first["id"]
    assert storage.review_detection(first["id"], "confirmed", "") is None
    assert len(storage.list_notifications()) == 1
