from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, Numeric, Enum, Text, JSON, ForeignKey, func
from app.core.database import Base

class Tontine(Base):
    __tablename__ = "tontines"
    id_tontine            = Column(Integer, primary_key=True, autoincrement=True)
    nom_tontine           = Column(String(120), nullable=False)
    id_admin              = Column(Integer, ForeignKey("utilisateurs.id_utilisateur", ondelete="RESTRICT"), nullable=False, index=True)
    description           = Column(Text, nullable=True)
    cotisation_periodique = Column(Numeric(12,2), nullable=False)
    frequence             = Column(Enum("hebdo","bimensuel","mensuel"), nullable=False, default="hebdo")
    nb_membres_max        = Column(Integer, nullable=False, default=10)
    nb_membres_actuel     = Column(Integer, nullable=False, default=0)
    nb_cycles_total       = Column(Integer, nullable=False, default=0)
    cagnotte_actuelle     = Column(Numeric(14,2), nullable=False, default=0)
    cycle_actuel          = Column(Integer, nullable=False, default=1)
    mode_attribution      = Column(Enum("fixe","encheres","aleatoire"), nullable=False, default="fixe")
    langue_tontine        = Column(Enum("fr","ff","ha","mfa"), nullable=False, default="fr")
    date_debut            = Column(Date, nullable=True)
    prochain_paiement     = Column(Date, nullable=True)
    penalite_retard_pct   = Column(Numeric(5,2), nullable=False, default=5)
    regles_json           = Column(JSON, nullable=True)
    statut                = Column(Enum("en_attente","actif","suspendu","termine"), nullable=False, default="en_attente")
    code_invitation       = Column(String(10), nullable=True)
    date_creation         = Column(DateTime, nullable=False, server_default=func.now())

class MembreTontine(Base):
    __tablename__ = "membres_tontine"
    id_membre       = Column(Integer, primary_key=True, autoincrement=True)
    id_tontine      = Column(Integer, ForeignKey("tontines.id_tontine", ondelete="CASCADE"), nullable=False)
    id_utilisateur  = Column(Integer, ForeignKey("utilisateurs.id_utilisateur", ondelete="RESTRICT"), nullable=False)
    ordre_reception = Column(Integer, nullable=True)
    statut          = Column(Enum("actif","inactif","suspendu","exclu"), nullable=False, default="actif")
    total_cotise    = Column(Numeric(14,2), nullable=False, default=0)
    nb_cotisations  = Column(Integer, nullable=False, default=0)
    nb_retards      = Column(Integer, nullable=False, default=0)
    a_recu_cagnotte = Column(Boolean, nullable=False, default=False)
    date_reception  = Column(Date, nullable=True)
    date_adhesion   = Column(DateTime, nullable=False, server_default=func.now())

class CotisationTontine(Base):
    __tablename__ = "cotisations_tontine"
    id_cotisation   = Column(Integer, primary_key=True, autoincrement=True)
    id_tontine      = Column(Integer, ForeignKey("tontines.id_tontine", ondelete="CASCADE"), nullable=False, index=True)
    id_membre       = Column(Integer, ForeignKey("membres_tontine.id_membre", ondelete="CASCADE"), nullable=False, index=True)
    id_utilisateur  = Column(Integer, ForeignKey("utilisateurs.id_utilisateur"), nullable=False)
    montant         = Column(Numeric(12,2), nullable=False)
    cycle           = Column(Integer, nullable=False, default=1)
    mode_paiement   = Column(Enum("wallet","mobile_money","cash"), nullable=False, default="wallet")
    statut          = Column(Enum("payee","en_attente","retard"), nullable=False, default="payee")
    penalite        = Column(Numeric(10,2), nullable=False, default=0)
    date_cotisation = Column(DateTime, nullable=False, server_default=func.now())
