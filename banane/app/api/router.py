# app/api/router.py — UbuntuTech v1.0
from fastapi import APIRouter
from app.api.routes import (
    auth, boutiques, utilisateurs, produits, ventes,
    clients, finances, vocal, ia, microfinance,
    sync, admin
)

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router)
api_router.include_router(boutiques.router)
api_router.include_router(utilisateurs.router)
api_router.include_router(produits.router)
api_router.include_router(ventes.router)
api_router.include_router(clients.router)
api_router.include_router(finances.router)
api_router.include_router(vocal.router)
api_router.include_router(ia.router)
api_router.include_router(microfinance.router)
api_router.include_router(sync.router)
api_router.include_router(admin.router)
