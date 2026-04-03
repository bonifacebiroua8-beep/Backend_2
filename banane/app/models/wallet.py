from sqlalchemy import Column, Integer, String, Boolean, DateTime, Numeric, ForeignKey, func
from app.core.database import Base

class Wallet(Base):
    __tablename__ = "wallets"
    id_wallet            = Column(Integer, primary_key=True, autoincrement=True)
    id_utilisateur       = Column(Integer, ForeignKey("utilisateurs.id_utilisateur", ondelete="CASCADE"), nullable=False, unique=True)
    solde                = Column(Numeric(14,2), nullable=False, default=0)
    solde_bloque         = Column(Numeric(14,2), nullable=False, default=0)
    devise               = Column(String(10), nullable=False, default="FCFA")
    plafond_journalier   = Column(Numeric(12,2), nullable=False, default=500000)
    nb_transactions_jour = Column(Integer, nullable=False, default=0)
    dernier_retrait      = Column(DateTime, nullable=True)
    actif                = Column(Boolean, nullable=False, default=True)
    date_creation        = Column(DateTime, nullable=False, server_default=func.now())
    date_maj             = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
