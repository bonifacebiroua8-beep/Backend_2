# UbuntuTech Backend v3.0

**Assistant IA Multilingue pour Micro-Entrepreneurs du Grand Nord Cameroun**
*Français · Fulfulde · Haoussa · Mafa*

---

## Stack Technique

| Composant | Tech |
|-----------|------|
| Framework | FastAPI 0.111 + Uvicorn |
| Base de données | MySQL 8.0 — 52 tables + 8 vues |
| IA / LLM | Groq API — Llama 3.3 70B |
| Vocal | faster-whisper (modèle tiny) |
| Sécurité | JWT + bcrypt + SlowAPI |
| Tâches | APScheduler (Africa/Douala) |
| Export | ReportLab PDF + OpenPyXL Excel |
| Hébergement | Railway |

---

## Démarrage rapide

```bash
# 1. Configurer l'environnement
cp .env.example .env
# Éditer .env avec vos vraies valeurs

# 2. Créer la base de données
mysql -h HOST -P PORT -u root -p < UbuntuTech_BD_COMPLETE_v3.sql

# 3. Lancer en développement
uvicorn main:app --reload --port 8000

# 4. Lancer en production
uvicorn main:app --host 0.0.0.0 --port $PORT --workers 2
```

---

## Routes API v3.0

### Authentification
| Route | Description |
|-------|-------------|
| `POST /api/v1/auth/register` | Inscription |
| `POST /api/v1/auth/login` | Connexion |
| `POST /api/v1/auth/logout` | Déconnexion |
| `POST /api/v1/auth/change-pin` | Changer PIN |
| `GET  /api/v1/auth/me` | Mon profil |

### Boutiques
| Route | Description |
|-------|-------------|
| `POST /api/v1/boutiques` | Créer boutique |
| `GET  /api/v1/boutiques` | Mes boutiques |
| `GET  /api/v1/boutiques/{id}/dashboard` | Dashboard complet |
| `PUT  /api/v1/boutiques/{id}` | Modifier |
| `DELETE /api/v1/boutiques/{id}` | Archiver |

### Produits & Stock
| Route | Description |
|-------|-------------|
| `POST /api/v1/produits` | Créer produit |
| `GET  /api/v1/produits/{id_boutique}` | Liste + search |
| `PUT  /api/v1/produits/{id}` | Modifier |
| `POST /api/v1/produits/{id}/stock/ajuster` | Ajuster stock |
| `GET  /api/v1/produits/{id_boutique}/alertes` | Alertes rupture |

### Ventes
| Route | Description |
|-------|-------------|
| `POST /api/v1/ventes` | Créer vente |
| `GET  /api/v1/ventes/{id_boutique}` | Liste ventes |
| `GET  /api/v1/ventes/detail/{id}` | Détail + lignes |
| `POST /api/v1/ventes/{id}/annuler` | Annuler |

### Clients
| Route | Description |
|-------|-------------|
| `POST /api/v1/clients` | Créer client |
| `GET  /api/v1/clients/{id_boutique}` | Liste clients |
| `POST /api/v1/clients/{id}/rembourser` | Rembourser crédit |

### Finances
| Route | Description |
|-------|-------------|
| `GET  /api/v1/finances/bilan/{id_boutique}` | Bilan période |
| `POST /api/v1/finances/depenses` | Enregistrer dépense |
| `POST /api/v1/finances/export-bilan/{id_boutique}` | Export PDF |

### Vocal
| Route | Description |
|-------|-------------|
| `POST /api/v1/vocal/transcrire` | Transcription Whisper |
| `POST /api/v1/vocal/{id}/confirmer` | Exécuter action |
| `GET  /api/v1/vocal/historique` | 10 dernières |

### IA Conseils
| Route | Description |
|-------|-------------|
| `POST /api/v1/ia/dialogue` | Dialogue Groq |
| `GET  /api/v1/ia/conseil-jour/{id_boutique}` | Conseil quotidien |
| `POST /api/v1/ia/dialogue/{id}/feedback` | Feedback |
| `GET  /api/v1/ia/historique` | Historique dialogues |

### Microfinance
| Route | Description |
|-------|-------------|
| `GET  /api/v1/microfinance/wallet` | Mon wallet |
| `POST /api/v1/microfinance/wallet/recharger` | Recharger (MoMo) |
| `POST /api/v1/microfinance/wallet/virer` | Virer à un utilisateur |
| `GET  /api/v1/microfinance/epargnes` | Mes épargnes |
| `POST /api/v1/microfinance/epargnes` | Créer objectif |
| `POST /api/v1/microfinance/epargnes/{id}/verser` | Verser |
| `GET  /api/v1/microfinance/banques` | Banques partenaires |
| `POST /api/v1/microfinance/credits/simuler` | Simuler crédit |
| `POST /api/v1/microfinance/credits/demander` | Demander crédit |
| `GET  /api/v1/microfinance/credits` | Mes crédits |
| `GET  /api/v1/microfinance/credits/{id}/echeancier` | Échéancier |
| `POST /api/v1/microfinance/credits/echeances/{id}/rembourser` | Rembourser |
| `POST /api/v1/microfinance/credits/{id}/garanties` | Ajouter garantie |
| `POST /api/v1/microfinance/tontines` | Créer tontine |
| `GET  /api/v1/microfinance/tontines` | Mes tontines |
| `POST /api/v1/microfinance/tontines/rejoindre` | Rejoindre |
| `GET  /api/v1/microfinance/tontines/{id}` | Détail tontine |
| `POST /api/v1/microfinance/tontines/{id}/cotiser` | Payer cotisation |
| `POST /api/v1/microfinance/tontines/{id}/litiges` | Signaler litige |

### Administration
| Route | Description |
|-------|-------------|
| `GET  /api/v1/admin/stats` | Statistiques globales |
| `GET  /api/v1/admin/dashboard` | Dashboard admin |
| `GET  /api/v1/admin/vocabulaire` | Vocabulaire IA |
| `POST /api/v1/admin/vocabulaire` | Ajouter mot |
| `PUT  /api/v1/admin/vocabulaire/{id}/valider` | Valider mot |
| `GET  /api/v1/admin/transcriptions/a-corriger` | À corriger |
| `POST /api/v1/admin/transcriptions/{id}/corriger` | Corriger |
| `GET  /api/v1/admin/connaissance-locale` | Connaissances |
| `POST /api/v1/admin/connaissance-locale` | Ajouter |
| `GET  /api/v1/admin/utilisateurs` | Liste utilisateurs |
| `PUT  /api/v1/admin/utilisateurs/{id}/abonnement` | Changer plan |
| `GET  /api/v1/admin/credits/en-attente` | Crédits à valider |
| `POST /api/v1/admin/credits/{id}/decider` | Approuver/Refuser |
| `GET  /api/v1/admin/metriques` | Métriques système |

### Sync & Utilisateurs
| Route | Description |
|-------|-------------|
| `POST /api/v1/sync/batch` | Sync offline |
| `GET  /api/v1/sync/status` | Statut sync |
| `GET  /api/v1/utilisateurs/moi` | Mon profil |
| `PUT  /api/v1/utilisateurs/moi` | Modifier profil |
| `GET  /api/v1/utilisateurs/moi/parametres` | Mes paramètres |
| `PUT  /api/v1/utilisateurs/moi/parametres` | Modifier paramètres |
| `GET  /api/v1/utilisateurs/moi/notifications` | Notifications |

---

## Tâches planifiées (Africa/Douala)

| Heure | Tâche |
|-------|-------|
| 00h30 | Marquer échéances en retard |
| 02h00 | Recalcul scores crédit + santé |
| 03h00 | Suppression exports > 7j |
| 08h00 | Rappels SMS J-7/J-3/J-1 crédits |
| 23h50 | Métriques quotidiennes |
| Chaque heure | Nettoyage sessions JWT |
| 1er du mois 00h05 | Reset compteurs freemium |

---

## Améliorations v3.0 vs v2.0

### Nouvelles tables
- `virements_wallet` — Transferts entre utilisateurs avec audit trail
- `cycles_tontine` — Historique complet des cycles
- `garanties_credit` — Garanties associées aux crédits
- `litiges_tontine` — Gestion des conflits tontiniers
- `score_fiabilite_tontine` — Score de réputation tontinière
- `otp_codes` — Codes OTP pour validations sensibles
- `recharges_wallet` — Historique recharges Mobile Money
- `providers_ia` — Gestion flexible des providers IA
- `meteo_commerciale` — Météo commerciale journalière
- `ab_tests_ia` — Tests A/B versions IA

### Corrections modèles
- `wallets` : ajout `plafond_journalier`, `nb_transactions_jour`
- `micro_credits` : ajout `motif_demande`, `approuve_par`, `nb_relances_envoyees`
- `epargnes` : ajout `categorie_objectif`, `prochaine_date_versement`
- `tontines` : ajout `mode_attribution`, `langue_tontine`, `nb_cycles_total`
- `membres_tontine` : ajout `nb_retards`

### Score ML crédit amélioré
- 5 critères : comportement financier + remboursements + engagement vocal + profil tontine + ancienneté
- Seuils améliorés : 45/65/80 (vs 50/70 avant)
- Montants max : 100k/300k/1M FCFA

---

*Porteur : Biroua Wandeya Boniface — M1 IA Appliquée, Université de Ngaoundéré*
*"Je réussis parce que nous réussissons" 🌍*
