# app/schemas/__init__.py — UbuntuTech v3.0
from __future__ import annotations
from datetime import datetime, date
from typing import Optional, List, Any
from pydantic import BaseModel, Field
from decimal import Decimal

class MessageOut(BaseModel):
    success: bool = True
    message: str

class RegisterIn(BaseModel):
    telephone: str = Field(..., min_length=8, max_length=20)
    nom_complet: str = Field(..., min_length=2, max_length=120)
    code_pin: str = Field(..., min_length=4, max_length=6)
    langue_principale: str = "fr"
    email: Optional[str] = None

class LoginIn(BaseModel):
    telephone: str
    code_pin: str

class UtilisateurOut(BaseModel):
    id_utilisateur: int
    telephone: str
    email: Optional[str] = None
    nom_complet: str
    photo_profil: Optional[str] = None
    langue_principale: str
    mode_interface: str
    type_abonnement: str
    score_sante_business: int
    score_credit: int
    actif: bool
    date_inscription: datetime
    class Config:
        from_attributes = True

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    utilisateur: UtilisateurOut

class ChangePINIn(BaseModel):
    ancien_pin: str
    nouveau_pin: str = Field(..., min_length=4, max_length=6)

class UtilisateurUpdateIn(BaseModel):
    nom_complet: Optional[str] = None
    email: Optional[str] = None
    photo_profil: Optional[str] = None
    langue_principale: Optional[str] = None
    mode_interface: Optional[str] = None

class BoutiqueCreateIn(BaseModel):
    nom_boutique: str = Field(..., min_length=2, max_length=120)
    type_commerce: str = "General"
    ville: str = "Ngaoundere"
    quartier: Optional[str] = None
    adresse_complete: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    description: Optional[str] = None

class BoutiqueOut(BaseModel):
    id_boutique: int
    id_utilisateur: int
    nom_boutique: str
    type_commerce: str
    ville: str
    quartier: Optional[str] = None
    actif: bool
    boutique_principale: bool
    date_creation: datetime
    class Config:
        from_attributes = True

class BoutiqueUpdateIn(BaseModel):
    nom_boutique: Optional[str] = None
    type_commerce: Optional[str] = None
    ville: Optional[str] = None
    quartier: Optional[str] = None
    description: Optional[str] = None

class DashboardOut(BaseModel):
    id_boutique: int
    nom_boutique: str
    score_sante_business: int
    label_score: str
    ventes_jour: float
    benefice_jour: float
    nb_ventes_jour: int
    nb_alertes_stock: int
    ventes_hier: float
    variation_pct: float
    meteo: str
    tendance: str
    total_credits_clients: float
    conseil_ia: Optional[str] = None

class ProduitCreateIn(BaseModel):
    id_boutique: int
    nom_produit: str = Field(..., min_length=1, max_length=150)
    prix_vente: float = Field(..., gt=0)
    prix_achat: float = 0
    quantite_stock: float = 0
    seuil_alerte_stock: float = 5
    unite: str = "unite"
    id_categorie: int = 10
    code_barres: Optional[str] = None
    description: Optional[str] = None

class ProduitUpdateIn(BaseModel):
    nom_produit: Optional[str] = None
    prix_vente: Optional[float] = None
    prix_achat: Optional[float] = None
    quantite_stock: Optional[float] = None
    seuil_alerte_stock: Optional[float] = None
    unite: Optional[str] = None
    id_categorie: Optional[int] = None
    actif: Optional[bool] = None

class ProduitOut(BaseModel):
    id_produit: int
    id_boutique: int
    nom_produit: str
    prix_vente: float
    prix_achat: float
    marge_pct: Optional[float] = None
    quantite_stock: float
    seuil_alerte_stock: float
    unite: str
    nb_ventes: int
    actif: bool
    statut_stock: Optional[str] = None
    class Config:
        from_attributes = True

class StockAjustIn(BaseModel):
    id_boutique: int
    quantite: float
    type_mouvement: str = "entree"
    motif: str = "approvisionnement"
    prix_unitaire: Optional[float] = None

class LigneVenteIn(BaseModel):
    id_produit: int
    quantite: float = Field(..., gt=0)
    prix_unitaire: Optional[float] = None
    remise_pct: float = 0

class VenteCreateIn(BaseModel):
    id_boutique: int
    lignes: List[LigneVenteIn]
    id_client: Optional[int] = None
    mode_paiement: str = "cash"
    montant_paye: Optional[float] = None
    note: Optional[str] = None
    source_saisie: str = "texte"
    langue_saisie: str = "fr"

class VenteOut(BaseModel):
    id_vente: int
    id_boutique: int
    montant_total: float
    montant_paye: float
    montant_credit: float
    mode_paiement: str
    statut: str
    date_vente: datetime
    class Config:
        from_attributes = True

class ClientCreateIn(BaseModel):
    id_boutique: int
    nom_client: str = Field(..., min_length=1, max_length=120)
    telephone: Optional[str] = None
    adresse: Optional[str] = None
    limite_credit: float = 10000
    notes: Optional[str] = None

class ClientOut(BaseModel):
    id_client: int
    id_boutique: int
    nom_client: str
    telephone: Optional[str] = None
    solde_credit: float
    limite_credit: float
    fiabilite_paiement: int
    nb_achats: int
    total_achats: float
    derniere_visite: Optional[datetime] = None
    actif: bool
    class Config:
        from_attributes = True

class RemboursementIn(BaseModel):
    montant: float = Field(..., gt=0)
    mode_paiement: str = "cash"

class DepenseCreateIn(BaseModel):
    id_boutique: int
    categorie: str = "autre"
    libelle: str = Field(..., min_length=1, max_length=200)
    montant: float = Field(..., gt=0)
    mode_paiement: str = "cash"
    note: Optional[str] = None
    source: str = "texte"

class DepenseOut(BaseModel):
    id_depense: int
    id_boutique: int
    categorie: str
    libelle: str
    montant: float
    mode_paiement: str
    date_depense: datetime
    class Config:
        from_attributes = True

class BilanOut(BaseModel):
    id_boutique: int
    periode: str
    revenus: float
    depenses: float
    benefice_net: float
    nb_ventes: int
    variation_pct: Optional[float] = None
    credits_clients: float = 0

class DialogueIn(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    langue: str = "fr"
    id_boutique: Optional[int] = None
    id_session: Optional[int] = None
    source: str = "texte"
    historique: Optional[List[str]] = None

class DialogueOut(BaseModel):
    id_dialogue: int
    reponse: str
    langue_reponse: str
    domaine: str
    score_confiance: float
    temps_reponse_ms: int
    suggestions: List[str]
    id_session: int

class FeedbackIn(BaseModel):
    utile: bool
    note: Optional[int] = None

class WalletOut(BaseModel):
    id_wallet: int
    solde: float
    solde_bloque: float
    devise: str
    plafond_journalier: float
    class Config:
        from_attributes = True

class RechargeIn(BaseModel):
    montant: float = Field(..., gt=0)
    provider: str = "mtn_momo"
    telephone_source: Optional[str] = None

class RechargeOut(BaseModel):
    id_recharge: int
    montant: float
    montant_net: float
    frais: float
    provider: str
    statut: str
    date_demande: datetime
    class Config:
        from_attributes = True

class VirementIn(BaseModel):
    telephone_receveur: str
    montant: float = Field(..., gt=0)
    motif: Optional[str] = None

class VirementOut(BaseModel):
    id_virement: int
    montant: float
    montant_net: float
    statut: str
    date_virement: datetime
    class Config:
        from_attributes = True

class EpargneCreateIn(BaseModel):
    objectif_libelle: Optional[str] = None
    categorie_objectif: str = "autre"
    objectif_montant: float = Field(..., gt=0)
    montant_mensuel_cible: float = Field(..., gt=0)
    date_cible: Optional[date] = None
    versement_auto: bool = False

class EpargneOut(BaseModel):
    id_epargne: int
    objectif_libelle: Optional[str] = None
    objectif_montant: float
    total_cumule: float
    progression_pct: float
    statut: str
    date_cible: Optional[date] = None
    class Config:
        from_attributes = True

class CreditDemandeIn(BaseModel):
    id_banque: int
    montant_demande: float = Field(..., gt=0)
    duree_semaines: int = Field(..., gt=0)
    objet_credit: Optional[str] = None
    motif_demande: Optional[str] = None

class CreditSimulerIn(BaseModel):
    id_banque: int
    montant: float = Field(..., gt=0)
    duree_semaines: int = Field(..., gt=0)

class CreditSimulerOut(BaseModel):
    montant: float
    taux_interet: float
    duree_semaines: int
    mensualite: float
    total_interet: float
    total_rembourser: float
    score_requis: int
    eligible: bool

class CreditOut(BaseModel):
    id_credit: int
    id_banque: int
    nom_banque: Optional[str] = None
    montant_demande: float
    montant_accorde: Optional[float] = None
    taux_interet: float
    mensualite: Optional[float] = None
    montant_rembourse: float
    statut: str
    score_ml_decision: Optional[int] = None
    date_demande: datetime
    class Config:
        from_attributes = True

class SignatureOTPIn(BaseModel):
    id_credit: int
    code_otp: str

class GarantieIn(BaseModel):
    type_garantie: str
    description: str
    valeur_estimee: Optional[float] = None

class TontineCreateIn(BaseModel):
    nom_tontine: str = Field(..., min_length=2, max_length=120)
    cotisation_periodique: float = Field(..., gt=0)
    frequence: str = "mensuel"
    nb_membres_max: int = Field(default=10, ge=2, le=50)
    description: Optional[str] = None
    penalite_retard_pct: float = 5.0
    mode_attribution: str = "fixe"
    langue_tontine: str = "fr"

class TontineOut(BaseModel):
    id_tontine: int
    nom_tontine: str
    cotisation_periodique: float
    frequence: str
    nb_membres_actuel: int
    nb_membres_max: int
    cagnotte_actuelle: float
    cycle_actuel: int
    statut: str
    code_invitation: Optional[str] = None
    prochain_paiement: Optional[date] = None
    class Config:
        from_attributes = True

class RejoindreIn(BaseModel):
    code_invitation: str

class CotisationPayerIn(BaseModel):
    id_tontine: int
    mode_paiement: str = "wallet"

class LitigeCreateIn(BaseModel):
    id_membre: int
    type_litige: str
    description: Optional[str] = None

class ScoreOut(BaseModel):
    score: int
    label: str
    eligibilite: str
    montant_max: int
    details: dict

class ParametreUpdateIn(BaseModel):
    theme: Optional[str] = None
    couleur_accent: Optional[str] = None
    taille_police: Optional[str] = None
    notif_stock_faible: Optional[bool] = None
    notif_remboursement: Optional[bool] = None
    notif_tontine: Optional[bool] = None
    notif_credit_retard: Optional[bool] = None
    mode_vocal_defaut: Optional[bool] = None
    langue_interface: Optional[str] = None
    biometrie: Optional[bool] = None

class VocabCreateIn(BaseModel):
    mot: str
    signification: str
    langue: str
    contexte: str = "general"
    exemple_contexte: Optional[str] = None

class VocabOut(BaseModel):
    id_vocab: int
    mot: str
    signification: str
    langue: str
    contexte: str
    confirme: bool
    nb_utilisations: int
    class Config:
        from_attributes = True

class ConnLocalCreateIn(BaseModel):
    type_info: str
    ville: Optional[str] = None
    region: Optional[str] = None
    cle: str
    valeur_json: Any
    langue: str = "all"

class AdminStatsOut(BaseModel):
    nb_utilisateurs: int
    nb_boutiques: int
    nb_ventes_total: int
    nb_abonnes_pro: int
    nb_abonnes_premium: int
    precision_fr: Optional[float] = None
    precision_ff: Optional[float] = None
    precision_ha: Optional[float] = None
    precision_mfa: Optional[float] = None

class SyncItemIn(BaseModel):
    table_cible: str
    id_enregistrement: Optional[int] = None
    operation: str
    donnees_json: dict
    priorite: int = 5

class SyncBatchIn(BaseModel):
    items: List[SyncItemIn]
    id_boutique: Optional[int] = None

class NotificationOut(BaseModel):
    id_notification: int
    type_notif: str
    titre: str
    message: str
    lue: bool
    date_creation: datetime
    class Config:
        from_attributes = True
