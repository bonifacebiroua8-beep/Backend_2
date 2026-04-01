# app/api/routes/microfinance.py — UbuntuTech v3.0
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from loguru import logger

from app.core.dependencies import get_db, get_current_user
from app.models.utilisateur import Utilisateur
from app.models.microfinance import BanquePartenaire, MicroCredit
from app.models.echeancier import EcheancierCredit
from app.models.tontine import Tontine, MembreTontine, CotisationTontine
from app.models.epargne import Epargne
from app.models.wallet import Wallet
from app.models.microfinance_new import (
    RechargeWallet, VirementWallet, GarantieCredit, LitigeTontine,
    ScoreFiabiliteTontine, CycleTontine
)
from app.schemas import (
    MessageOut, WalletOut, RechargeIn, RechargeOut, VirementIn, VirementOut,
    EpargneCreateIn, EpargneOut, CreditDemandeIn, CreditSimulerIn,
    CreditSimulerOut, CreditOut, SignatureOTPIn, GarantieIn,
    TontineCreateIn, TontineOut, RejoindreIn, CotisationPayerIn,
    LitigeCreateIn
)
from app.services.microfinance_service import WalletService, CreditService, TontineService
from app.utils.responses import ok, err

router = APIRouter(prefix="/microfinance", tags=["Microfinance"])


# ── WALLET ───────────────────────────────────────────────────

@router.get("/wallet", response_model=WalletOut)
def get_wallet(user: Utilisateur = Depends(get_current_user), db: Session = Depends(get_db)):
    wallet = WalletService.get_or_create(db, user.id_utilisateur)
    return WalletOut(
        id_wallet=wallet.id_wallet,
        solde=float(wallet.solde),
        solde_bloque=float(wallet.solde_bloque),
        devise=wallet.devise,
        plafond_journalier=float(wallet.plafond_journalier)
    )


@router.post("/wallet/recharger", response_model=RechargeOut, status_code=201)
def recharger_wallet(data: RechargeIn, user: Utilisateur = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        recharge = WalletService.recharger(db, user.id_utilisateur, data.montant, data.provider, data.telephone_source)
        return RechargeOut(
            id_recharge=recharge.id_recharge,
            montant=float(recharge.montant),
            montant_net=float(recharge.montant_net),
            frais=float(recharge.frais),
            provider=recharge.provider,
            statut=recharge.statut,
            date_demande=recharge.date_demande
        )
    except Exception as e:
        raise HTTPException(400, str(e))


@router.post("/wallet/virer", response_model=VirementOut, status_code=201)
def virer_wallet(data: VirementIn, user: Utilisateur = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        virement = WalletService.virer(db, user, data.telephone_receveur, data.montant, data.motif)
        return VirementOut(
            id_virement=virement.id_virement,
            montant=float(virement.montant),
            montant_net=float(virement.montant_net),
            statut=virement.statut,
            date_virement=virement.date_virement
        )
    except Exception as e:
        raise HTTPException(400, str(e))


@router.get("/wallet/historique")
def historique_wallet(limit: int = 20, user: Utilisateur = Depends(get_current_user), db: Session = Depends(get_db)):
    recharges = db.query(RechargeWallet).filter(
        RechargeWallet.id_utilisateur == user.id_utilisateur
    ).order_by(RechargeWallet.date_demande.desc()).limit(limit).all()
    virements = db.query(VirementWallet).filter(
        (VirementWallet.id_utilisateur_envoyeur == user.id_utilisateur) |
        (VirementWallet.id_utilisateur_receveur == user.id_utilisateur)
    ).order_by(VirementWallet.date_virement.desc()).limit(limit).all()
    return ok({"recharges": len(recharges), "virements": len(virements)})


# ── ÉPARGNE ──────────────────────────────────────────────────

@router.get("/epargnes", response_model=List[EpargneOut])
def liste_epargnes(user: Utilisateur = Depends(get_current_user), db: Session = Depends(get_db)):
    epargnes = db.query(Epargne).filter(
        Epargne.id_utilisateur == user.id_utilisateur,
        Epargne.statut != "abandonne"
    ).all()
    result = []
    for e in epargnes:
        pct = round(float(e.total_cumule) / float(e.objectif_montant) * 100, 1) if float(e.objectif_montant) > 0 else 0
        result.append(EpargneOut(
            id_epargne=e.id_epargne,
            objectif_libelle=e.objectif_libelle,
            objectif_montant=float(e.objectif_montant),
            total_cumule=float(e.total_cumule),
            progression_pct=min(pct, 100),
            statut=e.statut,
            date_cible=e.date_cible
        ))
    return result


@router.post("/epargnes", status_code=201)
def creer_epargne(data: EpargneCreateIn, user: Utilisateur = Depends(get_current_user), db: Session = Depends(get_db)):
    epargne = Epargne(
        id_utilisateur=user.id_utilisateur,
        objectif_libelle=data.objectif_libelle,
        categorie_objectif=data.categorie_objectif,
        objectif_montant=data.objectif_montant,
        montant_mensuel_cible=data.montant_mensuel_cible,
        versement_auto=data.versement_auto,
        date_cible=data.date_cible,
        total_cumule=0,
        statut="actif"
    )
    db.add(epargne)
    db.commit()
    db.refresh(epargne)
    return ok({"id_epargne": epargne.id_epargne, "message": "Objectif d'épargne créé"})


@router.post("/epargnes/{id_epargne}/verser")
def verser_epargne(id_epargne: int, montant: float, user: Utilisateur = Depends(get_current_user), db: Session = Depends(get_db)):
    epargne = db.query(Epargne).filter(Epargne.id_epargne == id_epargne, Epargne.id_utilisateur == user.id_utilisateur).first()
    if not epargne:
        raise HTTPException(404, "Épargne introuvable")
    wallet = WalletService.get_or_create(db, user.id_utilisateur)
    if float(wallet.solde) < montant:
        raise HTTPException(400, "Solde insuffisant")
    wallet.solde = float(wallet.solde) - montant
    epargne.total_cumule = float(epargne.total_cumule) + montant
    if float(epargne.total_cumule) >= float(epargne.objectif_montant):
        epargne.statut = "atteint"
    db.commit()
    return ok({"total_cumule": float(epargne.total_cumule), "message": f"{montant} FCFA versés"})


# ── MICROCRÉDIT ──────────────────────────────────────────────

@router.get("/banques", response_model=List[dict])
def liste_banques(user: Utilisateur = Depends(get_current_user), db: Session = Depends(get_db)):
    banques = db.query(BanquePartenaire).filter(BanquePartenaire.actif == True).order_by(BanquePartenaire.ordre_affichage).all()
    result = []
    for b in banques:
        eligible = int(user.score_credit) >= int(b.score_min_requis)
        result.append({
            "id_banque": b.id_banque, "nom_banque": b.nom_banque,
            "taux_min": float(b.taux_interet_min), "taux_max": float(b.taux_interet_max),
            "montant_min": float(b.montant_min), "montant_max": float(b.montant_max),
            "score_requis": b.score_min_requis, "eligible": eligible,
            "conditions": b.conditions_texte
        })
    return result


@router.post("/credits/simuler", response_model=CreditSimulerOut)
def simuler_credit(data: CreditSimulerIn, user: Utilisateur = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        result = CreditService.simuler(db, data.id_banque, data.montant, data.duree_semaines)
        result["eligible"] = int(user.score_credit) >= result["score_requis"]
        return CreditSimulerOut(**result)
    except Exception as e:
        raise HTTPException(400, str(e))


@router.post("/credits/demander", status_code=201)
def demander_credit(data: CreditDemandeIn, user: Utilisateur = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        credit = CreditService.demander(
            db, user, data.id_banque, data.montant_demande,
            data.duree_semaines, data.objet_credit, data.motif_demande
        )
        return ok({"id_credit": credit.id_credit, "statut": credit.statut,
                   "montant_accorde": float(credit.montant_accorde or 0),
                   "mensualite": float(credit.mensualite or 0),
                   "message": "Crédit approuvé !"})
    except Exception as e:
        raise HTTPException(400, str(e))


@router.get("/credits", response_model=List[CreditOut])
def mes_credits(user: Utilisateur = Depends(get_current_user), db: Session = Depends(get_db)):
    credits = db.query(MicroCredit).filter(MicroCredit.id_emprunteur == user.id_utilisateur).order_by(MicroCredit.date_demande.desc()).all()
    result = []
    for c in credits:
        banque = db.query(BanquePartenaire).filter(BanquePartenaire.id_banque == c.id_banque).first()
        result.append(CreditOut(
            id_credit=c.id_credit,
            id_banque=c.id_banque,
            nom_banque=banque.nom_banque if banque else None,
            montant_demande=float(c.montant_demande),
            montant_accorde=float(c.montant_accorde) if c.montant_accorde else None,
            taux_interet=float(c.taux_interet),
            mensualite=float(c.mensualite) if c.mensualite else None,
            montant_rembourse=float(c.montant_rembourse),
            statut=c.statut,
            score_ml_decision=c.score_ml_decision,
            date_demande=c.date_demande
        ))
    return result


@router.get("/credits/{id_credit}/echeancier")
def echeancier_credit(id_credit: int, user: Utilisateur = Depends(get_current_user), db: Session = Depends(get_db)):
    credit = db.query(MicroCredit).filter(MicroCredit.id_credit == id_credit, MicroCredit.id_emprunteur == user.id_utilisateur).first()
    if not credit:
        raise HTTPException(404, "Crédit introuvable")
    echeances = db.query(EcheancierCredit).filter(EcheancierCredit.id_credit == id_credit).order_by(EcheancierCredit.numero_echeance).all()
    return ok({
        "id_credit": id_credit,
        "montant_accorde": float(credit.montant_accorde or 0),
        "montant_rembourse": float(credit.montant_rembourse),
        "statut": credit.statut,
        "progression_pct": round(float(credit.montant_rembourse) / float(credit.montant_total_du or 1) * 100, 1),
        "echeances": [{
            "id_echeance": e.id_echeance,
            "numero": e.numero_echeance,
            "date": str(e.date_echeance),
            "montant_du": float(e.montant_du),
            "montant_paye": float(e.montant_paye),
            "statut": e.statut,
            "rappel_j7": e.rappel_j7_envoye,
            "rappel_j3": e.rappel_j3_envoye,
        } for e in echeances]
    })


@router.post("/credits/echeances/{id_echeance}/rembourser")
def rembourser_echeance(id_echeance: int, user: Utilisateur = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        ech = CreditService.rembourser_echeance(db, id_echeance, user)
        return ok({"message": "Échéance remboursée", "statut": ech.statut})
    except Exception as e:
        raise HTTPException(400, str(e))


@router.post("/credits/{id_credit}/garanties", status_code=201)
def ajouter_garantie(id_credit: int, data: GarantieIn, user: Utilisateur = Depends(get_current_user), db: Session = Depends(get_db)):
    credit = db.query(MicroCredit).filter(MicroCredit.id_credit == id_credit, MicroCredit.id_emprunteur == user.id_utilisateur).first()
    if not credit:
        raise HTTPException(404, "Crédit introuvable")
    garantie = GarantieCredit(
        id_credit=id_credit, id_utilisateur=user.id_utilisateur,
        type_garantie=data.type_garantie, description=data.description,
        valeur_estimee=data.valeur_estimee, statut="actif"
    )
    db.add(garantie)
    db.commit()
    return ok({"message": "Garantie ajoutée"})


# ── TONTINE ──────────────────────────────────────────────────

@router.post("/tontines", status_code=201)
def creer_tontine(data: TontineCreateIn, user: Utilisateur = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        tontine = TontineService.creer(db, user, data.model_dump())
        return ok({"id_tontine": tontine.id_tontine, "code_invitation": tontine.code_invitation,
                   "message": f"Tontine '{tontine.nom_tontine}' créée !"})
    except Exception as e:
        raise HTTPException(400, str(e))


@router.get("/tontines", response_model=List[TontineOut])
def mes_tontines(user: Utilisateur = Depends(get_current_user), db: Session = Depends(get_db)):
    membres = db.query(MembreTontine).filter(
        MembreTontine.id_utilisateur == user.id_utilisateur,
        MembreTontine.statut == "actif"
    ).all()
    tontines = []
    for m in membres:
        t = db.query(Tontine).filter(Tontine.id_tontine == m.id_tontine).first()
        if t:
            tontines.append(TontineOut(
                id_tontine=t.id_tontine, nom_tontine=t.nom_tontine,
                cotisation_periodique=float(t.cotisation_periodique),
                frequence=t.frequence, nb_membres_actuel=t.nb_membres_actuel,
                nb_membres_max=t.nb_membres_max, cagnotte_actuelle=float(t.cagnotte_actuelle),
                cycle_actuel=t.cycle_actuel, statut=t.statut,
                code_invitation=t.code_invitation, prochain_paiement=t.prochain_paiement
            ))
    return tontines


@router.post("/tontines/rejoindre", status_code=201)
def rejoindre_tontine(data: RejoindreIn, user: Utilisateur = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        tontine = TontineService.rejoindre(db, user, data.code_invitation)
        return ok({"id_tontine": tontine.id_tontine, "message": f"Vous avez rejoint '{tontine.nom_tontine}'"})
    except Exception as e:
        raise HTTPException(400, str(e))


@router.get("/tontines/{id_tontine}")
def detail_tontine(id_tontine: int, user: Utilisateur = Depends(get_current_user), db: Session = Depends(get_db)):
    tontine = db.query(Tontine).filter(Tontine.id_tontine == id_tontine).first()
    if not tontine:
        raise HTTPException(404, "Tontine introuvable")
    membres = db.query(MembreTontine).filter(MembreTontine.id_tontine == id_tontine, MembreTontine.statut == "actif").all()
    cotisations_cycle = db.query(CotisationTontine).filter(
        CotisationTontine.id_tontine == id_tontine,
        CotisationTontine.cycle == tontine.cycle_actuel
    ).count()
    return ok({
        "id_tontine": tontine.id_tontine, "nom_tontine": tontine.nom_tontine,
        "cotisation_periodique": float(tontine.cotisation_periodique),
        "frequence": tontine.frequence, "cagnotte": float(tontine.cagnotte_actuelle),
        "cycle_actuel": tontine.cycle_actuel, "statut": tontine.statut,
        "penalite_retard_pct": float(tontine.penalite_retard_pct),
        "nb_membres": len(membres),
        "cotisations_ce_cycle": cotisations_cycle,
        "code_invitation": tontine.code_invitation,
        "membres": [{"id_utilisateur": m.id_utilisateur, "ordre": m.ordre_reception,
                     "total_cotise": float(m.total_cotise), "a_recu": m.a_recu_cagnotte} for m in membres]
    })


@router.post("/tontines/{id_tontine}/cotiser")
def cotiser_tontine(id_tontine: int, data: CotisationPayerIn, user: Utilisateur = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        cotisation = TontineService.payer_cotisation(db, user, id_tontine, data.mode_paiement)
        return ok({"id_cotisation": cotisation.id_cotisation, "montant": float(cotisation.montant),
                   "message": "Cotisation enregistrée !"})
    except Exception as e:
        raise HTTPException(400, str(e))


@router.post("/tontines/{id_tontine}/litiges", status_code=201)
def creer_litige(id_tontine: int, data: LitigeCreateIn, user: Utilisateur = Depends(get_current_user), db: Session = Depends(get_db)):
    membre = db.query(MembreTontine).filter(MembreTontine.id_membre == data.id_membre).first()
    if not membre:
        raise HTTPException(404, "Membre introuvable")
    litige = LitigeTontine(
        id_tontine=id_tontine, id_membre=data.id_membre,
        id_rapporteur=user.id_utilisateur,
        type_litige=data.type_litige, description=data.description,
        statut="ouvert"
    )
    db.add(litige)
    db.commit()
    return ok({"message": "Litige signalé", "id_litige": litige.id_litige})
