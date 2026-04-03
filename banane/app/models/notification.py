from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, Text, ForeignKey, func
from app.core.database import Base

class Notification(Base):
    __tablename__ = "notifications"
    id_notification = Column(Integer, primary_key=True, autoincrement=True)
    id_utilisateur  = Column(Integer, ForeignKey("utilisateurs.id_utilisateur", ondelete="CASCADE"), nullable=False, index=True)
    id_boutique     = Column(Integer, nullable=True)
    type_notif      = Column(Enum("stock_faible","remboursement_du","credit_retard","rapport_hebdo","tontine_cotisation","abonnement_expire","sync_erreur","conseil_ia","systeme"), nullable=False)
    titre           = Column(String(150), nullable=False)
    message         = Column(Text, nullable=False)
    lue             = Column(Boolean, nullable=False, default=False)
    action_url      = Column(String(255), nullable=True)
    date_creation   = Column(DateTime, nullable=False, server_default=func.now())
    date_lecture    = Column(DateTime, nullable=True)
