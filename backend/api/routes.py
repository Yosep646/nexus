from fastapi import APIRouter, HTTPException, Query
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
        return storage.add_camera(payload.name, payload.url)
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

@router.get("/model/status")
def model_status():
    return {"ready": detector.ready, "labels": detector.labels}

@router.post("/cameras/{camera_id}/detect")
async def detect(camera_id: str):
    result = await classify_camera(camera_id)
    if result.get("status") == "ok" and result.get("predictions"):
        top = result["predictions"][0]
        result["review"] = evaluate(top["label"], top["confidence"])
        storage.save_detection(camera_id, top["label"], top["confidence"], result["review"]["status"])
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
