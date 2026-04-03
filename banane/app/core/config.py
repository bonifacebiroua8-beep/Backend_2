# app/core/config.py
# ============================================================
#  UBUNTUTECH — Configuration centralisée v2.0
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
    DB_NAME: str         = "ubuntutech"
    DB_USER: str         = "root"
    DB_PASSWORD: str     = "password"
    DB_POOL_SIZE: int    = 15
    DB_MAX_OVERFLOW: int = 30
    DB_POOL_RECYCLE: int = 3600

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
            f"?charset=utf8mb4"
        )

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
    # BUG B FIX — whisper-large-v3 nécessite ~10GB RAM (crash sur Railway)
    # "base" = 74MB RAM, suffisant pour FR/FF/HA en production
    # Pour améliorer la précision sur Fulfuldé/Haoussa : utiliser "small" (244MB)
    WHISPER_MODEL: str     = "tiny"
    MAX_AUDIO_SIZE_MB: int = 25   # augmenté de 10 → 25 pour enregistrements 5 min

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
    UPLOAD_DIR: str  = "./uploads_temp"
    EXPORT_DIR: str  = "./exports"
    LOG_DIR: str     = "./logs"
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
    """Crée les répertoires nécessaires au démarrage."""
    for d in [settings.UPLOAD_DIR, settings.EXPORT_DIR, settings.LOG_DIR]:
        os.makedirs(d, exist_ok=True)
