from enum import Enum

# --- Session Statuses ---
class SessionStatus(str, Enum):
    NEW = "new"
    QUEUED = "queued"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"

# --- Redis Session Hash Fields ---
# These are the keys used in the Redis hash for each session.
SESSION_STATUS = "status"
SESSION_ORIGINAL_FILENAME = "original_filename"
SESSION_S3_PATH = "s3_path"
SESSION_ATTEMPTS_LEFT = "attempts_left"
SESSION_RESULT_S3_PATH = "result_s3_path"
SESSION_ERROR_MESSAGE = "error"

# --- S3 Paths ---
S3_ORIGINALS_PREFIX = "originals"
S3_RESULTS_PREFIX = "results"

# --- File Validation ---
ALLOWED_CONTENT_TYPES = ["image/jpeg", "image/png"]
MAX_FILE_SIZE_MB = 10
