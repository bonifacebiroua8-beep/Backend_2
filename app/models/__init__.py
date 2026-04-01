# Importer tous les modèles — correspondance exacte avec la BD
from app.models.utilisateur import Utilisateur
from app.models.session import SessionAuth
from app.models.abonnement import PlanAbonnement, Abonnement
from app.models.boutique import Boutique
from app.models.role import Role
from app.models.employe import EmployeBoutique
from app.models.parametre import ParametreUtilisateur
from app.models.notification import Notification
from app.models.export import ExportGenere
from app.models.journal import JournalConnexion
from app.models.produit import CategorieProduit, Produit
from app.models.stock import MouvementStock
from app.models.client import Client
from app.models.vente import Vente, LigneVente
from app.models.depense import Depense
from app.models.transaction import TransactionFinanciere
from app.models.wallet import Wallet
from app.models.epargne import Epargne
from app.models.microfinance import BanquePartenaire, MicroCredit
from app.models.tontine import Tontine, MembreTontine, CotisationTontine
from app.models.transcription import TranscriptionVocale
from app.models.dialogue import SessionDialogue, HistoriqueDialogue
from app.models.ia import MemoirePrix, VocabulaireIA, ApprentissageLangue, VersionModeleIA, ConnaissanceLocale
from app.models.score import HistoriqueScore
from app.models.sync import SyncQueue
from app.models.administrateur import Administrateur
from app.models.admin_log import LogAdmin
from app.models.metrique import MetriqueSysteme
from app.models.prevision import PrevisionML
from app.models.echeancier import EcheancierCredit
# Nouveaux modèles v3.0
from app.models.microfinance_new import (
    VirementWallet, CycleTontine, GarantieCredit, LitigeTontine,
    ScoreFiabiliteTontine, OTPCode, RechargeWallet, ProviderIA,
    MeteoCommerciale, ABTestIA
)
