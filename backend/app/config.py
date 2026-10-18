import os
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional

# Base directory for backend
BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    ENV: str = "production"
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    CORS_ORIGINS: str = "*"
    
    # Security & Authentication
    JWT_SECRET: str = "ziro-free-learning-path-builder-jwt-secret-key-2026"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # LLM Settings
    GEMINI_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    LLM_PROVIDER: str = "deterministic"  # "gemini", "openai", "deterministic"
    
    # Calendar Settings
    GOOGLE_CALENDAR_CLIENT_ID: Optional[str] = None
    GOOGLE_CALENDAR_CLIENT_SECRET: Optional[str] = None
    GOOGLE_CALENDAR_REFRESH_TOKEN: Optional[str] = None
    
    # Database
    DATABASE_URL: str = f"sqlite:///{BASE_DIR}/learning_paths.db"

    class Config:
        env_file = [str(BASE_DIR.parent / ".env"), str(BASE_DIR / ".env")]
        extra = "ignore"

settings = Settings()
