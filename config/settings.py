from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    GROQ_API_KEY: str
    GROQ_MODEL: str = "llama3-8b-8192"
    LOG_LEVEL: str = "INFO"
    OUTPUT_DIR: str = "./outputs"

    class Config:
        env_file = ".env"


settings = Settings()

# Ensure output directory exists
Path(settings.OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
