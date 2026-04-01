from sqlalchemy import Column, Integer, String, Boolean, Date, DateTime, JSON, Enum, ForeignKey, func
from app.core.database import Base

class HistoriqueScore(Base):
    __tablename__ = "historique_scores"
    id_historique  = Column(Integer, primary_key=True, autoincrement=True)
    id_utilisateur = Column(Integer, ForeignKey("utilisateurs.id_utilisateur", ondelete="CASCADE"), nullable=False, index=True)
    id_boutique    = Column(Integer, nullable=True)
    type_score     = Column(Enum("sante_business","credit"), nullable=False)
    score          = Column(Integer, nullable=False)
    details_json   = Column(JSON, nullable=True)
    date_calcul    = Column(Date, nullable=False)
