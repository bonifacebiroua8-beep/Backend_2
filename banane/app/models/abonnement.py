from sqlalchemy import Column, Integer, SmallInteger, String, Boolean, DateTime, Date, Enum, Numeric, ForeignKey, func
from app.core.database import Base

class PlanAbonnement(Base):
    __tablename__ = "plans_abonnement"
    id_plan                    = Column(SmallInteger, primary_key=True, autoincrement=True)
    code_plan                  = Column(Enum("gratuit","pro","premium"), nullable=False, unique=True)
    nom_affichage              = Column(String(80), nullable=False)
    prix_mensuel               = Column(Numeric(10,2), nullable=False, default=0)
    prix_annuel                = Column(Numeric(10,2), nullable=False, default=0)
    limite_ventes_mois         = Column(SmallInteger, nullable=False, default=50)
    limite_produits            = Column(SmallInteger, nullable=False, default=20)
    limite_boutiques           = Column(SmallInteger, nullable=False, default=1)
    limite_employes            = Column(SmallInteger, nullable=False, default=0)
    limite_questions_ia        = Column(SmallInteger, nullable=False, default=20)
    limite_vocal_mois          = Column(SmallInteger, nullable=False, default=50)
    historique_jours           = Column(SmallInteger, nullable=False, default=7)
    export_pdf                 = Column(Boolean, nullable=False, default=False)
    export_excel               = Column(Boolean, nullable=False, default=False)
    microcredit_communautaire  = Column(Boolean, nullable=False, default=False)
    banques_partenaires        = Column(Boolean, nullable=False, default=False)
    contrats_electroniques     = Column(Boolean, nullable=False, default=False)
    coaching_ia_proactif       = Column(Boolean, nullable=False, default=False)
    previsions_ml              = Column(Boolean, nullable=False, default=False)
    reponses_vocales_ia        = Column(Boolean, nullable=False, default=False)
    multi_boutiques            = Column(Boolean, nullable=False, default=False)
    actif                      = Column(Boolean, nullable=False, default=True)

class Abonnement(Base):
    __tablename__ = "abonnements"
    id_abonnement      = Column(Integer, primary_key=True, autoincrement=True)
    id_utilisateur     = Column(Integer, ForeignKey("utilisateurs.id_utilisateur", ondelete="CASCADE"), nullable=False, index=True)
    id_plan            = Column(SmallInteger, ForeignKey("plans_abonnement.id_plan"), nullable=False)
    periodicite        = Column(Enum("mensuel","annuel"), nullable=False, default="mensuel")
    montant_paye       = Column(Numeric(10,2), nullable=False)
    moyen_paiement     = Column(Enum("mtn_momo","orange_money","cash","gratuit"), nullable=False, default="gratuit")
    reference_paiement = Column(String(100), nullable=True)
    statut             = Column(Enum("actif","expire","annule","rembourse"), nullable=False, default="actif")
    date_debut         = Column(Date, nullable=False)
    date_fin           = Column(Date, nullable=False)
    date_paiement      = Column(DateTime, nullable=False, server_default=func.now())
