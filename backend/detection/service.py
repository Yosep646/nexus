"""Classify one frame from a registered camera on demand."""
import asyncio
import os
import time
from pathlib import Path
import cv2
from fastapi import HTTPException
from backend.database.storage import get_camera
from backend.cameras.registry import _validate_url
from backend.detection.model import detector

def _capture_once(url: str):
    cap = cv2.VideoCapture(url)
    try:
        ok, frame = cap.read()
        return frame if ok else None
    finally:
        cap.release()

async def classify_camera(camera_id: str):
    camera = get_camera(camera_id)
    if camera is None:
        raise HTTPException(status_code=404, detail="Camera not found")
    if not detector.ready:
        return {"camera_id": camera_id, "status": "model_unavailable", "predictions": []}
    # Railway cannot connect to private LAN addresses; prefer recent uploaded frames.
    directory = Path(os.getenv("NEXUS_CAMERA_FRAMES_DIR", "/app/data/camera_frames" if Path("/app/data").is_dir() else "data/camera_frames"))
    path = directory / (camera_id + ".jpg")
    if path.is_file() and time.time() - path.stat().st_mtime <= 15:
        frame = await asyncio.to_thread(cv2.imread, str(path))
        if frame is not None:
            result = await asyncio.to_thread(detector.predict, frame)
            return {"camera_id": camera_id, **result, "_frame": frame if result.get("status") == "ok" else None}
    try:
        _validate_url(camera["url"])
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    frame = await asyncio.to_thread(_capture_once, camera["url"])
    if frame is None:
        raise HTTPException(status_code=503, detail="Camera frame unavailable")
    result = await asyncio.to_thread(detector.predict, frame)
    return {"camera_id": camera_id, **result, "_frame": frame if result.get("status") == "ok" else None}
