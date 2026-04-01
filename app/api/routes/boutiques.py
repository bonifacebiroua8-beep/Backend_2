# app/api/routes/boutiques.py — UbuntuTech v3.0
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from datetime import datetime, timedelta

from app.core.dependencies import get_db, get_current_user
from app.models.utilisateur import Utilisateur
from app.models.boutique import Boutique
from app.models.vente import Vente, LigneVente
from app.models.depense import Depense
from app.models.produit import Produit
from app.models.client import Client
from app.schemas import BoutiqueCreateIn, BoutiqueOut, BoutiqueUpdateIn, DashboardOut
from app.services.ia_service import IAService
from app.utils.responses import ok

router = APIRouter(prefix="/boutiques", tags=["Boutiques"])


@router.post("", response_model=BoutiqueOut, status_code=201)
def creer_boutique(data: BoutiqueCreateIn, user: Utilisateur = Depends(get_current_user), db: Session = Depends(get_db)):
    nb = db.query(Boutique).filter(Boutique.id_utilisateur == user.id_utilisateur, Boutique.actif == True).count()
    boutique = Boutique(
        id_utilisateur=user.id_utilisateur,
        nom_boutique=data.nom_boutique,
        type_commerce=data.type_commerce,
        ville=data.ville,
        quartier=data.quartier,
        adresse_complete=data.adresse_complete,
        latitude=data.latitude,
        longitude=data.longitude,
        description=data.description,
        boutique_principale=(nb == 0)
    )
    db.add(boutique)
    db.commit()
    db.refresh(boutique)
    return boutique


@router.get("", response_model=List[BoutiqueOut])
def mes_boutiques(user: Utilisateur = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Boutique).filter(Boutique.id_utilisateur == user.id_utilisateur, Boutique.actif == True).all()


@router.get("/{id_boutique}", response_model=BoutiqueOut)
def get_boutique(id_boutique: int, user: Utilisateur = Depends(get_current_user), db: Session = Depends(get_db)):
    b = db.query(Boutique).filter(Boutique.id_boutique == id_boutique, Boutique.id_utilisateur == user.id_utilisateur).first()
    if not b:
        raise HTTPException(404, "Boutique introuvable")
    return b


@router.put("/{id_boutique}", response_model=BoutiqueOut)
def modifier_boutique(id_boutique: int, data: BoutiqueUpdateIn, user: Utilisateur = Depends(get_current_user), db: Session = Depends(get_db)):
    b = db.query(Boutique).filter(Boutique.id_boutique == id_boutique, Boutique.id_utilisateur == user.id_utilisateur).first()
    if not b:
        raise HTTPException(404, "Boutique introuvable")
    for k, v in data.model_dump(exclude_none=True).items():
        setattr(b, k, v)
    db.commit()
    db.refresh(b)
    return b


@router.delete("/{id_boutique}")
def archiver_boutique(id_boutique: int, user: Utilisateur = Depends(get_current_user), db: Session = Depends(get_db)):
    b = db.query(Boutique).filter(Boutique.id_boutique == id_boutique, Boutique.id_utilisateur == user.id_utilisateur).first()
    if not b:
        raise HTTPException(404, "Boutique introuvable")
    b.actif = False
    db.commit()
    return ok({"message": "Boutique archivée"})


@router.get("/{id_boutique}/dashboard", response_model=DashboardOut)
def dashboard(id_boutique: int, user: Utilisateur = Depends(get_current_user), db: Session = Depends(get_db)):
    b = db.query(Boutique).filter(Boutique.id_boutique == id_boutique, Boutique.id_utilisateur == user.id_utilisateur).first()
    if not b:
        raise HTTPException(404, "Boutique introuvable")
    now = datetime.utcnow()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday = today - timedelta(days=1)

    ventes_jour = float(db.query(func.coalesce(func.sum(Vente.montant_total), 0)).filter(
        Vente.id_boutique == id_boutique, Vente.statut == "validee", Vente.date_vente >= today).scalar())
    nb_ventes = int(db.query(func.count(Vente.id_vente)).filter(
        Vente.id_boutique == id_boutique, Vente.statut == "validee", Vente.date_vente >= today).scalar())
    ventes_hier = float(db.query(func.coalesce(func.sum(Vente.montant_total), 0)).filter(
        Vente.id_boutique == id_boutique, Vente.statut == "validee",
        Vente.date_vente >= yesterday, Vente.date_vente < today).scalar())
    depenses_jour = float(db.query(func.coalesce(func.sum(Depense.montant), 0)).filter(
        Depense.id_boutique == id_boutique, Depense.date_depense >= today).scalar())
    nb_alertes = int(db.query(func.count(Produit.id_produit)).filter(
        Produit.id_boutique == id_boutique, Produit.actif == True,
        Produit.quantite_stock <= Produit.seuil_alerte_stock).scalar())
    credits_clients = float(db.query(func.coalesce(func.sum(Client.solde_credit), 0)).filter(
        Client.id_boutique == id_boutique, Client.actif == True, Client.solde_credit > 0).scalar())

    benefice = ventes_jour - depenses_jour
    variation = round((ventes_jour - ventes_hier) / ventes_hier * 100, 1) if ventes_hier > 0 else 0
    if variation > 10:
        meteo, tendance = "bon", "hausse"
    elif variation < -10:
        meteo, tendance = "difficile", "baisse"
    else:
        meteo, tendance = "moyen", "stable"

    score = int(user.score_sante_business)
    if score >= 80: label = "Excellent"
    elif score >= 60: label = "Bon"
    elif score >= 40: label = "Moyen"
    else: label = "Critique"

    conseil = None
    try:
        conseil = IAService.generer_conseil_quotidien(db, id_boutique, user)
    except Exception:
        pass

    return DashboardOut(
        id_boutique=id_boutique, nom_boutique=b.nom_boutique,
        score_sante_business=score, label_score=label,
        ventes_jour=ventes_jour, benefice_jour=benefice,
        nb_ventes_jour=nb_ventes, nb_alertes_stock=nb_alertes,
        ventes_hier=ventes_hier, variation_pct=variation,
        meteo=meteo, tendance=tendance,
        total_credits_clients=credits_clients, conseil_ia=conseil
    )
