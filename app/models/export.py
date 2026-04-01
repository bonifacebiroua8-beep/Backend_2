from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, Enum, ForeignKey, func
from app.core.database import Base

class ExportGenere(Base):
    __tablename__ = "exports_generes"
    id_export       = Column(Integer, primary_key=True, autoincrement=True)
    id_utilisateur  = Column(Integer, ForeignKey("utilisateurs.id_utilisateur", ondelete="CASCADE"), nullable=False, index=True)
    id_boutique     = Column(Integer, nullable=True)
    type_export     = Column(Enum("pdf","excel"), nullable=False)
    type_rapport    = Column(Enum("bilan_jour","bilan_semaine","bilan_mois","bilan_trimestre","bilan_annee","inventaire","transactions","credits_clients"), nullable=False)
    periode_debut   = Column(Date, nullable=False)
    periode_fin     = Column(Date, nullable=False)
    nom_fichier     = Column(String(255), nullable=False)
    chemin_fichier  = Column(String(500), nullable=True)
    taille_octets   = Column(Integer, nullable=True)
    statut          = Column(Enum("en_cours","termine","erreur"), nullable=False, default="en_cours")
    date_creation   = Column(DateTime, nullable=False, server_default=func.now())
    date_expiration = Column(DateTime, nullable=True)
