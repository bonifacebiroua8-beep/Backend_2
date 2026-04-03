from sqlalchemy import Column, Integer, String, Date, DateTime, Numeric, Enum, JSON, ForeignKey, func
from app.core.database import Base

class PrevisionML(Base):
    __tablename__ = "previsions_ml"
    id_prevision   = Column(Integer, primary_key=True, autoincrement=True)
    id_boutique    = Column(Integer, ForeignKey("boutiques.id_boutique", ondelete="CASCADE"), nullable=False, index=True)
    type_prevision = Column(Enum("ventes_7j","ventes_30j","stock_rupture","meilleur_produit","conseil_approvisionnement"), nullable=False)
    date_prevision = Column(Date, nullable=False)
    valeur_prevue  = Column(Numeric(14,2), nullable=True)
    confiance_pct  = Column(Integer, nullable=True)
    details_json   = Column(JSON, nullable=True)
    date_calcul    = Column(DateTime, nullable=False, server_default=func.now())
