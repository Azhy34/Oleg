from fastapi import APIRouter, UploadFile, File, Request
from pydantic import BaseModel

from backend.services.session_service import (
    create_session_service,
    start_generation_service,
    get_session_status_service
)

router = APIRouter(prefix="/v1", tags=["Sessions"])

class GenerateRequest(BaseModel):
    mask: str
    wallpaper_url: str

@router.post("/sessions/create")
async def create_session(
    request: Request,
    file: UploadFile = File(...)
):
    """
    Creates a new session by uploading an interior image.
    Delegates the business logic to the session service.
    """
    return await create_session_service(file)

@router.post("/sessions/{session_id}/generate")
async def generate_wallpaper(
    request: Request,
    session_id: str,
    payload: GenerateRequest
):
    """
    Starts the wallpaper generation process for a given session.
    Delegates the business logic to the session service.
    """
    return await start_generation_service(session_id, payload.mask, payload.wallpaper_url)

@router.get("/sessions/{session_id}/status")
async def get_session_status(
    request: Request,
    session_id: str
):
    """
    Retrieves the current status of a generation session.
    Delegates the business logic to the session service.
    """
    return await get_session_status_service(session_id)
