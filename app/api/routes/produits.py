# app/api/routes/produits.py — UbuntuTech v3.0
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from app.core.dependencies import get_db, get_current_user
from app.models.utilisateur import Utilisateur
from app.models.produit import Produit, CategorieProduit
from app.models.stock import MouvementStock
from app.schemas import ProduitCreateIn, ProduitOut, ProduitUpdateIn, StockAjustIn
from app.utils.responses import ok

router = APIRouter(prefix="/produits", tags=["Produits"])


@router.get("/categories")
def categories(db: Session = Depends(get_db)):
    cats = db.query(CategorieProduit).filter(CategorieProduit.actif == True).all()
    return ok({"categories": [{"id": c.id_categorie, "nom": c.nom_categorie, "icone": c.icone} for c in cats]})


@router.post("", response_model=ProduitOut, status_code=201)
def creer_produit(data: ProduitCreateIn, user: Utilisateur = Depends(get_current_user), db: Session = Depends(get_db)):
    marge = round((data.prix_vente - data.prix_achat) / data.prix_vente * 100, 2) if data.prix_vente > 0 else 0
    p = Produit(
        id_boutique=data.id_boutique, nom_produit=data.nom_produit,
        prix_vente=data.prix_vente, prix_achat=data.prix_achat,
        quantite_stock=data.quantite_stock, seuil_alerte_stock=data.seuil_alerte_stock,
        unite=data.unite, id_categorie=data.id_categorie,
        code_barres=data.code_barres, description=data.description, marge_pct=marge
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    out = ProduitOut.model_validate(p)
    out.statut_stock = _statut_stock(p)
    return out


@router.get("/{id_boutique}", response_model=List[ProduitOut])
def liste_produits(id_boutique: int, search: Optional[str] = None, id_categorie: Optional[int] = None,
                   user: Utilisateur = Depends(get_current_user), db: Session = Depends(get_db)):
    q = db.query(Produit).filter(Produit.id_boutique == id_boutique, Produit.actif == True)
    if search:
        q = q.filter(Produit.nom_produit.ilike(f"%{search}%"))
    if id_categorie:
        q = q.filter(Produit.id_categorie == id_categorie)
    produits = q.order_by(Produit.nom_produit).all()
    result = []
    for p in produits:
        out = ProduitOut.model_validate(p)
        out.statut_stock = _statut_stock(p)
        result.append(out)
    return result


@router.put("/{id_produit}", response_model=ProduitOut)
def modifier_produit(id_produit: int, data: ProduitUpdateIn, user: Utilisateur = Depends(get_current_user), db: Session = Depends(get_db)):
    p = db.query(Produit).filter(Produit.id_produit == id_produit).first()
    if not p:
        raise HTTPException(404, "Produit introuvable")
    for k, v in data.model_dump(exclude_none=True).items():
        setattr(p, k, v)
    if p.prix_vente and p.prix_achat:
        p.marge_pct = round((float(p.prix_vente) - float(p.prix_achat)) / float(p.prix_vente) * 100, 2)
    db.commit()
    db.refresh(p)
    return ProduitOut.model_validate(p)


@router.delete("/{id_produit}")
def supprimer_produit(id_produit: int, user: Utilisateur = Depends(get_current_user), db: Session = Depends(get_db)):
    p = db.query(Produit).filter(Produit.id_produit == id_produit).first()
    if not p:
        raise HTTPException(404, "Produit introuvable")
    p.actif = False
    db.commit()
    return ok({"message": "Produit supprimé"})


@router.post("/{id_produit}/stock/ajuster")
def ajuster_stock(id_produit: int, data: StockAjustIn, user: Utilisateur = Depends(get_current_user), db: Session = Depends(get_db)):
    p = db.query(Produit).filter(Produit.id_produit == id_produit).first()
    if not p:
        raise HTTPException(404, "Produit introuvable")
    avant = float(p.quantite_stock)
    if data.type_mouvement == "entree":
        p.quantite_stock = avant + data.quantite
    elif data.type_mouvement == "sortie":
        if avant < data.quantite:
            raise HTTPException(400, "Stock insuffisant")
        p.quantite_stock = avant - data.quantite
    else:
        p.quantite_stock = data.quantite
    apres = float(p.quantite_stock)
    mvt = MouvementStock(
        id_produit=id_produit, id_boutique=data.id_boutique,
        type_mouvement=data.type_mouvement, quantite=data.quantite,
        quantite_avant=avant, quantite_apres=apres,
        motif=data.motif, prix_unitaire=data.prix_unitaire, source="texte"
    )
    db.add(mvt)
    db.commit()
    return ok({"quantite_avant": avant, "quantite_apres": apres, "statut": _statut_stock(p)})


@router.get("/{id_boutique}/alertes")
def alertes_stock(id_boutique: int, user: Utilisateur = Depends(get_current_user), db: Session = Depends(get_db)):
    produits = db.query(Produit).filter(
        Produit.id_boutique == id_boutique, Produit.actif == True,
        Produit.quantite_stock <= Produit.seuil_alerte_stock
    ).all()
    return ok({"nb_alertes": len(produits), "produits": [
        {"id": p.id_produit, "nom": p.nom_produit, "stock": float(p.quantite_stock),
         "seuil": float(p.seuil_alerte_stock), "statut": _statut_stock(p)} for p in produits
    ]})


def _statut_stock(p: Produit) -> str:
    stock = float(p.quantite_stock)
    seuil = float(p.seuil_alerte_stock)
    if stock == 0: return "RUPTURE"
    if stock <= seuil: return "CRITIQUE"
    if stock <= seuil * 2: return "ATTENTION"
    return "OK"
