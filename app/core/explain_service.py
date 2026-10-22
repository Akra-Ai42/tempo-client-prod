"""Service d'explication des scores SHAP via LLM.

Role : transformer un score churn + top features SHAP en une explication
en francais clair a destination du conseiller bancaire.

Flux :
    1. Cle de cache = (client_id, features, model)
    2. Cache HIT -> retour immediat (0 appel LLM, 0 cout)
    3. Cache MISS -> construction prompt + appel LLM + mise en cache
    4. Retour structure (texte + metadonnees de cout)

"""

from dataclasses import dataclass
from typing import Optional

from app.llm.adapters import get_llm_provider
from app.llm.base import LLMProviderError
from app.llm.cache import TTLCache, build_cache_key


# Duree de vie des entrees du cache d'explication (24h).
# Les features d'un client changent peu dans la journee, donc une explication
# generee a 9h reste valable a 17h pour le meme etat du client.
CACHE_TTL_SECONDS = 86400  # 24 heures
CACHE_MAX_SIZE = 2000

# Instance singleton du cache pour tout le process
_explanation_cache = TTLCache(
    max_size=CACHE_MAX_SIZE,
    default_ttl_seconds=CACHE_TTL_SECONDS,
)


@dataclass(frozen=True)
class ExplanationResult:
    """Resultat de la generation d'explication."""
    text: str
    model_used: str
    prompt_tokens: int
    completion_tokens: int
    cost_usd: Optional[float]
    from_cache: bool
    latency_ms: Optional[int] = None


# Prompt systeme qui cadre le role du LLM (banking, francais, concis).
# Garde court (~150 tokens) : chaque mot ajoute se paye a chaque appel.
SYSTEM_PROMPT = """Tu es un assistant pour conseillers bancaires francais.
Tu recois le score de risque de depart (churn) d'un client et ses principales features explicatives.
Ton role : expliquer en francais clair, en 3 a 4 phrases maximum, pourquoi ce client presente ce niveau de risque.
Pas de jargon technique (evite "SHAP", "feature", "modele"). Parle en termes concrets : interactions, produits, anciennete, solde.
Reste factuel. N'invente aucune donnee. Ne suggere pas d'action : seulement l'explication.
"""


def _format_features_for_prompt(top_features: list[dict]) -> str:
    """Transforme les top features SHAP en bullet points lisibles."""
    lines = []
    for f in top_features:
        direction = f.get("direction", "?")
        signe = "augmente" if direction == "+" else "diminue"
        lines.append(
            f"- {f['feature']} = {f['value']} "
            f"({signe} le risque de depart, poids {abs(f['shap_value']):.3f})"
        )
    return "\n".join(lines)


def _build_user_prompt(
    client_prenom: str,
    client_nom: str,
    score_churn: float,
    top_features: list[dict],
) -> str:
    """Construit le prompt utilisateur a partir des donnees du client."""
    features_text = _format_features_for_prompt(top_features)
    return (
        f"Client : {client_prenom} {client_nom}\n"
        f"Score de risque de depart : {score_churn * 100:.0f}%\n\n"
        f"Features explicatives (par ordre d'importance) :\n"
        f"{features_text}\n\n"
        f"Explique en 3-4 phrases maximum."
    )


async def explain_score(
    client_id: int,
    client_prenom: str,
    client_nom: str,
    score_churn: float,
    top_features: list[dict],
    model_override: Optional[str] = None,
) -> ExplanationResult:
    """Genere ou recupere depuis le cache l'explication d'un score."""
    provider = get_llm_provider()
    model = model_override or getattr(provider, "model", "unknown")

    # 1. Chercher dans le cache
    cache_key = build_cache_key(client_id, top_features, model)
    cached = await _explanation_cache.get(cache_key)
    if cached is not None:
        return ExplanationResult(
            text=cached["text"],
            model_used=cached["model"],
            prompt_tokens=0,
            completion_tokens=0,
            cost_usd=0.0,
            from_cache=True,
            latency_ms=cached.get("original_latency_ms"),
        )

    # 2. Cache MISS : construire le prompt et appeler le LLM
    user_prompt = _build_user_prompt(
        client_prenom=client_prenom,
        client_nom=client_nom,
        score_churn=score_churn,
        top_features=top_features,
    )

    # Limite de tokens en sortie. 300 suffit pour 3-4 phrases en francais.
    # Plus eleve = reponses plus longues = plus cher sans valeur ajoutee.
    MAX_TOKENS = 300

    try:
        llm_response = await provider.complete(
            prompt=user_prompt,
            system=SYSTEM_PROMPT,
            max_tokens=MAX_TOKENS,
            temperature=0.3,
        )
    except LLMProviderError:
        raise

    # 3. Mettre en cache
    await _explanation_cache.set(
        key=cache_key,
        value={
            "text": llm_response.text,
            "model": llm_response.model,
            "original_latency_ms": llm_response.latency_ms,
        },
    )

    return ExplanationResult(
        text=llm_response.text,
        model_used=llm_response.model,
        prompt_tokens=llm_response.prompt_tokens,
        completion_tokens=llm_response.completion_tokens,
        cost_usd=llm_response.cost_usd,
        from_cache=False,
        latency_ms=llm_response.latency_ms,
    )


def get_cache_stats() -> dict:
    """Expose les stats du cache."""
    stats = _explanation_cache.stats()
    return {
        "size": _explanation_cache.size(),
        "max_size": CACHE_MAX_SIZE,
        "hits": stats.hits,
        "misses": stats.misses,
        "hit_rate": round(stats.hit_rate, 3),
        "evictions_lru": stats.evictions_lru,
        "evictions_ttl": stats.evictions_ttl,
    }


async def clear_cache() -> None:
    """Vide le cache (endpoint admin)."""
    await _explanation_cache.clear()


# === Script de test manuel ===

if __name__ == "__main__":
    import asyncio
    import logging

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    MARIE_FEATURES = [
        {"feature": "nb_interactions_90j", "value": 1, "shap_value": 0.284, "direction": "+"},
        {"feature": "solde_moyen", "value": 1250.0, "shap_value": 0.192, "direction": "+"},
        {"feature": "anciennete_mois", "value": 48, "shap_value": -0.087, "direction": "-"},
        {"feature": "produits_detenus", "value": 1, "shap_value": 0.142, "direction": "+"},
        {"feature": "derniere_interaction_jours", "value": 67, "shap_value": 0.098, "direction": "+"},
    ]

    KARIM_FEATURES = [
        {"feature": "nb_interactions_90j", "value": 12, "shap_value": -0.215, "direction": "-"},
        {"feature": "solde_moyen", "value": 18500.0, "shap_value": -0.178, "direction": "-"},
        {"feature": "anciennete_mois", "value": 156, "shap_value": -0.134, "direction": "-"},
    ]

    async def _test():
        print("\n" + "=" * 70)
        print("TEST 1 - Marie (cache miss attendu)")
        print("=" * 70)
        result1 = await explain_score(
            client_id=42,
            client_prenom="Marie",
            client_nom="Dupont",
            score_churn=0.87,
            top_features=MARIE_FEATURES,
        )
        print(f"from_cache : {result1.from_cache}")
        print(f"modele     : {result1.model_used}")
        print(f"tokens     : prompt={result1.prompt_tokens} completion={result1.completion_tokens}")
        print(f"cout       : {result1.cost_usd} USD")
        print(f"latence    : {result1.latency_ms} ms")
        print(f"\nTEXTE :\n{result1.text}")

        print("\n" + "=" * 70)
        print("TEST 2 - Marie encore (cache HIT attendu)")
        print("=" * 70)
        result2 = await explain_score(
            client_id=42,
            client_prenom="Marie",
            client_nom="Dupont",
            score_churn=0.87,
            top_features=MARIE_FEATURES,
        )
        print(f"from_cache : {result2.from_cache}  <- doit etre True")
        print(f"cout       : {result2.cost_usd} USD  <- doit etre 0.0")

        print("\n" + "=" * 70)
        print("TEST 3 - Karim (cache MISS - client different)")
        print("=" * 70)
        result3 = await explain_score(
            client_id=58,
            client_prenom="Karim",
            client_nom="Benali",
            score_churn=0.18,
            top_features=KARIM_FEATURES,
        )
        print(f"from_cache : {result3.from_cache}  <- doit etre False")
        print(f"cout       : {result3.cost_usd} USD")
        print(f"\nTEXTE :\n{result3.text}")

        print("\n" + "=" * 70)
        print("STATS DU CACHE")
        print("=" * 70)
        for k, v in get_cache_stats().items():
            print(f"  {k:20} : {v}")

        from app.llm.adapters import close_llm_provider
        await close_llm_provider()

    asyncio.run(_test())
