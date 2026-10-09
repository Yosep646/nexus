"""SQLite persistence for registered cameras and manual detection events."""
import os
import sqlite3
from pathlib import Path
from datetime import datetime, timezone
from uuid import uuid4

DB_PATH = Path(os.getenv("NEXUS_DB_PATH", "data/nexus.db"))

def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(str(DB_PATH), timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA busy_timeout=10000")
    connection.execute("PRAGMA foreign_keys=ON")
    return connection

def init_db():
    with connect() as db:
        db.execute("""CREATE TABLE IF NOT EXISTS cameras (
            id TEXT PRIMARY KEY, name TEXT NOT NULL, url TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'registered', created_at TEXT NOT NULL)""")
        db.execute("""CREATE TABLE IF NOT EXISTS detections (
            id TEXT PRIMARY KEY, camera_id TEXT NOT NULL,
            label TEXT NOT NULL, confidence REAL NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(camera_id) REFERENCES cameras(id))""")
        db.execute("CREATE INDEX IF NOT EXISTS idx_detections_date ON detections(created_at DESC)")
        columns = {row["name"] for row in db.execute("PRAGMA table_info(detections)")}
        if "review_status" not in columns:
            db.execute("ALTER TABLE detections ADD COLUMN review_status TEXT NOT NULL DEFAULT 'informational'")
        if "reviewed_at" not in columns:
            db.execute("ALTER TABLE detections ADD COLUMN reviewed_at TEXT")
        if "review_notes" not in columns:
            db.execute("ALTER TABLE detections ADD COLUMN review_notes TEXT")
        db.execute("CREATE INDEX IF NOT EXISTS idx_detections_review ON detections(review_status)")

def add_camera(name, url):
    from backend.cameras.registry import _validate_url
    _validate_url(url)
    name = name.strip()
    if not name:
        raise ValueError("Camera name cannot be empty")
    camera = {"id": str(uuid4()), "name": name, "url": url, "status": "registered"}
    with connect() as db:
        db.execute("INSERT INTO cameras VALUES (?, ?, ?, ?, ?)",
                   (camera["id"], name, url, camera["status"], datetime.now(timezone.utc).isoformat()))
    return camera

def list_cameras():
    with connect() as db:
        return [dict(r) for r in db.execute("SELECT id,name,url,status FROM cameras WHERE status != 'deleted' ORDER BY created_at DESC")]

def get_camera(camera_id):
    with connect() as db:
        row = db.execute("SELECT id,name,url,status FROM cameras WHERE id=? AND status != 'deleted'", (camera_id,)).fetchone()
    return dict(row) if row else None

def remove_camera(camera_id):
    with connect() as db:
        result = db.execute("UPDATE cameras SET status='deleted' WHERE id=? AND status != 'deleted'", (camera_id,))
    return result.rowcount > 0

def save_detection(camera_id, label, confidence, review_status='informational'):
    item = {"id": str(uuid4()), "camera_id": camera_id, "label": label,
            "confidence": float(confidence), "created_at": datetime.now(timezone.utc).isoformat(),
            "review_status": review_status}
    with connect() as db:
        db.execute("""INSERT INTO detections (id,camera_id,label,confidence,created_at,review_status)
                      VALUES (:id,:camera_id,:label,:confidence,:created_at,:review_status)""", item)
    return item

def list_detections(limit=100):
    with connect() as db:
        return [dict(r) for r in db.execute(
            "SELECT * FROM detections ORDER BY created_at DESC LIMIT ?", (min(max(limit, 1), 500),))]

def review_detection(detection_id: str, decision: str, notes: str):
    """Review an existing detection once; preserve an immutable decision timestamp."""
    if decision not in {"confirmed", "dismissed"}:
        raise ValueError("Unsupported review decision")
    with connect() as db:
        updated = db.execute(
            """UPDATE detections SET review_status=?, review_notes=?, reviewed_at=?
               WHERE id=? AND review_status='pending_human_review'""",
            (decision, notes, datetime.now(timezone.utc).isoformat(), detection_id))
        if updated.rowcount != 1:
            return None
        row = db.execute("SELECT * FROM detections WHERE id=?", (detection_id,)).fetchone()
        return dict(row)
