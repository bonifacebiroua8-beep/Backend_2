# app/api/routes/tontines.py — redirect vers microfinance
# Les routes tontines sont dans /microfinance/tontines
from fastapi import APIRouter
router = APIRouter(prefix="/tontines", tags=["Tontines"])
# Routes disponibles dans /api/v1/microfinance/tontines
