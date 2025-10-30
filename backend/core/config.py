from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Centralized application settings.
    All settings are loaded from a .env file.
    """
    # Pydantic settings configuration.
    # The .env file is expected to be in the same directory where the app is run.
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding='utf-8', extra='ignore')

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # CORS - can be a comma-separated list in the .env file
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    # AWS S3
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    S3_BUCKET_NAME: str
    S3_ENDPOINT_URL: str | None = None  # For MinIO or other S3-compatible services

    # Replicate API
    REPLICATE_API_TOKEN: str

# Create a single instance of the settings
settings = Settings()
