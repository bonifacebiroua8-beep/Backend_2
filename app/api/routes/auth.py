# app/api/routes/auth.py — UbuntuTech v3.0
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.core.dependencies import get_db, get_current_user
from app.models.utilisateur import Utilisateur
from app.schemas import RegisterIn, LoginIn, TokenOut, UtilisateurOut, ChangePINIn
from app.services.auth_service import AuthService
from app.utils.responses import ok

router = APIRouter(prefix="/auth", tags=["Authentification"])


@router.post("/register", response_model=TokenOut, status_code=201)
def register(data: RegisterIn, request: Request, db: Session = Depends(get_db)):
    try:
        result = AuthService.register(
            db, data.telephone, data.nom_complet,
            data.code_pin, data.langue_principale, data.email
        )
        return TokenOut(
            access_token=result["token"],
            expires_in=1440 * 60,
            utilisateur=UtilisateurOut.model_validate(result["user"])
        )
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/login", response_model=TokenOut)
def login(data: LoginIn, request: Request, db: Session = Depends(get_db)):
    try:
        ip = request.client.host if request.client else None
        result = AuthService.login(db, data.telephone, data.code_pin, ip)
        return TokenOut(
            access_token=result["token"],
            expires_in=1440 * 60,
            utilisateur=UtilisateurOut.model_validate(result["user"])
        )
    except ValueError as e:
        raise HTTPException(401, str(e))


@router.post("/logout")
def logout(request: Request, user: Utilisateur = Depends(get_current_user), db: Session = Depends(get_db)):
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    AuthService.logout(db, token, user.id_utilisateur)
    return ok({"message": "Déconnexion réussie"})


@router.post("/change-pin")
def change_pin(data: ChangePINIn, user: Utilisateur = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        AuthService.change_pin(db, user, data.ancien_pin, data.nouveau_pin)
        return ok({"message": "PIN modifié avec succès. Reconnectez-vous."})
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.get("/me", response_model=UtilisateurOut)
def me(user: Utilisateur = Depends(get_current_user)):
    return user
