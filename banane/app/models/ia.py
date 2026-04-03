from sqlalchemy import Column, Integer, String, Boolean, DateTime, Numeric, Enum, Text, JSON, ForeignKey, func
from app.core.database import Base

class MemoirePrix(Base):
    __tablename__ = "memoire_prix"
    id_memoire       = Column(Integer, primary_key=True, autoincrement=True)
    id_boutique      = Column(Integer, ForeignKey("boutiques.id_boutique", ondelete="CASCADE"), nullable=False)
    nom_produit      = Column(String(150), nullable=False)
    unite            = Column(String(30), nullable=True)
    prix_vente_moy   = Column(Numeric(12,2), nullable=False, default=0)
    prix_achat_moy   = Column(Numeric(12,2), nullable=False, default=0)
    nb_fois_vendu    = Column(Integer, nullable=False, default=1)
    derniere_vente   = Column(DateTime, nullable=True)
    date_creation    = Column(DateTime, nullable=False, server_default=func.now())
    date_mise_a_jour = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

class VocabulaireIA(Base):
    __tablename__ = "vocabulaire_ia"
    id_vocab        = Column(Integer, primary_key=True, autoincrement=True)
    id_boutique     = Column(Integer, ForeignKey("boutiques.id_boutique", ondelete="SET NULL"), nullable=True)
    mot             = Column(String(100), nullable=False)
    signification   = Column(String(255), nullable=False)
    langue          = Column(Enum("fr","ff","ha","mfa"), nullable=False, default="fr")
    contexte        = Column(Enum("produit","action","quantite","monnaie","unite","client","salutation","general"), nullable=False, default="general")
    source          = Column(Enum("admin","utilisateur","import","auto"), nullable=False, default="admin")
    nb_utilisations = Column(Integer, nullable=False, default=0)
    confirme        = Column(Boolean, nullable=False, default=False)
    actif           = Column(Boolean, nullable=False, default=True)
    date_creation   = Column(DateTime, nullable=False, server_default=func.now())

class ApprentissageLangue(Base):
    __tablename__ = "apprentissage_langue"
    id_apprentissage   = Column(Integer, primary_key=True, autoincrement=True)
    id_admin           = Column(Integer, ForeignKey("utilisateurs.id_utilisateur", ondelete="RESTRICT"), nullable=False)
    texte_source       = Column(Text, nullable=False)
    langue_source      = Column(Enum("fr","ff","ha","mfa"), nullable=False)
    texte_traduit      = Column(Text, nullable=False)
    type_apprentissage = Column(Enum("traduction","correction_whisper","nouveau_mot","expression_idiomatique","nom_produit_local","prix_marche"), nullable=False, default="traduction")
    exemple_contexte   = Column(Text, nullable=True)
    audio_exemple_url  = Column(String(255), nullable=True)
    version_modele     = Column(String(20), nullable=False, default="1.0")
    statut             = Column(Enum("brouillon","valide","integre","rejete"), nullable=False, default="brouillon", index=True)
    nb_utilisations    = Column(Integer, nullable=False, default=0)
    taux_succes        = Column(Numeric(5,2), nullable=False, default=0)
    date_creation      = Column(DateTime, nullable=False, server_default=func.now())
    date_validation    = Column(DateTime, nullable=True)
    date_integration   = Column(DateTime, nullable=True)

class VersionModeleIA(Base):
    __tablename__ = "versions_modele_ia"
    id_version     = Column(Integer, primary_key=True, autoincrement=True)
    version        = Column(String(20), nullable=False)
    type_modele    = Column(Enum("whisper_ff","whisper_ha","whisper_mfa","nlp_fr","nlp_ff","scoring_credit","previsions_ml","scoring_sante"), nullable=False)
    description    = Column(Text, nullable=True)
    chemin_fichier = Column(String(500), nullable=True)
    nb_exemples    = Column(Integer, nullable=False, default=0)
    precision_pct  = Column(Numeric(5,2), nullable=True)
    actif          = Column(Boolean, nullable=False, default=False)
    id_admin       = Column(Integer, nullable=True)
    date_creation  = Column(DateTime, nullable=False, server_default=func.now())
    date_activation = Column(DateTime, nullable=True)

class ConnaissanceLocale(Base):
    __tablename__ = "connaissance_locale"
    id_connaissance  = Column(Integer, primary_key=True, autoincrement=True)
    type_info        = Column(Enum("prix_marche","culture_saison","fete_locale","fournisseur","conseil_business","marche_info"), nullable=False)
    ville            = Column(String(100), nullable=True)
    region           = Column(String(100), nullable=True)
    cle              = Column(String(150), nullable=False, unique=True)
    valeur_json      = Column(JSON, nullable=False)
    langue           = Column(Enum("fr","ff","ha","mfa","all"), nullable=False, default="all")
    actif            = Column(Boolean, nullable=False, default=True)
    id_admin         = Column(Integer, nullable=True)
    date_creation    = Column(DateTime, nullable=False, server_default=func.now())
    date_mise_a_jour = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

