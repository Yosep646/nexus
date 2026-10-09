from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from backend.database import storage
from backend.cameras.stream import mjpeg
from backend.detection.model import detector
from backend.detection.service import classify_camera
from backend.alerts.policy import evaluate

router = APIRouter()

class CameraInput(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    url: str = Field(min_length=7, max_length=2048)

@router.get("/cameras")
def cameras():
    return storage.list_cameras()

@router.post("/cameras", status_code=201)
def create_camera(payload: CameraInput):
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
        storage.save_detection(camera_id, top["label"], top["confidence"])
        result["review"] = evaluate(top["label"], top["confidence"])
    return result

@router.get("/detections")
def detections(limit: int = Query(100, ge=1, le=500)):
    return storage.list_detections(limit)

@router.get("/stats")
def stats():
    from collections import Counter
    events = storage.list_detections(500)
    return {"cameras": len(storage.list_cameras()), "detections_sampled": len(events),
            "by_label": dict(Counter(event["label"] for event in events))}
