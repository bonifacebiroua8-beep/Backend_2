# app/utils/logger.py — UbuntuTech v3.0
import sys
from loguru import logger
from app.core.config import settings


def setup_logger():
    logger.remove()
    logger.add(sys.stdout, level=settings.LOG_LEVEL, colorize=True,
               format="<green>{time:HH:mm:ss}</green> | <level>{level}</level> | <cyan>{name}</cyan> | {message}")
    logger.add(f"{settings.LOG_DIR}/ubuntutech.log", level="INFO",
               rotation="50 MB", retention="30 days", compression="zip",
               format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name} | {message}")
    logger.info("Logger UbuntuTech initialisé")
