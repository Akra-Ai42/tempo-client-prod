# Tempo upgrade UX : récap et déploiement

## Les 7 fichiers modifiés / créés

| Fichier | Type | Ce que ça fait |
|---|---|---|
| `app/ml/shap_metier.py` | NOUVEAU | Mapping feature → phrase française banque (traduction déterministe, pas de LLM) |
| `app/core/schemas.py` | MODIF (ajout fin) | 2 nouveaux schemas Pydantic : `FacteurMetier` et `ExplainMetierResponse` |
| `app/core/routes.py` | MODIF (ajout import + nouvel endpoint) | Nouvel endpoint `POST /explain-metier/{client_id}` |
| `static/conseiller/app.js` | MODIF (fonction `loadAndRenderSHAP`) | Appelle `/explain-metier` et affiche les facteurs en langage métier |
| `static/direction/app.js` | REMPLACE (réorganisation complète) | Dashboard narratif 3 sections : Contexte / Signaux / Synthèse |
| `static/direction/index.html` | REMPLACE (nouveaux styles inline) | Styles pour les 3 nouvelles sections |
| `static/shared/style.css` | MODIF (ajout fin) | Classes `.facteurs-metier-list`, `.facteur-metier`, etc. |

**Rien d'autre n'a été touché** : auth, middlewares, DB, migrations, Dockerfile, les 3 incidents injectés, login, modèles ML.

## Comment déployer

### 1. Décompresse le zip à la racine de ton repo

```powershell
cd C:\Users\akram\Desktop\tempo-client-prod
# Decompresse tempo-upgrade.zip ici, il va ecraser les fichiers existants
# et ajouter app/ml/shap_metier.py
```

### 2. Vérifie les 7 fichiers modifiés

```powershell
git status
```

Tu dois voir exactement les 7 fichiers listés plus haut en modifié/nouveau, rien d'autre.

### 3. Teste en local avant de push

```powershell
.\venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000
```

Puis :
- Ouvre `http://localhost:8000/static/shared/login.html`
- Connecte-toi en `conseiller_lille` (ou autre conseiller)
- Sélectionne un client
- Vérifie que la section SHAP s'affiche en phrases françaises ("Son ancienneté de X ans augmente son risque de départ de +Y points")
- Déconnecte-toi, reconnecte-toi en `direction`
- Vérifie les 3 sections : Contexte en haut, Signaux au milieu, Synthèse en bas

### 4. Commit et push

```powershell
git add .
git commit -m "upgrade UX conseiller (SHAP metier) + direction (narration 3 sections)"
git push origin main
```

Render va redéployer automatiquement en 2-3 minutes.

## Détails techniques

### SHAP métier

Le nouveau endpoint `POST /explain-metier/{client_id}` retourne :

```json
{
  "client_id": 847,
  "churn_risk_pct": 74,
  "urgence": "high",
  "facteurs": [
    {
      "sens": "positif",
      "phrase": "Son ancienneté de 1 ans augmente son risque de départ de +18 points.",
      "justification": "Les clients récents partent 3 fois plus souvent dans l année, les clients fidèles restent.",
      "poids": 18,
      "feature": "anciennete_mois"
    },
    ...
  ]
}
```

Convention :
- `sens: "positif"` → la feature augmente le risque de churn (affiché en rouge/bordeaux côté UI)
- `sens: "negatif"` → la feature réduit le risque (affiché en vert sauge)

### Features traduites

Les 7 features connues sont traduites :
- `anciennete_mois` (converti en années)
- `produits_detenus`
- `nb_interactions_90j`
- `derniere_interaction_jours`
- `solde_moyen` (converti en euros)
- `age_client`
- `canal_prefere`

Si une feature n'est pas dans le mapping, elle est **skippée** (pas de jargon affiché). Si tu as de nouvelles features, ajoute-les dans `app/ml/shap_metier.py` dans le dict `GABARITS`.

### Direction : narration haut vers bas

**Section 1 — Ce qui se passe aujourd'hui** (en haut)
2 cartes pleine largeur avec mini-histogrammes CSS + narrative générée côté client (règles simples sur les deltas) :
- Clients haute urgence (histogramme bleu marine)
- Coût LLM mois courant (histogramme bordeaux)

**Section 2 — Signaux techniques** (milieu)
- Grid 2x1 : Latence moyenne LLM + Hit rate cache (couleur selon seuils)
- Carte pleine largeur : Dérive Evidently avec pills features

**Section 3 — Top 10 clients à risque** (préservée)

**Section 4 — Synthèse chiffrée** (en bas, KPI cards)
- Portefeuille total
- Clients haute urgence (en rouge)
- Coût LLM 24h (en rouge si > moyenne journalière × 2)
- Taux churn prédit (en marron doré)

## Garanties respectées

- Pas de tirets cadratins dans l'UI utilisateur
- Pas d'emojis dans l'UI
- Police Inter stricte
- Aucune nouvelle dépendance Python (utilise seulement ce qui est déjà installé)
- Aucune nouvelle dépendance frontend (pas de chart.js, pas de react, pas de tailwind)
- Aucune modification des 3 incidents injectés
- Aucune modification de l'auth, middlewares, DB, migrations
- Palette CSS existante respectée (`--ink`, `--paper`, `--accent`, `--highlight`, `--success`, `--danger`)

## Rollback si problème

Si quelque chose ne va pas en prod, rollback en 1 commande :

```powershell
git revert HEAD
git push origin main
```

Render redéploie la version précédente automatiquement.
