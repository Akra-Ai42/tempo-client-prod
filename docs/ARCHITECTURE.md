# Architecture technique — Tempo Client V2

## Vue d'ensemble

Tempo Client est une application FastAPI mono-service qui expose une API
REST et sert deux fronts HTML statiques (conseiller + direction) depuis
le même conteneur.

## Pile technique

| Couche | Techno |
|--------|--------|
| Backend | FastAPI 0.115 (Python 3.11) |
| Serveur | Uvicorn |
| Base de données | SQLite via SQLAlchemy 2.0 |
| ML | XGBoost (churn), scikit-learn (reco), SHAP (explication) |
| LLM | Interface `LLMProvider` abstraite, adapter OpenRouter par défaut |
| Scheduler | APScheduler (background) |
| Monitoring | Evidently (dérive données), log JSONL (coûts LLM) |
| Front | HTML / CSS / JS statique, servi par FastAPI |
| Auth | Session cookie signé via `SessionMiddleware` de Starlette |
| Déploiement | Docker, Render |

## Flux conseiller

1. Le conseiller se connecte sur `/static/shared/login.html`.
2. `POST /auth/login` vérifie les identifiants et pose un cookie de session.
3. Redirection vers `/static/conseiller/index.html`.
4. Le front appelle `GET /clients/mine` → liste filtrée par région.
5. Au clic sur un client :
   - `POST /score/{id}` → score churn + top 5 features SHAP.
   - `POST /explain/{id}` → explication LLM naturalisée.
   - `POST /recommend/{id}` → recommandations d'actions.

## Flux direction

1. Login identique.
2. Redirection vers `/static/direction/index.html`.
3. `GET /dashboard/direction` → KPI agrégés (nb clients, risque, coût LLM,
   dérive détectée).

## Interface LLMProvider

Le choix fort architectural de ce projet est l'abstraction `LLMProvider`
(`app/llm/base.py`). Tout appel LLM depuis le code métier passe par
cette interface. Deux implémentations :

- `OpenRouterProvider` : utilisée pour la démo. Agrège ~200 modèles via
  une API unique.
- `HouseSLMProvider` : stub pour le futur SLM maison hébergé sur le
  cluster GPU La Plateforme_.

Changer de provider = modifier une ligne dans la factory `get_llm_provider()`
et une variable d'environnement. Zéro refactor dans le code métier.

## RBAC

Le `RBACMiddleware` (`app/auth/rbac.py`) intercepte chaque requête :

- Routes publiques (health, login, statiques) → passent.
- Routes authentifiées → vérifient la session.
- Routes direction → vérifient le rôle.
- Filtrage par région sur `/clients/mine` → via `filter_clients_by_region()`.

## Scheduler

Trois tâches tournent en arrière-plan :

- `alert_risk_shift` (toutes les heures) : détecte les bascules en risque haut.
- `check_drift` (quotidien) : lance Evidently sur les features récentes.
- `check_llm_cost` (toutes les heures) : agrège les coûts du log.

## Déploiement

Push `main` → Render détecte le Dockerfile → build → déploiement auto.
La variable `$PORT` est fournie par Render et interprétée au runtime
via `sh -c` dans le CMD du Dockerfile.
