"""Interface abstraite LLMProvider.

Tout adapter concret (OpenRouter, Together AI, SLM maison GPU) DOIT
implémenter cette interface. Le code métier ne connaît que cette classe.

Design decisions:
    - Async par défaut (cohérent FastAPI async)
    - LLMResponse = dataclass immutable avec métadonnées de coût
    - provider_name séparé pour les logs et le monitoring
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class LLMResponse:
    """Réponse structurée d'un appel LLM, uniforme entre adapters.

    Attributes:
        text: Texte généré par le modèle.
        model: Identifiant du modèle utilisé (ex: "meta-llama/llama-3.3-70b-instruct").
        prompt_tokens: Nombre de tokens dans le prompt (input).
        completion_tokens: Nombre de tokens générés (output).
        total_tokens: Somme (certains providers ne renvoient que ça).
        cost_usd: Coût estimé de l'appel en USD, None si pricing inconnu.
        latency_ms: Latence totale de l'appel en millisecondes.
    """
    text: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: Optional[float] = None
    latency_ms: Optional[int] = None


class LLMProviderError(Exception):
    """Erreur racine du module LLM — toute erreur d'adapter en dérive."""
    pass


class LLMProviderTimeout(LLMProviderError):
    """Timeout sur l'appel — l'appelant peut décider de retry ou pas."""
    pass


class LLMProviderRateLimit(LLMProviderError):
    """Rate limit atteint — l'appelant doit backoff."""
    pass


class LLMProvider(ABC):
    """Interface pour tout fournisseur LLM — contrat uniforme.

    Toute implémentation DOIT être thread-safe pour permettre les appels
    concurrents depuis FastAPI.
    """

    @abstractmethod
    async def complete(
        self,
        prompt: str,
        system: Optional[str] = None,
        max_tokens: int = 500,
        temperature: float = 0.7,
    ) -> LLMResponse:
        """Appel asynchrone à un LLM.

        Args:
            prompt: Message utilisateur.
            system: Prompt système optionnel (persona, règles).
            max_tokens: Longueur max de la réponse générée.
            temperature: Créativité (0.0 déterministe, 1.0 créatif).

        Returns:
            LLMResponse avec le texte généré et les métadonnées.

        Raises:
            LLMProviderTimeout: Si l'appel dépasse le timeout.
            LLMProviderRateLimit: Si rate limit atteint après retries.
            LLMProviderError: Pour toute autre erreur (API down, auth KO, etc.).
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Nom du provider pour les logs et le monitoring (ex: 'openrouter')."""
        raise NotImplementedError
