# app/api/routes/finances.py — UbuntuTech v3.0
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import Optional
from app.core.dependencies import get_db, get_current_user
from app.models.utilisateur import Utilisateur
from app.models.vente import Vente, LigneVente
from app.models.depense import Depense
from app.models.client import Client
from app.schemas import DepenseCreateIn, DepenseOut, BilanOut
from app.services.export_service import ExportService
from app.utils.responses import ok

router = APIRouter(prefix="/finances", tags=["Finances"])


@router.get("/bilan/{id_boutique}", response_model=BilanOut)
def bilan(id_boutique: int, periode: str = "mois",
          user: Utilisateur = Depends(get_current_user), db: Session = Depends(get_db)):
    now = datetime.utcnow()
    if periode == "jour":
        debut = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif periode == "semaine":
        debut = now - timedelta(days=7)
    elif periode == "trimestre":
        debut = now - timedelta(days=90)
    elif periode == "annee":
        debut = now.replace(month=1, day=1, hour=0, minute=0, second=0)
    else:
        debut = now.replace(day=1, hour=0, minute=0, second=0)

    revenus = float(db.query(func.coalesce(func.sum(Vente.montant_total), 0)).filter(
        Vente.id_boutique == id_boutique, Vente.statut == "validee", Vente.date_vente >= debut).scalar())
    depenses = float(db.query(func.coalesce(func.sum(Depense.montant), 0)).filter(
        Depense.id_boutique == id_boutique, Depense.date_depense >= debut).scalar())
    nb_ventes = int(db.query(func.count(Vente.id_vente)).filter(
        Vente.id_boutique == id_boutique, Vente.statut == "validee", Vente.date_vente >= debut).scalar())
    credits = float(db.query(func.coalesce(func.sum(Client.solde_credit), 0)).filter(
        Client.id_boutique == id_boutique, Client.actif == True, Client.solde_credit > 0).scalar())

    return BilanOut(
        id_boutique=id_boutique, periode=periode,
        revenus=revenus, depenses=depenses,
        benefice_net=revenus - depenses, nb_ventes=nb_ventes,
        credits_clients=credits
    )


@router.post("/depenses", response_model=DepenseOut, status_code=201)
def creer_depense(data: DepenseCreateIn, user: Utilisateur = Depends(get_current_user), db: Session = Depends(get_db)):
    dep = Depense(
        id_boutique=data.id_boutique, categorie=data.categorie,
        libelle=data.libelle, montant=data.montant,
        mode_paiement=data.mode_paiement, note=data.note, source=data.source
    )
    db.add(dep)
    db.commit()
    db.refresh(dep)
    return dep


@router.get("/depenses/{id_boutique}")
def liste_depenses(id_boutique: int, limit: int = 50, user: Utilisateur = Depends(get_current_user), db: Session = Depends(get_db)):
    depenses = db.query(Depense).filter(Depense.id_boutique == id_boutique).order_by(Depense.date_depense.desc()).limit(limit).all()
    return ok({"depenses": [{"id": d.id_depense, "categorie": d.categorie, "libelle": d.libelle,
                              "montant": float(d.montant), "date": str(d.date_depense)} for d in depenses]})


@router.post("/export-bilan/{id_boutique}")
def exporter_bilan(id_boutique: int, periode: str = "mois", format: str = "pdf",
                   user: Utilisateur = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        path = ExportService.generer_bilan_pdf(db, id_boutique, user, periode)
        return ok({"fichier": path, "message": "Bilan généré"})
    except Exception as e:
        raise HTTPException(500, str(e))
