from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, Enum, ForeignKey, func
from app.core.database import Base

class SyncQueue(Base):
    __tablename__ = "sync_queue"
    id_sync           = Column(Integer, primary_key=True, autoincrement=True)
    id_utilisateur    = Column(Integer, ForeignKey("utilisateurs.id_utilisateur", ondelete="CASCADE"), nullable=False, index=True)
    id_boutique       = Column(Integer, nullable=True)
    table_cible       = Column(String(60), nullable=False)
    id_enregistrement = Column(Integer, nullable=True)
    operation         = Column(Enum("insert","update","delete"), nullable=False)
    donnees_json      = Column(JSON, nullable=False)
    priorite          = Column(Integer, nullable=False, default=5)
    statut            = Column(Enum("pending","done","failed","conflict"), nullable=False, default="pending", index=True)
    nb_tentatives     = Column(Integer, nullable=False, default=0)
    erreur_message    = Column(String(255), nullable=True)
    date_creation     = Column(DateTime, nullable=False, server_default=func.now())
    date_sync         = Column(DateTime, nullable=True)
