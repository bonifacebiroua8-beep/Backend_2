from sqlalchemy import Column, Integer, String, Boolean, Enum
from app.core.database import Base

class Role(Base):
    __tablename__ = "roles"
    id_role             = Column(Integer, primary_key=True, autoincrement=True)
    code_role           = Column(Enum("proprietaire","gerant","caissier","lecture_seule"), nullable=False, unique=True)
    nom_role            = Column(String(60), nullable=False)
    peut_vendre         = Column(Boolean, nullable=False, default=False)
    peut_gerer_stock    = Column(Boolean, nullable=False, default=False)
    peut_voir_finances  = Column(Boolean, nullable=False, default=False)
    peut_modifier_prix  = Column(Boolean, nullable=False, default=False)
    peut_gerer_employes = Column(Boolean, nullable=False, default=False)
    peut_voir_rapports  = Column(Boolean, nullable=False, default=False)
    peut_exporter       = Column(Boolean, nullable=False, default=False)
