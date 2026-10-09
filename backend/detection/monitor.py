"""Opt-in periodic monitoring. One worker loop, bounded camera concurrency."""
import asyncio
import logging
from backend.database import storage
from backend.detection.model import detector
from backend.detection.service import classify_camera
from backend.alerts.policy import evaluate
from backend.evidence.service import store_frame

log = logging.getLogger(__name__)


async def process_camera(camera_id: str):
    result = await classify_camera(camera_id)
    frame = result.pop("_frame", None)
    if result.get("status") != "ok" or not result.get("predictions"):
        return
    top = result["predictions"][0]
    decision = evaluate(top["label"], top["confidence"])
    event = storage.save_detection(camera_id, top["label"], top["confidence"], decision["status"])
    if frame is not None:
        try:
            await asyncio.to_thread(store_frame, event["id"], frame)
        except Exception:
            log.exception("Could not store evidence for %s", event["id"])


async def monitor_loop(interval_seconds: int = 15, max_concurrent: int = 2):
    """Monitor until cancelled; failures in one camera never stop the others."""
    semaphore = asyncio.Semaphore(max_concurrent)
    async def guarded(camera_id):
        async with semaphore:
            try:
                await asyncio.wait_for(process_camera(camera_id), timeout=45)
            except asyncio.CancelledError:
                raise
            except Exception:
                log.exception("Monitoring failed for camera %s", camera_id)

    while True:
        if detector.ready:
            cameras = storage.list_cameras()
            await asyncio.gather(*(guarded(cam["id"]) for cam in cameras))
        await asyncio.sleep(interval_seconds)
