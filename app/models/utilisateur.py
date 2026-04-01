from sqlalchemy import Column, Integer, String, Enum, SmallInteger, DateTime, Boolean, func
from app.core.database import Base

class Utilisateur(Base):
    __tablename__ = "utilisateurs"
    id_utilisateur       = Column(Integer, primary_key=True, autoincrement=True)
    telephone            = Column(String(20), unique=True, nullable=False, index=True)
    email                = Column(String(150), unique=True, nullable=True)
    nom_complet          = Column(String(120), nullable=False)
    photo_profil         = Column(String(255), nullable=True)
    langue_principale    = Column(Enum("fr","ff","ha","mfa"), nullable=False, default="fr")
    mode_interface       = Column(Enum("vocal","texte"), nullable=False, default="vocal")
    type_abonnement      = Column(Enum("gratuit","pro","premium"), nullable=False, default="gratuit")
    score_sante_business = Column(SmallInteger, nullable=False, default=50)
    score_credit         = Column(SmallInteger, nullable=False, default=50)
    nb_ventes_mois       = Column(SmallInteger, nullable=False, default=0)
    nb_questions_ia_mois = Column(SmallInteger, nullable=False, default=0)
    nb_vocal_mois        = Column(SmallInteger, nullable=False, default=0)
    actif                = Column(Boolean, nullable=False, default=True)
    email_verified       = Column(Boolean, nullable=False, default=False)
    code_pin_hash        = Column(String(255), nullable=True)
    biometrie_active     = Column(Boolean, nullable=False, default=False)
    date_inscription     = Column(DateTime, nullable=False, server_default=func.now())
    derniere_connexion   = Column(DateTime, nullable=True)
