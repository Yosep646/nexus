"""Private, size-limited JPEG evidence with atomic filesystem writes."""
import hashlib
import os
from pathlib import Path
from uuid import UUID, uuid4

import cv2
from backend.database import storage

MAX_JPEG_BYTES = 4 * 1024 * 1024


def evidence_root():
    root = Path(os.getenv("NEXUS_EVIDENCE_DIR", "data/evidence")).resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def store_frame(detection_id: str, frame):
    """Encode a captured frame and register its digest; never expose camera URLs."""
    UUID(detection_id)
    ok, encoded = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 82])
    if not ok:
        raise ValueError("JPEG encoding failed")
    data = encoded.tobytes()
    if not data or len(data) > MAX_JPEG_BYTES:
        raise ValueError("Evidence exceeds allowed size")
    filename = str(uuid4()) + ".jpg"
    folder = evidence_root() / detection_id
    folder.mkdir(mode=0o700, parents=True, exist_ok=True)
    final_path = folder / filename
    temp_path = folder / (filename + ".tmp")
    try:
        with temp_path.open("xb") as file:
            file.write(data)
            file.flush()
            os.fsync(file.fileno())
        temp_path.replace(final_path)
        return storage.save_evidence_record(detection_id, filename, hashlib.sha256(data).hexdigest())
    except Exception:
        temp_path.unlink(missing_ok=True)
        final_path.unlink(missing_ok=True)
        raise


def load_evidence(detection_id: str, evidence_id: str):
    UUID(detection_id)
    UUID(evidence_id)
    matches = [item for item in storage.list_evidence(detection_id) if item["id"] == evidence_id]
    if not matches:
        raise FileNotFoundError("Evidence record not found")
    record = matches[0]
    path = evidence_root() / detection_id / record["filename"]
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != record["sha256"]:
        raise ValueError("Evidence checksum mismatch")
    return data
