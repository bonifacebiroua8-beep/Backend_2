# app/api/routes/admin.py — UbuntuTech v3.0
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime, date

from app.core.dependencies import get_db, get_current_user, get_current_admin
from app.models.utilisateur import Utilisateur
from app.models.administrateur import Administrateur
from app.models.boutique import Boutique
from app.models.vente import Vente
from app.models.ia import VocabulaireIA, ApprentissageLangue, ConnaissanceLocale
from app.models.transcription import TranscriptionVocale
from app.models.dialogue import HistoriqueDialogue
from app.models.microfinance import MicroCredit
from app.models.admin_log import LogAdmin
from app.models.metrique import MetriqueSysteme
from app.schemas import VocabCreateIn, VocabOut, ConnLocalCreateIn, AdminStatsOut
from app.utils.responses import ok

router = APIRouter(prefix="/admin", tags=["Administration"])


# ── STATS ────────────────────────────────────────────────────

@router.get("/stats", response_model=AdminStatsOut)
def stats_admin(admin: Administrateur = Depends(get_current_admin), db: Session = Depends(get_db)):
    nb_users = db.query(func.count(Utilisateur.id_utilisateur)).filter(Utilisateur.actif == True).scalar()
    nb_boutiques = db.query(func.count(Boutique.id_boutique)).filter(Boutique.actif == True).scalar()
    nb_ventes = db.query(func.count(Vente.id_vente)).filter(Vente.statut == "validee").scalar()
    nb_pro = db.query(func.count(Utilisateur.id_utilisateur)).filter(Utilisateur.type_abonnement == "pro").scalar()
    nb_premium = db.query(func.count(Utilisateur.id_utilisateur)).filter(Utilisateur.type_abonnement == "premium").scalar()
    # Précision transcription par langue
    def precision_langue(langue):
        avg = db.query(func.avg(TranscriptionVocale.confiance_whisper)).filter(
            TranscriptionVocale.langue_detectee == langue,
            TranscriptionVocale.confiance_whisper != None
        ).scalar()
        return round(float(avg) * 100, 1) if avg else None
    return AdminStatsOut(
        nb_utilisateurs=int(nb_users), nb_boutiques=int(nb_boutiques),
        nb_ventes_total=int(nb_ventes), nb_abonnes_pro=int(nb_pro),
        nb_abonnes_premium=int(nb_premium),
        precision_fr=precision_langue("fr"), precision_ff=precision_langue("ff"),
        precision_ha=precision_langue("ha"), precision_mfa=precision_langue("mfa")
    )


@router.get("/dashboard")
def dashboard_admin(admin: Administrateur = Depends(get_current_admin), db: Session = Depends(get_db)):
    today = date.today()
    nb_users_today = db.query(func.count(Utilisateur.id_utilisateur)).filter(
        func.date(Utilisateur.date_inscription) == today).scalar()
    nb_ventes_today = db.query(func.count(Vente.id_vente)).filter(
        func.date(Vente.date_vente) == today, Vente.statut == "validee").scalar()
    nb_dialogues_today = db.query(func.count(HistoriqueDialogue.id_dialogue)).filter(
        func.date(HistoriqueDialogue.date_dialogue) == today).scalar()
    nb_transcriptions_today = db.query(func.count(TranscriptionVocale.id_transcription)).filter(
        func.date(TranscriptionVocale.date_creation) == today).scalar()
    credits_en_cours = db.query(func.count(MicroCredit.id_credit)).filter(MicroCredit.statut == "en_cours").scalar()
    return ok({
        "date": str(today),
        "nouveaux_utilisateurs_aujourd_hui": int(nb_users_today),
        "ventes_aujourd_hui": int(nb_ventes_today),
        "dialogues_ia_aujourd_hui": int(nb_dialogues_today),
        "transcriptions_aujourd_hui": int(nb_transcriptions_today),
        "credits_en_cours": int(credits_en_cours)
    })


# ── VOCABULAIRE IA ───────────────────────────────────────────

@router.get("/vocabulaire", response_model=List[VocabOut])
def liste_vocabulaire(langue: Optional[str] = None, confirme: Optional[bool] = None,
                       admin: Administrateur = Depends(get_current_admin), db: Session = Depends(get_db)):
    q = db.query(VocabulaireIA).filter(VocabulaireIA.actif == True)
    if langue:
        q = q.filter(VocabulaireIA.langue == langue)
    if confirme is not None:
        q = q.filter(VocabulaireIA.confirme == confirme)
    return q.order_by(VocabulaireIA.langue, VocabulaireIA.mot).all()


@router.post("/vocabulaire", response_model=VocabOut, status_code=201)
def ajouter_mot(data: VocabCreateIn, admin: Administrateur = Depends(get_current_admin), db: Session = Depends(get_db)):
    vocab = VocabulaireIA(
        mot=data.mot, signification=data.signification,
        langue=data.langue, contexte=data.contexte,
        source="admin", confirme=True, actif=True
    )
    db.add(vocab)
    db.log_admin_action(db, admin.id_admin, "vocab_ajout", {"mot": data.mot, "langue": data.langue})
    db.commit()
    db.refresh(vocab)
    return vocab


@router.put("/vocabulaire/{id_vocab}/valider")
def valider_mot(id_vocab: int, admin: Administrateur = Depends(get_current_admin), db: Session = Depends(get_db)):
    v = db.query(VocabulaireIA).filter(VocabulaireIA.id_vocab == id_vocab).first()
    if not v:
        raise HTTPException(404, "Mot introuvable")
    v.confirme = True
    _log_admin(db, admin.id_admin, "vocab_valide", {"id_vocab": id_vocab})
    db.commit()
    return ok({"message": f"Mot '{v.mot}' validé"})


@router.delete("/vocabulaire/{id_vocab}")
def supprimer_mot(id_vocab: int, admin: Administrateur = Depends(get_current_admin), db: Session = Depends(get_db)):
    v = db.query(VocabulaireIA).filter(VocabulaireIA.id_vocab == id_vocab).first()
    if not v:
        raise HTTPException(404, "Mot introuvable")
    v.actif = False
    db.commit()
    return ok({"message": "Mot supprimé"})


# ── CORRECTIONS WHISPER ──────────────────────────────────────

@router.get("/transcriptions/a-corriger")
def transcriptions_a_corriger(limit: int = 20, admin: Administrateur = Depends(get_current_admin), db: Session = Depends(get_db)):
    items = db.query(TranscriptionVocale).filter(
        TranscriptionVocale.validee_admin == False,
        TranscriptionVocale.confiance_whisper < 0.7
    ).order_by(TranscriptionVocale.date_creation.desc()).limit(limit).all()
    return ok({"items": [{
        "id": t.id_transcription, "texte": t.texte_transcrit,
        "langue": t.langue_detectee, "confiance": float(t.confiance_whisper or 0),
        "action": t.action_detectee
    } for t in items]})


@router.post("/transcriptions/{id}/corriger")
def corriger_transcription(id: int, correction: str, admin: Administrateur = Depends(get_current_admin), db: Session = Depends(get_db)):
    t = db.query(TranscriptionVocale).filter(TranscriptionVocale.id_transcription == id).first()
    if not t:
        raise HTTPException(404, "Transcription introuvable")
    t.correction_humaine = correction
    t.validee_admin = True
    db.commit()
    return ok({"message": "Correction enregistrée"})


# ── CONNAISSANCE LOCALE ──────────────────────────────────────

@router.get("/connaissance-locale")
def liste_connaissance(admin: Administrateur = Depends(get_current_admin), db: Session = Depends(get_db)):
    items = db.query(ConnaissanceLocale).filter(ConnaissanceLocale.actif == True).order_by(ConnaissanceLocale.type_info).all()
    return ok({"items": [{"id": c.id_connaissance, "type": c.type_info, "cle": c.cle,
                           "ville": c.ville, "langue": c.langue} for c in items]})


@router.post("/connaissance-locale", status_code=201)
def ajouter_connaissance(data: ConnLocalCreateIn, admin: Administrateur = Depends(get_current_admin), db: Session = Depends(get_db)):
    conn = ConnaissanceLocale(
        type_info=data.type_info, ville=data.ville, region=data.region,
        cle=data.cle, valeur_json=data.valeur_json, langue=data.langue,
        id_admin=admin.id_admin, actif=True
    )
    db.add(conn)
    db.commit()
    db.refresh(conn)
    return ok({"id": conn.id_connaissance, "message": "Connaissance ajoutée"})


# ── UTILISATEURS ADMIN ───────────────────────────────────────

@router.get("/utilisateurs")
def liste_utilisateurs(limit: int = 50, search: Optional[str] = None,
                        admin: Administrateur = Depends(get_current_admin), db: Session = Depends(get_db)):
    q = db.query(Utilisateur).filter(Utilisateur.actif == True)
    if search:
        q = q.filter(
            (Utilisateur.telephone.ilike(f"%{search}%")) |
            (Utilisateur.nom_complet.ilike(f"%{search}%"))
        )
    users = q.order_by(Utilisateur.date_inscription.desc()).limit(limit).all()
    return ok({"utilisateurs": [{
        "id": u.id_utilisateur, "telephone": u.telephone, "nom": u.nom_complet,
        "abonnement": u.type_abonnement, "score_credit": u.score_credit,
        "score_sante": u.score_sante_business, "inscription": str(u.date_inscription)
    } for u in users]})


@router.put("/utilisateurs/{id}/abonnement")
def changer_abonnement(id: int, plan: str, admin: Administrateur = Depends(get_current_admin), db: Session = Depends(get_db)):
    if plan not in ("gratuit", "pro", "premium"):
        raise HTTPException(400, "Plan invalide")
    user = db.query(Utilisateur).filter(Utilisateur.id_utilisateur == id).first()
    if not user:
        raise HTTPException(404, "Utilisateur introuvable")
    ancien = user.type_abonnement
    user.type_abonnement = plan
    _log_admin(db, admin.id_admin, "abonnement_change", {"user_id": id, "ancien": ancien, "nouveau": plan})
    db.commit()
    return ok({"message": f"Plan changé : {ancien} → {plan}"})


@router.post("/utilisateurs/{id}/admin")
def promouvoir_admin(id: int, niveau: str = "admin_support",
                      admin: Administrateur = Depends(get_current_admin), db: Session = Depends(get_db)):
    if admin.niveau_acces != "super_admin":
        raise HTTPException(403, "Seul le super_admin peut promouvoir")
    existe = db.query(Administrateur).filter(Administrateur.id_utilisateur == id).first()
    if existe:
        existe.actif = True
        existe.niveau_acces = niveau
    else:
        db.add(Administrateur(id_utilisateur=id, niveau_acces=niveau, actif=True))
    db.commit()
    return ok({"message": f"Utilisateur {id} promu {niveau}"})


# ── LOGS ADMIN ───────────────────────────────────────────────

@router.get("/logs")
def logs_admin(limit: int = 50, admin: Administrateur = Depends(get_current_admin), db: Session = Depends(get_db)):
    logs = db.query(LogAdmin).filter(LogAdmin.id_admin == admin.id_admin).order_by(LogAdmin.date_action.desc()).limit(limit).all()
    return ok({"logs": [{"action": l.action, "details": l.details_json, "date": str(l.date_action)} for l in logs]})


# ── MÉTRIQUES ────────────────────────────────────────────────

@router.get("/metriques")
def metriques(limit: int = 30, admin: Administrateur = Depends(get_current_admin), db: Session = Depends(get_db)):
    items = db.query(MetriqueSysteme).order_by(MetriqueSysteme.date_mesure.desc()).limit(limit).all()
    return ok({"metriques": [{
        "date": str(m.date_mesure), "utilisateurs": m.nb_utilisateurs_actifs,
        "ventes": m.nb_ventes_jour, "dialogues": m.nb_dialogues_ia_jour,
        "transcriptions": m.nb_transcriptions_jour
    } for m in items]})


# ── CRÉDITS ADMIN ────────────────────────────────────────────

@router.get("/credits/en-attente")
def credits_en_attente(admin: Administrateur = Depends(get_current_admin), db: Session = Depends(get_db)):
    if not admin.peut_approuver_credits:
        raise HTTPException(403, "Permission refusée")
    credits = db.query(MicroCredit).filter(MicroCredit.statut == "en_attente").order_by(MicroCredit.date_demande).all()
    return ok({"credits": [{
        "id": c.id_credit, "emprunteur": c.id_emprunteur,
        "montant": float(c.montant_demande), "banque": c.id_banque,
        "score": c.score_ml_decision, "date": str(c.date_demande)
    } for c in credits]})


@router.post("/credits/{id}/decider")
def decider_credit(id: int, approuve: bool, motif_refus: Optional[str] = None,
                    admin: Administrateur = Depends(get_current_admin), db: Session = Depends(get_db)):
    if not admin.peut_approuver_credits:
        raise HTTPException(403, "Permission refusée")
    credit = db.query(MicroCredit).filter(MicroCredit.id_credit == id).first()
    if not credit:
        raise HTTPException(404, "Crédit introuvable")
    credit.statut = "approuve" if approuve else "refuse"
    credit.motif_refus = motif_refus if not approuve else None
    credit.date_decision = datetime.utcnow()
    credit.approuve_par = admin.id_admin
    _log_admin(db, admin.id_admin, "credit_decision", {"id_credit": id, "approuve": approuve})
    db.commit()
    return ok({"message": "Approuvé" if approuve else "Refusé"})


def _log_admin(db: Session, id_admin: int, action: str, details: dict = None):
    try:
        db.add(LogAdmin(id_admin=id_admin, action=action, details_json=details))
        db.flush()
    except Exception:
        pass
