from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, Numeric, Enum, ForeignKey, func
from app.core.database import Base

class EcheancierCredit(Base):
    __tablename__ = "echeancier_credits"
    id_echeance        = Column(Integer, primary_key=True, autoincrement=True)
    id_credit          = Column(Integer, ForeignKey("micro_credits.id_credit", ondelete="CASCADE"), nullable=False, index=True)
    id_utilisateur     = Column(Integer, ForeignKey("utilisateurs.id_utilisateur", ondelete="RESTRICT"), nullable=False, index=True)
    numero_echeance    = Column(Integer, nullable=False)
    date_echeance      = Column(Date, nullable=False, index=True)
    montant_du         = Column(Numeric(12,2), nullable=False)
    montant_principal  = Column(Numeric(12,2), nullable=False, default=0)
    montant_interet    = Column(Numeric(12,2), nullable=False, default=0)
    montant_paye       = Column(Numeric(12,2), nullable=False, default=0)
    montant_penalite   = Column(Numeric(12,2), nullable=False, default=0)
    solde_restant      = Column(Numeric(12,2), nullable=False, default=0)
    statut             = Column(Enum("a_venir","due","payee","retard","partiellement_payee","annulee"), nullable=False, default="a_venir", index=True)
    date_paiement      = Column(DateTime, nullable=True)
    mode_paiement      = Column(Enum("wallet","mobile_money","cash","virement"), nullable=True)
    reference_paiement = Column(String(100), nullable=True)
    rappel_j7_envoye   = Column(Boolean, nullable=False, default=False)
    rappel_j3_envoye   = Column(Boolean, nullable=False, default=False)
    rappel_j1_envoye   = Column(Boolean, nullable=False, default=False)
    note               = Column(String(255), nullable=True)
    date_creation      = Column(DateTime, nullable=False, server_default=func.now())
    date_modification  = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
