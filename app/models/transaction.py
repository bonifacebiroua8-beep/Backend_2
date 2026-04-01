from sqlalchemy import Column, Integer, String, Boolean, DateTime, Numeric, Enum, Text, ForeignKey, func
from app.core.database import Base

class TransactionFinanciere(Base):
    __tablename__ = "transactions_financieres"
    id_transaction   = Column(Integer, primary_key=True, autoincrement=True)
    id_utilisateur   = Column(Integer, ForeignKey("utilisateurs.id_utilisateur", ondelete="RESTRICT"), nullable=False, index=True)
    id_boutique      = Column(Integer, ForeignKey("boutiques.id_boutique", ondelete="SET NULL"), nullable=True, index=True)
    id_vente         = Column(Integer, ForeignKey("ventes.id_vente", ondelete="SET NULL"), nullable=True)
    id_depense       = Column(Integer, nullable=True)
    type_transaction = Column(Enum("vente","achat_stock","depense_operationnelle","credit_client_accorde","credit_client_rembourse","depot_wallet","retrait_wallet","transfert_wallet","cotisation_tontine","reception_tontine","microcredit_recu","microcredit_rembourse","epargne_versement","epargne_retrait","abonnement","remboursement","autre"), nullable=False)
    montant          = Column(Numeric(12,2), nullable=False)
    sens             = Column(Enum("entree","sortie"), nullable=False)
    solde_apres      = Column(Numeric(12,2), nullable=True)
    libelle          = Column(String(255), nullable=False)
    description      = Column(Text, nullable=True)
    reference        = Column(String(100), nullable=True)
    synchro_serveur  = Column(Boolean, nullable=False, default=False)
    date_transaction = Column(DateTime, nullable=False, server_default=func.now(), index=True)
