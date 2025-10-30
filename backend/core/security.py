import re
from fastapi import HTTPException

# Regex to validate a URL (simplified for this use case)
URL_REGEX = re.compile(
    r'^(?:http|ftp)s?://'  # http:// or https://
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
    r'localhost|'  # localhost...
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
    r'(?::\d+)?'  # optional port
    r'(?:/?|[/?]\S+)$', re.IGNORECASE)

# Allowed image content types
ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/webp"]

def validate_wallpaper_url(url: str):
    """
    Validates if the provided URL is a valid HTTP/HTTPS URL.
    Raises HTTPException if the URL is invalid.
    """
    if not re.match(URL_REGEX, url):
        raise HTTPException(status_code=400, detail="Invalid wallpaper URL provided.")

    # Further checks could be added here, e.g., trying to HEAD the URL
    # to check Content-Type, but that would introduce a blocking network call.
    # For now, we rely on the regex and the worker to handle download errors.
    return True
