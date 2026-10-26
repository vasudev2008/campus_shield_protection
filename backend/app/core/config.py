import os
from pathlib import Path
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./smart_campus.db"
    SECRET_KEY: str = "CHANGE_ME"
    DEBUG: bool = True
    AI_MODEL_PATH: str = "models/yolo_weights.pt"  # optional
    ALERT_ESCALATION_CRITICAL_SECONDS: int = 20
    ALERT_ESCALATION_HIGH_SECONDS: int = 45

    class Config:
        env_file = os.getenv("ENV_FILE", ".env")
        env_file_encoding = "utf-8"

settings = Settings()
