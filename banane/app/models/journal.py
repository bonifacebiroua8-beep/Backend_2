from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, ForeignKey, func
from app.core.database import Base

class JournalConnexion(Base):
    __tablename__ = "journaux_connexion"
    id_journal     = Column(Integer, primary_key=True, autoincrement=True)
    id_utilisateur = Column(Integer, ForeignKey("utilisateurs.id_utilisateur", ondelete="CASCADE"), nullable=False, index=True)
    action         = Column(Enum("login","logout","echec","pin_change","delete_request"), nullable=False)
    ip_address     = Column(String(45), nullable=True)
    device_info    = Column(String(255), nullable=True)
    succes         = Column(Boolean, nullable=False, default=True)
    message        = Column(String(255), nullable=True)
    date_action    = Column(DateTime, nullable=False, server_default=func.now())
