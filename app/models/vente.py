from sqlalchemy import Column, Integer, String, Boolean, DateTime, Numeric, Enum, ForeignKey, func
from app.core.database import Base

class Vente(Base):
    __tablename__ = "ventes"
    id_vente        = Column(Integer, primary_key=True, autoincrement=True)
    id_boutique     = Column(Integer, ForeignKey("boutiques.id_boutique", ondelete="RESTRICT"), nullable=False, index=True)
    id_client       = Column(Integer, ForeignKey("clients.id_client", ondelete="SET NULL"), nullable=True, index=True)
    id_employe      = Column(Integer, nullable=True)
    id_transcription = Column(Integer, nullable=True)
    montant_total   = Column(Numeric(12,2), nullable=False)
    montant_paye    = Column(Numeric(12,2), nullable=False, default=0)
    montant_credit  = Column(Numeric(12,2), nullable=False, default=0)
    mode_paiement   = Column(Enum("cash","mobile_money","credit","tontine","mixte"), nullable=False, default="cash")
    source_saisie   = Column(Enum("vocal","texte","sync","import"), nullable=False, default="texte")
    langue_saisie   = Column(Enum("fr","ff","ha","mfa"), nullable=False, default="fr")
    statut          = Column(Enum("validee","annulee","remboursee"), nullable=False, default="validee", index=True)
    synchro_serveur = Column(Boolean, nullable=False, default=False)
    note            = Column(String(255), nullable=True)
    date_vente      = Column(DateTime, nullable=False, server_default=func.now(), index=True)

class LigneVente(Base):
    __tablename__ = "lignes_vente"
    id_ligne            = Column(Integer, primary_key=True, autoincrement=True)
    id_vente            = Column(Integer, ForeignKey("ventes.id_vente", ondelete="CASCADE"), nullable=False, index=True)
    id_produit          = Column(Integer, ForeignKey("produits.id_produit", ondelete="RESTRICT"), nullable=False, index=True)
    nom_produit_snap    = Column(String(150), nullable=False)
    quantite            = Column(Numeric(12,3), nullable=False)
    unite               = Column(String(30), nullable=False, default="unite")
    prix_unitaire       = Column(Numeric(12,2), nullable=False)
    prix_achat_snapshot = Column(Numeric(12,2), nullable=False, default=0)
    remise_pct          = Column(Numeric(5,2), nullable=False, default=0)
    montant_ligne       = Column(Numeric(12,2), nullable=False)
    marge_ligne         = Column(Numeric(12,2), nullable=False, default=0)
