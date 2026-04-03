# main.py — UbuntuTech Backend v3.0
# ============================================================
#  Lancer : uvicorn main:app --host 0.0.0.0 --port $PORT
# ============================================================
import os, time
os.makedirs(".logs", exist_ok=True)

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from loguru import logger

from app.core.config import settings, ensure_dirs
from app.core.database import check_db_connection
from app.api.router import api_router
from app.utils.logger import setup_logger
from app.tasks.scheduler import demarrer_scheduler, arreter_scheduler

limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logger()
    ensure_dirs()
    logger.info(f"🚀 UbuntuTech API v{settings.APP_VERSION} — {settings.APP_ENV}")
    logger.info(f"   Langues: FR · Fulfulde · Haoussa · Mafa")
    logger.info(f"   Whisper: {settings.WHISPER_MODEL} | Groq: {settings.GROQ_MODEL}")

    if check_db_connection():
        logger.info(f"✅ MySQL '{settings.DB_NAME}' connecté")
        try:
            import app.models  # noqa — enregistre tous les modèles auprès de Base
            from app.core.database import Base, engine
            Base.metadata.create_all(bind=engine)
            logger.info("✅ Tables vérifiées / créées")
        except Exception as e:
            logger.error(f"❌ Erreur create_all: {e}")
    else:
        logger.critical("❌ MySQL non accessible — vérifiez .env")

    try:
        demarrer_scheduler()
    except Exception as e:
        logger.warning(f"Scheduler non démarré: {e}")

    yield

    arreter_scheduler()
    logger.info("👋 UbuntuTech API arrêtée")


app = FastAPI(
    title="UbuntuTech API",
    description=(
        "Backend UbuntuTech v3.0 — Assistant IA Multilingue pour Micro-Entrepreneurs. "
        "Langues: FR · Fulfulde · Haoussa · Mafa. "
        "52 tables · 8 vues · FastAPI + Groq + Whisper + MySQL"
    ),
    version=settings.APP_VERSION,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET","POST","PUT","PATCH","DELETE","OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Process-Time-Ms"],
    max_age=3600,
)
if settings.APP_ENV == "production":
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])


@app.middleware("http")
async def add_process_time(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    ms = round((time.perf_counter() - start) * 1000, 2)
    response.headers["X-Process-Time-Ms"] = str(ms)
    if ms > 3000:
        logger.warning(f"⚠️ Requête lente {ms}ms: {request.method} {request.url.path}")
    return response


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    if settings.APP_ENV == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Erreur: {type(exc).__name__} — {exc} — {request.method} {request.url.path}")
    return JSONResponse(status_code=500, content={
        "success": False,
        "message": "Erreur serveur interne.",
        "detail": str(exc) if settings.DEBUG else None
    })


@app.exception_handler(404)
async def not_found(request: Request, exc):
    return JSONResponse(status_code=404, content={"success": False, "message": f"Route introuvable: {request.url.path}"})


if os.path.exists(settings.UPLOAD_DIR):
    app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

app.include_router(api_router)


@app.get("/", include_in_schema=False)
def root():
    return {
        "app": "UbuntuTech API", "version": settings.APP_VERSION,
        "env": settings.APP_ENV, "status": "running",
        "langues": ["fr", "ff", "ha", "mfa"],
        "docs": "/docs" if settings.DEBUG else "disabled",
        "devise": "Je réussis parce que nous réussissons 🌍"
    }


@app.get("/health")
def health():
    from app.core.database import get_db_info
    db_info = get_db_info()
    ok = db_info.get("status") == "ok"
    return JSONResponse(status_code=200 if ok else 503, content={
        "status": "healthy" if ok else "degraded",
        "database": db_info,
        "scheduler": "running",
        "version": settings.APP_VERSION,
        "timestamp": time.time()
    })


@app.api_route("/ping", methods=["GET","HEAD"], include_in_schema=False)
def ping():
    return {"status": "ok", "timestamp": time.time()}
