from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import Response
from starlette.concurrency import run_in_threadpool
import logging
from backend.evidence.service import store_frame, load_evidence

logger = logging.getLogger(__name__)
from backend.api.schemas import CameraCreate, ReviewRequest
from backend.database import storage
from backend.cameras.stream import mjpeg
from backend.detection.model import detector
from backend.detection.service import classify_camera
from backend.alerts.policy import evaluate

router = APIRouter()

@router.get("/cameras")
def cameras():
    return storage.list_cameras()

@router.post("/cameras", status_code=201)
def create_camera(payload: CameraCreate):
    try:
        if (payload.latitude is None) != (payload.longitude is None):
            raise ValueError("Latitude and longitude must be provided together")
        return storage.add_camera(payload.name, payload.url, payload.latitude, payload.longitude)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

@router.delete("/cameras/{camera_id}")
def delete_camera(camera_id: str):
    if not storage.remove_camera(camera_id):
        raise HTTPException(status_code=404, detail="Camera not found")
    return {"deleted": camera_id}

@router.get("/cameras/{camera_id}/stream")
async def camera_stream(camera_id: str):
    return await mjpeg(camera_id)


@router.get("/cameras/{camera_id}/snapshot")
async def camera_snapshot(camera_id: str):
    """One authenticated JPEG frame from an authorized IP camera, not a public relay."""
    import cv2
    from backend.database.storage import get_camera
    from backend.cameras.registry import _validate_url
    camera = get_camera(camera_id)
    if camera is None:
        raise HTTPException(status_code=404, detail="Camera not found")
    try:
        _validate_url(camera["url"])
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    def read_one():
        capture = cv2.VideoCapture(camera["url"])
        try:
            if not capture.isOpened():
                return None
            ok, frame = capture.read()
            if not ok:
                return None
            ok, jpg = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 75])
            return jpg.tobytes() if ok else None
        finally:
            capture.release()

    data = await run_in_threadpool(read_one)
    if data is None:
        raise HTTPException(status_code=503, detail="Camera stream unreachable from server")
    return Response(content=data, media_type="image/jpeg",
                    headers={"Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff"})



# LAN camera bridge: a trusted local agent pushes JPEG frames outward over HTTPS.
@router.post("/cameras/{camera_id}/frame")
async def receive_camera_frame(camera_id: str, request: Request):
    from pathlib import Path
    import os
    import cv2
    import numpy as np
    from datetime import datetime, timezone
    from backend.database.storage import get_camera
    if get_camera(camera_id) is None:
        raise HTTPException(status_code=404, detail="Camera not found")
    if request.headers.get("content-type", "").split(";")[0].strip().lower() != "image/jpeg":
        raise HTTPException(status_code=415, detail="Expected image/jpeg")
    if request.headers.get("content-length") and int(request.headers["content-length"]) > 2_000_000:
        raise HTTPException(status_code=413, detail="Frame too large")
    frame = await request.body()
    if len(frame) > 2_000_000 or len(frame) < 100:
        raise HTTPException(status_code=413, detail="Invalid frame size")
    try:
        if not frame.startswith(b"\\xff\\xd8") or not frame.endswith(b"\\xff\\xd9"):
            raise ValueError("Invalid JPEG markers")
        image = cv2.imdecode(np.frombuffer(frame, dtype=np.uint8), cv2.IMREAD_COLOR)
        if image is None or image.shape[0] > 4096 or image.shape[1] > 4096:
            raise ValueError("Unsupported image")
    except (OSError, ValueError) as exc:
        raise HTTPException(status_code=422, detail="Invalid JPEG frame") from exc
    directory = Path(os.getenv("NEXUS_CAMERA_FRAMES_DIR", "/app/data/camera_frames" if Path("/app/data").is_dir() else "data/camera_frames"))
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / (camera_id + ".jpg")
    temp = directory / (camera_id + ".tmp")
    temp.write_bytes(frame)
    temp.replace(target)
    return {"status": "received", "camera_id": camera_id, "timestamp": datetime.now(timezone.utc).isoformat()}

@router.get("/cameras/{camera_id}/frame")
def latest_camera_frame(camera_id: str):
    from pathlib import Path
    import os
    from datetime import datetime, timezone
    from backend.database.storage import get_camera
    if get_camera(camera_id) is None:
        raise HTTPException(status_code=404, detail="Camera not found")
    directory = Path(os.getenv("NEXUS_CAMERA_FRAMES_DIR", "/app/data/camera_frames" if Path("/app/data").is_dir() else "data/camera_frames"))
    target = directory / (camera_id + ".jpg")
    if not target.is_file():
        raise HTTPException(status_code=404, detail="No frame received from local agent")
    age = datetime.now(timezone.utc).timestamp() - target.stat().st_mtime
    if age > 15:
        raise HTTPException(status_code=503, detail="Local agent offline: last frame is stale")
    return Response(content=target.read_bytes(), media_type="image/jpeg",
                    headers={"Cache-Control": "private, no-store", "X-Frame-Age-Seconds": str(round(age, 2))})

@router.get("/risk-advisories")
def risk_advisories():
    """Preliminary, unverified advisories; never claim a forecast from a single image."""
    from backend.database.storage import list_detections
    labels = {"lluvia": "Lluvia observada: revisar pronósticos oficiales y zonas de quebradas; no implica un huayco confirmado.",
              "huayco": "Posible huayco observado: solicitar verificación humana inmediata.",
              "inundacion": "Posible inundación observada: revisar niveles y reportes oficiales.",
              "deslizamiento de tierra": "Posible movimiento de ladera: solicitar verificación humana."}
    output = []
    for item in list_detections(100):
        label = str(item.get("label", "")).lower()
        if label not in labels:
            continue
        output.append({"detection_id": item["id"], "camera_id": item["camera_id"],
                       "phenomenon": item["label"], "confidence": item["confidence"],
                       "created_at": item["created_at"], "review_status": item.get("review_status"),
                       "message": labels[label], "forecast": False})
    return output

@router.get("/model/status")
def model_status():
    return {"ready": detector.ready, "labels": detector.labels}

@router.post("/cameras/{camera_id}/detect")
async def detect(camera_id: str):
    result = await classify_camera(camera_id)
    frame = result.pop("_frame", None)
    if result.get("status") == "ok" and result.get("predictions"):
        top = result["predictions"][0]
        result["review"] = evaluate(top["label"], top["confidence"])
        event = storage.save_detection(camera_id, top["label"], top["confidence"], result["review"]["status"])
        result["detection_id"] = event["id"]
        if frame is not None:
            try:
                result["evidence"] = store_frame(event["id"], frame)
            except Exception:
                logger.exception("Evidence storage failed for detection %s", event["id"])
                result["evidence_status"] = "storage_failed"
    return result

@router.patch("/detections/{detection_id}/review")
def review_detection(detection_id: str, payload: ReviewRequest):
    reviewed = storage.review_detection(detection_id, payload.decision, payload.notes)
    if reviewed is None:
        raise HTTPException(status_code=409, detail="Detection not pending review or not found")
    return reviewed

@router.get("/detections")
def detections(limit: int = Query(100, ge=1, le=500),
               camera_id: str | None = None,
               label: str | None = None,
               review_status: str | None = None):
    from backend.database.storage import connect
    conditions, params = [], []
    if camera_id:
        conditions.append("camera_id=?")
        params.append(camera_id)
    if label:
        conditions.append("label=?")
        params.append(label)
    if review_status:
        if review_status not in ("informational", "pending_human_review", "confirmed", "dismissed"):
            raise HTTPException(status_code=422, detail="Invalid review status")
        conditions.append("review_status=?")
        params.append(review_status)
    where = " WHERE " + " AND ".join(conditions) if conditions else ""
    with connect() as db:
        return [dict(row) for row in db.execute(
            "SELECT * FROM detections" + where + " ORDER BY created_at DESC LIMIT ?",
            (*params, limit))]


@router.get("/stats")
def stats():
    from backend.database.storage import connect
    with connect() as db:
        rows = db.execute("SELECT label, COUNT(*) AS total FROM detections GROUP BY label").fetchall()
        counts = db.execute("""SELECT COUNT(*) AS total,
            SUM(CASE WHEN review_status='pending_human_review' THEN 1 ELSE 0 END) AS pending,
            SUM(CASE WHEN review_status='confirmed' THEN 1 ELSE 0 END) AS confirmed,
            SUM(CASE WHEN review_status='dismissed' THEN 1 ELSE 0 END) AS dismissed
            FROM detections""").fetchone()
    return {"cameras": len(storage.list_cameras()),
            "detections_total": counts["total"],
            "pending_review": counts["pending"] or 0,
            "confirmed": counts["confirmed"] or 0,
            "dismissed": counts["dismissed"] or 0,
            "by_label": {row["label"]: row["total"] for row in rows}}

@router.get("/readiness")
def readiness():
    """Operational readiness, independent of the public liveness endpoint."""
    from backend.database.storage import connect
    try:
        with connect() as db:
            db.execute("SELECT 1").fetchone()
    except Exception:
        raise HTTPException(status_code=503, detail="Database unavailable")
    return {"database": "ready", "model": "ready" if detector.ready else "unavailable",
            "inference_enabled": bool(detector.ready)}

@router.get("/audit")
def audit_events(limit: int = Query(100, ge=1, le=500)):
    """Read-only history of human review decisions."""
    return storage.list_audit_events(limit)

@router.get("/detections/{detection_id}/evidence")
def evidence_for_detection(detection_id: str):
    """Return registered evidence metadata, not unrestricted filesystem paths."""
    from backend.database.storage import connect
    with connect() as db:
        exists = db.execute("SELECT 1 FROM detections WHERE id=?", (detection_id,)).fetchone()
    if exists is None:
        raise HTTPException(status_code=404, detail="Detection not found")
    return storage.list_evidence(detection_id)

@router.get("/detections/{detection_id}/evidence/{evidence_id}/image")
def download_evidence(detection_id: str, evidence_id: str):
    """Return a verified JPEG under the same API-key protection as other routes."""
    try:
        data = load_evidence(detection_id, evidence_id)
    except (ValueError, FileNotFoundError):
        raise HTTPException(status_code=404, detail="Evidence unavailable")
    return Response(content=data, media_type="image/jpeg",
                    headers={"Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff"})

@router.get("/reports/detections.pdf")
def detection_report(limit: int = Query(200, ge=1, le=500)):
    """Authenticated PDF summary; events are not claims of confirmed disasters."""
    from backend.reports.pdf import build_report
    return Response(content=build_report(limit), media_type="application/pdf",
                    headers={"Content-Disposition": 'attachment; filename="nexus-detections.pdf"',
                             "Cache-Control": "private, no-store"})

@router.get("/notifications")
def notifications(limit: int = Query(100, ge=1, le=500)):
    """Confirmed alerts awaiting delivery; no external dispatch is implied."""
    return storage.list_notifications(limit)
