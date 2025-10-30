import os
import logging
from celery import Celery
import tempfile
import requests
import base64
from io import BytesIO

from backend.core.config import settings
from backend.services.redis_client import sync_redis_client
from backend.services.s3_client import download_file_from_s3, upload_file_like_object_to_s3
from backend.services.diffusion_client import diffusion_client
from backend.core import constants

# --- Logger ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Celery App ---
celery_app = Celery(
    "worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

def _prepare_input_files(session_id: str, mask_b64: str, wallpaper_url: str, tmpdir: str):
    """Downloads and prepares all necessary files for the diffusion model."""
    original_image_path = os.path.join(tmpdir, "original.jpg")
    wallpaper_image_path = os.path.join(tmpdir, "wallpaper.jpg")
    mask_image_path = os.path.join(tmpdir, "mask.png")

    # 1. Fetch original image from S3
    s3_path = sync_redis_client.hget(f"session:{session_id}", constants.SESSION_S3_PATH)
    if not s3_path:
        raise ValueError("S3 path not found in session.")
    download_file_from_s3(settings.S3_BUCKET_NAME, s3_path.decode(), original_image_path)

    # 2. Download wallpaper image from URL
    response = requests.get(wallpaper_url, timeout=15)
    response.raise_for_status()
    with open(wallpaper_image_path, "wb") as f:
        f.write(response.content)
    
    # 3. Decode mask from Base64
    with open(mask_image_path, "wb") as f:
        f.write(base64.b64decode(mask_b64))
        
    return original_image_path, mask_image_path, wallpaper_image_path

@celery_app.task(name="process_wallpaper", bind=True, max_retries=3, default_retry_delay=30)
def process_wallpaper(self, session_id: str, mask_b64: str, wallpaper_url: str):
    """
    Celery task to process wallpaper generation.
    Orchestrates file downloads, diffusion model execution, and result uploads.
    """
    try:
        # Set status to 'generating'
        sync_redis_client.hset(f"session:{session_id}", constants.SESSION_STATUS, constants.SessionStatus.GENERATING.value)

        with tempfile.TemporaryDirectory() as tmpdir:
            # Prepare all input files
            original_path, mask_path, wallpaper_path = _prepare_input_files(session_id, mask_b64, wallpaper_url, tmpdir)

            # Generate wallpaper using the diffusion client
            result_bytes = diffusion_client.generate_wallpaper(original_path, mask_path, wallpaper_path)

            # Upload result to S3
            result_s3_key = f"{constants.S3_RESULTS_PREFIX}/{session_id}.png"
            upload_file_like_object_to_s3(BytesIO(result_bytes), settings.S3_BUCKET_NAME, result_s3_key)

            # Update session in Redis on success
            final_data = {
                constants.SESSION_STATUS: constants.SessionStatus.COMPLETED.value,
                constants.SESSION_RESULT_S3_PATH: result_s3_key
            }
            sync_redis_client.hset(f"session:{session_id}", mapping=final_data)
            sync_redis_client.hincrby(f"session:{session_id}", constants.SESSION_ATTEMPTS_LEFT, -1)

    except Exception as e:
        logger.error(f"Task failed for session {session_id}: {e}", exc_info=True)
        try:
            # Retry with exponential backoff
            countdown = self.default_retry_delay * (2 ** self.request.retries)
            self.retry(exc=e, countdown=countdown)
        except self.MaxRetriesExceededError:
            # If all retries fail, mark the session as failed
            failure_data = {
                constants.SESSION_STATUS: constants.SessionStatus.FAILED.value,
                constants.SESSION_ERROR_MESSAGE: "Generation failed after multiple retries."
            }
            sync_redis_client.hset(f"session:{session_id}", mapping=failure_data)

    return {"status": "done", "session_id": session_id}
