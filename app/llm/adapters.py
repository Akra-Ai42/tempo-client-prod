"""Adapters concrets pour les différents providers LLM.

Adapters disponibles :
    - OpenRouterProvider : actuellement utilisé pour la démo
    - HouseSLMProvider : (futur) SLM maison sur cluster GPU La Plateforme_

La factory `get_llm_provider()` choisit l'adapter selon la config.
"""

from typing import Optional

from app.llm.base import LLMProvider, LLMResponse
from app.config import (
    OPENROUTER_API_KEY,
    OPENROUTER_MODEL,
    OPENROUTER_BASE_URL,
    OPENROUTER_SITE_URL,
    OPENROUTER_APP_NAME,
)


class OpenRouterProvider(LLMProvider):
    """Adapter pour OpenRouter.

    OpenRouter agrège ~200 modèles derrière une API unique compatible OpenAI.
    Permet de benchmarker différents modèles en changeant juste le nom du
    modèle dans .env (OPENROUTER_MODEL).

    Doc : https://openrouter.ai/docs
    """

    @property
    def provider_name(self) -> str:
        return "openrouter"

    def complete(
        self,
        prompt: str,
        system: Optional[str] = None,
        max_tokens: int = 500,
        temperature: float = 0.7,
    ) -> LLMResponse:
        # TODO : implémenter l'appel httpx vers OPENROUTER_BASE_URL/chat/completions
        # TODO : construire la liste messages avec system (si fourni) + user
        # TODO : headers = {
        #     "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        #     "HTTP-Referer": OPENROUTER_SITE_URL,
        #     "X-Title": OPENROUTER_APP_NAME,
        # }
        # TODO : parser la réponse, extraire usage pour coûts
        # TODO : calculer cost_usd depuis usage + pricing du modèle
        raise NotImplementedError("À implémenter en phase 4")


class HouseSLMProvider(LLMProvider):
    """Adapter pour SLM maison hébergé sur le cluster GPU La Plateforme_.

    Futur — à implémenter quand le SLM sera entraîné et déployé sur le cluster.
    Permettra la souveraineté complète : zéro facture externe, zéro
    dépendance à un provider US, latence minimale.
    """

    @property
    def provider_name(self) -> str:
        return "house_slm"

    def complete(
        self,
        prompt: str,
        system: Optional[str] = None,
        max_tokens: int = 500,
        temperature: float = 0.7,
    ) -> LLMResponse:
        # TODO : à implémenter quand le cluster GPU exposera un endpoint vLLM
        raise NotImplementedError("Pas encore disponible")


def get_llm_provider() -> LLMProvider:
    """Factory — retourne l'adapter configuré.

    Lu depuis la config, pas depuis un argument, pour que le code métier
    reste agnostique du choix d'implémentation.
    """
    # Phase démo : toujours OpenRouter
    # Phase cluster : if LLM_PROVIDER == "house_slm" return HouseSLMProvider()
    return OpenRouterProvider()
