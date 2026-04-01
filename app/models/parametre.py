from sqlalchemy import Column, Integer, Boolean, Enum, DateTime, ForeignKey, func
from app.core.database import Base

class ParametreUtilisateur(Base):
    __tablename__ = "parametres_utilisateur"
    id_param            = Column(Integer, primary_key=True, autoincrement=True)
    id_utilisateur      = Column(Integer, ForeignKey("utilisateurs.id_utilisateur", ondelete="CASCADE"), nullable=False, unique=True)
    theme               = Column(Enum("clair","sombre","auto"), nullable=False, default="clair")
    couleur_accent      = Column(Enum("vert","orange","bleu","violet"), nullable=False, default="vert")
    taille_police       = Column(Enum("petite","normale","grande"), nullable=False, default="normale")
    notif_stock_faible  = Column(Boolean, nullable=False, default=True)
    notif_remboursement = Column(Boolean, nullable=False, default=True)
    notif_rapport_hebdo = Column(Boolean, nullable=False, default=False)
    notif_tontine       = Column(Boolean, nullable=False, default=True)
    notif_credit_retard = Column(Boolean, nullable=False, default=True)
    mode_vocal_defaut   = Column(Boolean, nullable=False, default=True)
    langue_interface    = Column(Enum("fr","ff","ha","mfa"), nullable=False, default="fr")
    biometrie           = Column(Boolean, nullable=False, default=False)
    sauvegarde_auto     = Column(Boolean, nullable=False, default=True)
    date_modification   = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
