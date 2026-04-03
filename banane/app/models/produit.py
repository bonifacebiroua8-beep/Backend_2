from sqlalchemy import Column, Integer, SmallInteger, String, Boolean, DateTime, Numeric, Text, ForeignKey, func
from app.core.database import Base

class CategorieProduit(Base):
    __tablename__ = "categories_produits"
    id_categorie  = Column(SmallInteger, primary_key=True, autoincrement=True)
    nom_categorie = Column(String(80), nullable=False)
    icone         = Column(String(10), nullable=False, default="📦")
    couleur_hex   = Column(String(7), nullable=False, default="#1B8A4C")
    actif         = Column(Boolean, nullable=False, default=True)

class Produit(Base):
    __tablename__ = "produits"
    id_produit         = Column(Integer, primary_key=True, autoincrement=True)
    id_boutique        = Column(Integer, ForeignKey("boutiques.id_boutique", ondelete="RESTRICT"), nullable=False, index=True)
    id_categorie       = Column(SmallInteger, ForeignKey("categories_produits.id_categorie"), nullable=False, default=10)
    nom_produit        = Column(String(150), nullable=False)
    code_barres        = Column(String(50), nullable=True)
    description        = Column(Text, nullable=True)
    unite              = Column(String(30), nullable=False, default="unite")
    prix_vente         = Column(Numeric(12,2), nullable=False)
    prix_achat         = Column(Numeric(12,2), nullable=False, default=0)
    marge_pct          = Column(Numeric(5,2), nullable=True)
    quantite_stock     = Column(Numeric(12,3), nullable=False, default=0)
    seuil_alerte_stock = Column(Numeric(12,3), nullable=False, default=5)
    total_vendu        = Column(Numeric(12,3), nullable=False, default=0)
    nb_ventes          = Column(Integer, nullable=False, default=0)
    derniere_vente     = Column(DateTime, nullable=True)
    actif              = Column(Boolean, nullable=False, default=True)
    date_creation      = Column(DateTime, nullable=False, server_default=func.now())
    date_modification  = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
