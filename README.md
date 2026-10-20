# Tempo Client — Prod

Outil décisionnel pour conseillers bancaires : scoring churn, explications SHAP, recommandations de rétention.

Système en production, documenté, instrumenté. Trois incidents volontaires sont injectés dans ce repo pour l'exercice pédagogique Devoteam MSc1.

## Pile technique

- **Backend** : FastAPI, Python 3.11
- **ML** : XGBoost (churn), scikit-learn (reco), SHAP
- **LLM** : interface `LLMProvider` abstraite, adapter OpenRouter par défaut
- **Base de données** : SQLite
- **Front** : HTML / CSS / JS statique, servi par FastAPI
- **Scheduler** : APScheduler
- **Monitoring** : Evidently (dérive), logs structurés, tracking coûts LLM
- **Déploiement** : Docker, Render

## Démarrage rapide

```bash
# 1. Cloner et installer
git clone <repo>
cd tempo-client-prod
cp .env.example .env
# Éditer .env avec vos clés OpenRouter

# 2. Générer les données et entraîner les modèles
python scripts/generate_fake_data.py
python scripts/init_db.py
python scripts/train_models.py

# 3. Lancer l'API
uvicorn app.main:app --reload --port 8000

# 4. Ouvrir le navigateur
# → http://localhost:8000/conseiller.html (user : conseiller_lille / demo123)
# → http://localhost:8000/direction.html  (user : direction / demo123)
```

## Structure du projet

```
tempo-client-prod/
├── app/
│   ├── main.py              # Point d'entrée FastAPI
│   ├── config.py            # Configuration centralisée
│   ├── core/                # Logique métier, endpoints
│   ├── ml/                  # Modèles, SHAP, inférence
│   ├── llm/                 # Interface LLMProvider + adapters
│   ├── data/                # Accès SQLite, repositories
│   ├── auth/                # Session cookie, RBAC middleware
│   ├── scheduler/           # Tâches planifiées (alertes)
│   └── monitoring/          # Dérive, coûts, dashboards
├── static/
│   ├── conseiller/          # Interface conseiller
│   ├── direction/           # Interface direction
│   └── shared/              # CSS, JS communs
├── models/                  # Modèles ML sérialisés (.pkl)
├── data/                    # Datasets, SQLite db
├── scripts/                 # Scripts d'init et de maintenance
├── tests/                   # Tests
└── docs/                    # Documentation technique
```

## Utilisateurs de la démo

| Login                   | Rôle       | Région     |
|-------------------------|------------|------------|
| conseiller_lille        | conseiller | Lille      |
| conseiller_marseille    | conseiller | Marseille  |
| direction               | direction  | (toutes)   |

Mot de passe : `demo123` pour tous (démo uniquement — à ne jamais utiliser en prod réelle).

## Déploiement

Push vers la branche `main`, Render détecte le Dockerfile et déploie automatiquement.

Variables d'environnement à configurer sur Render :
- `OPENROUTER_API_KEY`
- `OPENROUTER_MODEL`
- `SESSION_SECRET`
- Voir `.env.example` pour la liste complète.

## Licence

Propriétaire — La Plateforme_ / Usine IA.
