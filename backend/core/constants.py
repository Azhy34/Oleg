from enum import Enum

# --- Session Statuses ---
class SessionStatus(str, Enum):
    NEW = "new"
    EMBEDDING_COMPLETED = "embedding_completed"
    QUEUED = "queued"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"

# --- Redis Session Hash Fields ---
# These are the keys used in the Redis hash for each session.
SESSION_STATUS = "status"
SESSION_ORIGINAL_FILENAME = "original_filename"
SESSION_ORIGINAL_IMAGE_B64 = "original_image_b64"
SESSION_EMBEDDING_B64 = "embedding_b64"
SESSION_ATTEMPTS_LEFT = "attempts_left"
SESSION_RESULT_URL = "result_url"
SESSION_ERROR_MESSAGE = "error"

# --- File Validation ---
ALLOWED_CONTENT_TYPES = ["image/jpeg", "image/png"]
MAX_FILE_SIZE_MB = 10
