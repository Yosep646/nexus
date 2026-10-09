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
        db.execute("PRAGMA journal_mode=WAL")
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
        db.execute("CREATE INDEX IF NOT EXISTS idx_detections_camera_date ON detections(camera_id, created_at DESC)")
        db.execute("""CREATE TABLE IF NOT EXISTS audit_events (
            id TEXT PRIMARY KEY, event_type TEXT NOT NULL, entity_id TEXT NOT NULL,
            details TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL)""")
        db.execute("CREATE INDEX IF NOT EXISTS idx_audit_events_date ON audit_events(created_at DESC)")
        db.execute("""CREATE TABLE IF NOT EXISTS evidence (
            id TEXT PRIMARY KEY, detection_id TEXT NOT NULL,
            filename TEXT NOT NULL, sha256 TEXT NOT NULL, created_at TEXT NOT NULL,
            FOREIGN KEY(detection_id) REFERENCES detections(id))""")
        db.execute("CREATE INDEX IF NOT EXISTS idx_evidence_detection ON evidence(detection_id)")

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
        db.execute("""INSERT INTO audit_events (id,event_type,entity_id,details,created_at)
                      VALUES (?,?,?,?,?)""",
                   (str(uuid4()), "detection_review", detection_id, decision,
                    datetime.now(timezone.utc).isoformat()))
        row = db.execute("SELECT * FROM detections WHERE id=?", (detection_id,)).fetchone()
        return dict(row)

def list_audit_events(limit=100):
    with connect() as db:
        return [dict(row) for row in db.execute(
            "SELECT * FROM audit_events ORDER BY created_at DESC LIMIT ?",
            (min(max(limit, 1), 500),))]

def save_evidence_record(detection_id, filename, sha256):
    """Register metadata for an existing detection; bytes are managed separately."""
    if not isinstance(sha256, str) or len(sha256) != 64 or any(ch not in "0123456789abcdef" for ch in sha256):
        raise ValueError("Expected a lowercase SHA-256 digest")
    if not filename or "/" in filename or "\\" in filename or filename in {".", ".."}:
        raise ValueError("Expected a plain evidence filename")
    record = {"id": str(uuid4()), "detection_id": detection_id, "filename": filename,
              "sha256": sha256, "created_at": datetime.now(timezone.utc).isoformat()}
    with connect() as db:
        db.execute("""INSERT INTO evidence (id,detection_id,filename,sha256,created_at)
                      VALUES (:id,:detection_id,:filename,:sha256,:created_at)""", record)
    return record

def list_evidence(detection_id):
    with connect() as db:
        return [dict(row) for row in db.execute(
            "SELECT * FROM evidence WHERE detection_id=? ORDER BY created_at DESC", (detection_id,))]
