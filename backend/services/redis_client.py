import redis.asyncio as redis
from backend.core.config import settings

# Asynchronous client for FastAPI
async_redis_client = redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)

# Synchronous client for Celery worker
sync_redis_client = redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
