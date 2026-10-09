"""LAN MJPEG streaming with OpenCV. Use only on a trusted local network."""
import asyncio
from concurrent.futures import ThreadPoolExecutor
import cv2
from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from backend.cameras.registry import _cameras

# Bound simultaneous camera reads to avoid unbounded worker growth.
_executor = ThreadPoolExecutor(max_workers=4)

def _frames(url: str):
    capture = cv2.VideoCapture(url)
    try:
        if not capture.isOpened():
            return
        while True:
            ok, frame = capture.read()
            if not ok:
                break
            ok, encoded = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 75])
            if ok:
                yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + encoded.tobytes() + b"\r\n"
    finally:
        capture.release()

async def mjpeg(camera_id: str):
    camera = _cameras.get(camera_id)
    if camera is None:
        raise HTTPException(status_code=404, detail="Camera not found")
    # Never allow untrusted remote clients to request arbitrary URLs.
    iterator = _frames(camera["url"])
    async def generate():
        loop = asyncio.get_running_loop()
        while True:
            chunk = await loop.run_in_executor(_executor, lambda: next(iterator, None))
            if chunk is None:
                break
            yield chunk
    return StreamingResponse(generate(), media_type="multipart/x-mixed-replace; boundary=frame")
