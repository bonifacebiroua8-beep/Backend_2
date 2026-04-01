# app/core/dependencies.py — UbuntuTech v3.0
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional

from app.core.database import get_db
from app.core.security import verify_token
from app.models.utilisateur import Utilisateur
from app.models.session import SessionAuth
from app.models.administrateur import Administrateur

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Utilisateur:
    token = credentials.credentials
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token invalide ou expiré")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Token invalide")

    # Vérifier session en BD
    session = db.query(SessionAuth).filter(
        SessionAuth.token_hash == token,
        SessionAuth.actif == True,
        SessionAuth.date_expiration > datetime.utcnow()
    ).first()
    if not session:
        raise HTTPException(status_code=401, detail="Session expirée — reconnectez-vous")

    user = db.query(Utilisateur).filter(
        Utilisateur.id_utilisateur == int(user_id),
        Utilisateur.actif == True
    ).first()
    if not user:
        raise HTTPException(status_code=401, detail="Utilisateur introuvable")

    # Mise à jour dernière connexion
    user.derniere_connexion = datetime.utcnow()
    db.commit()
    return user


def get_current_admin(
    user: Utilisateur = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Administrateur:
    admin = db.query(Administrateur).filter(
        Administrateur.id_utilisateur == user.id_utilisateur,
        Administrateur.actif == True
    ).first()
    if not admin:
        raise HTTPException(status_code=403, detail="Accès administrateur requis")
    return admin


def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: Session = Depends(get_db)
) -> Optional[Utilisateur]:
    if not credentials:
        return None
    try:
        return get_current_user(credentials, db)
    except Exception:
        return None
