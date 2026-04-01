from sqlalchemy import Column, Integer, String, Boolean, DateTime, Numeric, Enum, Text, JSON, ForeignKey, func
from app.core.database import Base

class TranscriptionVocale(Base):
    __tablename__ = "transcriptions_vocales"
    id_transcription  = Column(Integer, primary_key=True, autoincrement=True)
    id_utilisateur    = Column(Integer, ForeignKey("utilisateurs.id_utilisateur", ondelete="CASCADE"), nullable=False, index=True)
    id_boutique       = Column(Integer, ForeignKey("boutiques.id_boutique", ondelete="SET NULL"), nullable=True)
    fichier_audio     = Column(String(255), nullable=True)
    duree_secondes    = Column(Integer, nullable=True)
    taille_octets     = Column(Integer, nullable=True)
    langue_detectee   = Column(Enum("fr","ff","ha","mfa","inconnue"), nullable=False, default="fr")
    langue_demandee   = Column(Enum("fr","ff","ha","mfa"), nullable=False, default="fr")
    texte_transcrit   = Column(Text, nullable=True)
    confiance_whisper = Column(Numeric(4,3), nullable=True)
    entites_extraites = Column(JSON, nullable=True)
    action_detectee   = Column(Enum("vente","stock","client","depense","question_ia","inconnu"), nullable=False, default="inconnu")
    traitee           = Column(Boolean, nullable=False, default=False)
    action_executee   = Column(Boolean, nullable=False, default=False)
    erreur_traitement = Column(String(255), nullable=True)
    correction_humaine = Column(Text, nullable=True)
    validee_admin     = Column(Boolean, nullable=False, default=False)
    date_creation     = Column(DateTime, nullable=False, server_default=func.now())
