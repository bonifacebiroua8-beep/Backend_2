# app/api/routes/vocal.py — UbuntuTech v3.0
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional
from loguru import logger

from app.core.dependencies import get_db, get_current_user
from app.models.utilisateur import Utilisateur
from app.models.transcription import TranscriptionVocale
#from app.schemas import TranscriptionOut
from app.services.vocal_service import VocalService
from app.utils.responses import ok
from app.core.config import settings

router = APIRouter(prefix="/vocal", tags=["Vocal"])


@router.post("/transcrire",  status_code=201)
async def transcrire(
    audio: UploadFile = File(...),
    id_boutique: int = Form(...),
    langue: str = Form("fr"),
    user: Utilisateur = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Vérifier limite freemium
    if user.type_abonnement == "gratuit":
        if int(user.nb_vocal_mois or 0) >= settings.FREE_MAX_VOCAL_MOIS:
            raise HTTPException(429, f"Limite de {settings.FREE_MAX_VOCAL_MOIS} enregistrements/mois atteinte.")

    # Vérifier taille
    content = await audio.read()
    taille_mb = len(content) / (1024 * 1024)
    if taille_mb > settings.MAX_AUDIO_SIZE_MB:
        raise HTTPException(400, f"Audio trop volumineux ({taille_mb:.1f}MB > {settings.MAX_AUDIO_SIZE_MB}MB)")

    try:
        result = await VocalService.transcrire_et_analyser(
            db=db, user=user, id_boutique=id_boutique,
            audio_bytes=content, langue=langue,
            filename=audio.filename or "audio.wav"
        )
        return result
    except Exception as e:
        logger.error(f"Erreur transcription: {e}")
        raise HTTPException(500, f"Erreur transcription: {str(e)}")


@router.post("/{id_transcription}/confirmer")
def confirmer_action(
    id_transcription: int,
    confirmer: bool = True,
    id_boutique: int = Form(None),
    user: Utilisateur = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    transcription = db.query(TranscriptionVocale).filter(
        TranscriptionVocale.id_transcription == id_transcription,
        TranscriptionVocale.id_utilisateur == user.id_utilisateur
    ).first()
    if not transcription:
        raise HTTPException(404, "Transcription introuvable")
    if not confirmer:
        transcription.traitee = True
        db.commit()
        return ok({"message": "Action annulée"})
    try:
        result = VocalService.executer_action(db, user, transcription)
        return ok(result)
    except Exception as e:
        raise HTTPException(400, str(e))


@router.get("/historique")
def historique_vocal(limit: int = 10, user: Utilisateur = Depends(get_current_user), db: Session = Depends(get_db)):
    transcriptions = db.query(TranscriptionVocale).filter(
        TranscriptionVocale.id_utilisateur == user.id_utilisateur
    ).order_by(TranscriptionVocale.date_creation.desc()).limit(limit).all()
    return ok({"transcriptions": [{
        "id": t.id_transcription, "texte": t.texte_transcrit,
        "langue": t.langue_detectee, "action": t.action_detectee,
        "confiance": float(t.confiance_whisper) if t.confiance_whisper else None,
        "executee": t.action_executee, "date": str(t.date_creation)
    } for t in transcriptions]})
