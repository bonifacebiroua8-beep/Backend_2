from sqlalchemy import Column, Integer, Boolean, DateTime, Enum, ForeignKey, func
from app.core.database import Base

class Administrateur(Base):
    __tablename__ = "administrateurs"
    id_admin                   = Column(Integer, primary_key=True, autoincrement=True)
    id_utilisateur             = Column(Integer, ForeignKey("utilisateurs.id_utilisateur", ondelete="CASCADE"), nullable=False, unique=True)
    niveau_acces               = Column(Enum("super_admin","admin_ia","admin_support","admin_finance"), nullable=False, default="admin_support")
    peut_entrainer_ia          = Column(Boolean, nullable=False, default=True)
    peut_valider_vocab         = Column(Boolean, nullable=False, default=True)
    peut_modifier_connaissance = Column(Boolean, nullable=False, default=True)
    peut_voir_all_users        = Column(Boolean, nullable=False, default=True)
    peut_gerer_abonnements     = Column(Boolean, nullable=False, default=True)
    peut_approuver_credits     = Column(Boolean, nullable=False, default=False)
    actif                      = Column(Boolean, nullable=False, default=True)
    date_creation              = Column(DateTime, nullable=False, server_default=func.now())
