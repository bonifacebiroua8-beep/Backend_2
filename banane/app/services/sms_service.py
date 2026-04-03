# app/services/sms_service.py
# ============================================================
#  UBUNTUTECH — Service SMS Twilio v2.0
# ============================================================
from typing import Optional
from loguru import logger
from app.core.config import settings


class SMSService:

    @staticmethod
    def _get_client():
        if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN:
            raise RuntimeError("Twilio non configuré (TWILIO_ACCOUNT_SID / TWILIO_AUTH_TOKEN manquants)")
        from twilio.rest import Client
        return Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

    @staticmethod
    def envoyer(telephone: str, message: str) -> dict:
        """
        Envoie un SMS via Twilio.
        Retourne {"succes": bool, "sid": str|None, "erreur": str|None}
        """
        try:
            client = SMSService._get_client()
            msg = client.messages.create(
                body=message[:1600],
                from_=settings.TWILIO_PHONE_NUMBER,
                to=telephone,
            )
            logger.info(f"SMS envoyé : {telephone} — SID {msg.sid}")
            return {"succes": True, "sid": msg.sid, "erreur": None}
        except Exception as e:
            erreur = str(e)[:255]
            logger.error(f"SMS échec vers {telephone} : {erreur}")
            return {"succes": False, "sid": None, "erreur": erreur}

    @staticmethod
    def relance_credit(nom_client: str, montant: float, telephone: str) -> dict:
        message = (
            f"Bonjour {nom_client}, rappel amical : vous avez un crédit de "
            f"{montant:,.0f} FCFA à régulariser. Merci de passer. — UbuntuTech"
        )
        return SMSService.envoyer(telephone, message)

    @staticmethod
    def relance_echeance(nom_client: str, montant: float, date_echeance: str, telephone: str) -> dict:
        message = (
            f"Bonjour {nom_client}, votre prochaine échéance de "
            f"{montant:,.0f} FCFA est prévue le {date_echeance}. "
            f"Préparez le montant à l'avance. — UbuntuTech Microfinance"
        )
        return SMSService.envoyer(telephone, message)

    @staticmethod
    def relance_tontine(nom_membre: str, montant: float, cycle: int, telephone: str) -> dict:
        message = (
            f"Bonjour {nom_membre}, rappel : cotisation tontine cycle {cycle} "
            f"de {montant:,.0f} FCFA à régler. Restez solidaires ! — UbuntuTech"
        )
        return SMSService.envoyer(telephone, message)
