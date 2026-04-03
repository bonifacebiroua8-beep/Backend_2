from sqlalchemy import Column, Integer, String, Boolean, DateTime, Numeric, Enum, ForeignKey, func
from app.core.database import Base

class MouvementStock(Base):
    __tablename__ = "mouvements_stock"
    id_mouvement   = Column(Integer, primary_key=True, autoincrement=True)
    id_produit     = Column(Integer, ForeignKey("produits.id_produit", ondelete="RESTRICT"), nullable=False, index=True)
    id_boutique    = Column(Integer, ForeignKey("boutiques.id_boutique", ondelete="RESTRICT"), nullable=False, index=True)
    id_employe     = Column(Integer, nullable=True)
    type_mouvement = Column(Enum("entree","sortie","correction","perte","retour"), nullable=False)
    quantite       = Column(Numeric(12,3), nullable=False)
    quantite_avant = Column(Numeric(12,3), nullable=False)
    quantite_apres = Column(Numeric(12,3), nullable=False)
    prix_unitaire  = Column(Numeric(12,2), nullable=True)
    motif          = Column(String(150), nullable=False, default="vente")
    id_vente       = Column(Integer, nullable=True)
    source         = Column(Enum("vocal","texte","auto","sync","admin"), nullable=False, default="texte")
    synced         = Column(Boolean, nullable=False, default=False)
    date_mouvement = Column(DateTime, nullable=False, server_default=func.now())
