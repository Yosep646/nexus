from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from backend.cameras.registry import add_camera, list_cameras, remove_camera

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
