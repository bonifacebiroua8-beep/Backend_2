# app/tasks/scheduler.py — UbuntuTech v3.0
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from loguru import logger
from datetime import datetime, timedelta, date

scheduler = BackgroundScheduler(timezone="Africa/Douala")


def recalculer_scores():
    """02h00 — Recalcul scores santé + crédit tous les utilisateurs actifs"""
    try:
        from app.core.database import SessionLocal
        from app.models.utilisateur import Utilisateur
        from app.services.score_service import ScoreService
        db = SessionLocal()
        try:
            hier = datetime.utcnow() - timedelta(days=30)
            users = db.query(Utilisateur).filter(
                Utilisateur.actif == True,
                Utilisateur.derniere_connexion >= hier
            ).all()
            for user in users:
                try:
                    ScoreService.recalculer_tout(db, user)
                except Exception as e:
                    logger.warning(f"Score user {user.id_utilisateur}: {e}")
            logger.info(f"✅ Scores recalculés pour {len(users)} utilisateurs")
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Erreur recalcul scores: {e}")


def envoyer_rappels_echeances():
    """08h00 — Rappels SMS J-7, J-3, J-1 avant échéances crédit"""
    try:
        from app.core.database import SessionLocal
        from app.models.echeancier import EcheancierCredit
        from app.services.sms_service import SMSService
        db = SessionLocal()
        try:
            today = date.today()
            for jours, champ in [(7, "rappel_j7_envoye"), (3, "rappel_j3_envoye"), (1, "rappel_j1_envoye")]:
                date_cible = today + timedelta(days=jours)
                echeances = db.query(EcheancierCredit).filter(
                    EcheancierCredit.date_echeance == date_cible,
                    EcheancierCredit.statut.in_(["a_venir","due"]),
                    getattr(EcheancierCredit, champ) == False
                ).all()
                for ech in echeances:
                    try:
                        setattr(ech, champ, True)
                        logger.info(f"Rappel J-{jours} échéance {ech.id_echeance}")
                    except Exception as e:
                        logger.warning(f"Rappel échoué: {e}")
            db.commit()
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Erreur rappels: {e}")


def marquer_echeances_retard():
    """00h30 — Marquer échéances passées comme 'retard'"""
    try:
        from app.core.database import SessionLocal
        from app.models.echeancier import EcheancierCredit
        from app.models.microfinance import MicroCredit
        db = SessionLocal()
        try:
            today = date.today()
            echeances = db.query(EcheancierCredit).filter(
                EcheancierCredit.date_echeance < today,
                EcheancierCredit.statut.in_(["a_venir","due"])
            ).all()
            for ech in echeances:
                ech.statut = "retard"
                credit = db.query(MicroCredit).filter(MicroCredit.id_credit == ech.id_credit).first()
                if credit and credit.statut == "en_cours":
                    credit.statut = "en_retard"
            db.commit()
            logger.info(f"✅ {len(echeances)} échéances marquées en retard")
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Erreur retards: {e}")


def nettoyer_sessions():
    """Chaque heure — Nettoyer sessions JWT expirées"""
    try:
        from app.core.database import SessionLocal
        from app.models.session import SessionAuth
        db = SessionLocal()
        try:
            nb = db.query(SessionAuth).filter(
                SessionAuth.date_expiration < datetime.utcnow()
            ).update({"actif": False})
            db.commit()
            if nb > 0:
                logger.debug(f"Sessions expirées: {nb}")
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Erreur nettoyage sessions: {e}")


def supprimer_exports():
    """03h00 — Supprimer exports PDF/Excel > 7 jours"""
    try:
        import os
        from app.core.database import SessionLocal
        from app.models.export import ExportGenere
        db = SessionLocal()
        try:
            seuil = datetime.utcnow() - timedelta(days=7)
            exports = db.query(ExportGenere).filter(
                ExportGenere.date_expiration < datetime.utcnow(),
                ExportGenere.statut == "termine"
            ).all()
            for exp in exports:
                if exp.chemin_fichier and os.path.exists(exp.chemin_fichier):
                    try:
                        os.remove(exp.chemin_fichier)
                    except Exception:
                        pass
            db.commit()
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Erreur suppression exports: {e}")


def reset_compteurs_freemium():
    """1er du mois 00h05 — Réinitialiser compteurs freemium"""
    try:
        from app.core.database import SessionLocal
        from sqlalchemy import text
        db = SessionLocal()
        try:
            db.execute(text("UPDATE utilisateurs SET nb_ventes_mois=0, nb_questions_ia_mois=0, nb_vocal_mois=0"))
            db.commit()
            logger.info("✅ Compteurs freemium réinitialisés")
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Erreur reset freemium: {e}")


def calculer_metriques_quotidiennes():
    """23h50 — Snapshot métriques système"""
    try:
        from app.core.database import SessionLocal
        from app.models.utilisateur import Utilisateur
        from app.models.vente import Vente
        from app.models.dialogue import HistoriqueDialogue
        from app.models.transcription import TranscriptionVocale
        from app.models.metrique import MetriqueSysteme
        from sqlalchemy import func
        db = SessionLocal()
        try:
            today = date.today()
            existe = db.query(MetriqueSysteme).filter(MetriqueSysteme.date_mesure == today).first()
            if not existe:
                nb_total = db.query(func.count(Utilisateur.id_utilisateur)).filter(Utilisateur.actif == True).scalar()
                nb_actifs = db.query(func.count(Utilisateur.id_utilisateur)).filter(
                    Utilisateur.actif == True,
                    Utilisateur.derniere_connexion >= datetime.utcnow() - timedelta(days=1)
                ).scalar()
                nb_gratuit = db.query(func.count(Utilisateur.id_utilisateur)).filter(Utilisateur.type_abonnement == "gratuit").scalar()
                nb_pro = db.query(func.count(Utilisateur.id_utilisateur)).filter(Utilisateur.type_abonnement == "pro").scalar()
                nb_premium = db.query(func.count(Utilisateur.id_utilisateur)).filter(Utilisateur.type_abonnement == "premium").scalar()
                nb_ventes = db.query(func.count(Vente.id_vente)).filter(func.date(Vente.date_vente) == today).scalar()
                nb_dialogues = db.query(func.count(HistoriqueDialogue.id_dialogue)).filter(func.date(HistoriqueDialogue.date_dialogue) == today).scalar()
                nb_trans = db.query(func.count(TranscriptionVocale.id_transcription)).filter(func.date(TranscriptionVocale.date_creation) == today).scalar()
                db.add(MetriqueSysteme(
                    date_mesure=today,
                    nb_utilisateurs_total=int(nb_total or 0),
                    nb_utilisateurs_actifs=int(nb_actifs or 0),
                    nb_abonnes_gratuit=int(nb_gratuit or 0),
                    nb_abonnes_pro=int(nb_pro or 0),
                    nb_abonnes_premium=int(nb_premium or 0),
                    nb_ventes_jour=int(nb_ventes or 0),
                    nb_dialogues_ia_jour=int(nb_dialogues or 0),
                    nb_transcriptions_jour=int(nb_trans or 0),
                ))
                db.commit()
                logger.info("✅ Métriques quotidiennes enregistrées")
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Erreur métriques: {e}")


def demarrer_scheduler():
    if scheduler.running:
        return
    scheduler.add_job(recalculer_scores,        CronTrigger(hour=2,  minute=0),  id="scores")
    scheduler.add_job(envoyer_rappels_echeances, CronTrigger(hour=8,  minute=0),  id="rappels")
    scheduler.add_job(marquer_echeances_retard,  CronTrigger(hour=0,  minute=30), id="retards")
    scheduler.add_job(nettoyer_sessions,         CronTrigger(minute=0),           id="sessions")
    scheduler.add_job(supprimer_exports,         CronTrigger(hour=3,  minute=0),  id="exports")
    scheduler.add_job(calculer_metriques_quotidiennes, CronTrigger(hour=23, minute=50), id="metriques")
    scheduler.add_job(reset_compteurs_freemium,  CronTrigger(day=1, hour=0, minute=5), id="freemium")
    scheduler.start()
    logger.info("✅ Scheduler UbuntuTech démarré — 7 tâches planifiées")


def arreter_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler arrêté")
