from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, func
from app.core.database import Base

class LogAdmin(Base):
    __tablename__ = "logs_admin"
    id_log_admin = Column(Integer, primary_key=True, autoincrement=True)
    id_admin     = Column(Integer, ForeignKey("administrateurs.id_admin", ondelete="CASCADE"), nullable=False, index=True)
    action       = Column(String(100), nullable=False)
    details_json = Column(JSON, nullable=True)
    ip_address   = Column(String(45), nullable=True)
    date_action  = Column(DateTime, nullable=False, server_default=func.now(), index=True)
