from sqlalchemy import Column, Integer, String, Boolean, DateTime, Numeric, ForeignKey, func, Text
from app.core.database import Base

class Boutique(Base):
    __tablename__ = "boutiques"
    id_boutique         = Column(Integer, primary_key=True, autoincrement=True)
    id_utilisateur      = Column(Integer, ForeignKey("utilisateurs.id_utilisateur", ondelete="RESTRICT"), nullable=False, index=True)
    nom_boutique        = Column(String(120), nullable=False)
    type_commerce       = Column(String(100), nullable=False, default="General")
    description         = Column(Text, nullable=True)
    ville               = Column(String(100), nullable=False, default="Ngaoundere")
    quartier            = Column(String(100), nullable=True)
    adresse_complete    = Column(String(255), nullable=True)
    latitude            = Column(Numeric(10,7), nullable=True)
    longitude           = Column(Numeric(10,7), nullable=True)
    logo_url            = Column(String(255), nullable=True)
    boutique_principale = Column(Boolean, nullable=False, default=True)
    actif               = Column(Boolean, nullable=False, default=True)
    date_creation       = Column(DateTime, nullable=False, server_default=func.now())
    date_modification   = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
