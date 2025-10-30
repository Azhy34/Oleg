import boto3
from botocore.client import Config
from botocore.exceptions import BotoCoreError
from fastapi import HTTPException, UploadFile

from backend.core.config import settings

client_kwargs = {
    "aws_access_key_id": settings.AWS_ACCESS_KEY_ID,
    "aws_secret_access_key": settings.AWS_SECRET_ACCESS_KEY,
    "config": Config(signature_version="s3v4"),
}
if settings.S3_ENDPOINT_URL:
    client_kwargs["endpoint_url"] = settings.S3_ENDPOINT_URL

s3_client = boto3.client("s3", **client_kwargs)

def upload_file_to_s3(file: UploadFile, bucket_name: str, object_name: str):
    """
    Uploads a FastAPI UploadFile to an S3 bucket.
    """
    upload_file_like_object_to_s3(file.file, bucket_name, object_name)

def upload_file_like_object_to_s3(file_obj, bucket_name: str, object_name: str):
    """
    Uploads a file-like object (e.g., from open()) to an S3 bucket.
    """
    try:
        s3_client.upload_fileobj(file_obj, bucket_name, object_name)
    except BotoCoreError as e:
        raise HTTPException(status_code=500, detail=f"S3 upload failed: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred during file upload: {e}")

def download_file_from_s3(bucket_name: str, object_name: str, file_path: str):
    """
    Downloads a file from an S3 bucket.
    """
    try:
        s3_client.download_file(bucket_name, object_name, file_path)
    except BotoCoreError as e:
        # Handle client errors (e.g., file not found)
        raise Exception(f"Could not download file from S3: {e}")
