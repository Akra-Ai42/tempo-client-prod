"""Pricing OpenRouter — tarifs en USD par 1M tokens.

A mettre a jour periodiquement depuis https://openrouter.ai/models.
"""

OPENROUTER_PRICING: dict[str, dict[str, float]] = {
    "meta-llama/llama-3.3-70b-instruct": {
        "prompt_per_m": 0.23,
        "completion_per_m": 0.40,
    },
    "meta-llama/llama-3.1-8b-instruct": {
        "prompt_per_m": 0.055,
        "completion_per_m": 0.055,
    },
    "qwen/qwen-2.5-7b-instruct": {
        "prompt_per_m": 0.07,
        "completion_per_m": 0.07,
    },
    "anthropic/claude-3.5-haiku": {
        "prompt_per_m": 1.00,
        "completion_per_m": 5.00,
    },
    "google/gemini-flash-1.5": {
        "prompt_per_m": 0.075,
        "completion_per_m": 0.30,
    },
}


def estimate_cost_usd(
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
) -> float | None:
    """Calcule le cout estime d'un appel LLM.

    Returns:
        Cout en USD, ou None si le modele n'est pas dans le dict de pricing.
    """
    pricing = OPENROUTER_PRICING.get(model)
    if not pricing:
        return None

    prompt_cost = (prompt_tokens / 1_000_000) * pricing["prompt_per_m"]
    completion_cost = (completion_tokens / 1_000_000) * pricing["completion_per_m"]
    return round(prompt_cost + completion_cost, 6)
