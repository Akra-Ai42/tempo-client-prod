# Carnet de bord. Tempo Client V2

> Document vivant qui trace, brique par brique, la construction de Tempo Client V2.
> Chaque brique y est documentée avec un prisme pédagogique : les flux pas à pas
> décrivent ce qui se passe couche par couche, quand l'utilisateur fait X.
>
> Auteur : Akram Toumani
> Projet : Tempo Client V2, pack pédagogique Devoteam MSc1
> Démarrage : octobre 2026
> Objectif : démo Sloan Charrier dans 4 semaines, talk 1er décembre 2026
> État : 11/13 briques livrées, monitoring Evidently opérationnel, dérive détectée visible dans le dashboard

---

## Table des matières

### Vision et architecture
- Vision du projet
- Architecture globale cible
- Les 3 incidents injectés, approche B

### Parcours utilisateur conseiller
- Étape 1. Je me connecte (Brique 4)
- Étape 2. J'arrive sur mon dashboard (Briques 5 + 10a + UX V2)
- Étape 3. Je sélectionne un client (Brique 10a côté SHAP)
- Étape 4. Je lis l'analyse contextuelle (Brique 10b)
- Étape 5. Je consulte les actions recommandées (Brique 10c)
- Étape 6. Je me déconnecte (Brique 4 logout)

### Parcours utilisateur direction
- Étape D1. Je me connecte en tant que direction (Brique 4 + 7)
- Étape D2. Je consulte le dashboard business + ML Ops (Brique 7)
- Étape D3. Je bascule vers la vue conseiller (Brique 7 + 5)
- Étape D4. Je consulte la dérive et ouvre le rapport Evidently (Brique 8)

### Infrastructure sous-jacente
- Infra A. Au boot du serveur (Brique 3 ML + Brique 10a pré-scoring)
- Infra B. Chaque appel LLM (Briques 1 + 2)
- Infra C. Chaque requête RBAC (Brique 5)
- Infra D. Vue agrégée direction, pattern lecture pure (Brique 7)
- Infra E. Monitoring Evidently, adapter branché à chaud (Brique 8)

### Briques construites (ordre numérique)
- Brique 1. LLMProvider + OpenRouter (livrée)
- Brique 2. Cache LRU + explain service (livrée)
- Brique 3. Dataset + XGBoost + SHAP (livrée)
- Brique 4. Auth + session cookies (livrée)
- Brique 5. RBAC + /clients/mine (livrée)
- Brique 6. Front conseiller V2 UX premium (livrée)
- Brique 10a. Endpoint /score + pré-scoring (livrée)
- Brique 10b. Endpoint /explain + cache LLM + audit RGPD (livrée)
- Brique 10c. Endpoint /recommend + règles métier + audit (livrée)
- Brique 7. Dashboard direction V2 UX premium (livrée)
- Brique 8. Monitoring Evidently + détection de dérive (livrée) (à venir)
- Brique 9. Scheduler APScheduler (à venir)
- Brique 11. Injection des incidents (semaine 4)

### Références
- Métriques consolidées
- Glossaire technique
- Journal des pièges évités

---

## Vision du projet

Tempo Client V2 est un outil décisionnel pour conseillers bancaires qui combine :

- Un modèle ML qui prédit la probabilité qu'un client parte (churn)
- Une couche d'explication qui transforme les SHAP values en langage naturel via LLM
- Un système d'alertes et de recommandations d'actions
- Un dashboard direction avec les KPI business et ML Ops (coûts LLM, dérive)

Spécificité pédagogique : trois incidents volontaires sont injectés dans le code
pour servir d'exercice aux étudiants Devoteam MSc1 Finance/Assurance. Ils devront
les diagnostiquer et les corriger en 10 jours.

Positionnement stratégique Akram :

- Capitalisation sur le socle Khayav (FastAPI, Docker, Render)
- Préparation à la souveraineté (interface LLMProvider abstraite, bascule vers SLM maison sur cluster GPU La Plateforme_)
- Alignement avec le talk 1er décembre (angle avant/pendant/après, archi hexagonale appliquée à l'IA)

---

## Architecture globale cible

```
+-------------------------------------------------------------+
|                     TEMPO CLIENT V2                         |
+-------------------------------------------------------------+
|  Fronts HTML statiques                                      |
|  ├─ /static/shared/login.html         (livré)               |
|  ├─ /static/conseiller/index.html     (livré, V2 UX)        |
|  └─ /static/direction/index.html      (à venir, brique 7)   |
+-------------------------------------------------------------+
|  FastAPI (app/main.py)                                      |
|  ├─ POST /auth/login              (livré, brique 4)         |
|  ├─ POST /auth/logout             (livré, brique 4)         |
|  ├─ GET  /auth/me                 (livré, brique 4)         |
|  ├─ GET  /clients/mine            (livré, brique 5 et 10a)  |
|  ├─ POST /score/{client_id}       (livré, brique 10a)       |
|  ├─ POST /explain/{client_id}     (livré, brique 10b)       |
|  ├─ POST /recommend/{client_id}   (livré, brique 10c)       |
|  └─ GET  /dashboard/direction     (à venir, brique 7)       |
+-------------------------------------------------------------+
|  Dépendances FastAPI (Depends)                              |
|  ├─ get_current_user              (livré, brique 4)         |
|  ├─ require_conseiller            (livré, brique 5)         |
|  └─ require_direction             (livré, brique 5)         |
+-------------------------------------------------------------+
|  Services métier                                            |
|  ├─ app/core/explain_service.py   (livré, brique 2)         |
|  ├─ app/core/clients.py           (livré, brique 5)         |
|  ├─ app/core/scoring.py           (livré, brique 10a)       |
|  ├─ app/ml/churn_model.py         (livré, brique 3)         |
|  ├─ app/ml/shap_explainer.py      (livré, brique 3)         |
|  └─ app/ml/reco_model.py          (livré, brique 10c)       |
+-------------------------------------------------------------+
|  Infrastructure                                             |
|  ├─ LLMProvider abstrait          (livré, brique 1)         |
|  ├─ Cache TTL LRU                 (livré, brique 2)         |
|  ├─ SessionMiddleware             (livré, brique 4)         |
|  ├─ Audit log RGPD                (livré, brique 10b)       |
|  ├─ SQLite                        (à venir, brique 9)       |
|  ├─ APScheduler                   (à venir, brique 9)       |
|  └─ Evidently monitoring          (à venir, brique 8)       |
+-------------------------------------------------------------+
|  Déploiement : Docker + Render + $PORT dynamique            |
+-------------------------------------------------------------+
```

---

## Les 3 incidents injectés, approche B pure

Approche retenue : B pure. Le code source est 100 pourcent sain pendant tout le
développement. Aucun tag "INCIDENT-X" dans le code. Les 3 points d'injection sont
documentés uniquement dans le fichier privé `docs/INCIDENT_INJECTION_PLAYBOOK.md`,
non versionné sur GitHub public.

En semaine 4, les 3 modifications sont appliquées sur une branche `incidents/semaine-4`,
puis déployées. Le `main` reste propre pour la correction.

| Numéro | Nom | Impact métier | Statut |
|---|---|---|---|
| 1 | Facture LLM qui explose | DAF panique, 847 USD au lieu de 50 USD | À injecter semaine 4 |
| 2 | Dérive silencieuse | Recommandations qui ne collent plus | Dataset préparé en brique 3 |
| 3 | Faille RBAC | DPO alerté, risque CNIL 72h | À injecter semaine 4 |

Pourquoi l'approche B :

- Code 100 pourcent réaliste, vrai défi d'investigation pour les étudiants
- Repo publiable sur GitHub sans spoiler les futurs apprenants
- `grep INCIDENT` ne révèle rien, l'effet de surprise est préservé

---

# PARCOURS UTILISATEUR CONSEILLER

Cette section raconte Tempo Client V2 **depuis le point de vue du conseiller**.
Chaque étape décrit ce qui se passe **couche par couche** quand l'utilisateur
fait une action. C'est l'ordre de lecture recommandé pour un étudiant qui
découvre le projet.

---

## Étape 1. Je me connecte

### Scénario : Marie Dubois ouvre son navigateur sur Tempo Client

### Flux pas à pas

1. Le navigateur charge `/static/shared/login.html`
   → formulaire HTML sobre, champs username et password
2. Marie saisit `conseiller_lille` et `conseiller_lille2026`, clique "Se connecter"
3. `login.js` envoie un POST `/auth/login` avec payload JSON
   → `{ "username": "conseiller_lille", "password": "conseiller_lille2026" }`
   → `credentials: 'same-origin'` pour que le cookie soit géré
4. Côté serveur, `app/auth/routes.py` reçoit la requête
   → `app/auth/users.py` cherche l'user dans le dict `DEMO_USERS` de `config.py`
   → `verify_password()` compare le mot de passe avec le hash bcrypt stocké
   → si user inexistant : bcrypt bidon pour éviter la timing attack, puis `False`
   → si password incorrect : retourne `False`
   → si tout OK : retourne l'objet `User`
5. `login_user()` crée la session Starlette signée dans le cookie
   → `request.session["username"] = user.username`
   → `SessionMiddleware` encode et signe le cookie, durée 24h
6. La réponse HTTP 200 part avec le cookie `Set-Cookie: session=...`
   → body JSON : `{ "username", "role", "region", "full_name" }`
7. `login.js` reçoit la réponse, lit `info.role`
   → si `direction` : redirect vers `/static/direction/index.html`
   → sinon : redirect vers `/static/conseiller/index.html`
     ↓
Marie arrive sur son dashboard. Le cookie est posé dans son navigateur.
Les prochaines requêtes vers l'API l'enverront automatiquement.

### Détails techniques clés

- **Hash bcrypt rounds=12** : vérification en environ 100 ms, défense native brute-force
- **Message d'erreur générique** "Identifiants invalides" : défense contre énumération
- **Cookie signé, pas chiffré** : le serveur vérifie l'intégrité, pas la confidentialité
- **Pattern Dependency Injection** : chaque endpoint protégé déclare `Depends(get_current_user)`

---

## Étape 2. J'arrive sur mon dashboard

### Scénario : la page `/static/conseiller/index.html` se charge

### Flux pas à pas

1. Le navigateur charge le HTML, le CSS et `app.js`
   → `app.js` lance `loadMe().then(loadClients)` au boot
2. `loadMe()` appelle GET `/auth/me`
   → le cookie session est envoyé automatiquement
   → `get_current_user()` lit `request.session.get("username")`
   → si pas de session : réponse 401, le JS redirige vers login
   → si session valide : retourne `User`, body `{ username, role, region, full_name }`
3. `app.js` affiche le header : avatar avec initiales + "Marie Dubois - lille"
4. `loadClients()` appelle GET `/clients/mine`
   → `app/core/routes.py :: get_my_clients()` reçoit la requête
5. Côté serveur :
   → `get_all_clients()` retourne les 1000 clients chargés en mémoire au boot
   → `filter_clients_by_user(clients, user)` applique le RBAC régional :
       - si `user.role == "direction"` : retourne tout
       - si `user.role == "conseiller"` : filtre `c["region"] == user.region`
   → `get_all_scores()` retourne le dict `{client_id: ScoreData}` pré-calculé
   → chaque client est enrichi avec `score_churn` et `urgence`
   → tri décroissant par `score_churn` (les plus à risque en haut)
6. Réponse 200 avec liste `ClientWithUrgence` sérialisée en JSON
7. Côté front, `renderSidebar()` construit la liste :
   → chaque entrée : puce couleur (high rouge, medium brun, low vert) + nom + région + ancienneté + score
   → `renderGauge()` et `renderKPICards()` restent en standby, zone centrale vide
     ↓
Marie voit sa sidebar à gauche avec 489 clients Lille triés par urgence.
Zone centrale : "Sélectionnez un client dans la liste à gauche."

### Détails techniques clés

- **Pré-scoring au boot** : les 1000 scores sont déjà calculés, pas d'appel ML ici
- **Validation croisée** : 489 Lille + 511 Marseille = 1000 clients total, aucun doublon
- **Tri côté serveur** : plus simple et plus rapide que côté JS
- **Format `ClientWithUrgence`** : hérite de `ClientSummary`, ajoute `score_churn` et `urgence`

---

## Étape 3. Je sélectionne un client

### Scénario : Marie clique sur Yasmine Dupont dans la sidebar

### Flux pas à pas

1. Le gestionnaire JS `openClient(client)` est déclenché
   → `state.currentClientId` est mis à jour
   → `renderSidebar()` ré-applique la classe `.active` sur l'entrée cliquée
2. La zone centrale se remplit en 3 étapes synchrones puis 3 en parallèle :
   → `renderHero(client)` affiche le nom, méta, et la gauge circulaire SVG
   → `renderKPICards(client)` affiche les 4 cartes Profil / Activité / Finance / Risque
   → 3 placeholders apparaissent pour SHAP, Analyse et Recommandations
3. Les 3 appels API partent en parallèle :
   → POST `/score/{client_id}` pour les top features SHAP
   → POST `/explain/{client_id}` pour l'explication contextuelle LLM
   → POST `/recommend/{client_id}` pour les actions recommandées
4. L'appel `/score` est traité d'abord car léger (lookup dict) :
   → vérification existence client via `get_client_by_id(client_id)` → 404 si None
   → vérification RBAC régional (conseiller voit uniquement sa région) → 403 sinon
   → lookup `get_score(client_id)` dans le dict pré-calculé en mémoire
   → retourne `ScoreResponse` avec client_id, score_churn, top_features (5 features)
5. Le front reçoit la réponse, construit la section "Top facteurs explicatifs" :
   → une ligne par feature avec label lisible, valeur, flèche directionnelle colorée
   → flèche vers le haut rouge si feature pousse vers churn
   → flèche vers le bas verte si feature retient le client
   → valeurs SHAP formatées à 2 décimales
     ↓
Marie voit la fiche détaillée de Yasmine. Hero, KPI, SHAP affichés en moins d'une seconde.
Les sections Analyse et Recommandations arrivent indépendamment ensuite.

### Détails techniques clés

- **Pré-scoring = latence quasi nulle** : moins de 10 ms pour `/score/{id}`
- **Défense en profondeur RBAC** : `/clients/mine` filtre déjà, mais `/score/{id}` revérifie
- **Gauge SVG inline** : calcul de `stroke-dasharray` et `stroke-dashoffset` basé sur le score
- **Parallélisation JS** : les 3 fetchs ne bloquent pas, chaque section se remplit dès que sa réponse arrive

---

## Étape 4. Je lis l'analyse contextuelle

### Scénario : la section "Analyse Tempo" se remplit avec l'explication LLM

### Flux pas à pas

1. L'appel POST `/explain/{client_id}` arrive sur `app/core/routes.py`
2. Vérifications d'entrée (comme `/score`) :
   → `get_client_by_id()` → 404 si inexistant, audit log `outcome: not_found`
   → RBAC régional → 403 si cross-région, audit log `outcome: forbidden`
3. Récupération du score depuis le pré-scoring :
   → `get_score(client_id)` renvoie `ScoreData` avec `score_churn` et `top_features`
4. Appel au service `explain_service.explain_score(...)` enveloppé dans `asyncio.wait_for(timeout=30)` :
   → arguments : client_id, prénom, nom, score_churn, top_features
   → le service construit une cache key = hash(client_id, features, model)
   → cache HIT : retour en environ 5 ms avec `from_cache=True`, cost_usd=0, latency du MISS original
   → cache MISS : construit le prompt système (environ 150 tokens) + prompt user (features formatées)
       - appel `provider.complete(prompt, system, max_tokens=300, temperature=0.3)`
       - l'adapter `OpenRouterProvider` envoie à `meta-llama/llama-3.3-70b-instruct`
       - latence réelle environ 2 à 3 secondes selon charge OpenRouter
       - coût réel environ 0.000125 USD selon tokens
       - `log_llm_call()` écrit la ligne dans `data/llm_cost_log.jsonl`
       - mise en cache de la réponse avec TTL 86400 secondes
   → retourne `ExplanationResult` avec `text`, `model_used`, `from_cache`, `latency_ms`, `cost_usd`
5. Si `asyncio.TimeoutError` ou `LLMProviderError` : fallback texte sobre
   → audit log avec `outcome: llm_timeout` ou `llm_error`
   → UI reste fonctionnelle, pas de spinner infini
6. Succès : audit log avec `outcome: success` et `extra: {from_cache, model}`
   → écriture dans `data/audit_log.jsonl` : qui a demandé quoi, quand, avec quelle issue
7. Réponse HTTP 200 avec `ExplainResponse` enrichi
   → `client_id`, `explication`, `from_cache`, `latency_ms`, `cost_usd`, `llm_model`
8. Côté front :
   → la bulle de chargement italique disparaît
   → la bulle Analyse Tempo s'affiche avec le texte complet
   → sous la bulle, un bandeau sobre : `Cache HIT|MISS | 5ms | 0.000125 USD`
   → couleur verte si HIT, brun si MISS
     ↓
Marie lit une explication en français clair en 3-4 phrases.
Elle voit si le résultat est frais ou mis en cache, et combien ça a coûté.

### Détails techniques clés

- **Timeout 30s + fallback** : jamais de spinner infini, UI toujours fonctionnelle
- **Cache TTL 24h** : les features changent peu dans la journée pour un même client
- **Audit RGPD séparé** du log coût LLM : deux responsabilités, deux couches, deux fichiers
- **Hexagonal propre** : le service `explain_score` ignore qui est l'user, le endpoint connaît l'audit

---

## Étape 5. Je consulte les actions recommandées

### Scénario : la checklist des actions à mener se remplit

### Flux pas à pas

1. L'appel POST `/recommend/{client_id}` arrive sur `app/core/routes.py`
2. Vérifications d'entrée identiques à `/explain` :
   → existence client → 404 + audit log
   → RBAC régional → 403 + audit log
   → score présent dans le pré-scoring → 500 + audit log si manquant
3. Construction du contexte features à partir du client :
   → dict avec les 7 features : anciennete_mois, produits_detenus, solde_moyen,
     nb_interactions_90j, derniere_interaction_jours, age_client, canal_prefere
4. Appel `recommend_actions(features, churn_score=score_data.score_churn)` :
   → le moteur charge les règles depuis `_reco_rules` (chargé au boot)
   → pour chaque règle : évalue la condition Python dans un contexte restreint
       - `eval(condition, {"__builtins__": {}}, context_features_et_score)`
       - exemple : `"score_churn >= 0.7 and solde_moyen < 10000"` renvoie True ou False
       - exceptions silencieuses : règle non évaluable retourne False, warning loggué
   → filtre les règles qui matchent le client
   → tri par priorité : haute (0) > moyenne (1) > basse (2)
   → prend les 3 premières, les transforme en objets `Recommandation` Pydantic
5. Audit log avec `outcome: success` et `extra: {nb_recos}`
6. Réponse 200 avec `RecommendResponse` : `client_id` + liste de 0 à 3 recommandations
7. Côté front :
   → la liste de chargement est remplacée par la checklist
   → chaque reco : checkbox carrée à gauche, puce couleur selon priorité, action en gras, justification en gris
   → la couleur de la puce suit la priorité : haute rouge, moyenne brun, basse vert
   → clic sur une ligne : la case se coche, le texte se barre, l'état est persisté dans `localStorage`
     ↓
Marie voit ses 3 actions prioritaires. Elle coche celles qu'elle a traitées,
l'état est conservé même après rafraîchissement de la page.

### Détails techniques clés

- **`eval()` restreint** : contexte = features + score, `__builtins__` vide, règles contrôlées par le data scientist
- **Pas d'input utilisateur dans la condition** : sécurité par le périmètre, pas par la syntaxe
- **Persistance localStorage** : `tempo_done_recos` par client_id, sans aller-retour serveur
- **3 recos max** : un conseiller lit 3 actions, pas 10

---

## Étape 6. Je me déconnecte

### Scénario : Marie clique "Déconnexion" en haut à droite

### Flux pas à pas

1. Le handler JS déclenche POST `/auth/logout`
   → envoyé avec le cookie session
2. Côté serveur, `logout_user()` est appelé
   → `request.session.clear()` vide la session côté serveur
   → la réponse HTTP 200 inclut un nouveau cookie session, vide ou expiré
3. Le navigateur reçoit la réponse, le cookie est effacé
4. `app.js` redirige vers `/static/shared/login.html`
     ↓
Marie est déconnectée. Toute requête `/auth/me` renverrait maintenant 401.

---

# PARCOURS UTILISATEUR DIRECTION

Cette section décrit ce que vit la direction marketing quand elle utilise le
produit. Deux voix cohabitent sur une même page : la voix business (Comex,
portefeuille de risque) et la voix ML Ops (DSI, santé du système).

---

## Étape D1. Je me connecte en tant que direction

### Scénario : Claire, directrice marketing, saisit `direction` / `direction2026`

### Flux pas à pas

1. Claire ouvre `/static/shared/login.html` dans son navigateur
2. Elle saisit `direction` et `direction2026`, clique Connexion
3. Le JS envoie POST `/auth/login` avec credentials same-origin
   → `authenticate_user()` lit le dict `USERS` et vérifie le hash bcrypt
   → `request.session["username"] = "direction"` est stocké côté serveur
4. La réponse HTTP 200 contient `{username, role: "direction", region: null, full_name: "Direction Marketing"}`
5. Le JS inspecte `role` :
   → si `conseiller` : redirect vers `/static/conseiller/index.html`
   → si `direction` : redirect vers `/static/direction/index.html`
6. Claire arrive sur le dashboard direction
     ↓
Même mécanique d'auth que le conseiller. Seule la cible de redirection change.
La session est stockée côté serveur, cookie signé HMAC côté client.

### Détails techniques clés

- **Login agnostique du rôle** : `/auth/login` ne connaît pas la différence
- **Logique de redirection côté front** : le JS lit le rôle et choisit l'URL
- **Direction a `region: null`** : signal RBAC pour accès à toutes les régions

---

## Étape D2. Je consulte le dashboard business + ML Ops

### Scénario : Claire est sur `/static/direction/index.html`

### Flux pas à pas

1. Au chargement, `app.js` appelle `loadMe()` puis `loadDashboard()`
2. `loadMe()` GET `/auth/me` → récupère `full_name` et calcule les initiales
   → remplit la topbar avec "DM" (avatar) et "Direction Marketing"
3. `loadDashboard()` GET `/dashboard/direction` → vrai cœur de la brique 7
4. Côté serveur, l'endpoint `get_direction_dashboard()` compose 3 vues :
   → **Portfolio stats** depuis le pré-scoring en mémoire (zéro appel ML)
       - lit `get_all_scores()` qui retourne un dict `{id → ScoreData}`
       - compte high / medium / low, calcule les pourcentages
       - calcule score moyen portefeuille et taux churn prédit
   → **ML Ops stats** depuis `read_cost_log(since=get_first_of_month())`
       - lit `data/llm_cost_log.jsonl` ligne par ligne
       - filtre les entrées depuis le 1er du mois
       - agrège : total coût, nombre d'appels, latence moyenne, hit rate
       - fait le même calcul en parallèle pour les 24h glissantes
   → **Top 10 clients à risque** depuis le même `get_all_scores()`
       - trie par score_churn décroissant, prend les 10 premiers
       - enrichit avec `prenom`, `nom`, `region` depuis `get_all_clients()`
5. La réponse HTTP 200 renvoie un JSON structuré en 3 blocs
6. Côté front, 3 fonctions de rendu s'enchaînent :
   → `renderPortfolioSection()` : donut SVG 3 arcs + 4 stats business
   → `renderMLOpsSection()` : 4 KPI cards (coût mois, coût 24h, hit rate, latence)
   → `renderTopList()` : 10 lignes avec rang + nom + région + score + barre colorée
7. Chaque ligne du top 10 est cliquable
   → clic ouvre `/static/conseiller/index.html` dans un nouvel onglet
8. Un bouton "Actualiser" en haut à droite relance `loadDashboard()`
     ↓
Claire voit en une page : la santé du portefeuille, le coût du système,
et les 10 clients à traiter en priorité. Zéro attente, zéro surprise.

### Détails techniques clés

- **Zéro appel ML, zéro appel LLM** : le dashboard est purement en lecture
- **Latence serveur ~1 ms** sur 1000 clients grâce au pré-scoring en mémoire
- **Donut SVG inline** : 4 cercles concentriques avec `stroke-dasharray` et offsets
- **Palette V2 héritée** : surface-0 à 3, text-primary à quaternary, cohérent conseiller
- **Pattern Apple HIG** : KPI = icône + valeur grosse + sous-label petit
- **Code source 100 pourcent approche B** : nulle part de tag `INCIDENT` visible

---

## Étape D3. Je bascule vers la vue conseiller

### Scénario : Claire veut voir le détail d'un client

### Flux pas à pas

1. Claire clique sur une ligne du top 10 (ou sur le bouton "Vue conseiller" en topbar)
2. `window.open('/static/conseiller/index.html', '_blank')` ouvre un nouvel onglet
3. Le même cookie session est transmis automatiquement (same-origin)
4. `/auth/me` répond `{role: "direction", region: null, full_name: "Direction Marketing"}`
5. Le JS du conseiller appelle `/clients/mine`
6. Côté serveur, `filter_clients_by_user()` reçoit `user.region == None`
   → la fonction retourne la liste complète sans filtre (direction voit tout)
7. 1000 clients remontent, triés par score
     ↓
Claire se retrouve dans la vue conseiller avec les 1000 clients visibles.
Elle peut cliquer n'importe lequel et accéder à la fiche complète.
Même produit, deux rôles, zéro code dupliqué côté front.

### Détails techniques clés

- **Même URL pour les deux rôles** : le RBAC backend fait la différence
- **Direction = conseiller sans filtre régional** : élégance de la factorisation
- **Switch bidirectionnel implicite** : conseiller ne peut pas aller vers direction (403), direction peut aller partout

---

## Étape D4. Je consulte la dérive et ouvre le rapport Evidently

### Scénario : Claire voit la section "Dérive des données" sur son dashboard

### Flux pas à pas

1. Dans le dashboard direction, en-dessous de ML Ops, apparaît la section "Dérive des données (Evidently)"
2. Visuellement, Claire voit :
   → Un gros label "DÉTECTÉE" en rouge
   → Le ratio "3/6 features dérivées (50%)"
   → Trois badges rouges listant les features qui ont dérivé : solde_moyen, nb_interactions_90j, derniere_interaction_jours
   → La date du dernier calcul
3. En haut à droite de la section, deux boutons :
   → "Voir le rapport Evidently" : ouvre un nouvel onglet
   → "Vérifier maintenant" : force un recalcul
4. Claire clique sur "Voir le rapport Evidently"
   → Le navigateur ouvre GET /monitoring/drift/report dans un nouvel onglet
   → L'endpoint lit le fichier data/evidently_reports/latest.html
   → Renvoie le HTML brut avec HTMLResponse
5. Le navigateur rend la page Evidently :
   → Titre "Data Drift Report"
   → Tableau résumé : chaque feature avec son statut dérivé / non dérivé
   → Pour chaque feature dérivée : graphique de distribution baseline (bleu) vs current (rouge)
   → Métriques statistiques (Wasserstein distance, p-value, etc.)
6. Claire voit visuellement que les distributions ont bougé
   → solde_moyen : queue à droite dégarnie, mode décalé vers le bas
   → nb_interactions_90j : courbe aplatie, moins de pics
   → derniere_interaction_jours : queue à droite étalée
7. Elle revient sur le dashboard, clique sur "Vérifier maintenant"
   → Le bouton devient "Calcul en cours..."
   → POST /monitoring/drift/recompute force run_drift_report()
   → Evidently recalcule, nouveau rapport historisé + latest.html régénéré
   → Le dashboard se rafraîchit avec les nouvelles valeurs (identiques si rien n'a changé)
     ↓
Claire a maintenant une vue complète : le monitoring technique montre que les données qui alimentent le modèle ne ressemblent plus à celles sur lesquelles il a été entraîné. Le modèle continue de prédire, mais ses prédictions deviennent de moins en moins fiables.

### Détails techniques clés

- **Rapport Evidently généré au boot** et mis en cache mémoire via `_LAST_REPORT`
- **Dashboard lit le cache** : zéro recalcul à chaque GET /dashboard/direction
- **Recalcul manuel disponible** via le bouton (bascule le cache)
- **Rapport HTML historisé** : chaque run crée un fichier daté + met à jour latest.html
- **Protection direction only** : les 2 endpoints exigent `require_direction`
- **Pattern narratif** : le monitoring voit la dérive, mais si personne ne regarde le dashboard, l'incident se prépare en silence

---

# INFRASTRUCTURE SOUS-JACENTE

Cette section décrit ce qui tient le produit en coulisses. L'utilisateur ne
voit rien de tout ça, mais c'est ce qui rend l'expérience possible.

---

## Infra A. Au boot du serveur

### Scénario : `uvicorn app.main:app --reload --port 8000` démarre

### Flux pas à pas

1. FastAPI charge l'app, le `lifespan` démarre
2. `load_clients()` lit `data/clients_baseline.csv`
   → 1000 lignes parsées via pandas
   → stockées dans un singleton module `_all_clients: list[dict]`
3. `load_model()` lit `models/xgboost_churn.pkl`
   → `pickle.load()` reconstitue l'objet XGBoostClassifier
   → stocké dans un singleton `_model`
4. `load_explainer()` lit `models/shap_explainer.pkl`
   → `pickle.load()` reconstitue le `TreeExplainer`
   → stocké dans un singleton `_explainer`
5. `load_reco_rules()` lit `models/reco_model.pkl`
   → `pickle.load()` reconstitue le dict `{"version": "1.0", "rules": [...]}`
   → stocké dans un singleton `_reco_rules`
   → log : "Reco rules chargees (version 1.0, 5 regles)"
6. `precompute_all_scores()` boucle sur les 1000 clients :
   → pour chaque client, extrait les 7 features ML
   → `predict_churn(features)` renvoie le score 0.0 à 1.0 via XGBoost
   → `urgence_from_score(score)` renvoie high / medium / low
   → `get_top_features(features, top_n=5)` renvoie les 5 contributions SHAP
   → stocke `ScoreData(client_id, score_churn, urgence, top_features)` dans `_scored_clients`
   → log final : "Pre-scoring termine : 1000 clients en 1.23s (813 clients/s)"
7. `SessionMiddleware` est activé, cookies session prêts
8. Les routers `auth_router` et `core_router` sont inclus dans l'app
9. `uvicorn` affiche "Application startup complete"
     ↓
Le serveur est prêt. 1000 scores sont déjà en mémoire. Les requêtes `/score`,
`/explain` et `/recommend` seront ultra-rapides car tout le lourd est fait.

### Détails techniques clés

- **Pré-scoring = 1 à 2 secondes au boot** pour 1000 clients
- **Accès O(1)** aux scores pendant les requêtes HTTP
- **Singletons de module** : pattern simple, pas de dépendance globale explicite
- **Démarrage un peu plus lent, mais requêtes ultra-rapides** : trade-off assumé

---

## Infra B. Chaque appel LLM

### Scénario : un endpoint appelle `explain_service.explain_score(...)`

### Flux pas à pas

1. Le service construit une cache key : hash(client_id, features, model)
2. Il cherche dans son `TTLCache` interne :
   → cache HIT : retour en environ 5 ms, 0 appel réseau, 0 USD
   → cache MISS : construction du prompt
3. Prompt système d'environ 150 tokens cadrant le rôle (banking, français, concis)
4. Prompt user : nom, prénom, score, top features formatées en bullet points
5. Appel `provider.complete(prompt, system, max_tokens=300, temperature=0.3)` :
   → `OpenRouterProvider` utilise un singleton `httpx.AsyncClient` partagé
   → ouvre une requête POST vers `https://openrouter.ai/api/v1/chat/completions`
   → headers : Authorization Bearer, HTTP-Referer, X-Title
   → retry 3 fois avec backoff 1-2-4s sur 429 et 5xx (jamais sur 4xx)
   → timeout 30 secondes
6. OpenRouter route la requête vers Llama 70B
   → latence réelle environ 2 à 3 secondes depuis Europe
   → réponse : texte en français, environ 50 à 150 tokens
7. `provider.complete()` retourne un `LLMResponse` :
   → `text`, `model`, `prompt_tokens`, `completion_tokens`, `cost_usd`, `latency_ms`
   → le coût est calculé via le dict `pricing.py` : prix input + prix output par million tokens
8. `log_llm_call()` écrit une ligne JSONL dans `data/llm_cost_log.jsonl` :
   → `{ts, model, prompt_tokens, completion_tokens, cost_usd, latency_ms}`
   → append-only, versionné, auditable
9. Le service met en cache la réponse avec TTL 86400 secondes
10. Retourne `ExplanationResult` avec `from_cache=False`
     ↓
Le prochain appel pour le même client (features identiques) sera un cache HIT.
0 appel réseau. 0 USD. 5 ms. Même qualité d'explication.

### Détails techniques clés

- **Singleton httpx** : évite environ 50 ms de handshake TLS par appel
- **Retry seulement sur 429 et 5xx** : ne pas retry ce qui ne peut pas changer
- **Hash features avec `sort_keys=True`** : cache déterministe, pas de doublons
- **Modèle inclus dans la clé** : bascule modèle = cache invalidé, cohérent
- **Hit rate projeté 93 pourcent** : facture passe de 5 USD/mois à 0.36 USD/mois

---

## Infra C. Chaque requête RBAC

### Scénario : un endpoint protégé reçoit une requête

### Flux pas à pas

1. FastAPI résout la dépendance `Depends(get_current_user)` sur le endpoint
2. `get_current_user()` lit `request.session.get("username")`
   → si None : lève `HTTPException(401, "Non authentifie")`
   → si présent : récupère l'objet `User` via `get_user_by_username()`
3. Si l'endpoint utilise `Depends(require_direction)` :
   → vérifie `user.role == "direction"` → sinon 403 avec message "Acces reserve a la direction"
4. Pour un endpoint listing comme `/clients/mine` :
   → `filter_clients_by_user(all_clients, user)` applique le filtre régional
   → `direction` retourne tout, `conseiller` retourne `[c for c in clients if c["region"] == user.region]`
   → c'est cette ligne qui portera l'incident 3 (semaine 4) : `==` deviendra `!=`
5. Pour un endpoint ressource comme `/score/{client_id}` :
   → récupère le client via `get_client_by_id(client_id)`
   → vérifie explicitement `user.role == "conseiller" and client["region"] != user.region`
   → si incompatible : 403 "Acces refuse : ce client n'est pas dans votre perimetre"
     ↓
Le RBAC fonctionne en 2 couches : filtre pour les listings, vérification explicite
pour les ressources individuelles. Défense en profondeur.

### Détails techniques clés

- **Dépendances FastAPI** : pas de middleware global, chaque endpoint explicite
- **Factory `require_role(role)`** : closure Python retournant une fonction de dépendance
- **Point d'injection incident 3** : une seule ligne de code, isolée, testable en 2 secondes
- **Validation croisée** : 489 Lille + 511 Marseille = 1000, aucun client oublié ni doublé

---

## Infra D. Vue agrégée direction, pattern lecture pure

### Scénario : la direction demande le dashboard global

### Flux pas à pas

1. GET `/dashboard/direction` arrive avec cookie session direction
2. FastAPI résout `Depends(require_direction)`
   → vérifie `user.role == "direction"` → sinon 403
3. Le endpoint `get_direction_dashboard()` est purement orchestrateur :
   → il ne fait **aucun** appel ML, LLM, ni accès base de données
   → il **compose** 3 sources de vérité déjà en mémoire ou sur disque
4. Source 1 : scores pré-calculés en mémoire
   → `get_all_scores()` renvoie `{id → ScoreData}` depuis le singleton
   → aucun appel XGBoost, aucune ré-inférence
5. Source 2 : log coût LLM sur disque
   → `read_cost_log(since=get_first_of_month())` scanne `data/llm_cost_log.jsonl`
   → le fichier fait quelques KB, lecture séquentielle quasi instantanée
   → `read_cost_log(since=get_24h_ago())` fait le même travail avec un filtre différent
6. Source 3 : clients en mémoire
   → `get_all_clients()` renvoie `list[dict]` depuis le singleton
   → indexé par id en O(1) pour enrichir le top 10
7. Agrégation Python :
   → compte urgences, calcule pourcentages, score moyen, taux churn
   → trie les scores décroissants, prend les 10 premiers
   → enrichit chaque top avec prenom/nom/region du client
8. Retour : `DashboardKPI` Pydantic validé automatiquement
     ↓
Le endpoint renvoie en ~1 ms sur 1000 clients. Zéro I/O base, zéro inférence,
zéro appel réseau. Juste de la composition de données déjà payées au boot.

### Détails techniques clés

- **Pattern "vue agrégée pure"** : composition sans mutation, sans effet de bord
- **Hexagonal strict** : routes.py (centre) consomme llm_cost.py (adapter infra) + scoring (centre)
- **Changement de stockage transparent** : passer de JSONL à Postgres ne change que `read_cost_log()`, pas routes.py
- **Scalabilité limitée mais claire** : si le portefeuille passe à 1M clients, `get_all_scores()` ne tient plus en mémoire → c'est à ce moment-là qu'on introduit une base, pas avant
- **Trade-off assumé** : simplicité maintenant, migration en 2027 si besoin

---

## Infra E. Monitoring Evidently, adapter branché à chaud

### Scénario : la dérive des données est calculée et exposée

### Flux pas à pas

1. Au boot du serveur, le lifespan appelle `run_drift_report()`
   → Lit `clients_baseline.csv` (snapshot d'entraînement, 1000 lignes)
   → Lit `clients_current.csv` (données actuelles simulées, 1000 lignes)
   → Garde seulement 6 features numériques (exclut id, nom, prénom, région, canal, churn)
2. Evidently construit un `Report(metrics=[DataDriftPreset()])`
   → Pour chaque feature, applique un test statistique adapté
   → Wasserstein distance pour les features avec distribution continue
   → Chi² pour les catégorielles (si présentes)
   → Compare les distributions baseline vs current
3. Evidently détermine le verdict global :
   → Si plus de 50% des features ont dérivé → `dataset_drift = True`
   → Sinon → `dataset_drift = False`
4. Le résultat est extrait sous forme de dict :
   → `drift_detected`, `nb_features_drifted`, `nb_features_total`
   → `drifted_features` : liste des noms de features dérivées
   → `share_drifted` : ratio entre 0.0 et 1.0
   → `computed_at` : timestamp ISO
5. Deux fichiers HTML sont écrits sur disque :
   → `data/evidently_reports/drift_<timestamp>.html` : rapport historisé
   → `data/evidently_reports/latest.html` : rapport courant
6. Le dict de synthèse est mis en cache mémoire via `_LAST_REPORT`
7. Chaque GET /dashboard/direction lit ce cache (instantané)
8. Chaque POST /monitoring/drift/recompute refait le cycle complet (quelques centaines de ms)
     ↓
Le monitoring est en place. Il tourne automatiquement au boot et à la demande. Les 3 features dérivées (solde_moyen, nb_interactions_90j, derniere_interaction_jours) sont visibles dès le premier chargement du dashboard. Le rapport HTML complet est consultable en 1 clic.

### Détails techniques clés

- **Adapter hexagonal pur** : `drift.py` ne connaît ni le dashboard ni les endpoints
- **Changement d'outil = 1 fichier** : si on remplace Evidently par Nannyml ou Alibi Detect, on change uniquement `drift.py`
- **Deux usages d'une même source** : la synthèse JSON (pour le dashboard) et le HTML brut (pour le rapport détaillé)
- **Cache mémoire optimiste** : zéro recalcul par requête, re-exécution explicite
- **Point d'injection incident 2** : `scripts/init_db.py` qui charge actuellement baseline → changement vers current déclenchera la dérive dans le modèle réel

---

# BRIQUES CONSTRUITES (ordre numérique)

Cette section documente chaque brique avec ses décisions techniques, ses pièges
évités, ses métriques, et son flux pas à pas.

---

## Brique 1. LLMProvider + OpenRouter

Statut : livrée et validée en local, 20 octobre 2026.

### Objectif

Construire une interface abstraite pour parler à n'importe quel LLM, avec une
première implémentation OpenRouter robuste pour la production.

### Fichiers créés

```
app/llm/
├── __init__.py              Expose les classes publiques
├── base.py                  Interface abstraite LLMProvider + dataclass LLMResponse
├── pricing.py               Dict de pricing OpenRouter + estimate_cost_usd()
└── adapters.py              OpenRouterProvider async + HouseSLMProvider stub + factory

app/monitoring/
└── llm_cost.py              log_llm_call() vers data/llm_cost_log.jsonl
```

### Flux pas à pas (voir aussi Infra B)

**Scénario : premier appel LLM depuis le code**

1. L'app appelle `provider = get_llm_provider()` (factory)
   → retourne `OpenRouterProvider(model="meta-llama/llama-3.3-70b-instruct")`
2. L'app appelle `await provider.complete(prompt, system, max_tokens, temperature)`
3. Le provider utilise son `httpx.AsyncClient` singleton
4. POST vers `https://openrouter.ai/api/v1/chat/completions`
5. Retry 3 fois avec backoff si 429 ou 5xx
6. Timeout 30 secondes
7. Retourne `LLMResponse` avec text, model, tokens, cost_usd, latency_ms
8. `log_llm_call()` écrit la ligne JSONL
     ↓
L'appelant obtient une réponse structurée, le coût est tracé automatiquement.

### Design decisions

| Décision | Choix | Raison |
|---|---|---|
| Interface abstraite | `LLMProvider` ABC | Permet bascule SLM maison en changeant 1 ligne |
| Mode d'appel | Async (`httpx.AsyncClient`) | Cohérent avec FastAPI async |
| Session httpx | Singleton partagé | Évite handshake TLS à chaque appel (environ 50 ms économisés) |
| Retry | 3 fois avec backoff 1-2-4s | Résiste aux 429 et 5xx |
| Timeout | 30 secondes | Suffisant pour Llama 70B en charge |

### Métriques réelles validées

```json
{
  "ts": "2026-10-20T09:55:49.688167",
  "model": "meta-llama/llama-3.3-70b-instruct",
  "prompt_tokens": 68,
  "completion_tokens": 54,
  "cost_usd": 3.7e-05,
  "latency_ms": 594
}
```

### Tips

> Tip. Singleton httpx. Chaque `httpx.AsyncClient()` ouvre un pool. Un singleton
> réutilise la connexion TCP, environ 50 ms économisés par appel. Sur 1000 appels
> par jour : 50 secondes économisées quotidiennement.

> Tip. Retry seulement sur 429 et 5xx. 4xx hors 429 = erreur client, retry inutile.
> 429 = rate limit, retry peut passer. 5xx = serveur, retry peut passer.
> Règle d'or : jamais retry une erreur dont la cause ne va pas disparaître.

---

## Brique 2. Cache LRU + explain service

Statut : livrée et validée en local, 20 octobre 2026.

### Objectif

Construire une couche de cache intelligent pour ne pas rappeler le LLM
inutilement, et un service d'explication qui orchestre cache et LLM.

### Fichiers créés

```
app/llm/
└── cache.py                 Classe TTLCache + build_cache_key()

app/core/
└── explain_service.py       Service explain_score() (portera incident 1)
```

### Flux pas à pas

**Scénario : `await explain_score(client_id, prénom, nom, score, top_features)` est appelé**

1. Construction de la cache key : `hash(client_id, features, model)`
2. Lookup dans `_explanation_cache.get(cache_key)` :
   → cache HIT : retour en environ 5 ms, from_cache=True, cost_usd=0.0
   → cache MISS : continuer
3. Construction du prompt user via `_build_user_prompt()` :
   → nom, prénom, score formaté en pourcentage, features en bullet points
4. Appel `provider.complete(prompt, system=SYSTEM_PROMPT, max_tokens=300, temperature=0.3)`
5. Mise en cache de la réponse avec TTL 86400 s
   → stocke `{text, model, original_latency_ms}`
6. Retourne `ExplanationResult(text, model_used, prompt_tokens, completion_tokens, cost_usd, from_cache=False, latency_ms)`
     ↓
Le prochain appel pour le même client (features identiques, même modèle) sera un HIT.

### Note approche B, incident 1

Le service contient 3 variables sensibles qui seront modifiées en semaine 4 :

- `CACHE_TTL_SECONDS` (actuellement 86400)
- `SYSTEM_PROMPT` (actuellement environ 150 tokens)
- `MAX_TOKENS` (actuellement 300)

Aucun marqueur dans le code. Documentation uniquement dans le playbook privé.

### Métriques réelles validées

Test 1, Marie, cache MISS : 329 + 124 tokens, 0.000125 USD, 2922 ms.
Test 2, Marie, cache HIT : 0 tokens, 0.0 USD, environ 5 ms.
Test 3, Karim, cache MISS, client différent : 264 + 146 tokens, 0.000119 USD, 6890 ms.

Hit rate final : 1/3 = 0.333. En production, projection 0.93 avec 1000 clients consultés plusieurs fois par jour.

### Tips

> Tip. JSON déterministe pour hashing. `json.dumps({"a": 1, "b": 2})` et
> `json.dumps({"b": 2, "a": 1})` donnent des strings différentes. Toujours
> `json.dumps(obj, sort_keys=True)` quand on hashe un dict.

> Tip. Modèle dans la cache key. Pendant la démo du talk, tu peux basculer
> Llama 70B vers Qwen 7B. Changer de modèle = clés différentes = explications
> fraîches. Benchmark non biaisé.

---

## Brique 3. Dataset + XGBoost + SHAP

Statut : livrée et validée en local, 20 octobre 2026.

### Objectif

Construire la fondation ML. Dataset synthétique de 1000 clients, modèle XGBoost
de scoring churn, explainer SHAP pour les contributions features.

### Fichiers créés

```
scripts/
├── generate_fake_data.py    Génère baseline + current (avec dérive incident 2)
└── train_models.py          Entraîne XGBoost + SHAP + sérialise reco rules

app/ml/
├── churn_model.py           load_model() + predict_churn() + urgence_from_score()
├── shap_explainer.py        load_explainer() + get_top_features(top_n=5)
└── reco_model.py            Scaffolding stub, implémenté en brique 10c

models/
├── xgboost_churn.pkl        Modèle XGBoost sérialisé
├── shap_explainer.pkl       SHAP TreeExplainer sérialisé
└── reco_model.pkl           Dict de règles métier reco

data/
├── clients_baseline.csv     1000 clients baseline (7.3 pourcent churners)
└── clients_current.csv      1000 clients AVEC dérive (63.6 pourcent churners)
```

### Flux pas à pas

**Scénario : premier scoring d'un client en isolation**

1. `features = {anciennete_mois: 48, produits_detenus: 1, solde_moyen: 850, ...}`
2. `score = predict_churn(features)` :
   → récupère le singleton `_model` chargé via `load_model()`
   → prépare un DataFrame avec les 7 colonnes dans l'ordre `FEATURE_ORDER`
   → appelle `_model.predict_proba(df)[:, 1][0]`
   → retourne un float entre 0.0 et 1.0
3. `urgence = urgence_from_score(score)` :
   → mapping : score >= 0.7 → "high", >= 0.4 → "medium", sinon "low"
4. `top5 = get_top_features(features, top_n=5)` :
   → récupère le singleton `_explainer` chargé via `load_explainer()`
   → calcule les SHAP values pour cette instance
   → trie par valeur absolue, retourne les 5 plus importantes
   → chaque entrée : `{feature, value, shap_value, direction}` où direction = "+" ou "-"
     ↓
On a un score, une urgence, et les 5 features qui expliquent le score.

### Comprendre XGBoost, SHAP et LLM

Les 3 acteurs ont des rôles différents :

- **XGBoost (le devin)** : donne un score 0.0 à 1.0. Boîte noire, ne dit pas pourquoi.
- **SHAP (le détective)** : n'est pas un modèle ML. Algorithme mathématique qui analyse XGBoost pour attribuer à chaque feature sa contribution. Preuve : SHAP n'a pas de `.fit()`.
- **LLM (le traducteur)** : transforme les shap_values en français lisible. Ne calcule rien, reformule.

En une phrase pour un étudiant : **XGBoost dit COMBIEN, SHAP dit POURQUOI, LLM dit COMMENT l'expliquer à un humain**.

### Les 7 features

| Numéro | Feature | Signal churn |
|---|---|---|
| 1 | `anciennete_mois` | Peu ancien = plus volatile |
| 2 | `produits_detenus` | Un seul produit = faible engagement |
| 3 | `solde_moyen` | Solde bas = client fragile |
| 4 | `nb_interactions_90j` | **Le plus fort signal** |
| 5 | `derniere_interaction_jours` | Trop ancien = décroche |
| 6 | `age_client` | Jeune = plus volatile |
| 7 | `canal_prefere` | Téléphone = moins digital |

### Métriques réelles validées

```
Accuracy          : 0.965
AUC-ROC           : 0.944
Precision churner : 0.83
Recall churner    : 0.67

Client sain   : score = 0.000 (low)
Client risque : score = 0.999 (high)
Delta         : 0.999, séparation parfaite

Top SHAP sur client à risque:
  1. nb_interactions_90j      = 1     | shap = +3.770
  2. solde_moyen              = 850.0 | shap = +1.115
  3. produits_detenus         = 1     | shap = +1.001
  4. canal_prefere            = 3     | shap = +0.763
  5. derniere_interaction_j   = 75    | shap = +0.515
```

### Pièges évités

> Piège. Ordre des features critique. XGBoost attend un ordre précis. Si tu lui
> passes les features dans le mauvais ordre, il mélange les valeurs sans erreur
> Python. Prédictions aberrantes silencieuses. Solution : constante `FEATURE_ORDER`.

> Piège. Dataset déséquilibré. 3.8 pourcent de churners au début, XGBoost prédit
> "stable" tout le temps. Rééquilibrer à environ 15-35 pourcent + `scale_pos_weight`.

---

## Brique 4. Auth + session cookies

Statut : livrée et validée en local, 20 octobre 2026.

### Objectif

Authentification avec 3 users hardcodés, mots de passe hashés bcrypt, et
session cookie signé via Starlette.

### Fichiers créés ou modifiés

```
app/auth/
├── __init__.py              Expose User et dépendances publiques
├── models.py                Dataclass User + modèles Pydantic
├── users.py                 get_user_by_username() + verify_password() via bcrypt
├── session.py               login_user, logout_user, get_current_user (Depends)
└── routes.py                POST /auth/login, POST /auth/logout, GET /auth/me

app/
├── main.py                  SessionMiddleware activé + auth_router inclus
└── config.py                DEMO_USERS enrichi avec password_hash bcrypt
```

### Flux pas à pas : voir Étape 1 et Étape 6 du parcours utilisateur ci-dessus

### Design decisions

| Décision | Choix | Raison |
|---|---|---|
| Mécanisme | Session cookie signé (SessionMiddleware) | Simple, pas de JWT, parfait POC |
| Stockage users | Dict Python dans config.py | Pas de table users SQLite pour un POC |
| Hash password | bcrypt rounds=12 | Standard sécurité, défense brute-force |
| Durée session | 86400 s (24h) | Confort démo et tests |
| Pattern | Dependency injection FastAPI | Testable sans démarrer FastAPI |

### Les 3 utilisateurs de démo

| Username | Password | Role | Région |
|---|---|---|---|
| `conseiller_lille` | `conseiller_lille2026` | conseiller | lille |
| `conseiller_marseille` | `conseiller_marseille2026` | conseiller | marseille |
| `direction` | `direction2026` | direction | voit tout |

### Tips

> Tip. bcrypt rounds=12. Volontairement lent (environ 100 ms) : défense native
> contre brute-force. Attaquant limité à environ 10 tentatives par seconde.

> Tip. Timing attack defense. Si l'user n'existe pas, bcrypt bidon avant False.
> Timing uniforme = sécurité.

> Tip. Message d'erreur générique. "Identifiants invalides" au lieu de "Password
> incorrect". Défense contre l'énumération de comptes.

> Piège. Hash bcrypt stocké en str au lieu de bytes. `ValueError: Invalid salt`
> au `bcrypt.checkpw()`. Solution : toujours `b'$2b$12$...'` dans le dict.

---

## Brique 5. RBAC + /clients/mine

Statut : livrée et validée en local, 20 octobre 2026.

### Objectif

Contrôle d'accès basé sur les rôles et premier endpoint métier : `GET /clients/mine`.
Portera l'incident 3 en semaine 4.

### Fichiers créés ou modifiés

```
app/auth/
└── rbac.py                  require_role() + require_conseiller/direction + filter_clients_by_user

app/core/
├── clients.py               load_clients() + get_all_clients() + get_client_by_id()
├── routes.py                GET /clients/mine
└── schemas.py               ClientSummary + ClientWithUrgence

app/main.py                  load_clients() dans lifespan + core_router inclus
```

### Flux pas à pas : voir Étape 2 du parcours utilisateur et Infra C

### Note approche B, incident 3

La fonction `filter_clients_by_user()` contient la ligne inversée en semaine 4 :

```python
return [c for c in clients if c["region"] == user.region]
```

Aucun marqueur dans le code. Modification `==` → `!=` dans le playbook privé.

Impact prévu : Marie (Lille) voit les clients Marseille et inversement. Détection
immédiate, risque RGPD.

### Tests réels validés

| Rôle | Clients visibles | Régions |
|---|---|---|
| conseiller_lille | 489 | {lille} |
| conseiller_marseille | 511 | {marseille} |
| direction | 1000 | {lille, marseille} |

**489 + 511 = 1000**. Aucun client oublié ni doublé.

### Tips

> Tip. Dépendances vs Middleware. Un middleware global intercepte tout. Une
> dépendance FastAPI est locale, auto-documentée, testable isolément. Pour un
> POC avec peu de règles, les dépendances gagnent.

> Tip. Validation croisée. Vérifier 489 + 511 = 1000. C'est le vrai test d'un
> filtre régional : aucun client ne doit disparaître ni apparaître en double.

---

## Brique 6. Front conseiller V2 UX premium

Statut : livrée et validée en local, 20 octobre 2026.

### Objectif

Construire la première interface utilisateur. Deux étapes de construction :
d'abord un front fonctionnel (brique 6 initiale), puis une refonte V2 UX
inspirée Apple HIG pour atteindre un niveau produit premium.

### Fichiers créés ou modifiés

```
static/shared/
├── login.html               Page de connexion (formulaire centré)
├── login.js                 Logique login + redirection selon rôle
└── style.css                Design system complet enrichi V2 (tokens Apple HIG)

static/conseiller/
├── index.html               Dashboard V2 : topbar + sidebar + main
└── app.js                   Logique JS complète (state, filtres, rendu, checklist)
```

### Flux pas à pas : voir Étape 2 à 5 du parcours utilisateur

### Évolution V1 vers V2 UX

**V1 fonctionnelle (livrée initialement)**

- Table HTML plate avec 7 colonnes
- 489 lignes affichées, scroll vertical imposé
- Fiche détaillée en liste `<li>` sans hiérarchie
- Placeholders textuels pour les sections LLM et recos

**V2 UX premium (refonte)**

- Layout grid : topbar 56px + sidebar 320px + main scrollable
- Sidebar : recherche live + 3 pills urgence + liste 2 lignes par client + puce couleur
- Hero zone : nom en 22px + méta + gauge circulaire SVG 72px avec stroke-dasharray animé
- 4 KPI cards : icône SVG + valeur grosse (24px) + sous-label petit (11px), pattern Apple HIG
- Section SHAP : liste propre avec flèches directionnelles colorées
- Section Analyse Tempo : bulle de chat avec header "Tempo Analyst" + input désactivé "bientôt"
- Section Recos : checklist cliquable, état persisté dans localStorage par client_id

### Design decisions V2

| Décision | Choix | Raison |
|---|---|---|
| Framework CSS | CSS vanilla sobre | Pas de dépendance, cohérent avec style Khayav |
| JS | fetch() vanilla + état global `state` | 300 lignes max, pas de framework |
| Login | Page séparée | Standard, URLs claires |
| Sidebar | Fixe 320px à gauche | Conseiller switche entre clients en permanence |
| Recherche | Champ texte simple + 3 pills urgence | Pas d'overengineering |
| Badge score | Gauge circulaire SVG | Apple feel, lisible en 0.3 seconde |
| KPI cards | Icône + valeur grosse + label petit | Pattern Apple HIG classique |
| Bulle LLM | Header "Tempo Analyst" + bulle + input désactivé | Prépare le futur chat conseiller |
| Recos | Checklist avec persistance localStorage | Ergonomie terrain |
| Palette | Muted banking + neutres enrichis | Hiérarchie typographique à la Apple |

### Palette CSS V2

```css
/* Neutres Apple HIG */
--text-primary:   #1a1a1a;
--text-secondary: #4a4a4a;
--text-tertiary:  #8a8a8a;
--text-quaternary:#b4b4b4;

--surface-0:      #fafaf7;  /* fond */
--surface-1:      #ffffff;  /* cards */
--surface-2:      #f3f3f0;  /* zones secondaires */
--surface-3:      #e8e8e4;  /* hover */

/* Couleurs métier (existantes, conservées) */
--accent:         #2d4a66;  /* bleu banking */
--highlight:      #8b7355;  /* brun alertes */
--success:        #4a6a4a;  /* vert validations */
--danger:         #9c3b3b;  /* rouge erreurs */
```

Aucun emoji. Textes sobres. Niveau produit banking réel.

### Tips

> Tip. URLs relatives dans les fetch. `fetch('/auth/me')`, pas
> `http://localhost:8000/auth/me`. En prod sur Render, zéro config, le front
> et l'API sont servis par le même domaine.

> Tip. credentials same-origin. Dans tous les fetch pour que le cookie session
> soit envoyé automatiquement. Sans ça, 401 même après login.

> Tip. localStorage pour la persistance utilisateur. Les cases cochées des recos
> sont stockées en `localStorage['tempo_done_recos']` indexées par client_id.
> Zéro aller-retour serveur, UX immédiate.

> Tip. Gauge SVG avec stroke-dasharray. Calcul : circumference = 2 * PI * r.
> `stroke-dashoffset = circumference * (1 - scorePct / 100)`. Animation fluide
> avec transition CSS.

> Piège. Caractères spéciaux dans heredoc Bash sous Windows. Les flèches
> unicode (↑ ↓) peuvent être mal encodées. Vérifier avec `grep -c`.

> Piège. Cache navigateur après refonte. `Uncaught TypeError: Cannot read
> properties of null`. Solution : Ctrl + Shift + R systématique après refonte
> HTML. Ou F12 + Disable cache coché.

---

## Brique 10a. Endpoint /score + pré-scoring

Statut : livrée et validée en local, 20 octobre 2026.

### Objectif

Connecter la couche ML (XGBoost + SHAP de la brique 3) à l'API HTTP, et remplir
les placeholders du front conseiller avec de vrais scores et de vraies features SHAP.

Choix stratégique : pré-scorer tous les clients au démarrage pour éviter les
500 appels XGBoost par listing `/clients/mine`.

### Fichiers créés ou modifiés

```
app/core/
├── scoring.py               NOUVEAU. precompute_all_scores() + get_score() + get_all_scores()
├── routes.py                PATCH. /clients/mine enrichi + /score/{id} implémenté
└── schemas.py               AJOUT. ClientWithUrgence (hérite de ClientSummary)

app/main.py                  PATCH. load_model + load_explainer + precompute_all_scores dans lifespan
```

### Flux pas à pas : voir Étape 3 du parcours utilisateur et Infra A

### Design decisions

| Décision | Choix | Raison |
|---|---|---|
| Scoring strategy | Hybride (pré-scorer au boot) | Boot 1 à 2s, requêtes rapides |
| /clients/mine | Enrichi avec score + urgence | 1 seul appel, toutes les lignes |
| Format /score/{id} | Score + top 5 SHAP | Suffit pour la fiche détaillée |
| Stockage scores | Dict Python en mémoire | Simple, SQLite viendra brique 9 |
| Refus RBAC cross-région | 403 Forbidden | Standard REST |

### Tips

> Tip. Pré-scoring vs lazy loading. 1 à 2 secondes au boot contre 500 appels
> XGBoost par listing. Trade-off assumé : léger boot plus lent contre énorme
> gain en latence utilisateur.

> Tip. RBAC régional sur /score/{id}. Le filtrage de /clients/mine protège la
> liste, mais /score/{id} doit vérifier explicitement. Un conseiller Lille
> connaît un id Marseille et pourrait le fetcher directement. Défense en profondeur.

---

## Brique 10b. Endpoint /explain + cache LLM + audit RGPD

Statut : livrée et validée en local, 20 octobre 2026.

### Objectif

Connecter le service d'explication (brique 2) à l'API HTTP, afficher les
explications LLM dans le front conseiller avec cache HIT/MISS visible,
tracer l'accès dans un log d'audit RGPD séparé.

### Fichiers créés ou modifiés

```
app/monitoring/
└── audit_log.py             NOUVEAU. log_audit_event() vers data/audit_log.jsonl

app/core/
├── routes.py                PATCH. /explain/{id} implémenté avec timeout + fallback
└── schemas.py               PATCH. ExplainResponse enrichi (from_cache, latency, cost, llm_model)

static/conseiller/
└── app.js                   PATCH. Affichage explication + bandeau cache sobre
```

### Flux pas à pas : voir Étape 4 du parcours utilisateur

### Design decisions

| Décision | Choix | Raison |
|---|---|---|
| Payload au service | Équilibré (score + top + prénom + nom) | Pas de surcharge, LLM concis |
| Pré-chauffer cache | Non, lazy aux clics | Pour démo live du talk, cache MISS visible |
| Timeout LLM | 30s + fallback texte | UI jamais bloquée |
| Format réponse | Enrichi (text + cache + latency + cost) | Métadonnées = or du talk |
| Métadonnées front | Bandeau sobre sous bulle | Pédagogique + spectaculaire démo |
| Audit RGPD | Fichier séparé, pas dans log LLM | Hexagonal propre : 2 responsabilités, 2 couches |

### Approche hexagonale appliquée

Point clé pour le talk 1er décembre : **le log coût LLM est dans l'adapter LLM,
le log audit RGPD est dans le centre (endpoint)**. Deux responsabilités distinctes,
deux fichiers distincts, deux couches distinctes. C'est de l'hexagonal appliqué.

### Format audit_log.jsonl

```json
{"ts":"2026-10-20T19:52:14.337","event_type":"explain_requested","username":"conseiller_lille","user_role":"conseiller","client_id":426,"outcome":"success","extra":{"from_cache":false,"model":"meta-llama/llama-3.3-70b-instruct"}}
```

### Tips

> Tip. Audit séparé du log coût. Le log coût LLM vit dans l'adapter (brique 1,
> infra). Le log audit vit dans l'endpoint (brique 10b, centre). L'adapter ne
> sait pas qui est l'user. L'endpoint ne sait pas combien coûte le LLM. Chacun
> son rôle, chacun son fichier.

> Tip. Protected namespace Pydantic. Pydantic v2 réserve le préfixe `model_`.
> `model_used` déclenche un UserWarning. Renommer `llm_model` ou désactiver
> avec `model_config = {"protected_namespaces": ()}`.

> Piège. Venv perdu après pause. `ModuleNotFoundError: No module named 'xgboost'`
> alors que tout marchait. Cause : Git Bash a repris Python 3.13 système.
> Solution : `source venv/Scripts/activate` systématique.

---

## Brique 10c. Endpoint /recommend + règles métier + audit

Statut : livrée et validée en local, 20 octobre 2026.

### Objectif

Connecter le moteur de recommandation (règles métier chargées depuis
`reco_model.pkl` en brique 3) à l'API HTTP. Afficher les 3 actions
prioritaires dans la checklist du front conseiller.

### Fichiers créés ou modifiés

```
app/ml/
└── reco_model.py            REFONTE. load_reco_rules() + recommend_actions() avec eval restreint

app/core/
└── routes.py                PATCH. /recommend/{id} implémenté avec RBAC + audit

app/main.py                  PATCH. load_reco_rules() dans lifespan

static/conseiller/
└── app.js                   PATCH. Checklist stylée avec priorité colorée + persistance localStorage
```

### Flux pas à pas : voir Étape 5 du parcours utilisateur

### Format de reco_model.pkl

```python
{
    'version': '1.0',
    'description': 'Regles metier pour recommander des actions de retention',
    'rules': [
        {
            'condition': 'score_churn >= 0.7 and solde_moyen >= 10000',
            'action': 'RDV conseiller urgent + offre fidelite premium',
            'priorite': 'haute',
            'justification': 'Client a fort potentiel qui part : action commerciale immediate.'
        },
        # ... 4 autres règles
    ]
}
```

### Design decisions

| Décision | Choix | Raison |
|---|---|---|
| Nombre max de recos | 3 | Un conseiller lit 3 actions, pas 10 |
| Priorisation | Haute > Moyenne > Basse (tri Python) | Simplicité, cohérent avec reco_model |
| Format réponse | Juste la liste | Pas de surcharge |
| Chargement pkl | Au boot dans lifespan | Cohérent avec autres modèles |
| Audit RGPD | Oui, cohérent avec /explain | Traçabilité uniforme |

### Sécurité du eval()

Les conditions sont des strings Python. On utilise `eval()` avec contexte
restreint :

```python
eval(condition, {"__builtins__": {}}, context_features_et_score)
```

Acceptable car :
- Les règles ne viennent pas d'input utilisateur
- Elles sont écrites par le data scientist
- Elles sont sérialisées dans un pkl contrôlé
- `__builtins__` vide = pas d'accès à l'environnement
- Exceptions silencieuses = la règle non évaluable retourne False

### Tips

> Tip. Priorité en dict d'ordre. `PRIORITY_ORDER = {"haute": 0, "moyenne": 1, "basse": 2}`.
> `matched.sort(key=lambda r: PRIORITY_ORDER.get(r["priorite"], 99))`. Simple,
> clair, extensible.

> Tip. Fallback règle non évaluable. Si `eval()` plante (feature manquante, règle
> mal formée), la règle retourne False silencieusement avec un warning. Le moteur
> continue, le conseiller voit les autres recos.

---

## Brique 7. Dashboard direction V2 UX premium

Statut : livrée et validée en local, 22 octobre 2026.

### Objectif

Construire la vue direction du produit. Deux cibles sur une même page : le
Comex (voix business, répartition d'urgence, taux churn prédit, portefeuille)
et la DSI (voix technique, coûts LLM, hit rate cache, latence moyenne). Le but
est de boucler le produit avant la démo Sloan, en appliquant la même grammaire
V2 UX premium que la vue conseiller.

### Fichiers créés ou modifiés

```
app/monitoring/
├── llm_cost.py              Nettoyé approche B + ajout read_cost_log()
└── drift.py                 Nettoyé approche B (incident 2 reste dans le code sain)

app/core/
├── schemas.py               Ajout TopClientEntry, PortfolioStats, MLOpsStats, DashboardKPI enrichi
└── routes.py                Implémentation complète de GET /dashboard/direction

static/direction/
├── index.html               Refonte V2 UX : topbar + sections business + ML Ops + top 10
└── app.js                   Rendu complet : donut SVG, 4 KPI cards, top 10 cliquable
```

### Flux pas à pas : voir Étapes D1 à D3 du parcours utilisateur direction + Infra D

### Les 7 décisions prises

| Décision | Choix | Raison |
|---|---|---|
| Calcul des KPI | À chaque requête | 1 ms sur 1000 clients, pas d'optim prématurée |
| Visualisations | SVG inline sobre | Cohérent avec gauge brique 10a, zéro dépendance externe |
| Top clients à risque | Top 10 toutes régions | Simplicité pour la démo Sloan |
| Période coûts LLM | Mois courant + 24h glissantes | 2 cartes : Comex (budget mensuel) + DSI (détection explosion) |
| Refresh de la page | Statique + bouton Actualiser | C-level feel, pas de polling intempestif |
| Drill-down top 10 | Clic → ouvre vue conseiller | Réutilise V2 UX existante, zéro code dupliqué |
| Switch direction → conseiller | Bouton "Vue conseiller" en topbar | Direction peut explorer, conseiller ne peut pas inversement |

### Structure de la réponse `/dashboard/direction`

```json
{
  "portfolio": {
    "total_clients": 1000,
    "nb_high": 142, "nb_medium": 237, "nb_low": 621,
    "pct_high": 14.2, "pct_medium": 23.7, "pct_low": 62.1,
    "score_moyen": 0.342,
    "taux_churn_predit": 14.2
  },
  "ml_ops": {
    "cost_llm_mois_courant_usd": 0.00037,
    "cost_llm_24h_usd": 0.00037,
    "nb_appels_mois": 3,
    "nb_appels_24h": 3,
    "hit_rate_pct": 33.3,
    "avg_latency_ms": 3302,
    "last_call_at": "2026-10-22T09:12:33"
  },
  "top_clients_risque": [
    {"id": 426, "prenom": "...", "nom": "...", "region": "Lille", "score_churn": 0.94, "urgence": "high"}
  ]
}
```

### Visualisations SVG inline

**Donut 3 arcs** (répartition urgence)

Technique : 3 cercles SVG concentriques avec `stroke-dasharray` qui définit la longueur de l'arc et `stroke-dashoffset` qui définit où il commence. Chaque arc commence là où le précédent s'arrête (offset négatif cumulé). Le total au centre est écrit en `<text>` SVG. Le groupe entier est tourné de -90° pour que le premier arc parte du haut.

**Barres horizontales** (top 10)

Chaque ligne a une barre colorée dont la largeur est proportionnelle au score du client, normalisée sur le score max du top 10. Couleurs : danger pour high, highlight pour medium, success pour low. La flèche à droite indique la cliquabilité.

### Pattern archi hexagonale

Le dashboard direction est un **exemple parfait** du pattern hexagonal pour le talk :

- **Adapter technique** `app/monitoring/llm_cost.py` : `read_cost_log()` scanne le JSONL. Ne connaît pas qui l'appelle.
- **Centre métier** `app/core/routes.py` : `get_direction_dashboard()` agrège les 3 sources. Ne connaît pas comment c'est stocké.
- **Adapter présentation** `static/direction/app.js` : `renderDonut()`, `renderPortfolioSection()`. Ne connaît pas d'où viennent les données.

**Démonstration en 1 phrase** : si demain on migre `llm_cost_log.jsonl` vers Postgres, on change **uniquement** `read_cost_log()`. `routes.py` et `app.js` ne bougent pas. **C'est ça l'archi hexagonale appliquée à l'IA.**

### Nettoyage approche B

Au moment de livrer la brique 7, deux fichiers contenaient encore des commentaires `INCIDENT` inline :

- `app/monitoring/llm_cost.py` → commentaire INCIDENT 1 sur la facture LLM
- `app/monitoring/drift.py` → commentaire INCIDENT 2 sur la dérive

Les deux ont été nettoyés en même temps que la brique 7. Un `grep -rn "INCIDENT" app/ --exclude-dir=__pycache__` renvoie désormais **zéro ligne**. L'approche B est officiellement pure dans le code source.

### Tips

> Tip. Toujours un `Path()` wrapper dans les adapters. `LLM_COST_LOG_PATH`
> est une string dans config.py. L'adapter `read_cost_log()` l'enveloppe en
> `log_path = Path(LLM_COST_LOG_PATH)` au point d'usage. Démarcation claire
> entre config (plate) et usage (objet).

> Tip. Donut SVG rotation -90°. Un cercle SVG commence son arc à 3h.
> `transform="rotate(-90 cx cy)"` sur le groupe le fait commencer à 12h,
> ce qui est l'attente visuelle d'un camembert.

> Tip. `stroke-dasharray="length circumference"` et offset cumulé. La longueur
> de l'arc est le 1er paramètre, l'espace blanc après est le 2e. Mettre la
> circumference entière comme 2e paramètre garantit un seul arc visible.

> Tip. Ouverture dans un nouvel onglet avec `window.open(url, '_blank')`.
> Le même cookie session est transmis automatiquement. Zéro travail d'auth
> à refaire entre dashboard direction et vue conseiller.

> Piège. Heredoc Bash tronqué sur Git Bash Windows. Un gros bloc JS avec
> template literals `${...}` peut faire fermer le heredoc prématurément.
> Solution : passer par `python << PYEOF` avec `Path.write_text()`.

> Piège. Cache navigateur agressif même après Ctrl+Shift+R. Si le fichier
> est à jour sur disque mais l'erreur pointe sur l'ancien code, ouvrir
> une fenêtre privée Ctrl+Shift+N. Zéro cache possible.

### Métriques

- Latence serveur `/dashboard/direction` : ~1 ms sur 1000 clients
- Zéro appel ML, zéro appel LLM
- Taille des fichiers : index.html 7 KB, app.js 11 KB, routes.py +120 lignes
- Donut SVG : 140×140 pixels, 4 cercles concentriques, zéro dépendance

---

## Brique 8. Monitoring Evidently + détection de dérive

Statut : livrée et validée en local, 22 octobre 2026.

### Objectif

Mettre en place une détection automatique de dérive des données via Evidently.
Le monitoring compare les features actuelles à une baseline d'entraînement, et
alerte visuellement dans le dashboard direction si les distributions ont trop
bougé. **C'est la brique qui prépare le narratif de l'incident 2 pour le talk** :
la dérive sera visible dans le dashboard depuis plusieurs semaines, mais sans
alerte proactive personne ne la verra avant que le modèle commence à sous-performer.

### Fichiers créés ou modifiés

```
requirements.txt            Ajout evidently==0.4.37
app/config.py               CLIENTS_BASELINE_CSV + CLIENTS_CURRENT_CSV
app/monitoring/drift.py     Réécriture complète : DataDriftPreset + cache mémoire
app/core/schemas.py         Ajout DriftStats, DashboardKPI enrichi
app/core/routes.py          Import Path, drift dans dashboard, 2 nouveaux endpoints
app/main.py                 run_drift_report au boot (lifespan)
static/direction/index.html CSS .drift-feature + .drift-features
static/direction/app.js     renderDriftSection + binding bouton recompute
data/evidently_reports/     Dossier auto-créé : latest.html + rapports historisés
```

### Flux pas à pas : voir Étape D4 du parcours direction + Infra E

### Les 7 décisions prises

| Décision | Choix | Raison |
|---|---|---|
| Quand lancer la détection | Hybride : au boot + endpoint recalcul manuel | Résultat immédiat au premier appel + flexibilité démo |
| Méthode statistique | DataDriftPreset Evidently | Standard de la lib, HTML beau out of the box |
| Seuil de détection | 50% par défaut Evidently + liste features exposée | Comex voit "OK / Détecté", DSI voit la liste précise |
| Stockage rapport HTML | latest.html + historique daté | Dashboard pointe sur latest, brique 9 pourra lister l'historique |
| Où placer le service | drift.py existant complété | Pattern cohérent avec llm_cost.py |
| UX dans le dashboard | Enrichir dashboard + lien rapport | Minimum viable, maximum visuel |
| Source des données current | Fichier clients_current.csv fixe | Déjà prévu comme point d'injection incident 2 |

### Structure de la réponse `/dashboard/direction` (bloc drift)

```json
"drift": {
  "drift_detected": true,
  "nb_features_drifted": 3,
  "nb_features_total": 6,
  "drifted_features": [
    "derniere_interaction_jours",
    "nb_interactions_90j",
    "solde_moyen"
  ],
  "share_drifted": 0.5,
  "computed_at": "2026-10-22T13:00:34.464347",
  "report_available": true
}
```

### Les 2 nouveaux endpoints

- **POST /monitoring/drift/recompute** (direction only) : force un recalcul Evidently complet, met à jour `_LAST_REPORT` en mémoire + régénère latest.html
- **GET /monitoring/drift/report** (direction only) : sert le HTML Evidently latest.html directement dans le navigateur via HTMLResponse

### Pattern archi hexagonale

La brique 8 est **le troisième exemple hexagonal du projet**, après l'adapter LLM (brique 1) et l'adapter log coût (brique 7). Elle complète la démonstration pour le talk :

- **Adapter technique** `app/monitoring/drift.py` : contient tout le code Evidently. Signature `run_drift_report(reference_df=None, current_df=None)`. Si on remplace Evidently par Nannyml ou Alibi Detect demain, on change **ce fichier et rien d'autre**.
- **Centre métier** `app/core/routes.py` : consomme `run_drift_report()` et `get_last_drift_report()` comme boîtes noires. Ne connaît pas Evidently.
- **Adapter présentation** `static/direction/app.js` : `renderDriftSection()` affiche. Ne connaît pas l'adapter technique.
- **Bonus production** : le même adapter sert 2 formats de sortie (dict JSON synthétique pour le dashboard, HTML brut pour le rapport détaillé). **Un adapter, deux consommateurs, zéro duplication.**

### Résultat observé (données du jour)

Sur les 6 features numériques testées (age_client, anciennete_mois, produits_detenus, solde_moyen, nb_interactions_90j, derniere_interaction_jours), **3 ont dérivé** :

- **solde_moyen** : les clients actuels ont des soldes significativement plus faibles
- **nb_interactions_90j** : moins d'interactions récentes en moyenne
- **derniere_interaction_jours** : les clients contactent moins souvent, l'écart depuis la dernière interaction s'est allongé

**Interprétation métier** : les clients deviennent moins actifs et moins engagés. **Signal fort de churn à venir.** Le modèle, entraîné sur une baseline où les clients étaient plus actifs, va avoir tendance à sous-estimer le risque de churn sur ces nouveaux profils.

### Narratif pour le talk 1er décembre

Le dashboard affiche "DÉTECTÉE" **dès aujourd'hui**. Pas semaine 4, dès maintenant. Pourquoi ?

Parce que les 2 CSV baseline et current sont déjà différents. **Mais le modèle, lui, tourne sur les features de baseline** (celles chargées par `init_db.py`). Donc **la dérive est signalée, mais pas encore impactante**.

**Semaine 4, l'incident 2 déclenche** : `scripts/init_db.py` est modifié pour charger `clients_current.csv` à la place. **À ce moment-là** :
- Le modèle commence à prédire sur des données qui ont dérivé depuis 3 semaines
- Les scores de churn deviennent incohérents (sous-estimés)
- Les clients à risque réel ne sont plus détectés
- Les conseillers appellent les mauvais clients
- La direction découvre le problème en analysant les résultats business

**Diagnostic post-mortem** : "le monitoring avait raison depuis 3 semaines, personne ne regardait le dashboard". **C'est l'histoire de 80% des incidents MLOps en entreprise.**

### Tips

> Tip. Cache mémoire via module-level singleton. `_LAST_REPORT: Optional[dict] = None` au top-level de `drift.py` + `get_last_drift_report()` qui le retourne. Pattern lightweight, zéro dépendance, parfait pour un cache "dernier résultat connu".

> Tip. Signature flexible avec None par défaut. `run_drift_report(reference_df=None, current_df=None)`. Si rien n'est passé, charge les 2 CSV. Permet aux tests unitaires de passer des DataFrames custom tout en gardant un appel ultra-simple en prod.

> Tip. Rapport HTML dual : historisé + latest. Chaque run écrit 2 fichiers : `drift_<ts>.html` pour l'historique + `latest.html` pour l'accès rapide. Dashboard pointe sur latest, brique 9 pourra lister l'historique.

> Tip. HTMLResponse de FastAPI pour servir du HTML brut. Au lieu de retourner un JSON ou de rediriger, `HTMLResponse(content=html, status_code=200)` sert le contenu directement. Parfait pour les rapports générés.

> Piège. Oublier `from pathlib import Path` en top-level. Si Path est utilisé dans un endpoint sans import explicite, NameError au premier appel. Vérifier à l'import : `python -c "from app.core.routes import router"`.

> Piège. Evidently v0.4 vs v0.5 : API différente. En v0.4, `from evidently.report import Report`. En v0.5+, `from evidently import Report`. Figer la version dans requirements.txt (`evidently==0.4.37`).

### Métriques

- Latence calcul initial Evidently au boot : ~500 ms sur 1000 lignes
- Latence GET /dashboard/direction (lecture cache) : ~1 ms
- Latence POST /monitoring/drift/recompute : ~500 ms (recalcul complet)
- Taille rapport HTML Evidently : ~1.5 MB
- 3/6 features détectées comme dérivées (seuil 50% atteint pile)

---


## Brique 9. Scheduler

Statut : à construire.

Objectif prévu : APScheduler avec 3 tâches (alertes bascule risque, check drift, check coûts LLM) + SQLite pour historisation.

---

## Brique 11. Injection des incidents

Statut : semaine 4.

Objectif prévu : appliquer les 3 modifications documentées dans le playbook privé sur une branche `incidents/semaine-4`, puis déployer.

---

# RÉFÉRENCES

---

## Métriques consolidées

### Coûts LLM (session du 20/10/2026)

| Appel | Modèle | Prompt | Completion | Coût | Latence |
|---|---|---|---|---|---|
| B1 test | Llama 70B | 68 | 54 | 0.000037 USD | 594 ms |
| B2 test1 Marie | Llama 70B | 329 | 124 | 0.000125 USD | 2922 ms |
| B2 test3 Karim | Llama 70B | 264 | 146 | 0.000119 USD | 6890 ms |
| TOTAL | | 661 | 324 | 0.000281 USD | - |

### Performance modèle churn (brique 3)

| Métrique | Valeur |
|---|---|
| Accuracy | 0.965 |
| AUC-ROC | 0.944 |
| Precision churner | 0.83 |
| Recall churner | 0.67 |
| F1-score churner | 0.74 |

### Validation RBAC (brique 5)

| Rôle | Clients visibles | Régions |
|---|---|---|
| conseiller_lille | 489 | {lille} |
| conseiller_marseille | 511 | {marseille} |
| direction | 1000 | {lille, marseille} |

**489 + 511 = 1000**. Aucun client oublié ni doublé.

### Pré-scoring (brique 10a)

| Métrique | Valeur mesurée |
|---|---|
| Nombre de clients | 1000 |
| Durée pré-scoring au boot | 1 à 2 secondes |
| Latence `/score/{id}` après boot | moins de 10 ms |
| Latence `/clients/mine` après boot | moins de 50 ms |

### Gains du cache (projection business)

| Scénario | Appels LLM/mois | Coût/mois |
|---|---|---|
| Sans cache | 40 000 | environ 5.00 USD |
| Avec cache hit rate 93 pourcent | 2 800 | environ 0.36 USD |
| Gain | /14 | moins 93 pourcent |

---

## Glossaire technique

**AUC-ROC** : capacité d'un classifier binaire à distinguer les 2 classes. Supérieur à 0.9 égale excellent.

**Backoff exponentiel** : stratégie de retry où le délai double à chaque tentative (1s, 2s, 4s, 8s).

**bcrypt** : hash de mot de passe volontairement lent (environ 100 ms) pour résister au brute-force.

**Cache LRU** : quand plein, vire l'entrée pas utilisée depuis le plus longtemps.

**Closure** : fonction Python qui capture des variables de son environnement.

**Dataclass frozen** : classe Python immutable.

**Dependency Injection (FastAPI)** : FastAPI injecte automatiquement les dépendances via `Depends()`.

**Features** : variables d'entrée d'un modèle ML.

**Hit rate** : taux de succès du cache. Objectif production : supérieur à 80 pourcent.

**Lazy loading** : calculer à la demande au lieu de pré-calculer. Opposé du pré-scoring.

**Pickle** : format de sérialisation Python.

**Pré-scoring** : calculer tous les scores au démarrage. Boot plus lent, requêtes ultra-rapides.

**RBAC (Role-Based Access Control)** : contrôle d'accès basé sur les rôles.

**Scale_pos_weight** : paramètre XGBoost qui donne plus de poids à la classe minoritaire.

**Session cookie signé** : cookie avec donnée + signature cryptographique, vérifiable sans stocker de session en DB.

**SessionMiddleware (Starlette)** : middleware qui gère automatiquement les cookies de session signés.

**SHAP** : méthode mathématique pour attribuer à chaque feature sa contribution. N'est pas un modèle ML, c'est un algorithme d'analyse.

**Singleton** : pattern où une classe ou variable n'a qu'une instance partagée.

**Timing attack** : attaque qui exploite les différences de temps de réponse.

**TreeExplainer** : SHAP optimisé pour les modèles arbres. 1000 fois plus rapide que KernelExplainer.

**TTL** : durée de vie d'une entrée en cache.

**XGBoost** : algorithme d'arbres de décision gradient-boosted. Standard tabulaire.

---

## Journal des pièges évités

### Piège numéro 1. Python 3.14 trop récent pour la stack ML

Symptôme : `pip install -r requirements.txt` échoue sur xgboost/shap.
Solution : Python 3.11 via `py -3.11 -m venv venv`.
Leçon : rester sur Python 3.11 ou 3.12 pour tout projet ML en 2026.

### Piège numéro 2. pricing.py manquant

Symptôme : `ModuleNotFoundError: No module named 'app.llm.pricing'`.
Leçon : `ls -la app/llm/` avant tout test.

### Piège numéro 3. Dataset déséquilibré

Symptôme : XGBoost prédit "stable" tout le temps, recall churner < 0.2.
Solution : rééquilibrer les seuils + `scale_pos_weight`.
Leçon : viser 15 à 35 pourcent de churners pour un dataset de scoring binaire.

### Piège numéro 4. ModuleNotFoundError sur `python scripts/x.py`

Symptôme : `ModuleNotFoundError: No module named 'app'`.
Solution : `sys.path.insert(...)` OU `python -m scripts.x`.

### Piège numéro 5. Dataset non régénéré après modification

Symptôme : `train_models` affiche les mêmes stats après changement de `generate_fake_data.py`.
Solution : commande combinée systématique.

### Piège numéro 6. Heredoc Bash corrompu

Symptôme : fichier incomplet, imports qui plantent.
Solution : `ls -la` + `python -c` d'import après chaque gros heredoc.

### Piège numéro 7. Scaffolding avec commentaires INCIDENT inline

Symptôme : approche B impossible si le code source contient `INCIDENT 3`.
Solution : nettoyer les tags dans `explain_service.py`, `rbac.py`, `routes.py`.
Leçon : décider approche A ou B avant le scaffolding.

### Piège numéro 8. Hash bcrypt stocké en str au lieu de bytes

Symptôme : `ValueError: Invalid salt` au `bcrypt.checkpw()`.
Solution : toujours `b'$2b$12$...'` dans le dict.

### Piège numéro 9. me.nom_affiche inexistant dans le front

Symptôme : header affiche "undefined, lille".
Cause : scaffolding attendait `nom_affiche`, mais `/auth/me` retourne `full_name`.
Leçon : vérifier la cohérence des noms de champs entre backend et front.

### Piège numéro 10. Scaffolding attend des champs qui n'existent pas encore

Symptôme : table affiche `undefined` dans Score et Urgence.
Solution brique 6 : placeholder sobre. Solution brique 10a : enrichir `/clients/mine`.

### Piège numéro 11. Venv Python 3.11 non activé après pause

Symptôme : `ModuleNotFoundError: No module named 'xgboost'` au boot uvicorn alors que tout marchait avant pause.
Cause : Git Bash a repris Python 3.13 système par défaut.
Solution : `source venv/Scripts/activate` + vérifier `which python`.
Leçon : première commande d'une nouvelle session doit être l'activation du venv.

### Piège numéro 12. Hard reload nécessaire après refonte front

Symptôme : `Uncaught TypeError: Cannot read properties of null` sur `getElementById` d'un élément pourtant présent dans le HTML sur disque.
Cause : navigateur sert l'ancienne version depuis son cache.
Solution : Ctrl + Shift + R systématique après refonte HTML.
Leçon : en dev front, laisser F12 ouvert avec "Disable cache" coché.

### Piège numéro 13. Heredoc Bash tronqué sur Git Bash Windows

Symptôme : `cat > fichier.js << 'EOF'` écrit un fichier incomplet, sans erreur visible. Le prompt revient à la ligne au milieu du contenu attendu.
Cause : template literals JS `${...}` perturbent le parsing du heredoc Bash sur Git Bash Windows. Un backtick ou une séquence de caractères peut déclencher la fermeture prématurée.
Solution : pour tout fichier front > 100 lignes avec template literals, passer par `python << 'PYEOF'` avec `Path.write_text()`. Python gère le texte comme un bloc atomique, Bash ne voit qu'une commande simple.
Leçon : les heredocs Bash sont parfaits pour les petits fichiers texte. Pour du code moderne avec interpolations, préférer un wrapper Python.

### Piège numéro 14. Cache navigateur persistant malgré Ctrl+Shift+R

Symptôme : la console affiche une erreur qui pointe sur une ligne de code qui n'existe plus dans le fichier à jour sur disque (par exemple `app.js:18` alors que le nouveau fichier a sa ligne 18 ailleurs).
Cause : le navigateur garde l'ancien JS en cache plus agressivement que prévu, même après hard reload.
Solution : trois niveaux. D'abord Ctrl+Shift+R classique. Ensuite F12 ouvert + onglet Network + case "Disable cache" cochée. En dernier recours : fenêtre privée (Ctrl+Shift+N) qui garantit zéro cache possible.
Leçon : la fenêtre privée est le test imparable. Si ça marche en privée et pas en normal, c'est 100 pourcent du cache.

---

Dernière mise à jour : 22 octobre 2026, après la brique 8 (monitoring Evidently + détection de dérive).
Prochaine mise à jour : à la livraison de la brique 9 (scheduler APScheduler + SQLite historisation).

---
