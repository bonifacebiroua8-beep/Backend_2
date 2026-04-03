# app/api/routes/ventes.py — UbuntuTech v3.0
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime
from app.core.dependencies import get_db, get_current_user
from app.models.utilisateur import Utilisateur
from app.models.vente import Vente, LigneVente
from app.models.produit import Produit
from app.models.client import Client
from app.schemas import VenteCreateIn, VenteOut
from app.services.vente_service import VenteService
from app.utils.responses import ok

router = APIRouter(prefix="/ventes", tags=["Ventes"])


@router.post("", response_model=VenteOut, status_code=201)
def creer_vente(data: VenteCreateIn, user: Utilisateur = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        vente = VenteService.creer_vente(db, user, data)
        return VenteOut(
            id_vente=vente.id_vente, id_boutique=vente.id_boutique,
            montant_total=float(vente.montant_total), montant_paye=float(vente.montant_paye),
            montant_credit=float(vente.montant_credit), mode_paiement=vente.mode_paiement,
            statut=vente.statut, date_vente=vente.date_vente, nb_lignes=0
        )
    except Exception as e:
        raise HTTPException(400, str(e))


@router.get("/{id_boutique}", response_model=List[VenteOut])
def liste_ventes(id_boutique: int, limit: int = 50, user: Utilisateur = Depends(get_current_user), db: Session = Depends(get_db)):
    ventes = db.query(Vente).filter(
        Vente.id_boutique == id_boutique, Vente.statut == "validee"
    ).order_by(Vente.date_vente.desc()).limit(limit).all()
    result = []
    for v in ventes:
        nb = db.query(func.count(LigneVente.id_ligne)).filter(LigneVente.id_vente == v.id_vente).scalar()
        result.append(VenteOut(
            id_vente=v.id_vente, id_boutique=v.id_boutique,
            montant_total=float(v.montant_total), montant_paye=float(v.montant_paye),
            montant_credit=float(v.montant_credit), mode_paiement=v.mode_paiement,
            statut=v.statut, date_vente=v.date_vente, nb_lignes=int(nb or 0)
        ))
    return result


@router.get("/detail/{id_vente}")
def detail_vente(id_vente: int, user: Utilisateur = Depends(get_current_user), db: Session = Depends(get_db)):
    vente = db.query(Vente).filter(Vente.id_vente == id_vente).first()
    if not vente:
        raise HTTPException(404, "Vente introuvable")
    lignes = db.query(LigneVente).filter(LigneVente.id_vente == id_vente).all()
    return ok({
        "id_vente": vente.id_vente, "montant_total": float(vente.montant_total),
        "mode_paiement": vente.mode_paiement, "statut": vente.statut,
        "date_vente": str(vente.date_vente),
        "lignes": [{"produit": l.nom_produit_snap, "quantite": float(l.quantite),
                    "prix": float(l.prix_unitaire), "montant": float(l.montant_ligne)} for l in lignes]
    })


@router.post("/{id_vente}/annuler")
def annuler_vente(id_vente: int, user: Utilisateur = Depends(get_current_user), db: Session = Depends(get_db)):
    vente = db.query(Vente).filter(Vente.id_vente == id_vente).first()
    if not vente:
        raise HTTPException(404, "Vente introuvable")
    if vente.statut != "validee":
        raise HTTPException(400, "Seules les ventes validées peuvent être annulées")
    vente.statut = "annulee"
    # Remettre le stock
    lignes = db.query(LigneVente).filter(LigneVente.id_vente == id_vente).all()
    for l in lignes:
        p = db.query(Produit).filter(Produit.id_produit == l.id_produit).first()
        if p:
            p.quantite_stock = float(p.quantite_stock) + float(l.quantite)
    db.commit()
    return ok({"message": "Vente annulée et stock restauré"})
