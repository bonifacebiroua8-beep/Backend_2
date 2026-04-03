from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, ForeignKey, func
from app.core.database import Base

class EmployeBoutique(Base):
    __tablename__ = "employes_boutique"
    id_employe        = Column(Integer, primary_key=True, autoincrement=True)
    id_boutique       = Column(Integer, ForeignKey("boutiques.id_boutique", ondelete="CASCADE"), nullable=False)
    id_utilisateur    = Column(Integer, ForeignKey("utilisateurs.id_utilisateur", ondelete="CASCADE"), nullable=False)
    id_role           = Column(Integer, ForeignKey("roles.id_role"), nullable=False)
    nom_employe       = Column(String(120), nullable=False)
    telephone_employe = Column(String(20), nullable=True)
    actif             = Column(Boolean, nullable=False, default=True)
    date_embauche     = Column(Date, nullable=True)
    date_creation     = Column(DateTime, nullable=False, server_default=func.now())
