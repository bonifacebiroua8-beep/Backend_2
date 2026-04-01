# app/services/ia_service.py
# ============================================================
#  UBUNTUTECH — Service IA : Groq Llama 3.3 70B + Fallback v3.0
#  Améliorations v3 :
#   - Classifier multilingue (fr, ff, ha, mfa)
#   - Prompts enrichis par langue
#   - Fallback complet pour tous les domaines
#   - Mémoire inter-sessions depuis la DB
# ============================================================
import time
import random
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from loguru import logger
import httpx

from app.models.dialogue import SessionDialogue, HistoriqueDialogue
from app.models.utilisateur import Utilisateur
from app.models.vente import Vente
from app.models.produit import Produit
from app.models.depense import Depense
from app.models.client import Client
from app.core.config import settings
try:
    from app.services.chromadb_service import ChromaDBService
    _CHROMA_OK = True

except Exception:
    ChromaDBService = None
    _CHROMA_OK = False



# ══════════════════════════════════════════════════════════════
# CLASSIFIER MULTILINGUE — fr + ff + ha + mfa
# ══════════════════════════════════════════════════════════════
INTENTIONS = {
    "stock": {
        "fr":  ["stock", "produit", "rupture", "quantite", "commander", "inventaire", "article", "marchandise", "manque"],
        "ff":  ["buyre", "nde", "heɓaani", "addu", "kuuje", "winde"],
        "ha":  ["kaya", "karin", "karanci", "sayo", "kaya", "hannun jari"],
        "mfa": ["tsəkwar", "hina", "mana tsəkwar"],
    },
    "finances": {
        "fr":  ["bénéfice", "benefice", "profit", "depense", "revenu", "bilan", "finance", "argent", "gagné", "gagne", "chiffre", "perte"],
        "ff":  ["kaalis", "yooro", "ɓoornude", "jom kaalis", "winnditaade", "faayiida"],
        "ha":  ["kudi", "riba", "asara", "kashe kudi", "kudin shiga", "ribar kudi"],
        "mfa": ["lami", "ndzəŋ", "tsak lami", "mbulum lami"],
    },
    "credit": {
        "fr":  ["crédit", "credit", "prêt", "pret", "emprunter", "score", "éligible", "eligible", "banque", "dette"],
        "ff":  ["defte", "jom defte", "hokkude", "ñaagaade", "banke"],
        "ha":  ["bashi", "bada bashi", "rancen kudi", "banki", "cancen"],
        "mfa": ["dete", "bərfə dete", "banki"],
    },
    "business": {
        "fr":  ["vente", "vendu", "vendre", "client", "chiffre", "transaction", "acheteur", "commerce"],
        "ff":  ["sayaare", "soodano", "jeyɗo", "ngalu", "maaro", "jaayɗo"],
        "ha":  ["siyar da", "sayar", "abokin ciniki", "kasuwanci", "ciniki"],
        "mfa": ["plari", "slan", "ndəv", "mbiyar"],
    },
    "saison_fete": {
        "fr":  ["ramadan", "tabaski", "noël", "noel", "fête", "fete", "saison", "récolte", "recolte", "aïd", "aid"],
        "ff":  ["koorka", "tabaski", "juulde", "ndungu", "lewru"],
        "ha":  ["azumi", "babbar sallah", "ƙaramar sallah", "damina", "girbi"],
        "mfa": ["sla", "azəm", "masla"],
    },
    "marche_local": {
        "fr":  ["prix", "marché", "marche", "fournisseur", "acheter", "grossiste", "negocier", "négocier"],
        "ff":  ["njaru", "luumo", "jeyɗo huunde", "nanngi njaru", "loomre"],
        "ha":  ["farashi", "kasuwa", "mai saida", "tattaunawa", "bargain"],
        "mfa": ["ndzər", "shigi", "wuta ndzər"],
    },
    "prevision": {
        "fr":  ["prévision", "prevision", "futur", "semaine prochaine", "mois prochain", "tendance", "prévoir", "demain"],
        "ff":  ["eggo", "fahin", "caggal jonte", "caggal lewru", "fewndo"],
        "ha":  ["hasashe", "gobe", "mako mai zuwa", "watan nan gaba", "tsinkaya"],
        "mfa": ["ɗaf", "yuw", "tsik ɗaf"],
    },
    "tontine": {
        "fr":  ["tontine", "cotisation", "tour", "cycle", "groupe", "association", "njangi"],
        "ff":  ["liggey", "boowal", "ɓooyngel", "debbo", "gannde"],
        "ha":  ["adashi", "tara", "kungiya", "zagaye", "aro"],
        "mfa": ["njangi", "nkap", "mbiyar njangi"],
    },
    "microfinance": {
        "fr":  ["micro", "emprunt", "remboursement", "mensualité", "mensualite", "microfinance", "mfi"],
        "ff":  ["hokkude kaalis", "reddude", "lewru kala", "kaalis hooram"],
        "ha":  ["aro", "biya", "kudin wata", "dawo da kudi", "karamin bashi"],
        "mfa": ["bərfə", "wul bərfə", "tsak wata"],
    },
}

# ══════════════════════════════════════════════════════════════
# PROMPTS SYSTEME PAR LANGUE
# ══════════════════════════════════════════════════════════════
PROMPTS_LANGUE = {
    "fr": (
        "Réponds en français, de façon concise (max 150 mots), pratique et bienveillante. "
        "Utilise des chiffres concrets. Tu es un ami-conseiller, pas un professeur."
    ),
    "ff": (
        "L'utilisateur parle Fulfuldé (Pulaar). "
        "Réponds OBLIGATOIREMENT en Fulfuldé autant que possible, avec quelques mots français si nécessaire. "
        "Exemples de mots utiles : kaalis=argent, buyre=produit, faayiida=bénéfice, defte=dette, "
        "sayaare=vente, luumo=marché, nde=ici/ce. "
        "Sois très court (max 80 mots), chaleureux, pratique. "
        "Si tu ne sais pas un mot en fulfuldé, utilise le français entre parenthèses."
    ),
    "ha": (
        "L'utilisateur parle Haoussa. "
        "Réponds OBLIGATOIREMENT en Haoussa autant que possible, avec quelques mots français si nécessaire. "
        "Exemples de mots utiles : kudi=argent, kaya=marchandise, riba=bénéfice, bashi=dette, "
        "siyar=vendre, kasuwa=marché, ciniki=commerce, gobe=demain. "
        "Sois très court (max 80 mots), chaleureux, pratique. "
        "Si tu ne sais pas un mot en haoussa, utilise le français entre parenthèses."
    ),
    "en": (
        "Respond in English, concisely and practically. "
        "You are a friendly business advisor, not a professor. "
        "Use concrete numbers and actionable advice."
    ),
    "mfa": (
        "L'utilisateur parle Mafa (langue du Nord-Cameroun, massif des Mandara). "
        "Réponds avec quelques mots Mafa mélangés au français. "
        "Exemples de mots utiles : lami=argent, tsəkwar=marchandise, ndzəŋ=bénéfice, "
        "dete=dette, plari=vendre, shigi=marché, njangi=tontine. "
        "Sois très court (max 80 mots), chaleureux, pratique. "
        "Utilise le français pour les concepts complexes."
    ),
}


class IAService:

    # ── Client Groq avec retry ────────────────────────────────
    _GROQ_MAX_RETRIES = 2
    _GROQ_RETRY_DELAYS = [1.0, 3.0]

    @staticmethod
    def _appeler_groq(messages: list, max_tokens: int = None) -> Optional[str]:
        if not settings.GROQ_API_KEY:
            logger.warning("GROQ_API_KEY non configuree")
            return None

        max_tokens = max_tokens or settings.GROQ_MAX_TOKENS

        for attempt in range(IAService._GROQ_MAX_RETRIES):
            try:
                with httpx.Client(timeout=httpx.Timeout(
                    
                    connect=10.0,
                    read=45.0,
                    write=10.0,
                    pool=5.0
                )) as client:
                    
                    resp = client.post(
                        "https://api.groq.com/openai/v1/chat/completions",
                        headers={
                            "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                            "Content-Type":  "application/json",
                        },
                        json={
                            "model":       settings.GROQ_MODEL,
                            "messages":    messages,
                            "max_tokens":  max_tokens,
                            "temperature": settings.GROQ_TEMPERATURE,
                            "stop":        None,
                        },
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        return data["choices"][0]["message"]["content"].strip()
                    elif resp.status_code == 429:
                        wait = IAService._GROQ_RETRY_DELAYS[attempt] * 2 + random.uniform(0, 1)
                        logger.warning(f"Groq rate limit (tentative {attempt+1}) — attente {wait:.1f}s")
                        if attempt < IAService._GROQ_MAX_RETRIES - 1:
                            time.sleep(wait)
                        continue
                    elif resp.status_code >= 500:
                        logger.warning(f"Groq erreur serveur {resp.status_code} (tentative {attempt+1})")
                        if attempt < IAService._GROQ_MAX_RETRIES - 1:
                            time.sleep(IAService._GROQ_RETRY_DELAYS[attempt] + random.uniform(0, 0.5))
                        continue
                    else:
                        logger.error(f"Groq erreur {resp.status_code}: {resp.text[:300]}")
                        return None

            except httpx.RemoteProtocolError as e:
                wait = IAService._GROQ_RETRY_DELAYS[attempt] + random.uniform(0, 0.5)
                logger.warning(
                    f"Groq deconnecte (tentative {attempt+1}/{IAService._GROQ_MAX_RETRIES})"
                    f" — retry dans {wait:.1f}s : {e}"
                )
                if attempt < IAService._GROQ_MAX_RETRIES - 1:
                    time.sleep(wait)
                continue
            except httpx.TimeoutException:
                logger.warning(f"Groq timeout ({settings.GROQ_TIMEOUT}s, tentative {attempt+1}) — fallback")
                return None
            except httpx.ConnectError as e:
                wait = IAService._GROQ_RETRY_DELAYS[attempt] + random.uniform(0, 0.5)
                logger.warning(f"Groq connexion impossible (tentative {attempt+1}) — retry dans {wait:.1f}s : {e}")
                if attempt < IAService._GROQ_MAX_RETRIES - 1:
                    time.sleep(wait)
                continue
            except Exception as e:
                logger.error(f"Groq exception inattendue : {e}")
                return None

        logger.error(f"Groq : echec apres {IAService._GROQ_MAX_RETRIES} tentatives — bascule sur fallback")
        return None

    # ── Mémoire inter-sessions ────────────────────────────────
    @staticmethod
    def _charger_memoire_utilisateur(
        db: Session,
        id_utilisateur: int,
        id_boutique: Optional[int],
        limite: int = 6,
    ) -> List[dict]:
        """
        Charge les derniers échanges de l'utilisateur depuis la DB
        pour fournir un contexte historique même entre sessions.
        """
        try:
            q = db.query(HistoriqueDialogue).filter(
                HistoriqueDialogue.id_utilisateur == id_utilisateur,
            )
            if id_boutique:
                q = q.filter(HistoriqueDialogue.id_boutique == id_boutique)

            items = q.order_by(HistoriqueDialogue.date_dialogue.desc()).limit(limite).all()
            items = list(reversed(items))

            messages = []
            for item in items:
                messages.append({"role": "user",      "content": item.message_utilisateur})
                messages.append({"role": "assistant",  "content": item.reponse_ia})
            return messages
        except Exception as e:
            logger.warning(f"Memoire inter-sessions non chargee : {e}")
            return []

    # ── Classifier multilingue ────────────────────────────────
    @staticmethod
    def _classifier(message: str, langue: str) -> tuple:
        msg = message.lower()
        lang_key = langue if langue in ("fr", "ff", "ha", "mfa") else "fr"

        for domaine, mots_par_langue in INTENTIONS.items():
            # Vérifier d'abord dans la langue native
            mots_natifs = mots_par_langue.get(lang_key, [])
            if any(kw in msg for kw in mots_natifs):
                return domaine, f"{domaine}_query"
            # Vérifier aussi en français (mots mixtes fréquents)
            mots_fr = mots_par_langue.get("fr", [])
            if any(kw in msg for kw in mots_fr):
                return domaine, f"{domaine}_query"

        return "general", "general_query"

    # ── Contexte boutique riche ───────────────────────────────
    @staticmethod
    def _construire_contexte_systeme(
        db: Session,
        user: Utilisateur,
        id_boutique: Optional[int],
        langue: str,
    ) -> str:
        now = datetime.utcnow()
        debut_mois = now.replace(day=1, hour=0, minute=0, second=0)
        hier = now - timedelta(days=1)

        ctx = [
            "Tu es UbuntuTech, l'assistant IA intelligent pour micro-entrepreneurs du Grand Nord Cameroun.",
            f"Commerçant : {user.nom_complet}. Plan : {user.type_abonnement}.",
            f"Score santé business : {user.score_sante_business or 50}/100. Score crédit : {user.score_credit or 50}/100.",
        ]

        if id_boutique:
            try:
                produits = db.query(Produit).filter(
                    Produit.id_boutique == id_boutique, Produit.actif == True
                ).limit(15).all()

                if produits:
                    critiques = [p for p in produits if float(p.quantite_stock) <= float(p.seuil_alerte_stock)]
                    top_ventes = sorted(produits, key=lambda p: int(p.nb_ventes or 0), reverse=True)[:3]
                    ctx.append(f"Stock : {len(produits)} produits, {len(critiques)} en alerte.")
                    if critiques:
                        ctx.append(f"Produits critiques : {', '.join(p.nom_produit for p in critiques[:3])}.")
                    if top_ventes:
                        ctx.append(f"Top ventes : {', '.join(p.nom_produit for p in top_ventes)}.")
            except Exception:
                pass

            try:
                rev = db.query(func.sum(Vente.montant_total)).filter(
                    Vente.id_boutique == id_boutique,
                    Vente.statut == "validee",
                    Vente.date_vente >= debut_mois
                ).scalar() or 0

                nb_v = db.query(func.count(Vente.id_vente)).filter(
                    Vente.id_boutique == id_boutique,
                    Vente.statut == "validee",
                    Vente.date_vente >= debut_mois
                ).scalar() or 0

                dep = db.query(func.sum(Depense.montant)).filter(
                    Depense.id_boutique == id_boutique,
                    Depense.date_depense >= debut_mois
                ).scalar() or 0

                ctx.append(
                    f"Ce mois ({now.strftime('%B %Y')}) : "
                    f"revenus {float(rev):,.0f} FCFA, dépenses {float(dep):,.0f} FCFA, "
                    f"bénéfice {float(rev)-float(dep):,.0f} FCFA sur {nb_v} ventes."
                )

                rev_hier = db.query(func.sum(Vente.montant_total)).filter(
                    Vente.id_boutique == id_boutique,
                    Vente.statut == "validee",
                    Vente.date_vente >= hier,
                    Vente.date_vente < now,
                ).scalar() or 0
                ctx.append(f"Ventes hier : {float(rev_hier):,.0f} FCFA.")
            except Exception:
                pass

            try:
                res = db.query(func.sum(Client.solde_credit), func.count(Client.id_client)).filter(
                    Client.id_boutique == id_boutique, Client.solde_credit > 0
                ).first()
                if res and res[0]:
                    ctx.append(f"Crédits clients : {float(res[0]):,.0f} FCFA chez {res[1]} client(s).")
            except Exception:
                pass

        # Prompt langue
        prompt_langue = PROMPTS_LANGUE.get(langue, PROMPTS_LANGUE["fr"])
        ctx.append(prompt_langue)

        return " ".join(ctx)

    # ── Point d'entrée dialogue ───────────────────────────────
    @staticmethod
    def dialoguer(
        db: Session,
        message: str,
        langue: str,
        source: str,
        user: Utilisateur,
        id_boutique: Optional[int] = None,
        id_session: Optional[int] = None,
        historique: Optional[List[str]] = None,
    ) -> dict:
        debut = time.time()

        session = IAService._get_ou_creer_session(db, user.id_utilisateur, id_boutique, id_session)
        domaine, intention = IAService._classifier(message, langue)

        if (user.type_abonnement == "gratuit" and
                int(user.nb_questions_ia_mois or 0) >= settings.FREE_MAX_QUESTIONS_IA):
            reponse = (
                f"Vous avez atteint la limite de {settings.FREE_MAX_QUESTIONS_IA} questions IA ce mois. "
                f"Passez au plan Pro pour continuer à me consulter. 😊"
            )
            confiance = 1.0
        else:
            systeme = IAService._construire_contexte_systeme(db, user, id_boutique, langue)

            # ── INJECTION RAG ChromaDB — mémoire locale validée par admin
            try:
                rag_ctx = ChromaDBService.construire_contexte_rag(message, langue)
                if rag_ctx:
                    systeme += rag_ctx
            except Exception as e:
                logger.warning(f"RAG ChromaDB échoué (non bloquant) : {e}")

            msgs = [{"role": "system", "content": systeme}]

            # Mémoire inter-sessions depuis la DB
            memoire_db = IAService._charger_memoire_utilisateur(db, user.id_utilisateur, id_boutique)
            if memoire_db:
                msgs.extend(memoire_db)

            # Historique session courante (priorité sur la mémoire DB)
            if historique:
                for i, h in enumerate(historique[-6:]):
                    msgs.append({"role": "user" if i % 2 == 0 else "assistant", "content": h})

            msgs.append({"role": "user", "content": message})

            reponse = IAService._appeler_groq(msgs)
            confiance = 0.95 if reponse else 0.75

            if not reponse:
                res = IAService._fallback_regles(db, message, langue, domaine, intention, user, id_boutique)
                reponse   = res["texte"]
                confiance = res.get("confiance", 0.75)

        temps_ms = int((time.time() - debut) * 1000)

        # FIX DEADLOCK : 2 transactions séparées
        dial = HistoriqueDialogue(
            id_session_dialogue = session.id_session_dialogue,
            id_utilisateur      = user.id_utilisateur,
            id_boutique         = id_boutique,
            message_utilisateur = message,
            langue_message      = langue,
            source_message      = source,
            reponse_ia          = reponse,
            langue_reponse      = langue,
            intention           = intention,
            domaine             = domaine,
            score_confiance     = min(confiance, 0.999),
            temps_reponse_ms    = temps_ms,
            date_dialogue       = datetime.utcnow(),
        )
        db.add(dial)

        session.nb_tours           = int(session.nb_tours or 0) + 1
        session.derniere_intention = intention
        session.date_expiration    = datetime.utcnow() + timedelta(minutes=30)

        db.flush()

        db.execute(
            text(
                "UPDATE utilisateurs "
                "SET nb_questions_ia_mois = nb_questions_ia_mois + 1 "
                "WHERE id_utilisateur = :uid"
            ),
            {"uid": user.id_utilisateur},
        )
        user.nb_questions_ia_mois = int(user.nb_questions_ia_mois or 0) + 1

        db.commit()
        db.refresh(dial)

        suggestions = IAService._suggestions_contextuelles(domaine, user)

        logger.info(
            f"IA dialogue : user={user.id_utilisateur}, domaine={domaine}, langue={langue}, "
            f"temps={temps_ms}ms, confiance={confiance:.2f}"
        )

        return {
            "id_dialogue":      dial.id_dialogue,
            "reponse":          reponse,
            "reponse_ia":       reponse,
            "langue_reponse":   langue,
            "domaine":          domaine,
            "intention":        intention,
            "score_confiance":  confiance,
            "temps_reponse_ms": temps_ms,
            "id_session":       session.id_session_dialogue,
            "suggestions":      suggestions,
        }

    @staticmethod
    def _get_ou_creer_session(db, id_utilisateur, id_boutique, id_session):
        if id_session:
            s = db.query(SessionDialogue).filter(
                SessionDialogue.id_session_dialogue == id_session,
                SessionDialogue.id_utilisateur      == id_utilisateur,
                SessionDialogue.statut              == "active",
                SessionDialogue.date_expiration     > datetime.utcnow(),
            ).first()
            if s:
                return s

        s = db.query(SessionDialogue).filter(
            SessionDialogue.id_utilisateur  == id_utilisateur,
            SessionDialogue.statut          == "active",
            SessionDialogue.date_expiration > datetime.utcnow(),
        ).order_by(SessionDialogue.date_creation.desc()).first()
        if s:
            return s

        now = datetime.utcnow()
        s = SessionDialogue(
            id_utilisateur  = id_utilisateur,
            id_boutique     = id_boutique,
            nb_tours        = 0,
            statut          = "active",
            date_creation   = now,
            date_expiration = now + timedelta(minutes=30),
        )
        db.add(s)
        db.flush()
        return s

    @staticmethod
    def _suggestions_contextuelles(domaine: str, user) -> list:
        base = ["📦 Mon stock", "💰 Mon bénéfice", "📊 Mes ventes", "🏦 Mon crédit"]
        if domaine == "stock":
            return ["📦 Produits critiques", "📊 Top ventes", "💰 Mon bénéfice", "🏦 Mon crédit"]
        elif domaine == "finances":
            return ["📊 Bilan du mois", "📉 Mes dépenses", "💹 Prévision", "📦 Mon stock"]
        elif domaine == "credit":
            return ["🏦 Simuler un crédit", "📊 Améliorer mon score", "🤝 Tontine", "💰 Mon bénéfice"]
        elif domaine == "prevision":
            return ["📈 Ventes semaine", "📦 Ruptures à venir", "💡 Conseil saisonnier", "📊 Bilan"]
        elif domaine == "tontine":
            return ["🤝 Ma tontine", "💳 Prochaine cotisation", "📊 Bilan", "🏦 Mon crédit"]
        elif domaine == "microfinance":
            return ["💳 Mes remboursements", "🏦 Mon score crédit", "💰 Mon bénéfice", "🤝 Tontine"]
        elif domaine == "business":
            return ["📊 Mes meilleures ventes", "👥 Mes clients", "💰 Mon bénéfice", "📦 Mon stock"]
        elif domaine == "marche_local":
            return ["💹 Prix du marché", "📦 Mes fournisseurs", "📊 Mes ventes", "💰 Mon bénéfice"]
        elif domaine == "saison_fete":
            return ["📈 Prévision saison", "📦 Stock fête", "💰 Bilan", "🏦 Mon crédit"]
        return base

    # ── Fallback complet pour tous les domaines ───────────────
    @staticmethod
    def _fallback_regles(db, message, langue, domaine, intention, user, id_boutique) -> dict:
        """Réponses par règles si Groq indisponible — couvre tous les domaines."""
        prenom = user.nom_complet.split()[0] if user.nom_complet else "ami"

        # ── Stock ──
        if domaine == "stock" and id_boutique:
            try:
                produits = db.query(Produit).filter(
                    Produit.id_boutique == id_boutique, Produit.actif == True
                ).all()
                if not produits:
                    return {"texte": "Aucun produit enregistré dans votre boutique.", "confiance": 0.9}
                critiques = [p for p in produits if float(p.quantite_stock) <= float(p.seuil_alerte_stock)]
                if critiques:
                    noms = ", ".join(p.nom_produit for p in critiques[:3])
                    texte = f"⚠️ {len(critiques)} produit(s) en rupture imminente : {noms}. Commandez aujourd'hui !"
                else:
                    texte = f"✅ Stock OK — {len(produits)} produits, aucune alerte critique."
                return {"texte": texte, "confiance": 0.90}
            except Exception:
                pass

        # ── Finances ──
        elif domaine == "finances" and id_boutique:
            try:
                debut_mois = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0)
                rev = db.query(func.sum(Vente.montant_total)).filter(
                    Vente.id_boutique == id_boutique,
                    Vente.statut == "validee",
                    Vente.date_vente >= debut_mois
                ).scalar() or 0
                dep = db.query(func.sum(Depense.montant)).filter(
                    Depense.id_boutique == id_boutique,
                    Depense.date_depense >= debut_mois
                ).scalar() or 0
                ben = float(rev) - float(dep)
                texte = (
                    f"💰 Ce mois : revenus {float(rev):,.0f} FCFA, dépenses {float(dep):,.0f} FCFA. "
                    f"Bénéfice net : {ben:,.0f} FCFA. "
                    f"{'📈 En bonne forme !' if ben > 0 else '⚠️ Dépenses supérieures aux revenus.'}"
                )
                return {"texte": texte, "confiance": 0.92}
            except Exception:
                pass

        # ── Crédit ──
        elif domaine == "credit":
            score = int(user.score_credit or 50)
            if score >= 70:
                texte = f"✅ Votre score crédit de {score}/100 est excellent ! Vous êtes éligible à un crédit jusqu'à 150 000 FCFA."
            elif score >= 50:
                texte = f"⭐ Score crédit {score}/100 — Crédit communautaire accessible. Remboursez vos dettes pour améliorer."
            else:
                texte = f"⚠️ Score {score}/100 — insuffisant pour l'instant. Enregistrez vos ventes régulièrement pour améliorer."
            return {"texte": texte, "confiance": 0.88}

        # ── Business / Ventes ──
        elif domaine == "business" and id_boutique:
            try:
                debut_mois = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0)
                nb_ventes = db.query(func.count(Vente.id_vente)).filter(
                    Vente.id_boutique == id_boutique,
                    Vente.statut == "validee",
                    Vente.date_vente >= debut_mois
                ).scalar() or 0
                ca = db.query(func.sum(Vente.montant_total)).filter(
                    Vente.id_boutique == id_boutique,
                    Vente.statut == "validee",
                    Vente.date_vente >= debut_mois
                ).scalar() or 0
                texte = (
                    f"📊 Ce mois : {nb_ventes} vente(s) pour un CA de {float(ca):,.0f} FCFA. "
                    f"{'📈 Bon rythme !' if nb_ventes > 10 else '💡 Pensez à fidéliser vos clients.'}"
                )
                return {"texte": texte, "confiance": 0.88}
            except Exception:
                pass

        # ── Prévision ──
        elif domaine == "prevision" and id_boutique:
            try:
                debut_semaine = datetime.utcnow() - timedelta(days=7)
                ca_semaine = db.query(func.sum(Vente.montant_total)).filter(
                    Vente.id_boutique == id_boutique,
                    Vente.statut == "validee",
                    Vente.date_vente >= debut_semaine
                ).scalar() or 0
                prevision_semaine = float(ca_semaine) * 1.1
                texte = (
                    f"📈 Basé sur vos 7 derniers jours ({float(ca_semaine):,.0f} FCFA), "
                    f"prévision semaine prochaine : ~{prevision_semaine:,.0f} FCFA. "
                    f"Assurez votre stock pour maintenir ce rythme."
                )
                return {"texte": texte, "confiance": 0.82}
            except Exception:
                pass

        # ── Tontine ──
        elif domaine == "tontine":
            texte = (
                f"🤝 {prenom}, votre tontine (njangi) est un excellent outil d'épargne collective. "
                f"Consultez l'onglet Microfinance pour voir vos cotisations et le calendrier des tours."
            )
            return {"texte": texte, "confiance": 0.83}

        # ── Microfinance ──
        elif domaine == "microfinance":
            score = int(user.score_credit or 50)
            texte = (
                f"💳 Votre score crédit actuel est {score}/100. "
                f"{'Vous êtes éligible à un microcrédit.' if score >= 50 else 'Continuez à enregistrer vos ventes pour améliorer votre score.'} "
                f"Consultez l'onglet Microfinance pour les détails."
            )
            return {"texte": texte, "confiance": 0.85}

        # ── Marché local ──
        elif domaine == "marche_local":
            mois = datetime.utcnow().month
            if mois in (6, 7, 8, 9):
                conseil = "En saison des pluies, négociez les prix des produits frais tôt le matin au marché."
            elif mois in (11, 12, 1, 2):
                conseil = "En saison sèche, stockez davantage car les prix montent avec la rareté."
            else:
                conseil = "Comparez toujours 2-3 fournisseurs avant d'acheter pour obtenir le meilleur prix."
            texte = f"🛒 {conseil} Enregistrez vos achats dans l'app pour suivre vos dépenses fournisseurs."
            return {"texte": texte, "confiance": 0.80}

        # ── Saison / Fête ──
        elif domaine == "saison_fete":
            mois = datetime.utcnow().month
            if mois in (3, 4):
                conseil = "Ramadan approche : augmentez votre stock de denrées alimentaires et boissons."
            elif mois in (6, 7):
                conseil = "Tabaski : prévoyez du stock de moutons, habits et produits alimentaires."
            elif mois == 12:
                conseil = "Fin d'année : boostez votre stock de produits cadeaux et alimentaires."
            else:
                conseil = "Anticipez les fêtes locales pour maximiser vos ventes saisonnières."
            texte = f"🎉 {conseil} Consultez vos prévisions pour planifier."
            return {"texte": texte, "confiance": 0.82}

        # ── Général (fallback final) ──
        score = int(user.score_sante_business or 50)
        texte = (
            f"Bonjour {prenom} 👋 ! Score santé business : {score}/100. "
            f"Posez-moi une question sur votre stock, vos finances, votre crédit, vos ventes ou votre tontine."
        )
        return {"texte": texte, "confiance": 0.75}

    # ── Conseil quotidien ─────────────────────────────────────
    @staticmethod
    def generer_conseil_quotidien(
        db: Session, id_boutique: int, user: Utilisateur
    ) -> str:
        try:
            hier = datetime.utcnow() - timedelta(days=1)
            rev_hier = db.query(func.sum(Vente.montant_total)).filter(
                Vente.id_boutique == id_boutique,
                Vente.statut == "validee",
                Vente.date_vente >= hier,
            ).scalar() or 0

            critiques = db.query(Produit).filter(
                Produit.id_boutique == id_boutique,
                Produit.actif == True,
                Produit.quantite_stock <= Produit.seuil_alerte_stock
            ).limit(3).all()

            prompt = (
                f"Micro-entrepreneur à Ngaoundéré, Cameroun. "
                f"Ventes hier : {float(rev_hier):,.0f} FCFA. "
                f"Score santé : {user.score_sante_business or 50}/100. "
            )
            if critiques:
                prompt += f"Stock critique : {', '.join(p.nom_produit for p in critiques[:2])}. "

            mois = datetime.utcnow().month
            if mois in (3, 4):
                prompt += "Saison sèche fin / Ramadan potentiel. "
            elif mois in (6, 7, 8, 9):
                prompt += "Saison des pluies. "
            elif mois in (11, 12):
                prompt += "Approche fin d'année / fêtes. "

            prompt += "Donne un conseil actionnable ultra-court (1-2 phrases max) pour aujourd'hui."

            msgs = [
                {"role": "system", "content": "Tu es l'assistant UbuntuTech. Sois direct, concis, pratique, encourageant."},
                {"role": "user",   "content": prompt},
            ]
            conseil = IAService._appeler_groq(msgs, max_tokens=100)
            if conseil:
                return conseil
        except Exception as e:
            logger.warning(f"Conseil quotidien Groq echoue : {e}")

        try:
            if critiques:
                noms = ", ".join(p.nom_produit for p in critiques[:2])
                return f"⚡ Commander aujourd'hui : {noms} — stock critique. Ne laissez pas vos clients repartir sans rien !"
            if float(rev_hier) > 0:
                return f"✅ Vous avez réalisé {float(rev_hier):,.0f} FCFA hier. Continuez sur cette lancée !"
            return "💡 Enregistrez vos ventes d'aujourd'hui pour améliorer votre score santé business."
        except Exception:
            return "💡 Bonne journée ! N'oubliez pas d'enregistrer toutes vos ventes."

    # ── Météo commerciale ─────────────────────────────────────
    @staticmethod
    def calculer_meteo_commerciale(
        db: Session, id_boutique: int
    ) -> Dict:
        now = datetime.utcnow()
        hier = now - timedelta(days=1)
        avant_hier = now - timedelta(days=2)

        try:
            rev_hier = float(db.query(func.sum(Vente.montant_total)).filter(
                Vente.id_boutique == id_boutique,
                Vente.statut == "validee",
                Vente.date_vente >= hier,
            ).scalar() or 0)

            rev_avant_hier = float(db.query(func.sum(Vente.montant_total)).filter(
                Vente.id_boutique == id_boutique,
                Vente.statut == "validee",
                Vente.date_vente >= avant_hier,
                Vente.date_vente < hier,
            ).scalar() or 0)

            variation = 0.0
            if rev_avant_hier > 0:
                variation = ((rev_hier - rev_avant_hier) / rev_avant_hier) * 100

            if rev_hier > rev_avant_hier * 1.1:
                statut, tendance = "bon", "hausse"
            elif rev_hier < rev_avant_hier * 0.9:
                statut, tendance = "difficile", "baisse"
            else:
                statut, tendance = "moyen", "stable"

            return {
                "statut":       statut,
                "tendance":     tendance,
                "variation_pct": round(variation, 1),
                "ventes_hier":  rev_hier,
            }
        except Exception:
            return {"statut": "moyen", "tendance": "stable", "variation_pct": 0, "ventes_hier": 0}
