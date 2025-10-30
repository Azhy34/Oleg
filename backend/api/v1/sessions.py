from fastapi import APIRouter, UploadFile, File, Request
from pydantic import BaseModel

from backend.services.session_service import (
    create_session_service,
    start_generation_service,
    get_session_status_service,
    # generate_embedding_service # Temporarily disable
)

router = APIRouter(prefix="/v1", tags=["Sessions"])

class GenerateRequest(BaseModel):
    mask: str
    wallpaper_url: str

@router.post("/sessions/create", status_code=201)
async def create_session(file: UploadFile = File(...)):
    """
    Creates a new wallpaper generation session.

    - **file**: The user's interior image to be processed.

    Returns the newly created session's data, including its ID.
    """
    return await create_session_service(file)


# @router.post("/sessions/{session_id}/embed", status_code=202)
# async def generate_embedding(session_id: str, request: Request):
#     """
#     Generates and saves the embedding for the session's image.
#
#     - **session_id**: The ID of the session.
#     - **request**: The request object to access the embedding service.
#
#     Returns an acceptance message.
#     """
#     # TODO: This is temporarily disabled until the user provides the SAM model file.
#     # embedding_service = request.app.state.embedding_service
#     # return await generate_embedding_service(session_id, embedding_service)
#     raise HTTPException(status_code=503, detail="Embedding generation is temporarily disabled. SAM model file is missing.")


@router.post("/sessions/{session_id}/generate", status_code=202)
async def generate_wallpaper(session_id: str, payload: GenerateRequest):
    """
    Starts the wallpaper generation task for a specific session.

    - **session_id**: The ID of the session.
    - **payload**: A JSON object containing the mask and the wallpaper URL.

    Returns an acceptance message. The actual result must be polled via the status endpoint.
    """
    return await start_generation_service(session_id, payload.mask, payload.wallpaper_url)


@router.get("/sessions/{session_id}/status")
async def get_session_status(session_id: str):
    """
    Retrieves the current status of a generation session.

    - **session_id**: The ID of the session to check.

    Returns the session's status, which can be 'pending', 'generating', 'completed', or 'failed'.
    If completed, the result URL is also provided.
    """
    return await get_session_status_service(session_id)
