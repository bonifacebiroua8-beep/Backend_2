from sqlalchemy import Column, Integer, Date, SmallInteger, Numeric
from app.core.database import Base

class MetriqueSysteme(Base):
    __tablename__ = "metriques_systeme"
    id_metrique                 = Column(Integer, primary_key=True, autoincrement=True)
    date_mesure                 = Column(Date, nullable=False, unique=True)
    nb_utilisateurs_total       = Column(Integer, nullable=False, default=0)
    nb_utilisateurs_actifs      = Column(Integer, nullable=False, default=0)
    nb_nouveaux_inscrits        = Column(SmallInteger, nullable=False, default=0)
    nb_abonnes_gratuit          = Column(Integer, nullable=False, default=0)
    nb_abonnes_pro              = Column(Integer, nullable=False, default=0)
    nb_abonnes_premium          = Column(Integer, nullable=False, default=0)
    nb_ventes_jour              = Column(Integer, nullable=False, default=0)
    nb_transcriptions_jour      = Column(Integer, nullable=False, default=0)
    nb_dialogues_ia_jour        = Column(Integer, nullable=False, default=0)
    nb_syncs_jour               = Column(Integer, nullable=False, default=0)
    revenu_abonnements_jour     = Column(Numeric(12,2), nullable=False, default=0)
    precision_transcription_fr  = Column(Numeric(5,2), nullable=True)
    precision_transcription_ff  = Column(Numeric(5,2), nullable=True)
    precision_transcription_ha  = Column(Numeric(5,2), nullable=True)
    precision_transcription_mfa = Column(Numeric(5,2), nullable=True)
