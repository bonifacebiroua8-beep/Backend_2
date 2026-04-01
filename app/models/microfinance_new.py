# app/models/microfinance_new.py
# Nouveaux modèles microfinance v3.0
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, Numeric, Enum, Text, ForeignKey, func
from app.core.database import Base


class VirementWallet(Base):
    __tablename__ = "virements_wallet"
    id_virement              = Column(Integer, primary_key=True, autoincrement=True)
    id_wallet_envoyeur       = Column(Integer, ForeignKey("wallets.id_wallet", ondelete="RESTRICT"), nullable=False, index=True)
    id_wallet_receveur       = Column(Integer, ForeignKey("wallets.id_wallet", ondelete="RESTRICT"), nullable=False, index=True)
    id_utilisateur_envoyeur  = Column(Integer, ForeignKey("utilisateurs.id_utilisateur"), nullable=False)
    id_utilisateur_receveur  = Column(Integer, ForeignKey("utilisateurs.id_utilisateur"), nullable=False)
    montant                  = Column(Numeric(12,2), nullable=False)
    frais                    = Column(Numeric(10,2), nullable=False, default=0)
    montant_net              = Column(Numeric(12,2), nullable=False)
    motif                    = Column(String(255), nullable=True)
    reference_otp            = Column(String(10), nullable=True)
    otp_valide               = Column(Boolean, nullable=False, default=False)
    solde_avant_envoyeur     = Column(Numeric(14,2), nullable=True)
    solde_apres_envoyeur     = Column(Numeric(14,2), nullable=True)
    statut                   = Column(Enum("en_attente","confirme","echec","annule","rembourse"), nullable=False, default="en_attente", index=True)
    date_virement            = Column(DateTime, nullable=False, server_default=func.now(), index=True)
    date_confirmation        = Column(DateTime, nullable=True)


class CycleTontine(Base):
    __tablename__ = "cycles_tontine"
    id_cycle         = Column(Integer, primary_key=True, autoincrement=True)
    id_tontine       = Column(Integer, ForeignKey("tontines.id_tontine", ondelete="CASCADE"), nullable=False, index=True)
    numero_cycle     = Column(Integer, nullable=False)
    id_beneficiaire  = Column(Integer, ForeignKey("membres_tontine.id_membre", ondelete="RESTRICT"), nullable=False, index=True)
    montant_verse    = Column(Numeric(14,2), nullable=False, default=0)
    nb_cotisants     = Column(Integer, nullable=False, default=0)
    date_debut_cycle = Column(Date, nullable=False)
    date_fin_cycle   = Column(Date, nullable=True)
    date_versement   = Column(DateTime, nullable=True)
    statut           = Column(Enum("en_cours","termine","annule","reporte"), nullable=False, default="en_cours")
    note             = Column(Text, nullable=True)
    date_creation    = Column(DateTime, nullable=False, server_default=func.now())


class GarantieCredit(Base):
    __tablename__ = "garanties_credit"
    id_garantie     = Column(Integer, primary_key=True, autoincrement=True)
    id_credit       = Column(Integer, ForeignKey("micro_credits.id_credit", ondelete="CASCADE"), nullable=False, index=True)
    id_utilisateur  = Column(Integer, ForeignKey("utilisateurs.id_utilisateur", ondelete="RESTRICT"), nullable=False, index=True)
    type_garantie   = Column(Enum("materiel","caution_personnelle","immobilier","stock","autre"), nullable=False)
    description     = Column(String(255), nullable=False)
    valeur_estimee  = Column(Numeric(12,2), nullable=True)
    document_url    = Column(String(500), nullable=True)
    statut          = Column(Enum("actif","libere","saisi","expire"), nullable=False, default="actif")
    date_liberation = Column(DateTime, nullable=True)
    date_creation   = Column(DateTime, nullable=False, server_default=func.now())


class LitigeTontine(Base):
    __tablename__ = "litiges_tontine"
    id_litige         = Column(Integer, primary_key=True, autoincrement=True)
    id_tontine        = Column(Integer, ForeignKey("tontines.id_tontine", ondelete="CASCADE"), nullable=False, index=True)
    id_membre         = Column(Integer, ForeignKey("membres_tontine.id_membre", ondelete="CASCADE"), nullable=False, index=True)
    id_rapporteur     = Column(Integer, ForeignKey("utilisateurs.id_utilisateur"), nullable=False)
    type_litige       = Column(Enum("cotisation_contestee","paiement_refuse","exclusion_demandee","fraude_suspectee","autre"), nullable=False)
    description       = Column(Text, nullable=True)
    statut            = Column(Enum("ouvert","en_cours","resolu","ferme"), nullable=False, default="ouvert")
    resolution        = Column(Text, nullable=True)
    tranche_penalite  = Column(Numeric(10,2), nullable=False, default=0)
    date_ouverture    = Column(DateTime, nullable=False, server_default=func.now())
    date_resolution   = Column(DateTime, nullable=True)


class ScoreFiabiliteTontine(Base):
    __tablename__ = "score_fiabilite_tontine"
    id_score                  = Column(Integer, primary_key=True, autoincrement=True)
    id_utilisateur            = Column(Integer, ForeignKey("utilisateurs.id_utilisateur", ondelete="CASCADE"), nullable=False, unique=True)
    score                     = Column(Integer, nullable=False, default=50)
    nb_tontines_actives       = Column(Integer, nullable=False, default=0)
    nb_tontines_total         = Column(Integer, nullable=False, default=0)
    nb_cotisations_total      = Column(Integer, nullable=False, default=0)
    nb_cotisations_retard     = Column(Integer, nullable=False, default=0)
    nb_exclusions             = Column(Integer, nullable=False, default=0)
    nb_litiges                = Column(Integer, nullable=False, default=0)
    pct_ponctualite           = Column(Numeric(5,2), nullable=False, default=100)
    date_dernier_calcul       = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    date_creation             = Column(DateTime, nullable=False, server_default=func.now())


class OTPCode(Base):
    __tablename__ = "otp_codes"
    id_otp           = Column(Integer, primary_key=True, autoincrement=True)
    id_utilisateur   = Column(Integer, ForeignKey("utilisateurs.id_utilisateur", ondelete="CASCADE"), nullable=False, index=True)
    telephone        = Column(String(20), nullable=False)
    code_hash        = Column(String(255), nullable=False)
    type_otp         = Column(Enum("signature_credit","validation_compte","changement_telephone","retrait_wallet","validation_tontine"), nullable=False, default="signature_credit")
    id_reference     = Column(Integer, nullable=True)
    nb_tentatives    = Column(Integer, nullable=False, default=0)
    max_tentatives   = Column(Integer, nullable=False, default=3)
    utilise          = Column(Boolean, nullable=False, default=False)
    date_creation    = Column(DateTime, nullable=False, server_default=func.now())
    date_expiration  = Column(DateTime, nullable=False)
    date_utilisation = Column(DateTime, nullable=True)


class RechargeWallet(Base):
    __tablename__ = "recharges_wallet"
    id_recharge         = Column(Integer, primary_key=True, autoincrement=True)
    id_utilisateur      = Column(Integer, ForeignKey("utilisateurs.id_utilisateur", ondelete="RESTRICT"), nullable=False, index=True)
    id_wallet           = Column(Integer, ForeignKey("wallets.id_wallet", ondelete="RESTRICT"), nullable=False, index=True)
    montant             = Column(Numeric(12,2), nullable=False)
    frais               = Column(Numeric(10,2), nullable=False, default=0)
    montant_net         = Column(Numeric(12,2), nullable=False)
    provider            = Column(Enum("mtn_momo","orange_money","virement","cash","admin"), nullable=False, default="mtn_momo")
    telephone_source    = Column(String(20), nullable=True)
    reference_operateur = Column(String(100), nullable=True)
    statut              = Column(Enum("en_attente","confirme","echec","rembourse"), nullable=False, default="en_attente", index=True)
    message_operateur   = Column(String(255), nullable=True)
    solde_avant         = Column(Numeric(14,2), nullable=True)
    solde_apres         = Column(Numeric(14,2), nullable=True)
    date_demande        = Column(DateTime, nullable=False, server_default=func.now(), index=True)
    date_confirmation   = Column(DateTime, nullable=True)


class ProviderIA(Base):
    __tablename__ = "providers_ia"
    id_provider         = Column(Integer, primary_key=True, autoincrement=True)
    code_provider       = Column(String(30), nullable=False, unique=True)
    nom_provider        = Column(String(80), nullable=False)
    type_service        = Column(Enum("llm","transcription_vocale","text_to_speech","sms","mobile_money"), nullable=False)
    modele_defaut       = Column(String(100), nullable=True)
    api_key_env_var     = Column(String(80), nullable=True)
    account_sid_env_var = Column(String(80), nullable=True)
    endpoint_url        = Column(String(255), nullable=True)
    gratuit             = Column(Boolean, nullable=False, default=False)
    actif               = Column(Boolean, nullable=False, default=True)
    priorite            = Column(Integer, nullable=False, default=5)
    langue_supportees   = Column(String(50), nullable=True)
    notes               = Column(Text, nullable=True)
    date_creation       = Column(DateTime, nullable=False, server_default=func.now())
    date_modification   = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())


class MeteoCommerciale(Base):
    __tablename__ = "meteo_commerciale"
    id_meteo             = Column(Integer, primary_key=True, autoincrement=True)
    id_boutique          = Column(Integer, ForeignKey("boutiques.id_boutique", ondelete="CASCADE"), nullable=False, index=True)
    date_meteo           = Column(Date, nullable=False)
    niveau               = Column(Enum("excellent","bon","moyen","difficile","critique"), nullable=False, default="moyen")
    score_jour           = Column(Integer, nullable=False, default=50)
    ventes_jour          = Column(Numeric(12,2), nullable=False, default=0)
    benefice_jour        = Column(Numeric(12,2), nullable=False, default=0)
    nb_transactions      = Column(Integer, nullable=False, default=0)
    nb_alertes_stock     = Column(Integer, nullable=False, default=0)
    variation_vs_hier    = Column(Numeric(6,2), nullable=True)
    variation_vs_semaine = Column(Numeric(6,2), nullable=True)
    tendance             = Column(Enum("hausse","stable","baisse"), nullable=False, default="stable")
    conseil_ia_jour      = Column(Text, nullable=True)
    details_json         = Column(Text, nullable=True)
    date_calcul          = Column(DateTime, nullable=False, server_default=func.now())


class ABTestIA(Base):
    __tablename__ = "ab_tests_ia"
    id_test              = Column(Integer, primary_key=True, autoincrement=True)
    nom_test             = Column(String(150), nullable=False)
    description          = Column(Text, nullable=True)
    id_version_a         = Column(Integer, ForeignKey("versions_modele_ia.id_version", ondelete="RESTRICT"), nullable=False)
    id_version_b         = Column(Integer, ForeignKey("versions_modele_ia.id_version", ondelete="RESTRICT"), nullable=False)
    type_modele          = Column(Enum("whisper_ff","whisper_ha","whisper_mfa","nlp_fr","nlp_ff","scoring_credit","previsions_ml","scoring_sante"), nullable=False)
    pourcentage_trafic_b = Column(Integer, nullable=False, default=20)
    nb_tests_a           = Column(Integer, nullable=False, default=0)
    nb_succes_a          = Column(Integer, nullable=False, default=0)
    precision_a          = Column(Numeric(5,2), nullable=True)
    nb_tests_b           = Column(Integer, nullable=False, default=0)
    nb_succes_b          = Column(Integer, nullable=False, default=0)
    precision_b          = Column(Numeric(5,2), nullable=True)
    gagnant              = Column(Enum("a","b","egalite","indetermine"), nullable=False, default="indetermine")
    statut               = Column(Enum("en_cours","termine","annule","en_attente"), nullable=False, default="en_attente")
    id_admin             = Column(Integer, nullable=True)
    date_debut           = Column(DateTime, nullable=True)
    date_fin             = Column(DateTime, nullable=True)
    date_creation        = Column(DateTime, nullable=False, server_default=func.now())
