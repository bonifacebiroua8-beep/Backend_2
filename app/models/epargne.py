from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, Numeric, Enum, JSON, ForeignKey, func
from app.core.database import Base

class Epargne(Base):
    __tablename__ = "epargnes"
    id_epargne                = Column(Integer, primary_key=True, autoincrement=True)
    id_utilisateur            = Column(Integer, ForeignKey("utilisateurs.id_utilisateur", ondelete="CASCADE"), nullable=False, index=True)
    objectif_libelle          = Column(String(150), nullable=True)
    categorie_objectif        = Column(Enum("stock","equipement","urgence","education","autre"), nullable=False, default="autre")
    objectif_montant          = Column(Numeric(12,2), nullable=False, default=0)
    montant_mensuel_cible     = Column(Numeric(12,2), nullable=False, default=0)
    total_cumule              = Column(Numeric(14,2), nullable=False, default=0)
    statut                    = Column(Enum("actif","atteint","abandonne"), nullable=False, default="actif")
    versement_auto            = Column(Boolean, nullable=False, default=False)
    prochaine_date_versement  = Column(Date, nullable=True)
    historique_versements     = Column(JSON, nullable=True)
    date_cible                = Column(Date, nullable=True)
    date_creation             = Column(DateTime, nullable=False, server_default=func.now())
    date_modification         = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
