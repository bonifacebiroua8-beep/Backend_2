# app/services/vente_service.py — UbuntuTech v3.0
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from loguru import logger

from app.models.vente import Vente, LigneVente
from app.models.produit import Produit
from app.models.client import Client
from app.models.stock import MouvementStock
from app.models.transaction import TransactionFinanciere
from app.models.utilisateur import Utilisateur
from app.core.config import settings


class VenteService:

    @staticmethod
    def creer_vente(db: Session, user: Utilisateur, data) -> Vente:
        # Vérifier limite freemium
        if user.type_abonnement == "gratuit":
            if int(user.nb_ventes_mois or 0) >= settings.FREE_MAX_VENTES_MOIS:
                raise ValueError(f"Limite de {settings.FREE_MAX_VENTES_MOIS} ventes/mois atteinte. Passez au plan Pro.")

        montant_total = 0.0
        lignes_data = []

        for ligne in data.lignes:
            produit = db.query(Produit).filter(
                Produit.id_produit == ligne.id_produit,
                Produit.id_boutique == data.id_boutique,
                Produit.actif == True
            ).first()
            if not produit:
                raise ValueError(f"Produit {ligne.id_produit} introuvable ou inactif")
            if float(produit.quantite_stock) < float(ligne.quantite):
                raise ValueError(f"Stock insuffisant pour '{produit.nom_produit}' (dispo: {produit.quantite_stock})")

            prix = float(ligne.prix_unitaire) if ligne.prix_unitaire else float(produit.prix_vente)
            remise = float(ligne.remise_pct) / 100
            montant_ligne = round(prix * float(ligne.quantite) * (1 - remise), 2)
            marge = round((prix - float(produit.prix_achat)) * float(ligne.quantite), 2)
            montant_total += montant_ligne
            lignes_data.append({
                "produit": produit, "quantite": float(ligne.quantite),
                "prix": prix, "remise": ligne.remise_pct,
                "montant": montant_ligne, "marge": marge
            })

        montant_paye = float(data.montant_paye) if data.montant_paye is not None else montant_total
        montant_credit = max(0.0, montant_total - montant_paye)

        # Vérifier limite crédit client
        if montant_credit > 0 and data.id_client:
            client = db.query(Client).filter(Client.id_client == data.id_client).first()
            if client:
                nouveau_credit = float(client.solde_credit) + montant_credit
                if nouveau_credit > float(client.limite_credit):
                    raise ValueError(f"Limite de crédit dépassée pour ce client ({client.limite_credit} FCFA)")

        vente = Vente(
            id_boutique=data.id_boutique, id_client=data.id_client,
            montant_total=montant_total, montant_paye=montant_paye,
            montant_credit=montant_credit, mode_paiement=data.mode_paiement,
            source_saisie=data.source_saisie, langue_saisie=data.langue_saisie,
            statut="validee", note=data.note
        )
        db.add(vente)
        db.flush()

        for ld in lignes_data:
            p = ld["produit"]
            ligne = LigneVente(
                id_vente=vente.id_vente, id_produit=p.id_produit,
                nom_produit_snap=p.nom_produit, quantite=ld["quantite"],
                unite=p.unite, prix_unitaire=ld["prix"],
                prix_achat_snapshot=float(p.prix_achat),
                remise_pct=ld["remise"], montant_ligne=ld["montant"],
                marge_ligne=ld["marge"]
            )
            db.add(ligne)
            # Mise à jour stock
            avant = float(p.quantite_stock)
            p.quantite_stock = avant - ld["quantite"]
            p.nb_ventes = int(p.nb_ventes or 0) + 1
            p.total_vendu = float(p.total_vendu or 0) + ld["quantite"]
            p.derniere_vente = datetime.utcnow()
            # Mouvement stock
            db.add(MouvementStock(
                id_produit=p.id_produit, id_boutique=data.id_boutique,
                type_mouvement="sortie", quantite=ld["quantite"],
                quantite_avant=avant, quantite_apres=float(p.quantite_stock),
                motif="vente", id_vente=vente.id_vente,
                source=data.source_saisie
            ))

        # Mettre à jour client si crédit
        if montant_credit > 0 and data.id_client:
            client = db.query(Client).filter(Client.id_client == data.id_client).first()
            if client:
                client.solde_credit = float(client.solde_credit) + montant_credit
                client.nb_achats = int(client.nb_achats or 0) + 1
                client.total_achats = float(client.total_achats or 0) + montant_total
                client.derniere_visite = datetime.utcnow()

        # Transaction financière
        db.add(TransactionFinanciere(
            id_utilisateur=user.id_utilisateur, id_boutique=data.id_boutique,
            id_vente=vente.id_vente, type_transaction="vente",
            montant=montant_total, sens="entree",
            libelle=f"Vente #{vente.id_vente} — {len(lignes_data)} article(s)"
        ))

        # Compteur freemium
        db.flush()
        from sqlalchemy import text
        db.execute(text("UPDATE utilisateurs SET nb_ventes_mois = nb_ventes_mois + 1 WHERE id_utilisateur = :uid"),
                   {"uid": user.id_utilisateur})
        user.nb_ventes_mois = int(user.nb_ventes_mois or 0) + 1

        db.commit()
        db.refresh(vente)
        logger.info(f"Vente #{vente.id_vente} — boutique {data.id_boutique} — {montant_total} FCFA")
        return vente
