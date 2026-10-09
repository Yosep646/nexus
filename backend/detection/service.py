"""Per-camera inference endpoint: captures a single frame on demand.
Do not use classification alone for real emergency warnings.
"""
import asyncio
import cv2
from fastapi import HTTPException
from backend.cameras.registry import _cameras
from backend.detection.model import detector

def _capture_once(url: str):
    cap = cv2.VideoCapture(url)
    try:
        ok, frame = cap.read()
        return frame if ok else None
    finally:
        cap.release()

async def classify_camera(camera_id: str):
    camera = _cameras.get(camera_id)
    if camera is None:
        raise HTTPException(status_code=404, detail="Camera not found")
    if not detector.ready:
        return {"camera_id": camera_id, "status": "model_unavailable", "predictions": []}
    frame = await asyncio.to_thread(_capture_once, camera["url"])
    if frame is None:
        raise HTTPException(status_code=503, detail="Camera frame unavailable")
    result = await asyncio.to_thread(detector.predict, frame)
    return {"camera_id": camera_id, **result}
