# app/services/auth_service.py — UbuntuTech v3.0
import random, string
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from loguru import logger

from app.models.utilisateur import Utilisateur
from app.models.session import SessionAuth
from app.models.parametre import ParametreUtilisateur
from app.models.wallet import Wallet
from app.models.microfinance_new import ScoreFiabiliteTontine
from app.models.journal import JournalConnexion
from app.core.security import hash_pin, verify_pin, create_access_token
from app.core.config import settings


class AuthService:

    @staticmethod
    def register(db: Session, telephone: str, nom_complet: str,
                 code_pin: str, langue: str = "fr",
                 email: Optional[str] = None) -> dict:
        # Vérifier doublon téléphone
        if db.query(Utilisateur).filter(Utilisateur.telephone == telephone).first():
            raise ValueError("Ce numéro de téléphone est déjà utilisé")
        if email and db.query(Utilisateur).filter(Utilisateur.email == email).first():
            raise ValueError("Cet email est déjà utilisé")

        user = Utilisateur(
            telephone=telephone, nom_complet=nom_complet,
            email=email, langue_principale=langue,
            code_pin_hash=hash_pin(code_pin),
            type_abonnement="gratuit", actif=True,
            score_credit=50, score_sante_business=50
        )
        db.add(user)
        db.flush()

        # Créer paramètres par défaut
        db.add(ParametreUtilisateur(id_utilisateur=user.id_utilisateur, langue_interface=langue))
        # Créer wallet
        db.add(Wallet(id_utilisateur=user.id_utilisateur, solde=0, solde_bloque=0))
        # Créer score fiabilité tontine
        db.add(ScoreFiabiliteTontine(id_utilisateur=user.id_utilisateur, score=50))

        db.commit()
        db.refresh(user)

        token = create_access_token(user.id_utilisateur)
        AuthService._creer_session(db, user.id_utilisateur, token)

        logger.info(f"Inscription: {telephone} — {nom_complet}")
        return {"user": user, "token": token}

    @staticmethod
    def login(db: Session, telephone: str, code_pin: str,
              ip: Optional[str] = None, device: Optional[str] = None) -> dict:
        user = db.query(Utilisateur).filter(
            Utilisateur.telephone == telephone, Utilisateur.actif == True
        ).first()

        if not user or not user.code_pin_hash:
            AuthService._log_echec(db, None, ip, device)
            raise ValueError("Numéro ou PIN incorrect")

        if not verify_pin(code_pin, user.code_pin_hash):
            AuthService._log_echec(db, user.id_utilisateur, ip, device)
            raise ValueError("PIN incorrect")

        # Révoquer anciens tokens
        db.query(SessionAuth).filter(
            SessionAuth.id_utilisateur == user.id_utilisateur,
            SessionAuth.actif == True
        ).update({"actif": False})

        token = create_access_token(user.id_utilisateur)
        AuthService._creer_session(db, user.id_utilisateur, token, ip, device)
        user.derniere_connexion = datetime.utcnow()

        db.add(JournalConnexion(
            id_utilisateur=user.id_utilisateur,
            action="login", ip_address=ip, device_info=device, succes=True
        ))
        db.commit()
        return {"user": user, "token": token}

    @staticmethod
    def logout(db: Session, token: str, user_id: int):
        db.query(SessionAuth).filter(
            SessionAuth.token_hash == token,
            SessionAuth.id_utilisateur == user_id
        ).update({"actif": False})
        db.add(JournalConnexion(id_utilisateur=user_id, action="logout", succes=True))
        db.commit()

    @staticmethod
    def change_pin(db: Session, user: Utilisateur, ancien_pin: str, nouveau_pin: str):
        if not verify_pin(ancien_pin, user.code_pin_hash):
            raise ValueError("Ancien PIN incorrect")
        user.code_pin_hash = hash_pin(nouveau_pin)
        # Révoquer toutes les sessions
        db.query(SessionAuth).filter(SessionAuth.id_utilisateur == user.id_utilisateur).update({"actif": False})
        db.add(JournalConnexion(id_utilisateur=user.id_utilisateur, action="pin_change", succes=True))
        db.commit()

    @staticmethod
    def _creer_session(db: Session, user_id: int, token: str,
                       ip: Optional[str] = None, device: Optional[str] = None):
        expire = datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        session = SessionAuth(
            id_utilisateur=user_id, token_hash=token,
            ip_address=ip, device_info=device,
            actif=True, date_expiration=expire
        )
        db.add(session)
        db.flush()

    @staticmethod
    def _log_echec(db: Session, user_id: Optional[int], ip: Optional[str], device: Optional[str]):
        if user_id:
            db.add(JournalConnexion(
                id_utilisateur=user_id, action="echec",
                ip_address=ip, device_info=device, succes=False
            ))
            db.commit()
