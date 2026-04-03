from sqlalchemy import Column, Integer, String, Boolean, DateTime, Numeric, Enum, Text, JSON, SmallInteger, ForeignKey, func
from app.core.database import Base

class SessionDialogue(Base):
    __tablename__ = "sessions_dialogue"
    id_session_dialogue = Column(Integer, primary_key=True, autoincrement=True)
    id_utilisateur      = Column(Integer, ForeignKey("utilisateurs.id_utilisateur", ondelete="CASCADE"), nullable=False, index=True)
    id_boutique         = Column(Integer, nullable=True)
    contexte_json       = Column(JSON, nullable=True)
    derniere_intention  = Column(String(100), nullable=True)
    nb_tours            = Column(Integer, nullable=False, default=0)
    statut              = Column(Enum("active","expiree","fermee"), nullable=False, default="active", index=True)
    date_creation       = Column(DateTime, nullable=False, server_default=func.now())
    date_expiration     = Column(DateTime, nullable=False)
    date_fermeture      = Column(DateTime, nullable=True)

class HistoriqueDialogue(Base):
    __tablename__ = "historique_dialogues"
    id_dialogue         = Column(Integer, primary_key=True, autoincrement=True)
    id_session_dialogue = Column(Integer, ForeignKey("sessions_dialogue.id_session_dialogue", ondelete="SET NULL"), nullable=True)
    id_utilisateur      = Column(Integer, ForeignKey("utilisateurs.id_utilisateur", ondelete="CASCADE"), nullable=False, index=True)
    id_boutique         = Column(Integer, nullable=True)
    message_utilisateur = Column(Text, nullable=False)
    langue_message      = Column(Enum("fr","ff","ha","mfa"), nullable=False, default="fr")
    source_message      = Column(Enum("texte","vocal"), nullable=False, default="texte")
    reponse_ia          = Column(Text, nullable=True)
    langue_reponse      = Column(Enum("fr","ff","ha","mfa"), nullable=False, default="fr")
    intention           = Column(String(100), nullable=True)
    domaine             = Column(Enum("business","stock","finances","credit","tontine","saison_fete","marche_local","prevision","general","inconnu"), nullable=False, default="inconnu")
    score_confiance     = Column(Numeric(4,3), nullable=True)
    temps_reponse_ms    = Column(SmallInteger, nullable=True)
    note_utilisateur    = Column(Integer, nullable=True)
    utile               = Column(Boolean, nullable=True)
    a_corriger          = Column(Boolean, nullable=False, default=False)
    correction_admin    = Column(Text, nullable=True)
    date_dialogue       = Column(DateTime, nullable=False, server_default=func.now(), index=True)
