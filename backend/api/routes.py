from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from backend.cameras.registry import add_camera, list_cameras, remove_camera
from backend.cameras.stream import mjpeg
from backend.detection.model import detector
from backend.detection.service import classify_camera

router = APIRouter()

class CameraInput(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    url: str = Field(min_length=7, max_length=2048)

@router.get("/cameras")
def cameras():
    return list_cameras()

@router.post("/cameras", status_code=201)
def create_camera(payload: CameraInput):
    try:
        return add_camera(payload.name, payload.url)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

@router.delete("/cameras/{camera_id}")
def delete_camera(camera_id: str):
    if not remove_camera(camera_id):
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
    return await classify_camera(camera_id)
