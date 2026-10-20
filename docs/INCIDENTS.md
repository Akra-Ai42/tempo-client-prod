# Incidents injectés — document formateur

⚠️ **Ce fichier est à destination du formateur / de l'équipe pédagogique.
Il ne doit PAS être partagé aux étudiants pendant la semaine Devoteam.**

Ce document décrit les 3 incidents volontairement injectés dans
`tempo-client-prod`, les symptômes attendus, les étapes de diagnostic
que les étudiants doivent suivre, et les correctifs attendus.

---

## Incident 1 — Facture LLM qui explose

### Scénario client

La DAF reçoit la facture OpenRouter du mois : 847 $, soit 17× le budget
mensuel de 50 $ voté en comité. Mail paniqué envoyé à l'équipe Tempo
samedi 11h, deadline de correction : 48 h.

### Causes réelles dans le code

Trois bugs combinés dans `app/llm/adapters.py` et `app/core/routes.py` :

1. **Cache cassé** : chaque `/explain/{client_id}` refait l'appel LLM
   complet, même pour les mêmes features. Le cache en mémoire a été
   désactivé par un commit "temporaire" qui n'a jamais été revert.

2. **Prompt système gonflé** : le prompt système est passé de 150 tokens
   à 850 tokens au fil de 12 commits (chaque dev a ajouté sa règle sans
   nettoyer). Résultat : chaque appel coûte 5× plus cher.

3. **`max_tokens` trop élevé** : fixé à 2000 au lieu de 300. Les réponses
   font 10 lignes au lieu de 2.

### Fichiers à préparer (branche `incident-1`)

- `docs/fake_facture_openrouter_sept.csv` : facture détaillée.
- `data/llm_cost_log.jsonl` : log pré-rempli de 30 jours d'appels.
- `docs/mail_DAF.txt` : mail de la DAF.
- Dashboard Grafana basique (optionnel) : courbe des coûts.

### Diagnostic attendu

1. Les étudiants ouvrent le dashboard direction → KPI "Coût LLM mois courant"
   est en rouge.
2. Ils ouvrent `llm_cost_log.jsonl` → remarquent le nombre d'appels par
   jour anormalement élevé.
3. Ils grep `cache` dans le code → trouvent le TODO oublié.
4. Ils regardent les prompt_tokens dans le log → remarquent qu'ils sont
   constants à ~850 → cherchent la source → prompt système.
5. Ils regardent completion_tokens → remarquent qu'ils plafonnent à
   ~1800 → cherchent `max_tokens`.

### Correctifs attendus

- Réactiver le cache LRU des explications (TTL 24h sur features identiques).
- Nettoyer le prompt système, le redescendre à ~200 tokens.
- Fixer `max_tokens=300`.
- Ajouter une alerte Scheduler : si coût journalier > 2 $, log warning.

### Post-mortem Google SRE attendu

Format classique : what happened / impact / timeline / root cause /
action items.

---

## Incident 2 — Dérive silencieuse

### Scénario client

Marketing remarque que les recommandations faites par les conseillers
depuis Tempo "ne collent plus" : trop de "RDV urgent" là où la réalité
est plus calme. Perte de confiance dans l'outil.

### Causes réelles dans le code

Dans `scripts/generate_fake_data.py`, le dataset `clients_current.csv`
contient une dérive volontaire sur deux features :

1. `nb_interactions_90j` : moyenne passée de ~6 à ~2 (contexte macro
   fictif : baisse générale des visites agence).

2. `solde_moyen` : variance augmentée + queue à gauche (plus de clients
   pauvres).

Le modèle XGBoost a été entraîné sur `clients_baseline.csv` et n'est
jamais ré-entraîné. Il prédit mal sur `clients_current.csv`.

### Fichiers à préparer

- `data/evidently_reports/drift_<ts>.html` : rapport Evidently rouge.
- `docs/mail_marketing.txt` : mail du directeur marketing.

### Diagnostic attendu

1. Lecture du rapport Evidently (auto-généré par le scheduler).
2. Comparaison distributions baseline vs. current → 2 features en rouge.
3. Compréhension : modèle entraîné sur une distribution, prédiction sur
   une autre.

### Correctifs attendus

- Réentraîner le modèle sur un échantillon qui mixe baseline + current.
- Mettre en place un job de ré-entraînement mensuel.
- Ajouter une alerte Scheduler : si dérive détectée sur > 1 feature
  → log warning + email direction.

---

## Incident 3 — Faille RBAC (bonus ambitieux)

### Scénario client

Le DPO reçoit un signalement : un conseiller de Lille a affirmé en
réunion savoir des choses sur des clients de Marseille. Ces clients ne
sont pas dans son périmètre. Risque RGPD → notification CNIL sous 72 h
si incident de sécurité confirmé.

### Causes réelles dans le code

Dans `app/auth/rbac.py`, fonction `filter_clients_by_region` :

```python
# ⚠️ BUG VOLONTAIRE — devrait être `== user["region"]`
return [c for c in all_clients if c["region"] != user["region"]]
```

La condition est inversée. Résultat : le conseiller Lille voit TOUS les
clients SAUF ceux de Lille, c'est-à-dire ceux de Marseille.

### Fichiers à préparer

- Table `access_log` pré-remplie avec 150 lignes dont 80 d'accès
  cross-région (via script).
- `docs/mail_DPO.txt` : mail du DPO avec rappel délai CNIL.

### Diagnostic attendu

1. Les étudiants lisent le mail DPO.
2. Ils requêtent `access_log` :
   ```sql
   SELECT * FROM access_log WHERE user_region != client_region;
   ```
3. 80 lignes remontent → confirmation du leak.
4. Ils remontent au code → trouvent la condition inversée.

### Correctifs attendus

- Fix de la condition.
- Ajout du test `test_conseiller_sees_only_his_region` manquant.
- Audit SQL complet des accès passés.
- Notification CNIL dans les 72 h (ligne métier/juridique).

### Pourquoi bonus

Cet incident mêle technique, juridique et process. Il demande aux
étudiants de penser au-delà du bug : audit, notification, communication
interne. C'est le niveau ingénieur IA senior / tech lead.
