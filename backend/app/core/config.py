import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]
BACKEND_DIR = Path(__file__).resolve().parents[1]

if (BACKEND_DIR / ".env").exists():
    load_dotenv(BACKEND_DIR / ".env")
if (BASE_DIR / ".env").exists():
    load_dotenv(BASE_DIR / ".env")

DEFAULT_DB_PATH = str(BASE_DIR / "app.db")

class Settings(BaseSettings):
    APP_ENV: str = "development"
    SECRET_KEY: str = "dev_secret_key_change_in_production_123456789"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    DATABASE_URL: str = f"sqlite:///{DEFAULT_DB_PATH}"
    FRONTEND_URL: str = "http://localhost:3000"
    N8N_WEBHOOK_URL: str = "http://localhost:5678/webhook/pmtool-events"
    N8N_WEBHOOK_SECRET: str = "pmtool_startup_secure_hmac_secret_2026_key"
    LLM_PROVIDER: str = "gemini"
    OPENAI_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    NEXUS_PUBLIC_API_URL: str = "http://localhost:8000"

    # Meta WhatsApp Business Cloud API Configuration
    META_WA_PHONE_NUMBER_ID: str = ""
    META_WA_ACCESS_TOKEN: str = ""
    META_WA_API_BASE_URL: str = "https://graph.facebook.com/v23.0"
    META_WA_VERIFY_TOKEN: str = "nexus_wa_verify_token_prod_2026"
    META_APP_SECRET: str = ""

    model_config = SettingsConfigDict(
        env_file=(str(BACKEND_DIR / ".env"), str(BASE_DIR / ".env")),
        extra="ignore"
    )

settings = Settings()
