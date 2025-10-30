import os
from celery import Celery
import tempfile
import requests
import base64
from io import BytesIO

from backend.core.config import settings
from backend.services.redis_client import sync_redis_client
from backend.services.s3_client import download_file_from_s3, upload_file_like_object_to_s3
from backend.services.diffusion_client import diffusion_client

# --- Celery App ---
celery_app = Celery(
    "worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

@celery_app.task(name="process_wallpaper", bind=True, max_retries=3, default_retry_delay=30)
def process_wallpaper(self, session_id: str, mask_b64: str, wallpaper_url: str):
    """
    Celery task to process wallpaper generation.
    This task orchestrates the process: fetching data, calling the diffusion service,
    and updating the session status.
    """
    try:
        sync_redis_client.hset(f"session:{session_id}", "status", "processing")

        with tempfile.TemporaryDirectory() as tmpdir:
            original_image_path = os.path.join(tmpdir, "original.jpg")
            wallpaper_image_path = os.path.join(tmpdir, "wallpaper.jpg")
            mask_image_path = os.path.join(tmpdir, "mask.png")

            # Fetch original image from S3
            s3_path = sync_redis_client.hget(f"session:{session_id}", "s3_path")
            if not s3_path:
                raise ValueError("S3 path not found in session.")
            download_file_from_s3(settings.S3_BUCKET_NAME, s3_path, original_image_path)

            # Download wallpaper image
            response = requests.get(wallpaper_url, timeout=15)
            response.raise_for_status()
            with open(wallpaper_image_path, "wb") as f:
                f.write(response.content)
            
            # Decode mask from Base64
            with open(mask_image_path, "wb") as f:
                f.write(base64.b64decode(mask_b64))

            # Generate wallpaper using the diffusion client
            result_bytes = diffusion_client.generate_wallpaper(
                original_image_path, mask_image_path, wallpaper_image_path
            )

            # Upload result to S3
            result_s3_key = f"results/{session_id}.png"
            upload_file_like_object_to_s3(BytesIO(result_bytes), settings.S3_BUCKET_NAME, result_s3_key)

            # Update session in Redis
            final_data = {
                "status": "completed",
                "result_s3_path": result_s3_key
            }
            sync_redis_client.hset(f"session:{session_id}", mapping=final_data)
            sync_redis_client.hincrby(f"session:{session_id}", "attempts_left", -1)

    except Exception as e:
        error_message = f"Task failed for session {session_id}: {str(e)}"
        print(error_message)
        try:
            # Retry with exponential backoff
            countdown = self.default_retry_delay * (2 ** self.request.retries)
            self.retry(exc=e, countdown=countdown)
        except self.MaxRetriesExceededError:
            failure_data = {
                "status": "failed",
                "error": "Generation failed after multiple retries."
            }
            sync_redis_client.hset(f"session:{session_id}", mapping=failure_data)

    return {"status": "done", "session_id": session_id}
