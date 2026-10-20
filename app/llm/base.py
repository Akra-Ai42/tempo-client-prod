"""Interface abstraite LLMProvider.

Tout adapter concret (OpenRouter, Together AI, SLM maison GPU) DOIT
implémenter cette interface. Le code métier ne connaît que cette classe.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class LLMResponse:
    """Réponse structurée d'un appel LLM, uniforme entre adapters."""
    text: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: Optional[float] = None  # None si l'adapter ne fournit pas le coût


class LLMProvider(ABC):
    """Interface pour tout fournisseur LLM — contrat uniforme."""

    @abstractmethod
    def complete(
        self,
        prompt: str,
        system: Optional[str] = None,
        max_tokens: int = 500,
        temperature: float = 0.7,
    ) -> LLMResponse:
        """Appel synchrone à un LLM.

        Args:
            prompt: Message utilisateur.
            system: Prompt système optionnel.
            max_tokens: Longueur max de la réponse.
            temperature: Créativité (0.0 déterministe, 1.0 créatif).

        Returns:
            LLMResponse avec le texte généré et les métadonnées de coût.
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Nom du provider pour les logs et le monitoring."""
        raise NotImplementedError
