# app/core/database.py — UbuntuTech v3.0 — Aiven SSL
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from loguru import logger
from app.core.config import settings

connect_args = {}
if settings.DB_SSL:
    connect_args["ssl"] = {"ssl_mode": "REQUIRED"}

engine = create_engine(
    settings.DATABASE_URL,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_recycle=settings.DB_POOL_RECYCLE,
    pool_pre_ping=True,
    connect_args=connect_args,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_connection() -> bool:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Connexion BD échouée: {e}")
        return False


def get_db_info() -> dict:
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT VERSION()")).scalar()
            return {"status": "ok", "version": result, "database": settings.DB_NAME}
    except Exception as e:
        return {"status": "error", "message": str(e)}
