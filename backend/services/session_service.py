import uuid
from fastapi import UploadFile, HTTPException

from backend.core.config import settings
from backend.services.redis_client import async_redis_client
from backend.services.s3_client import upload_file_to_s3
from backend.core.security import validate_wallpaper_url
from backend.worker.worker import process_wallpaper
from backend.core import constants

async def create_session_service(file: UploadFile):
    """
    Handles the business logic for creating a new session.
    Validates the file, uploads it to S3, and creates a session record in Redis.
    """
    if file.content_type not in constants.ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a JPG or PNG.")
    
    max_size = constants.MAX_FILE_SIZE_MB * 1024 * 1024
    if file.size > max_size:
        raise HTTPException(status_code=413, detail=f"File is too large. Maximum size is {constants.MAX_FILE_SIZE_MB}MB.")

    session_id = str(uuid.uuid4())
    s3_key = f"{constants.S3_ORIGINALS_PREFIX}/{session_id}.jpg"
    
    upload_file_to_s3(file, settings.S3_BUCKET_NAME, s3_key)

    # Session data is stored in a Redis hash.
    # Example: HSET session:some-uuid-123 status "new" original_filename "my_image.jpg" ...
    session_data = {
        constants.SESSION_STATUS: constants.SessionStatus.NEW.value,
        constants.SESSION_ORIGINAL_FILENAME: file.filename,
        constants.SESSION_S3_PATH: s3_key,
        constants.SESSION_ATTEMPTS_LEFT: "10"
    }
    await async_redis_client.hset(f"session:{session_id}", mapping=session_data)
    
    return {"session_id": session_id}

async def start_generation_service(session_id: str, mask: str, wallpaper_url: str):
    """
    Handles the business logic for starting the wallpaper generation.
    Validates the session, checks attempts, and queues the Celery task.
    """
    if not await async_redis_client.exists(f"session:{session_id}"):
        raise HTTPException(status_code=404, detail="Session not found.")

    attempts_left_bytes = await async_redis_client.hget(f"session:{session_id}", constants.SESSION_ATTEMPTS_LEFT)
    if not attempts_left_bytes or int(attempts_left_bytes) <= 0:
        raise HTTPException(status_code=403, detail="No attempts left for this session.")

    validate_wallpaper_url(wallpaper_url)

    # Queue the background task using Celery.
    process_wallpaper.delay(session_id, mask, wallpaper_url)
    
    # Update session status to 'queued'
    await async_redis_client.hset(
        f"session:{session_id}", 
        constants.SESSION_STATUS, 
        constants.SessionStatus.QUEUED.value
    )
    
    return {"status": constants.SessionStatus.QUEUED.value, "session_id": session_id}

async def get_session_status_service(session_id: str):
    """
    Retrieves the status and data of a given session from Redis.
    """
    session_data = await async_redis_client.hgetall(f"session:{session_id}")
    if not session_data:
        raise HTTPException(status_code=404, detail="Session not found.")
        
    return session_data
