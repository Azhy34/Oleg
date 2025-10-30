import sys
import os

# Add project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from backend.core.config import settings
from backend.api.v1.sessions import router as sessions_router

# --------------------------------------------------------------------------
# Rate Limiting Setup
# --------------------------------------------------------------------------
# Limits API requests to prevent abuse.
limiter = Limiter(key_func=get_remote_address, default_limits=["100 per minute"])

# --------------------------------------------------------------------------
# FastAPI App Initialization
# --------------------------------------------------------------------------
app = FastAPI(
    title="AI Wallpaper Generator API",
    description="API for creating and managing wallpaper generation sessions.",
    version="0.1.0",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# --------------------------------------------------------------------------
# CORS (Cross-Origin Resource Sharing) Middleware
# --------------------------------------------------------------------------
# Allows the frontend application to communicate with this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------------------------------
# Health Check Endpoint
# --------------------------------------------------------------------------
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Provides a simple health check endpoint to confirm that the API is up and running.
    """
    return {"status": "ok"}

# --------------------------------------------------------------------------
# API Routers
# --------------------------------------------------------------------------
# Includes the routers for different parts of the API.
app.include_router(sessions_router)
