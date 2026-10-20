# Playbook démo — Tempo Client V2

Script de la démonstration à Sloan Charrier (Devoteam) prévue dans 4 semaines.

Durée cible : **15 à 20 minutes**.

---

## Objectif de la démo

Montrer que :

1. Le format "incident response" est pédagogiquement crédible et
   techniquement reproductible.
2. Le socle technique capitalisé sur Khayav tient en production.
3. L'interface `LLMProvider` abstraite ouvre la voie à la souveraineté
   (SLM maison sur cluster GPU).

---

## Plan de la démo

### 0 — Contexte (1 min)

> "Tempo Client est un outil décisionnel pour conseillers bancaires.
> Scoring churn, explications SHAP naturalisées via LLM, recommandations.
> Il tourne en production. Trois incidents sont injectés pour l'exercice.
> Les étudiants Devoteam vont les diagnostiquer et les corriger en 10 jours."

### 1 — Tour du système en production (3 min)

- Login `conseiller_lille` → interface conseiller.
- Liste des clients, clic sur un client → score + SHAP + explication LLM
  + recommandations.
- Login `direction` → dashboard KPI.
- Montrer : "le système fonctionne, mais trois voyants rouges — on va voir
  ce qu'ils cachent."

### 2 — Incident 1 : facture LLM (4 min)

- Montrer le mail DAF (`docs/mail_DAF.txt`).
- Ouvrir le dashboard direction → coût 847 $ en rouge.
- Expliquer les 3 bugs combinés : cache cassé + prompt gonflé + max_tokens.
- Montrer comment un étudiant diagnostique : log JSONL → tokens par appel
  → racine du problème.

### 3 — Incident 2 : dérive silencieuse (4 min)

- Montrer le rapport Evidently (`data/evidently_reports/...html`).
- Deux features en rouge : `nb_interactions_90j`, `solde_moyen`.
- Expliquer : modèle entraîné sur baseline, inférence sur current.
- Montrer la boucle de ré-entraînement attendue.

### 4 — Incident 3 : faille RBAC (3 min)

- Montrer le mail DPO (`docs/mail_DPO.txt`).
- Requête SQL sur `access_log` → 80 accès cross-région.
- Montrer la condition inversée dans `app/auth/rbac.py`.
- Expliquer pourquoi c'est "bonus ambitieux" : juridique + 72 h CNIL.

### 5 — Angle stratégique (3 min)

- Ouvrir `app/llm/base.py` → montrer l'interface abstraite.
- Expliquer : "aujourd'hui adapter OpenRouter. Demain adapter SLM maison
  sur cluster GPU La Plateforme_. Changement d'une ligne de config, zéro
  refactor métier. Souveraineté complète, zéro facture externe."
- Lien avec le talk 1er décembre : "ce même système, 3 moments narratifs
  — avant / pendant / après".

### 6 — Questions (2 min)

Préparer les réponses sur :

- Pourquoi SQLite (démo moyenne, prod réelle = PostgreSQL managed).
- Pourquoi pas Streamlit (style Khayav préservé, cohérence pédagogique).
- Pourquoi pas de tests exhaustifs (scope assumé 4 semaines).
- Pourquoi 2 interfaces (conseiller + direction = pédagogiquement
  nécessaire pour l'incident 3).

---

## Fichiers à montrer pendant la démo

- Code : `app/llm/base.py`, `app/llm/adapters.py`, `app/auth/rbac.py`,
  `app/core/routes.py`
- UI : `/static/conseiller/index.html`, `/static/direction/index.html`
- Logs : `data/llm_cost_log.jsonl`, requête SQL `access_log`
- Rapports : `data/evidently_reports/`
- Docs : `docs/ARCHITECTURE.md`, `docs/INCIDENTS.md`

## Préparation technique

- Avoir deux onglets prêts : conseiller + direction.
- Avoir une fenêtre terminal avec `tail -f` sur les logs.
- Avoir une fenêtre SQLite ouverte sur `tempo.db`.
- Avoir le rapport Evidently prêt à ouvrir.
