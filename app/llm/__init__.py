"""Interface LLMProvider + adapters.

L'ensemble du code métier appelle UNIQUEMENT la classe abstraite LLMProvider.
Le choix de l'adapter concret se fait via la factory `get_llm_provider()`
dans adapters.py, selon la variable d'environnement.

Cette abstraction permet de basculer de OpenRouter vers un SLM maison
hébergé sur le cluster GPU La Plateforme_ en changeant une seule ligne
de config, sans toucher au code métier.
"""

from app.llm.base import LLMProvider
from app.llm.adapters import get_llm_provider

__all__ = ["LLMProvider", "get_llm_provider"]
