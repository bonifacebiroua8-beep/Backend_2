# app/api/routes/ia.py — UbuntuTech v3.0
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.dependencies import get_db, get_current_user
from app.models.utilisateur import Utilisateur
from app.models.dialogue import HistoriqueDialogue
from app.schemas import DialogueIn, DialogueOut, FeedbackIn
from app.services.ia_service import IAService
from app.utils.responses import ok

router = APIRouter(prefix="/ia", tags=["IA Conseils"])


@router.post("/dialogue", response_model=DialogueOut)
def dialoguer(data: DialogueIn, user: Utilisateur = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        result = IAService.dialoguer(
            db=db, message=data.message, langue=data.langue,
            source=data.source, user=user,
            id_boutique=data.id_boutique, id_session=data.id_session,
            historique=data.historique
        )
        return DialogueOut(
            id_dialogue=result["id_dialogue"],
            reponse=result["reponse"],
            langue_reponse=result["langue_reponse"],
            domaine=result["domaine"],
            score_confiance=result["score_confiance"],
            temps_reponse_ms=result["temps_reponse_ms"],
            suggestions=result["suggestions"],
            id_session=result["id_session"]
        )
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/conseil-jour/{id_boutique}")
def conseil_jour(id_boutique: int, user: Utilisateur = Depends(get_current_user), db: Session = Depends(get_db)):
    conseil = IAService.generer_conseil_quotidien(db, id_boutique, user)
    return ok({"conseil": conseil})


@router.post("/dialogue/{id_dialogue}/feedback")
def feedback(id_dialogue: int, data: FeedbackIn, user: Utilisateur = Depends(get_current_user), db: Session = Depends(get_db)):
    dial = db.query(HistoriqueDialogue).filter(
        HistoriqueDialogue.id_dialogue == id_dialogue,
        HistoriqueDialogue.id_utilisateur == user.id_utilisateur
    ).first()
    if not dial:
        raise HTTPException(404, "Dialogue introuvable")
    dial.utile = data.utile
    if data.note:
        dial.note_utilisateur = data.note
    db.commit()
    return ok({"message": "Merci pour votre retour !"})


@router.get("/historique")
def historique(limit: int = 20, user: Utilisateur = Depends(get_current_user), db: Session = Depends(get_db)):
    dialogues = db.query(HistoriqueDialogue).filter(
        HistoriqueDialogue.id_utilisateur == user.id_utilisateur
    ).order_by(HistoriqueDialogue.date_dialogue.desc()).limit(limit).all()
    return ok({"dialogues": [{
        "id": d.id_dialogue, "message": d.message_utilisateur[:100],
        "reponse": d.reponse_ia[:200] if d.reponse_ia else None,
        "langue": d.langue_message, "domaine": d.domaine,
        "date": str(d.date_dialogue)
    } for d in dialogues]})
