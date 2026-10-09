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
        return [dict(r) for r in db.execute("SELECT id,name,url,status FROM cameras ORDER BY created_at DESC")]

def get_camera(camera_id):
    with connect() as db:
        row = db.execute("SELECT id,name,url,status FROM cameras WHERE id=?", (camera_id,)).fetchone()
    return dict(row) if row else None

def remove_camera(camera_id):
    with connect() as db:
        result = db.execute("DELETE FROM cameras WHERE id=?", (camera_id,))
    return result.rowcount > 0

def save_detection(camera_id, label, confidence):
    item = {"id": str(uuid4()), "camera_id": camera_id, "label": label,
            "confidence": float(confidence), "created_at": datetime.now(timezone.utc).isoformat()}
    with connect() as db:
        db.execute("INSERT INTO detections VALUES (:id,:camera_id,:label,:confidence,:created_at)", item)
    return item

def list_detections(limit=100):
    with connect() as db:
        return [dict(r) for r in db.execute(
            "SELECT * FROM detections ORDER BY created_at DESC LIMIT ?", (min(max(limit, 1), 500),))]
