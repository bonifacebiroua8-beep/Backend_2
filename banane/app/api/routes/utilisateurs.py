# app/api/routes/utilisateurs.py — UbuntuTech v3.0
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.dependencies import get_db, get_current_user
from app.models.utilisateur import Utilisateur
from app.models.parametre import ParametreUtilisateur
from app.models.notification import Notification
from app.schemas import UtilisateurOut, UtilisateurUpdateIn, ParametreUpdateIn, NotificationOut
from app.utils.responses import ok
from typing import List

router = APIRouter(prefix="/utilisateurs", tags=["Utilisateurs"])


@router.get("/moi", response_model=UtilisateurOut)
def get_moi(user: Utilisateur = Depends(get_current_user)):
    return user


@router.put("/moi", response_model=UtilisateurOut)
def modifier_profil(data: UtilisateurUpdateIn, user: Utilisateur = Depends(get_current_user), db: Session = Depends(get_db)):
    for k, v in data.model_dump(exclude_none=True).items():
        setattr(user, k, v)
    db.commit()
    db.refresh(user)
    return user


@router.get("/moi/parametres")
def get_params(user: Utilisateur = Depends(get_current_user), db: Session = Depends(get_db)):
    p = db.query(ParametreUtilisateur).filter(ParametreUtilisateur.id_utilisateur == user.id_utilisateur).first()
    if not p:
        p = ParametreUtilisateur(id_utilisateur=user.id_utilisateur)
        db.add(p); db.commit(); db.refresh(p)
    return ok({"theme": p.theme, "couleur_accent": p.couleur_accent, "taille_police": p.taille_police,
               "notif_stock_faible": p.notif_stock_faible, "notif_tontine": p.notif_tontine,
               "mode_vocal_defaut": p.mode_vocal_defaut, "langue_interface": p.langue_interface,
               "biometrie": p.biometrie})


@router.put("/moi/parametres")
def modifier_params(data: ParametreUpdateIn, user: Utilisateur = Depends(get_current_user), db: Session = Depends(get_db)):
    p = db.query(ParametreUtilisateur).filter(ParametreUtilisateur.id_utilisateur == user.id_utilisateur).first()
    if not p:
        p = ParametreUtilisateur(id_utilisateur=user.id_utilisateur)
        db.add(p)
    for k, v in data.model_dump(exclude_none=True).items():
        setattr(p, k, v)
    db.commit()
    return ok({"message": "Paramètres mis à jour"})


@router.get("/moi/notifications", response_model=List[NotificationOut])
def get_notifications(limit: int = 20, user: Utilisateur = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Notification).filter(
        Notification.id_utilisateur == user.id_utilisateur
    ).order_by(Notification.date_creation.desc()).limit(limit).all()


@router.put("/moi/notifications/{id}/lue")
def marquer_lue(id: int, user: Utilisateur = Depends(get_current_user), db: Session = Depends(get_db)):
    n = db.query(Notification).filter(Notification.id_notification == id, Notification.id_utilisateur == user.id_utilisateur).first()
    if n:
        n.lue = True
        db.commit()
    return ok({"message": "Notification marquée comme lue"})


@router.delete("/moi/compte")
def supprimer_compte(user: Utilisateur = Depends(get_current_user), db: Session = Depends(get_db)):
    user.actif = False
    db.commit()
    return ok({"message": "Compte désactivé. Vous avez 30 jours pour le réactiver."})
