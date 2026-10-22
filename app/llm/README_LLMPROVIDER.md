# Brique LLMProvider — Dev itératif Tempo Client V2

Première brique de code réel pour Tempo Client V2. Remplace les stubs
`app/llm/base.py` et `app/llm/adapters.py` du scaffolding par ces versions
complètes et testées.

## Fichiers livrés

| Fichier | Destination dans le repo | Rôle |
|---------|--------------------------|------|
| `base.py` | `app/llm/base.py` | Interface abstraite + dataclass + exceptions |
| `pricing.py` | `app/llm/pricing.py` | **NOUVEAU** — Dict de pricing + calcul coût |
| `adapters.py` | `app/llm/adapters.py` | OpenRouterProvider complet + factory |

Et mettre à jour `app/llm/__init__.py` :

```python
from app.llm.base import LLMProvider, LLMResponse, LLMProviderError
from app.llm.adapters import get_llm_provider, close_llm_provider

__all__ = [
    "LLMProvider",
    "LLMResponse",
    "LLMProviderError",
    "get_llm_provider",
    "close_llm_provider",
]
```

## Ce qui est implémenté

### `base.py`
- `LLMResponse` dataclass frozen avec tokens, coût, latence
- Hiérarchie d'exceptions : `LLMProviderError` → `LLMProviderTimeout`, `LLMProviderRateLimit`
- Interface `LLMProvider` async + `provider_name`

### `pricing.py`
- 5 modèles OpenRouter avec pricing réel octobre 2026 :
  - Llama 3.3 70B (standard)
  - Llama 3.1 8B (budget)
  - Qwen 2.5 7B (alternative open-source)
  - Claude 3.5 Haiku (premium)
  - Gemini Flash 1.5 (rapide)
- Fonction `estimate_cost_usd(model, prompt_tokens, completion_tokens)`

### `adapters.py`
- `OpenRouterProvider` async complet :
  - Session `httpx.AsyncClient` partagée (pool connexions)
  - Headers OpenRouter corrects (Authorization + HTTP-Referer + X-Title)
  - Retry 3× avec backoff exponentiel **1-2-4 secondes**
  - Retry UNIQUEMENT sur 429 (rate limit) et 5xx (serveur)
  - Pas de retry sur 4xx (erreur client, inutile)
  - Logs JSON structurés sur chaque appel
  - Mesure de latence
  - Appel au tracker de coûts (`log_llm_call`)
- `HouseSLMProvider` stub pour futur SLM maison
- Factory `get_llm_provider()` avec singleton (réutilise la session httpx)
- `close_llm_provider()` à appeler au shutdown FastAPI
- **Script de test manuel intégré** (`if __name__ == "__main__"`)

## Comment tester

### 1. Mettre à jour le repo
```bash
cd tempo-client-prod
cp /chemin/vers/base.py app/llm/base.py
cp /chemin/vers/pricing.py app/llm/pricing.py
cp /chemin/vers/adapters.py app/llm/adapters.py
# Éditer app/llm/__init__.py comme indiqué ci-dessus
```

### 2. Installer les deps
```bash
pip install -r requirements.txt
```

### 3. Configurer .env
```bash
cp .env.example .env
# Éditer .env et renseigner OPENROUTER_API_KEY
# Récupérer la clé sur https://openrouter.ai/keys
```

### 4. Test manuel
```bash
python -m app.llm.adapters
```

Résultat attendu :
```
[TEST] Provider: openrouter
[TEST] Modèle: meta-llama/llama-3.3-70b-instruct

============================================================
RÉPONSE  : Un modèle de scoring churn bancaire est un algorithme...
============================================================
Modèle   : meta-llama/llama-3.3-70b-instruct
Tokens   : prompt=42 completion=28
Coût     : 2.1e-05 USD
Latence  : 1247 ms
============================================================
```

Et vérifier que `data/llm_cost_log.jsonl` a été créé avec une ligne.

### 5. Tester le retry (optionnel)
Pour simuler un rate limit, utiliser une clé API invalide — tu verras les
3 tentatives dans les logs avant l'exception finale.

## Patterns intégrés

Ce code met en œuvre **4 patterns de ta boîte à outils** issus de l'analyse
SOPHIA / LÉON / Khayav :

1. **Appel LLM via httpx direct** (comme Khayav) — pas de SDK LangChain inutile.
2. **Session réutilisée en singleton** — évite une connexion TCP par appel.
3. **Gestion d'erreurs typées** — remplace les `except: pass` silencieux de SOPHIA.
4. **Logs structurés JSON** — remplace les `print()` de SOPHIA/LÉON/Khayav.

## Prochaine étape

Une fois cette brique validée, on code :
- `/explain/{client_id}` endpoint qui l'utilise (avec cache LRU)
- Puis `/score/{client_id}` (XGBoost + SHAP)
- Puis le front conseiller fonctionnel

**But semaine 1** : `/explain` fonctionne de bout en bout, interface
conseiller affiche l'explication d'un vrai client.
