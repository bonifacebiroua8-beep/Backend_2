# app/services/score_service.py — UbuntuTech v3.0
from datetime import datetime, timedelta, date
from sqlalchemy.orm import Session
from sqlalchemy import func
from loguru import logger

from app.models.utilisateur import Utilisateur
from app.models.boutique import Boutique
from app.models.vente import Vente
from app.models.produit import Produit
from app.models.depense import Depense
from app.models.microfinance import MicroCredit
from app.models.score import HistoriqueScore
from app.models.transcription import TranscriptionVocale
from app.models.microfinance_new import ScoreFiabiliteTontine


class ScoreService:

    @staticmethod
    def calculer_score_sante(db: Session, id_boutique: int, user: Utilisateur, sauvegarder: bool = True) -> dict:
        score = 0
        details = {}
        now = datetime.utcnow()
        debut_30j = now - timedelta(days=30)
        debut_mois = now.replace(day=1, hour=0, minute=0, second=0)

        # 1. Régularité des ventes (25 pts)
        nb_jours_actifs = db.query(
            func.count(func.distinct(func.date(Vente.date_vente)))
        ).filter(Vente.id_boutique == id_boutique, Vente.statut == "validee",
                 Vente.date_vente >= debut_30j).scalar() or 0
        pts_reg = min(25, int(nb_jours_actifs / 20 * 25))
        score += pts_reg
        details["regularite_ventes"] = {"pts": pts_reg, "jours_actifs": nb_jours_actifs}

        # 2. Marge bénéficiaire (25 pts)
        revenus = float(db.query(func.sum(Vente.montant_total)).filter(
            Vente.id_boutique == id_boutique, Vente.statut == "validee",
            Vente.date_vente >= debut_mois).scalar() or 0)
        depenses = float(db.query(func.sum(Depense.montant)).filter(
            Depense.id_boutique == id_boutique, Depense.date_depense >= debut_mois).scalar() or 0)
        if revenus > 0:
            marge = (revenus - depenses) / revenus
            pts_marge = min(25, int(marge * 50))
        else:
            pts_marge = 0
        score += pts_marge
        details["marge_beneficiaire"] = {"pts": pts_marge, "revenus": revenus, "depenses": depenses}

        # 3. Gestion stock (20 pts)
        nb_produits = db.query(func.count(Produit.id_produit)).filter(
            Produit.id_boutique == id_boutique, Produit.actif == True).scalar() or 1
        nb_alertes = db.query(func.count(Produit.id_produit)).filter(
            Produit.id_boutique == id_boutique, Produit.actif == True,
            Produit.quantite_stock <= Produit.seuil_alerte_stock).scalar() or 0
        pct_alerte = nb_alertes / max(nb_produits, 1)
        pts_stock = int((1 - pct_alerte) * 20)
        score += pts_stock
        details["gestion_stock"] = {"pts": pts_stock, "nb_produits": nb_produits, "nb_alertes": nb_alertes}

        # 4. Diversification (15 pts)
        pts_div = min(15, nb_produits * 2)
        score += pts_div
        details["diversification"] = {"pts": pts_div, "nb_produits": nb_produits}

        # 5. Recouvrement crédits (15 pts)
        pts_recouvr = int((int(user.score_credit or 50) / 100) * 15)
        score += pts_recouvr
        details["recouvrement_credits"] = {"pts": pts_recouvr}

        score_final = min(100, max(0, score))
        if score_final >= 80: label = "Excellent"
        elif score_final >= 60: label = "Bon"
        elif score_final >= 40: label = "Moyen"
        else: label = "Critique"

        if sauvegarder:
            db.add(HistoriqueScore(
                id_utilisateur=user.id_utilisateur, id_boutique=id_boutique,
                type_score="sante_business", score=score_final,
                details_json=details, date_calcul=date.today()
            ))
            user.score_sante_business = score_final

        return {"score": score_final, "label": label, "details": details}

    @staticmethod
    def calculer_score_credit(db: Session, user: Utilisateur, sauvegarder: bool = True) -> dict:
        score = 0
        details = {}

        # 1. Comportement financier — ventes régulières (35 pts)
        nb_jours_90 = db.query(
            func.count(func.distinct(func.date(Vente.date_vente)))
        ).filter(Vente.statut == "validee",
                 Vente.date_vente >= datetime.utcnow() - timedelta(days=90)).scalar() or 0
        pts_finance = min(35, int(nb_jours_90 / 60 * 35))
        score += pts_finance
        details["comportement_financier"] = {"pts": pts_finance, "jours_actifs_90j": nb_jours_90}

        # 2. Historique remboursements (25 pts)
        credits = db.query(MicroCredit).filter(MicroCredit.id_emprunteur == user.id_utilisateur).all()
        if credits:
            rembourses = [c for c in credits if c.statut == "rembourse"]
            en_retard = [c for c in credits if c.statut == "en_retard"]
            ratio = len(rembourses) / len(credits)
            penalite = len(en_retard) * 5
            pts_remb = max(0, int(ratio * 25) - penalite)
        else:
            pts_remb = 12  # Bénéfice du doute
        score += pts_remb
        details["historique_remboursements"] = {"pts": pts_remb, "nb_credits": len(credits) if credits else 0}

        # 3. Engagement application vocal (20 pts)
        nb_vocal_30j = db.query(func.count(TranscriptionVocale.id_transcription)).filter(
            TranscriptionVocale.id_utilisateur == user.id_utilisateur,
            TranscriptionVocale.date_creation >= datetime.utcnow() - timedelta(days=30)
        ).scalar() or 0
        pts_vocal = min(20, int(nb_vocal_30j / 20 * 20))
        score += pts_vocal
        details["engagement_vocal"] = {"pts": pts_vocal, "transcriptions_30j": nb_vocal_30j}

        # 4. Profil tontinier (12 pts)
        sft = db.query(ScoreFiabiliteTontine).filter(
            ScoreFiabiliteTontine.id_utilisateur == user.id_utilisateur).first()
        pts_tontine = int((sft.score / 100 * 12)) if sft else 6
        score += pts_tontine
        details["profil_tontine"] = {"pts": pts_tontine}

        # 5. Ancienneté (8 pts)
        jours = (datetime.utcnow() - user.date_inscription).days
        pts_anc = min(8, int(jours / 365 * 8))
        score += pts_anc
        details["anciennete"] = {"pts": pts_anc, "jours": jours}

        score_final = min(100, max(0, score))

        # Éligibilité
        if score_final >= 80:
            eligibilite, montant_max = "eligible_banques", 1000000
        elif score_final >= 65:
            eligibilite, montant_max = "eligible_ubuntutech", 300000
        elif score_final >= 45:
            eligibilite, montant_max = "eligible_tontine", 100000
        else:
            eligibilite, montant_max = "non_eligible", 0

        if sauvegarder:
            db.add(HistoriqueScore(
                id_utilisateur=user.id_utilisateur,
                type_score="credit", score=score_final,
                details_json=details, date_calcul=date.today()
            ))
            user.score_credit = score_final

        return {
            "score": score_final, "eligibilite": eligibilite,
            "montant_max": montant_max, "details": details,
            "label": "Excellent" if score_final >= 80 else "Bon" if score_final >= 65 else "Moyen" if score_final >= 45 else "Faible"
        }

    @staticmethod
    def recalculer_tout(db: Session, user: Utilisateur):
        ScoreService.calculer_score_credit(db, user)
        boutiques = db.query(Boutique).filter(
            Boutique.id_utilisateur == user.id_utilisateur, Boutique.actif == True).all()
        for b in boutiques:
            ScoreService.calculer_score_sante(db, b.id_boutique, user)
        db.commit()

    @staticmethod
    def recalculer_score_fiabilite_tontine(db: Session, id_utilisateur: int):
        from app.models.tontine import MembreTontine, CotisationTontine
        membres = db.query(MembreTontine).filter(MembreTontine.id_utilisateur == id_utilisateur).all()
        nb_tontines = len(membres)
        nb_tontines_actives = len([m for m in membres if m.statut == "actif"])
        nb_cotisations = sum(m.nb_cotisations for m in membres)
        nb_retards = sum(m.nb_retards for m in membres)
        pct = round((nb_cotisations - nb_retards) / max(nb_cotisations, 1) * 100, 1)
        score = max(0, min(100, int(pct)))
        sft = db.query(ScoreFiabiliteTontine).filter(ScoreFiabiliteTontine.id_utilisateur == id_utilisateur).first()
        if not sft:
            sft = ScoreFiabiliteTontine(id_utilisateur=id_utilisateur)
            db.add(sft)
        sft.score = score
        sft.nb_tontines_total = nb_tontines
        sft.nb_tontines_actives = nb_tontines_actives
        sft.nb_cotisations_total = nb_cotisations
        sft.nb_cotisations_retard = nb_retards
        sft.pct_ponctualite = pct
        db.commit()
