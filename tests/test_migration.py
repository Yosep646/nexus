import sqlite3
from backend.database import storage


def test_legacy_database_migration_preserves_rows(tmp_path, monkeypatch):
    path = tmp_path / "legacy.db"
    monkeypatch.setattr(storage, "DB_PATH", path)
    with sqlite3.connect(path) as db:
        db.execute("CREATE TABLE cameras (id TEXT PRIMARY KEY, name TEXT NOT NULL, url TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'registered', created_at TEXT NOT NULL)")
        db.execute("CREATE TABLE detections (id TEXT PRIMARY KEY, camera_id TEXT NOT NULL, label TEXT NOT NULL, confidence REAL NOT NULL, created_at TEXT NOT NULL, FOREIGN KEY(camera_id) REFERENCES cameras(id))")
        db.execute("INSERT INTO cameras VALUES ('cam','Test','http://192.168.1.10/video','registered','2026-01-01')")
        db.execute("INSERT INTO detections VALUES ('det','cam','normal',0.9,'2026-01-01')")
    storage.init_db()
    storage.init_db()
    with storage.connect() as db:
        row = db.execute("SELECT * FROM detections WHERE id='det'").fetchone()
        assert row["label"] == "normal"
        assert row["review_status"] == "informational"
        assert db.execute("SELECT COUNT(*) FROM cameras").fetchone()[0] == 1
        assert db.execute("SELECT COUNT(*) FROM evidence").fetchone()[0] == 0
        assert db.execute("SELECT COUNT(*) FROM notifications").fetchone()[0] == 0
