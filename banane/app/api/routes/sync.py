# app/api/routes/sync.py — UbuntuTech v3.0
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.dependencies import get_db, get_current_user
from app.models.utilisateur import Utilisateur
from app.models.sync import SyncQueue
from app.schemas import SyncBatchIn
from app.utils.responses import ok
from datetime import datetime

router = APIRouter(prefix="/sync", tags=["Synchronisation"])


@router.post("/batch")
def sync_batch(data: SyncBatchIn, user: Utilisateur = Depends(get_current_user), db: Session = Depends(get_db)):
    created = 0
    for item in data.items:
        s = SyncQueue(
            id_utilisateur=user.id_utilisateur,
            id_boutique=data.id_boutique,
            table_cible=item.table_cible,
            id_enregistrement=item.id_enregistrement,
            operation=item.operation,
            donnees_json=item.donnees_json,
            priorite=item.priorite,
            statut="pending"
        )
        db.add(s)
        created += 1
    db.commit()
    return ok({"items_queued": created, "message": "Synchronisation en attente"})


@router.get("/status")
def sync_status(user: Utilisateur = Depends(get_current_user), db: Session = Depends(get_db)):
    pending = db.query(SyncQueue).filter(SyncQueue.id_utilisateur == user.id_utilisateur, SyncQueue.statut == "pending").count()
    failed = db.query(SyncQueue).filter(SyncQueue.id_utilisateur == user.id_utilisateur, SyncQueue.statut == "failed").count()
    return ok({"pending": pending, "failed": failed, "synced": True if pending == 0 else False})
