# app/core/config.py
# ============================================================
#  UBUNTUTECH — Configuration centralisée v3.0
# ============================================================
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List
import os


class Settings(BaseSettings):
    # ── App ──────────────────────────────────────────────────
    APP_NAME: str     = "UbuntuTech"
    APP_VERSION: str  = "1.0.0"
    APP_ENV: str      = "development"
    DEBUG: bool       = False
    SECRET_KEY: str   = "change_me_in_production"

    # ── Base de données ──────────────────────────────────────
    DB_HOST: str         = "localhost"
    DB_PORT: int         = 3306
    DB_NAME: str         = "defaultdb"
    DB_USER: str         = "avnadmin"
    DB_PASSWORD: str     = ""
    DB_SSL: bool         = True
    DB_POOL_SIZE: int    = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_RECYCLE: int = 1800

    @property
    def DATABASE_URL(self) -> str:
        url = (
            f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
            f"?charset=utf8mb4"
        )
        if self.DB_SSL:
            url += "&ssl_ca=/etc/ssl/certs/ca-certificates.crt"
        return url

    # ── JWT ──────────────────────────────────────────────────
    JWT_SECRET_KEY: str                  = "change_me_jwt_secret"
    JWT_ALGORITHM: str                   = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int   = 30

    # ── Groq ─────────────────────────────────────────────────
    GROQ_API_KEY: str       = ""
    GROQ_MODEL: str         = "llama-3.3-70b-versatile"
    GROQ_MAX_TOKENS: int    = 1024
    GROQ_TEMPERATURE: float = 0.7
    GROQ_TIMEOUT: int       = 45

    # ── Whisper ──────────────────────────────────────────────
    WHISPER_MODEL: str     = "small"
    MAX_AUDIO_SIZE_MB: int = 25

    # ── Twilio ───────────────────────────────────────────────
    TWILIO_ACCOUNT_SID:  str = ""
    TWILIO_AUTH_TOKEN:   str = ""
    TWILIO_PHONE_NUMBER: str = ""

    # ── Freemium limites ─────────────────────────────────────
    FREE_MAX_VENTES_MOIS:  int = 50
    FREE_MAX_PRODUITS:     int = 20
    FREE_MAX_QUESTIONS_IA: int = 20
    FREE_MAX_VOCAL_MOIS:   int = 50
    FREE_HISTORIQUE_JOURS: int = 7
    PRO_MAX_PRODUITS:      int = 200

    # ── CORS ─────────────────────────────────────────────────
    CORS_ORIGINS: str = "*"

    @property
    def CORS_ORIGINS_LIST(self) -> List[str]:
        if self.CORS_ORIGINS == "*":
            return ["*"]
        return [o.strip() for o in self.CORS_ORIGINS.split(",")]

    # ── Chemins ──────────────────────────────────────────────
    UPLOAD_DIR: str  = "/tmp/uploads_temp"
    EXPORT_DIR: str  = "/tmp/exports"
    LOG_DIR: str     = "/tmp/logs"
    LOG_LEVEL: str   = "INFO"

    # ── Rate limiting ─────────────────────────────────────────
    RATE_LIMIT_PER_MINUTE: int = 60

    class Config:
        env_file          = ".env"
        env_file_encoding = "utf-8"
        case_sensitive    = True
        extra             = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()


def ensure_dirs():
    for d in [settings.UPLOAD_DIR, settings.EXPORT_DIR, settings.LOG_DIR]:
        os.makedirs(d, exist_ok=True)
