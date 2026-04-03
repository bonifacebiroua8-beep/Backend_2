# app/services/microfinance_service.py — UbuntuTech v3.0
import random, string
from datetime import datetime, timedelta, date
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from loguru import logger

from app.models.wallet import Wallet
from app.models.microfinance import BanquePartenaire, MicroCredit
from app.models.echeancier import EcheancierCredit
from app.models.tontine import Tontine, MembreTontine, CotisationTontine
from app.models.epargne import Epargne
from app.models.transaction import TransactionFinanciere
from app.models.microfinance_new import (
    VirementWallet, CycleTontine, GarantieCredit, LitigeTontine,
    ScoreFiabiliteTontine, OTPCode, RechargeWallet
)
from app.models.utilisateur import Utilisateur
from app.core.security import hash_pin, verify_pin
from app.core.config import settings


class WalletService:

    @staticmethod
    def get_or_create(db: Session, id_utilisateur: int) -> Wallet:
        w = db.query(Wallet).filter(Wallet.id_utilisateur == id_utilisateur).first()
        if not w:
            w = Wallet(id_utilisateur=id_utilisateur, solde=0, solde_bloque=0)
            db.add(w)
            db.commit()
            db.refresh(w)
        return w

    @staticmethod
    def recharger(db: Session, id_utilisateur: int, montant: float, provider: str, telephone_source: Optional[str] = None) -> RechargeWallet:
        wallet = WalletService.get_or_create(db, id_utilisateur)
        frais = montant * 0.01 if provider in ("mtn_momo", "orange_money") else 0
        montant_net = montant - frais
        solde_avant = float(wallet.solde)
        wallet.solde = float(wallet.solde) + montant_net
        recharge = RechargeWallet(
            id_utilisateur=id_utilisateur,
            id_wallet=wallet.id_wallet,
            montant=montant, frais=frais, montant_net=montant_net,
            provider=provider, telephone_source=telephone_source,
            statut="confirme",
            solde_avant=solde_avant,
            solde_apres=float(wallet.solde),
            date_confirmation=datetime.utcnow()
        )
        db.add(recharge)
        TransactionFinanciere_log(db, id_utilisateur, "depot_wallet", montant_net, "entree",
            f"Recharge {provider} — {montant} FCFA", float(wallet.solde))
        db.commit()
        db.refresh(recharge)
        return recharge

    @staticmethod
    def virer(db: Session, envoyeur: Utilisateur, telephone_receveur: str, montant: float, motif: Optional[str] = None) -> VirementWallet:
        receveur = db.query(Utilisateur).filter(Utilisateur.telephone == telephone_receveur).first()
        if not receveur:
            raise ValueError("Destinataire introuvable")
        w_env = WalletService.get_or_create(db, envoyeur.id_utilisateur)
        w_rec = WalletService.get_or_create(db, receveur.id_utilisateur)
        frais = montant * 0.005  # 0.5% frais interne
        montant_net = montant - frais
        if float(w_env.solde) < montant:
            raise ValueError("Solde insuffisant")
        if float(w_env.plafond_journalier) < montant:
            raise ValueError(f"Montant dépasse le plafond journalier de {w_env.plafond_journalier} FCFA")
        solde_avant = float(w_env.solde)
        w_env.solde = float(w_env.solde) - montant
        w_rec.solde = float(w_rec.solde) + montant_net
        virement = VirementWallet(
            id_wallet_envoyeur=w_env.id_wallet,
            id_wallet_receveur=w_rec.id_wallet,
            id_utilisateur_envoyeur=envoyeur.id_utilisateur,
            id_utilisateur_receveur=receveur.id_utilisateur,
            montant=montant, frais=frais, montant_net=montant_net,
            motif=motif, otp_valide=True, statut="confirme",
            solde_avant_envoyeur=solde_avant,
            solde_apres_envoyeur=float(w_env.solde),
            date_confirmation=datetime.utcnow()
        )
        db.add(virement)
        db.commit()
        db.refresh(virement)
        return virement


class CreditService:

    @staticmethod
    def simuler(db: Session, id_banque: int, montant: float, duree_semaines: int) -> dict:
        banque = db.query(BanquePartenaire).filter(BanquePartenaire.id_banque == id_banque).first()
        if not banque:
            raise ValueError("Banque introuvable")
        taux_mensuel = float(banque.taux_interet_min) / 100 / 4
        nb_echeances = duree_semaines
        if taux_mensuel > 0:
            mensualite = montant * taux_mensuel / (1 - (1 + taux_mensuel) ** (-nb_echeances))
        else:
            mensualite = montant / nb_echeances
        total = mensualite * nb_echeances
        return {
            "montant": montant, "taux_interet": float(banque.taux_interet_min),
            "duree_semaines": duree_semaines, "mensualite": round(mensualite, 2),
            "total_interet": round(total - montant, 2), "total_rembourser": round(total, 2),
            "score_requis": int(banque.score_min_requis), "eligible": True
        }

    @staticmethod
    def demander(db: Session, user: Utilisateur, id_banque: int, montant: float,
                 duree_semaines: int, objet: Optional[str] = None, motif: Optional[str] = None) -> MicroCredit:
        banque = db.query(BanquePartenaire).filter(BanquePartenaire.id_banque == id_banque, BanquePartenaire.actif == True).first()
        if not banque:
            raise ValueError("Banque partenaire introuvable ou inactive")
        if float(user.score_credit) < float(banque.score_min_requis):
            raise ValueError(f"Score crédit insuffisant. Requis: {banque.score_min_requis}, votre score: {user.score_credit}")
        sim = CreditService.simuler(db, id_banque, montant, duree_semaines)
        credit = MicroCredit(
            id_emprunteur=user.id_utilisateur,
            id_banque=id_banque,
            montant_demande=montant,
            duree_semaines=duree_semaines,
            objet_credit=objet,
            motif_demande=motif,
            montant_accorde=montant,
            taux_interet=banque.taux_interet_min,
            score_ml_decision=user.score_credit,
            montant_total_du=sim["total_rembourser"],
            mensualite=sim["mensualite"],
            nb_echeances=duree_semaines,
            statut="approuve",
            date_decision=datetime.utcnow(),
            date_debut=date.today(),
            date_echeance=date.today() + timedelta(weeks=duree_semaines)
        )
        db.add(credit)
        db.flush()
        # Générer l'échéancier
        for i in range(1, duree_semaines + 1):
            ech = EcheancierCredit(
                id_credit=credit.id_credit,
                id_utilisateur=user.id_utilisateur,
                numero_echeance=i,
                date_echeance=date.today() + timedelta(weeks=i),
                montant_du=sim["mensualite"],
                montant_principal=montant/duree_semaines,
                montant_interet=sim["mensualite"] - montant/duree_semaines,
                solde_restant=sim["total_rembourser"] - sim["mensualite"] * i
            )
            db.add(ech)
        db.commit()
        db.refresh(credit)
        return credit

    @staticmethod
    def rembourser_echeance(db: Session, id_echeance: int, user: Utilisateur) -> EcheancierCredit:
        ech = db.query(EcheancierCredit).filter(
            EcheancierCredit.id_echeance == id_echeance,
            EcheancierCredit.id_utilisateur == user.id_utilisateur
        ).first()
        if not ech:
            raise ValueError("Échéance introuvable")
        if ech.statut == "payee":
            raise ValueError("Échéance déjà payée")
        wallet = WalletService.get_or_create(db, user.id_utilisateur)
        if float(wallet.solde) < float(ech.montant_du):
            raise ValueError("Solde wallet insuffisant")
        wallet.solde = float(wallet.solde) - float(ech.montant_du)
        ech.statut = "payee"
        ech.montant_paye = ech.montant_du
        ech.date_paiement = datetime.utcnow()
        ech.mode_paiement = "wallet"
        credit = db.query(MicroCredit).filter(MicroCredit.id_credit == ech.id_credit).first()
        if credit:
            credit.montant_rembourse = float(credit.montant_rembourse) + float(ech.montant_du)
            reste = db.query(EcheancierCredit).filter(
                EcheancierCredit.id_credit == credit.id_credit,
                EcheancierCredit.statut.in_(["a_venir","due","retard"])
            ).count()
            if reste == 0:
                credit.statut = "rembourse"
        db.commit()
        db.refresh(ech)
        return ech


class TontineService:

    @staticmethod
    def creer(db: Session, user: Utilisateur, data: dict) -> Tontine:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        tontine = Tontine(
            nom_tontine=data["nom_tontine"],
            id_admin=user.id_utilisateur,
            description=data.get("description"),
            cotisation_periodique=data["cotisation_periodique"],
            frequence=data["frequence"],
            nb_membres_max=data["nb_membres_max"],
            penalite_retard_pct=data.get("penalite_retard_pct", 5),
            mode_attribution=data.get("mode_attribution", "fixe"),
            langue_tontine=data.get("langue_tontine", "fr"),
            code_invitation=code,
            statut="en_attente"
        )
        db.add(tontine)
        db.flush()
        membre = MembreTontine(
            id_tontine=tontine.id_tontine,
            id_utilisateur=user.id_utilisateur,
            ordre_reception=1, statut="actif"
        )
        db.add(membre)
        tontine.nb_membres_actuel = 1
        db.commit()
        db.refresh(tontine)
        return tontine

    @staticmethod
    def rejoindre(db: Session, user: Utilisateur, code_invitation: str) -> Tontine:
        tontine = db.query(Tontine).filter(
            Tontine.code_invitation == code_invitation,
            Tontine.statut.in_(["en_attente","actif"])
        ).first()
        if not tontine:
            raise ValueError("Code d'invitation invalide ou tontine fermée")
        if tontine.nb_membres_actuel >= tontine.nb_membres_max:
            raise ValueError("Tontine complète")
        existe = db.query(MembreTontine).filter(
            MembreTontine.id_tontine == tontine.id_tontine,
            MembreTontine.id_utilisateur == user.id_utilisateur
        ).first()
        if existe:
            raise ValueError("Vous êtes déjà membre de cette tontine")
        ordre = tontine.nb_membres_actuel + 1
        membre = MembreTontine(
            id_tontine=tontine.id_tontine,
            id_utilisateur=user.id_utilisateur,
            ordre_reception=ordre, statut="actif"
        )
        db.add(membre)
        # Bloquer une cotisation dans le wallet comme caution
        wallet = WalletService.get_or_create(db, user.id_utilisateur)
        cotisation = float(tontine.cotisation_periodique)
        if float(wallet.solde) >= cotisation:
            wallet.solde = float(wallet.solde) - cotisation
            wallet.solde_bloque = float(wallet.solde_bloque) + cotisation
        tontine.nb_membres_actuel += 1
        db.commit()
        db.refresh(tontine)
        return tontine

    @staticmethod
    def payer_cotisation(db: Session, user: Utilisateur, id_tontine: int, mode_paiement: str = "wallet") -> CotisationTontine:
        tontine = db.query(Tontine).filter(Tontine.id_tontine == id_tontine).first()
        if not tontine:
            raise ValueError("Tontine introuvable")
        membre = db.query(MembreTontine).filter(
            MembreTontine.id_tontine == id_tontine,
            MembreTontine.id_utilisateur == user.id_utilisateur,
            MembreTontine.statut == "actif"
        ).first()
        if not membre:
            raise ValueError("Vous n'êtes pas membre actif de cette tontine")
        montant = float(tontine.cotisation_periodique)
        if mode_paiement == "wallet":
            wallet = WalletService.get_or_create(db, user.id_utilisateur)
            if float(wallet.solde) < montant:
                raise ValueError("Solde wallet insuffisant")
            wallet.solde = float(wallet.solde) - montant
        cotisation = CotisationTontine(
            id_tontine=id_tontine,
            id_membre=membre.id_membre,
            id_utilisateur=user.id_utilisateur,
            montant=montant,
            cycle=tontine.cycle_actuel,
            mode_paiement=mode_paiement,
            statut="payee"
        )
        db.add(cotisation)
        membre.total_cotise = float(membre.total_cotise) + montant
        membre.nb_cotisations = membre.nb_cotisations + 1
        tontine.cagnotte_actuelle = float(tontine.cagnotte_actuelle) + montant
        db.commit()
        db.refresh(cotisation)
        return cotisation


def TransactionFinanciere_log(db: Session, id_utilisateur: int, type_tx: str,
                               montant: float, sens: str, libelle: str,
                               solde_apres: Optional[float] = None,
                               id_boutique: Optional[int] = None):
    tx = TransactionFinanciere(
        id_utilisateur=id_utilisateur,
        id_boutique=id_boutique,
        type_transaction=type_tx,
        montant=montant,
        sens=sens,
        solde_apres=solde_apres,
        libelle=libelle,
    )
    db.add(tx)
