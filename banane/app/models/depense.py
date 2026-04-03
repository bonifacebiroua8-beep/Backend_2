from sqlalchemy import Column, Integer, String, Boolean, DateTime, Numeric, Enum, Text, ForeignKey, func
from app.core.database import Base

class Depense(Base):
    __tablename__ = "depenses"
    id_depense    = Column(Integer, primary_key=True, autoincrement=True)
    id_boutique   = Column(Integer, ForeignKey("boutiques.id_boutique", ondelete="RESTRICT"), nullable=False, index=True)
    id_employe    = Column(Integer, nullable=True)
    categorie     = Column(Enum("loyer","transport","salaire","fournisseur","eau_electricite","telephone","entretien","publicite","taxes","autre"), nullable=False, default="autre")
    libelle       = Column(String(200), nullable=False)
    montant       = Column(Numeric(12,2), nullable=False)
    mode_paiement = Column(Enum("cash","mobile_money","virement","cheque"), nullable=False, default="cash")
    source        = Column(Enum("vocal","texte","import"), nullable=False, default="texte")
    synced        = Column(Boolean, nullable=False, default=False)
    note          = Column(Text, nullable=True)
    date_depense  = Column(DateTime, nullable=False, server_default=func.now(), index=True)
