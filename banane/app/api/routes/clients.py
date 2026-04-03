# app/api/routes/clients.py — UbuntuTech v3.0
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.dependencies import get_db, get_current_user
from app.models.utilisateur import Utilisateur
from app.models.client import Client
from app.schemas import ClientCreateIn, ClientOut, RemboursementIn
from app.utils.responses import ok

router = APIRouter(prefix="/clients", tags=["Clients"])


@router.post("", response_model=ClientOut, status_code=201)
def creer_client(data: ClientCreateIn, user: Utilisateur = Depends(get_current_user), db: Session = Depends(get_db)):
    client = Client(
        id_boutique=data.id_boutique, nom_client=data.nom_client,
        telephone=data.telephone, adresse=data.adresse,
        limite_credit=data.limite_credit, notes=data.notes
    )
    db.add(client)
    db.commit()
    db.refresh(client)
    return client


@router.get("/{id_boutique}", response_model=List[ClientOut])
def liste_clients(id_boutique: int, user: Utilisateur = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Client).filter(Client.id_boutique == id_boutique, Client.actif == True).order_by(Client.nom_client).all()


@router.get("/detail/{id_client}", response_model=ClientOut)
def get_client(id_client: int, user: Utilisateur = Depends(get_current_user), db: Session = Depends(get_db)):
    client = db.query(Client).filter(Client.id_client == id_client).first()
    if not client:
        raise HTTPException(404, "Client introuvable")
    return client


@router.post("/{id_client}/rembourser")
def rembourser(id_client: int, data: RemboursementIn, user: Utilisateur = Depends(get_current_user), db: Session = Depends(get_db)):
    client = db.query(Client).filter(Client.id_client == id_client).first()
    if not client:
        raise HTTPException(404, "Client introuvable")
    if data.montant > float(client.solde_credit):
        raise HTTPException(400, f"Montant supérieur au crédit dû ({client.solde_credit} FCFA)")
    client.solde_credit = float(client.solde_credit) - data.montant
    db.commit()
    return ok({"solde_restant": float(client.solde_credit), "message": f"{data.montant} FCFA remboursés"})


@router.delete("/{id_client}")
def supprimer_client(id_client: int, user: Utilisateur = Depends(get_current_user), db: Session = Depends(get_db)):
    client = db.query(Client).filter(Client.id_client == id_client).first()
    if not client:
        raise HTTPException(404, "Client introuvable")
    client.actif = False
    db.commit()
    return ok({"message": "Client supprimé"})
