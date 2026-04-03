from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, func
from app.core.database import Base

class SessionAuth(Base):
    __tablename__ = "sessions"
    id_session      = Column(Integer, primary_key=True, autoincrement=True)
    id_utilisateur  = Column(Integer, ForeignKey("utilisateurs.id_utilisateur", ondelete="CASCADE"), nullable=False, index=True)
    token_hash      = Column(String(255), unique=True, nullable=False)
    device_info     = Column(String(255), nullable=True)
    ip_address      = Column(String(45), nullable=True)
    actif           = Column(Boolean, nullable=False, default=True)
    date_creation   = Column(DateTime, nullable=False, server_default=func.now())
    date_expiration = Column(DateTime, nullable=False)
