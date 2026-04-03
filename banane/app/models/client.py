# app/models/client.py
# FIX : colonne quartier ajoutée
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Numeric, Text, ForeignKey, func
from app.core.database import Base

class Client(Base):
    __tablename__ = "clients"
    id_client          = Column(Integer, primary_key=True, autoincrement=True)
    id_boutique        = Column(Integer, ForeignKey("boutiques.id_boutique", ondelete="RESTRICT"), nullable=False, index=True)
    nom_client         = Column(String(120), nullable=False)
    telephone          = Column(String(20), nullable=True)
    adresse            = Column(String(255), nullable=True)
    quartier           = Column(String(100), nullable=True)
    solde_credit       = Column(Numeric(12,2), nullable=False, default=0)
    limite_credit      = Column(Numeric(12,2), nullable=False, default=10000)
    fiabilite_paiement = Column(Integer, nullable=False, default=50)
    nb_achats          = Column(Integer, nullable=False, default=0)
    total_achats       = Column(Numeric(14,2), nullable=False, default=0)
    derniere_visite    = Column(DateTime, nullable=True)
    actif              = Column(Boolean, nullable=False, default=True)
    notes              = Column(Text, nullable=True)
    date_creation      = Column(DateTime, nullable=False, server_default=func.now())
