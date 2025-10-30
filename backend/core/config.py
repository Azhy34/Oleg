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
    REDIS_URL: str

    # CORS - can be a comma-separated list in the .env file
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    # Replicate API
    REPLICATE_API_TOKEN: str

    # SAM Model
    SAM_MODEL_TYPE: str = "vit_b"
    SAM_CHECKPOINT_PATH: str = "sam_vit_b_01ec64.pth"

# Create a single instance of the settings
settings = Settings()
