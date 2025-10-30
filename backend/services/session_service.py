import uuid
import base64
from fastapi import UploadFile, HTTPException
import numpy as np
import io

from backend.core.config import settings
from backend.services.redis_client import async_redis_client
from backend.core.security import validate_wallpaper_url
from backend.worker.celery_app import celery_app
from backend.core import constants
from backend.services.embedding_service import EmbeddingService

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
    
    # Read image content and encode it in Base64
    image_bytes = await file.read()
    image_b64 = base64.b64encode(image_bytes).decode('utf-8')

    # Session data is stored in a Redis hash.
    session_data = {
        constants.SESSION_STATUS: constants.SessionStatus.NEW.value,
        constants.SESSION_ORIGINAL_FILENAME: file.filename,
        constants.SESSION_ORIGINAL_IMAGE_B64: image_b64,
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
    celery_app.send_task(
        "process_wallpaper",
        args=[session_id, mask, wallpaper_url]
    )
    
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

async def generate_embedding_service(session_id: str, embedding_service: EmbeddingService):
    """
    Generates, uploads, and links an embedding for a session's image.
    """
    session_key = f"session:{session_id}"
    if not await async_redis_client.exists(session_key):
        raise HTTPException(status_code=404, detail="Session not found.")

    # 1. Download original image from Redis
    image_b64 = await async_redis_client.hget(session_key, constants.SESSION_ORIGINAL_IMAGE_B64)
    image_bytes = base64.b64decode(image_b64)

    # 2. Generate embedding
    embedding = embedding_service.generate_embedding_from_bytes(image_bytes)

    # 3. Upload embedding to Redis
    embedding_bytes = io.BytesIO()
    np.save(embedding_bytes, embedding, allow_pickle=False)
    embedding_bytes.seek(0)
    embedding_b64 = base64.b64encode(embedding_bytes.read()).decode('utf-8')

    # 4. Update session in Redis
    await async_redis_client.hset(
        session_key,
        mapping={
            constants.SESSION_EMBEDDING_B64: embedding_b64,
            constants.SESSION_STATUS: constants.SessionStatus.EMBEDDING_COMPLETED.value
        }
    )

    return {"status": "embedding_generated", "session_id": session_id}
