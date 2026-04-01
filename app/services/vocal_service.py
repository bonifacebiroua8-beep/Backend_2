# app/services/vocal_service.py — UbuntuTech v3.0
import os, tempfile, re
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from loguru import logger

from app.models.transcription import TranscriptionVocale
from app.models.utilisateur import Utilisateur
from app.models.produit import Produit
from app.schemas import TranscriptionOut
from app.core.config import settings
from app.services.ia_service import IAService


ACTIONS_FR = {
    "vente":    ["vendu","vente","vendu","j'ai vendu","on a vendu","soodani","sayar","vaz"],
    "stock":    ["reçu","réceptionné","arrivée","stock","approvisionnement","heɓaani"],
    "depense":  ["payé","dépense","achat","loyer","transport","gay","biya"],
    "client":   ["crédit","à crédit","à payer","doit","defte","bashi","gʷalak"],
    "question": ["combien","comment","quel","bilan","résumé","conseil","aide","help"],
}

ENTITES_PATTERN = {
    "montant": r'(\d[\d\s]*(?:\d{3}|000)?\s*(?:francs?|fcfa|f|cfa)?)',
    "quantite": r'(\d+(?:[.,]\d+)?\s*(?:kg|kilo|litre|l|sac|pièce|unite|carton|sachet)?)',
}


class VocalService:

    @staticmethod
    async def transcrire_et_analyser(db: Session, user: Utilisateur, id_boutique: int,
                                      audio_bytes: bytes, langue: str, filename: str) -> TranscriptionOut:
        # Sauvegarder le fichier audio temporairement
        ext = filename.rsplit(".", 1)[-1] if "." in filename else "wav"
        with tempfile.NamedTemporaryFile(suffix=f".{ext}", delete=False) as f:
            f.write(audio_bytes)
            tmp_path = f.name

        texte = None
        confiance = None
        try:
            texte, confiance = VocalService._transcrire_whisper(tmp_path, langue)
        except Exception as e:
            logger.warning(f"Whisper échoué: {e} — utilisation fallback")
            texte = ""
        finally:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass

        action, entites = VocalService._analyser_intention(texte or "", langue)
        message_confirmation = VocalService._generer_confirmation(texte or "", action, entites, langue)

        transcription = TranscriptionVocale(
            id_utilisateur=user.id_utilisateur,
            id_boutique=id_boutique,
            langue_detectee=langue,
            langue_demandee=langue,
            texte_transcrit=texte,
            confiance_whisper=confiance,
            entites_extraites=entites,
            action_detectee=action,
            taille_octets=len(audio_bytes),
            traitee=False, action_executee=False
        )
        db.add(transcription)

        # Compteur freemium
        from sqlalchemy import text
        db.execute(text("UPDATE utilisateurs SET nb_vocal_mois = nb_vocal_mois + 1 WHERE id_utilisateur = :uid"),
                   {"uid": user.id_utilisateur})
        db.commit()
        db.refresh(transcription)

        return TranscriptionOut(
            id_transcription=transcription.id_transcription,
            texte_transcrit=texte,
            langue_detectee=langue,
            confiance_whisper=float(confiance) if confiance else None,
            action_detectee=action,
            entites_extraites=entites,
            message_confirmation=message_confirmation
        )

    @staticmethod
    def _transcrire_whisper(audio_path: str, langue: str) -> tuple:
        try:
            from faster_whisper import WhisperModel
            model = WhisperModel(settings.WHISPER_MODEL, device="cpu", compute_type="int8")
            lang_map = {"fr": "fr", "ff": "fr", "ha": "fr", "mfa": "fr"}
            segments, info = model.transcribe(audio_path, language=lang_map.get(langue, "fr"), beam_size=5)
            texte = " ".join([s.text for s in segments]).strip()
            confiance = round(getattr(info, "language_probability", 0.8), 3)
            return texte, confiance
        except ImportError:
            logger.warning("faster-whisper non disponible")
            return "", 0.5
        except Exception as e:
            logger.error(f"Erreur Whisper: {e}")
            return "", 0.3

    @staticmethod
    def _analyser_intention(texte: str, langue: str) -> tuple:
        texte_lower = texte.lower()
        action = "inconnu"
        for act, mots in ACTIONS_FR.items():
            if any(m in texte_lower for m in mots):
                action = act
                break
        if action == "question":
            action = "question_ia"

        entites = {}
        for nom, pattern in ENTITES_PATTERN.items():
            match = re.search(pattern, texte_lower)
            if match:
                val = re.sub(r'[^\d.,]', '', match.group(1).replace(" ", ""))
                try:
                    entites[nom] = float(val.replace(",", "."))
                except Exception:
                    pass

        # Extraire produit (mots entre action et montant)
        mots = texte_lower.split()
        for i, mot in enumerate(mots):
            if mot in ["riz","sucre","huile","sel","farine","savon","mil","maïs",
                       "muuzel","gawri","shinkafa","mewre","malum"]:
                entites["produit"] = mot
                break

        return action, entites

    @staticmethod
    def _generer_confirmation(texte: str, action: str, entites: dict, langue: str) -> str:
        montant = entites.get("montant", "")
        produit = entites.get("produit", "")
        qte = entites.get("quantite", "")
        msgs = {
            "vente": f"Vente enregistrée{' : ' + produit if produit else ''}{' — ' + str(qte) if qte else ''}{' — ' + str(int(montant)) + ' FCFA' if montant else ''} ✅",
            "stock": f"Entrée stock enregistrée{' : ' + produit if produit else ''} ✅",
            "depense": f"Dépense enregistrée{' : ' + str(int(montant)) + ' FCFA' if montant else ''} ✅",
            "client": f"Crédit client noté{' : ' + str(int(montant)) + ' FCFA' if montant else ''} ✅",
            "question_ia": "Question transmise à l'IA... 🤖",
            "inconnu": "Commande non reconnue — veuillez réessayer 🎙️"
        }
        return msgs.get(action, "Commande reçue ✅")

    @staticmethod
    def executer_action(db: Session, user: Utilisateur, transcription: TranscriptionVocale) -> dict:
        action = transcription.action_detectee
        entites = transcription.entites_extraites or {}

        if action == "question_ia":
            reponse = IAService.dialoguer(
                db=db, message=transcription.texte_transcrit or "",
                langue=transcription.langue_detectee,
                source="vocal", user=user,
                id_boutique=transcription.id_boutique
            )
            transcription.action_executee = True
            transcription.traitee = True
            db.commit()
            return {"action": "question_ia", "reponse_ia": reponse["reponse"]}

        transcription.action_executee = True
        transcription.traitee = True
        db.commit()
        return {"action": action, "entites": entites, "message": "Action enregistrée"}
