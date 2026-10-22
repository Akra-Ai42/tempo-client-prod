"""Adapters concrets pour les différents providers LLM.

Adapters disponibles :
    - OpenRouterProvider : utilisé pour la démo Tempo Client V2
    - HouseSLMProvider : (futur) SLM maison sur cluster GPU La Plateforme_

La factory `get_llm_provider()` choisit l'adapter selon la config.
"""

import asyncio
import json
import logging
import time
from typing import Optional

import httpx

from app.config import (
    OPENROUTER_API_KEY,
    OPENROUTER_MODEL,
    OPENROUTER_BASE_URL,
    OPENROUTER_SITE_URL,
    OPENROUTER_APP_NAME,
)
from app.llm.base import (
    LLMProvider,
    LLMResponse,
    LLMProviderError,
    LLMProviderTimeout,
    LLMProviderRateLimit,
)
from app.llm.pricing import estimate_cost_usd
from app.monitoring.llm_cost import log_llm_call


logger = logging.getLogger(__name__)


# Config retry — exposé pour tests / tweaks
MAX_RETRIES = 3
BACKOFF_BASE_SECONDS = 1.0  # 1s, puis 2s, puis 4s
REQUEST_TIMEOUT_SECONDS = 30.0


class OpenRouterProvider(LLMProvider):
    """Adapter pour OpenRouter.

    OpenRouter agrège ~200 modèles derrière une API unique compatible OpenAI.
    Permet de benchmarker différents modèles en changeant juste le nom du
    modèle dans .env (OPENROUTER_MODEL).

    Doc : https://openrouter.ai/docs

    Design :
        - async via httpx.AsyncClient
        - Retry 3x avec backoff exponentiel sur 429 et 5xx
        - Logs JSON structurés sur chaque appel (succès ou échec)
        - Coût calculé via le dict de pricing + loggé dans llm_cost_log.jsonl
        - Session httpx réutilisée (pas de connexion par appel)
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        self._api_key = api_key or OPENROUTER_API_KEY
        self._model = model or OPENROUTER_MODEL
        self._base_url = base_url or OPENROUTER_BASE_URL

        if not self._api_key:
            raise LLMProviderError(
                "OPENROUTER_API_KEY manquante — vérifier .env"
            )

        # Client httpx partagé (pool de connexions réutilisées)
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(REQUEST_TIMEOUT_SECONDS),
            headers=self._base_headers(),
        )

    @property
    def provider_name(self) -> str:
        return "openrouter"

    @property
    def model(self) -> str:
        """Modèle actuellement utilisé — exposé pour les logs et le dashboard."""
        return self._model

    def _base_headers(self) -> dict:
        """Headers requis par OpenRouter.

        - Authorization : clé API Bearer
        - HTTP-Referer : URL du site (pour tracking OpenRouter)
        - X-Title : nom de l'app (apparaît dans le dashboard OpenRouter)
        """
        return {
            "Authorization": f"Bearer {self._api_key}",
            "HTTP-Referer": OPENROUTER_SITE_URL or "http://localhost",
            "X-Title": OPENROUTER_APP_NAME,
            "Content-Type": "application/json",
        }

    def _build_messages(
        self,
        prompt: str,
        system: Optional[str],
    ) -> list[dict]:
        """Construit la liste messages format OpenAI."""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        return messages

    def _log_structured(
        self,
        level: str,
        event: str,
        **extra,
    ) -> None:
        """Log JSON structuré — standardise les champs pour l'exploitation."""
        payload = {
            "event": event,
            "provider": self.provider_name,
            "model": self._model,
            **extra,
        }
        if level == "info":
            logger.info(json.dumps(payload))
        elif level == "warning":
            logger.warning(json.dumps(payload))
        elif level == "error":
            logger.error(json.dumps(payload))

    async def _call_once(
        self,
        messages: list[dict],
        max_tokens: int,
        temperature: float,
    ) -> httpx.Response:
        """Un seul appel HTTP — levée brute des erreurs httpx."""
        url = f"{self._base_url}/chat/completions"
        body = {
            "model": self._model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        return await self._client.post(url, json=body)

    async def complete(
        self,
        prompt: str,
        system: Optional[str] = None,
        max_tokens: int = 500,
        temperature: float = 0.7,
    ) -> LLMResponse:
        """Appel OpenRouter avec retry 1-2-4s sur 429 et 5xx.

        Erreurs 4xx (hors 429) ne sont PAS retry — c'est une erreur côté
        appelant, le retry ne la résoudra pas.
        """
        messages = self._build_messages(prompt, system)
        start = time.monotonic()

        last_error: Optional[Exception] = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = await self._call_once(messages, max_tokens, temperature)
            except httpx.TimeoutException as e:
                last_error = e
                self._log_structured(
                    "warning",
                    "timeout",
                    attempt=attempt,
                    error=str(e),
                )
                if attempt == MAX_RETRIES:
                    raise LLMProviderTimeout(
                        f"Timeout après {MAX_RETRIES} tentatives"
                    ) from e
                await asyncio.sleep(BACKOFF_BASE_SECONDS * (2 ** (attempt - 1)))
                continue
            except httpx.HTTPError as e:
                last_error = e
                self._log_structured(
                    "error",
                    "network_error",
                    attempt=attempt,
                    error=str(e),
                )
                if attempt == MAX_RETRIES:
                    raise LLMProviderError(f"Erreur réseau: {e}") from e
                await asyncio.sleep(BACKOFF_BASE_SECONDS * (2 ** (attempt - 1)))
                continue

            # Analyse status code
            if response.status_code == 200:
                break

            if response.status_code == 429:
                # Rate limit — retry avec backoff
                self._log_structured(
                    "warning",
                    "rate_limit",
                    attempt=attempt,
                    status=429,
                )
                if attempt == MAX_RETRIES:
                    raise LLMProviderRateLimit(
                        f"Rate limit après {MAX_RETRIES} tentatives"
                    )
                await asyncio.sleep(BACKOFF_BASE_SECONDS * (2 ** (attempt - 1)))
                continue

            if 500 <= response.status_code < 600:
                # Erreur serveur — retry
                self._log_structured(
                    "warning",
                    "server_error",
                    attempt=attempt,
                    status=response.status_code,
                    body=response.text[:300],
                )
                if attempt == MAX_RETRIES:
                    raise LLMProviderError(
                        f"Erreur serveur {response.status_code} après {MAX_RETRIES} tentatives"
                    )
                await asyncio.sleep(BACKOFF_BASE_SECONDS * (2 ** (attempt - 1)))
                continue

            # 4xx hors 429 — pas de retry (erreur côté client)
            self._log_structured(
                "error",
                "client_error",
                status=response.status_code,
                body=response.text[:300],
            )
            raise LLMProviderError(
                f"Erreur client {response.status_code}: {response.text[:200]}"
            )

        # Succès — parsing réponse
        latency_ms = int((time.monotonic() - start) * 1000)
        return self._parse_response(response, latency_ms)

    def _parse_response(
        self,
        response: httpx.Response,
        latency_ms: int,
    ) -> LLMResponse:
        """Parse la réponse OpenAI-compatible et calcule le coût."""
        try:
            data = response.json()
        except json.JSONDecodeError as e:
            raise LLMProviderError(f"Réponse non-JSON: {e}") from e

        try:
            text = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            total_tokens = usage.get("total_tokens", prompt_tokens + completion_tokens)
            model_used = data.get("model", self._model)
        except (KeyError, IndexError, TypeError) as e:
            raise LLMProviderError(f"Format de réponse inattendu: {e}") from e

        cost_usd = estimate_cost_usd(model_used, prompt_tokens, completion_tokens)

        # Log structuré du succès
        self._log_structured(
            "info",
            "completion_ok",
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost_usd=cost_usd,
            latency_ms=latency_ms,
        )

        # Log append-only pour le dashboard direction (incident 1 l'exploite)
        if cost_usd is not None:
            log_llm_call(
                model=model_used,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                cost_usd=cost_usd,
                endpoint="llm.complete",
            )

        return LLMResponse(
            text=text,
            model=model_used,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            cost_usd=cost_usd,
            latency_ms=latency_ms,
        )

    async def aclose(self) -> None:
        """Ferme le client httpx proprement — à appeler au shutdown FastAPI."""
        await self._client.aclose()


class HouseSLMProvider(LLMProvider):
    """Adapter pour SLM maison hébergé sur le cluster GPU La Plateforme_.

    Futur — à implémenter quand le SLM sera entraîné et déployé sur le cluster
    (7× RTX 5090, 224 Go VRAM cumulée).

    Permettra la souveraineté complète : zéro facture externe, zéro
    dépendance à un provider US, latence minimale.

    Implémentation prévue :
        - Endpoint vLLM / Ollama exposé par le cluster
        - Même interface complete() → zéro refactor du code métier
        - Coût = 0 USD (infra interne amortie)
    """

    @property
    def provider_name(self) -> str:
        return "house_slm"

    async def complete(
        self,
        prompt: str,
        system: Optional[str] = None,
        max_tokens: int = 500,
        temperature: float = 0.7,
    ) -> LLMResponse:
        raise NotImplementedError(
            "SLM maison pas encore disponible. Utiliser OpenRouterProvider."
        )


# === Factory + singleton léger ===

_provider_instance: Optional[LLMProvider] = None


def get_llm_provider() -> LLMProvider:
    """Factory — retourne l'adapter configuré.

    Garde une instance singleton pour réutiliser la session httpx entre
    les appels (pool de connexions).

    Lu depuis la config, pas depuis un argument, pour que le code métier
    reste agnostique du choix d'implémentation.
    """
    global _provider_instance
    if _provider_instance is None:
        # Phase démo : toujours OpenRouter
        # Phase cluster : if LLM_PROVIDER == "house_slm" return HouseSLMProvider()
        _provider_instance = OpenRouterProvider()
    return _provider_instance


async def close_llm_provider() -> None:
    """À appeler au shutdown FastAPI pour fermer le client httpx."""
    global _provider_instance
    if _provider_instance is not None and hasattr(_provider_instance, "aclose"):
        await _provider_instance.aclose()
        _provider_instance = None


# === Script de test manuel ===

if __name__ == "__main__":
    """Test manuel rapide — lance avec:
        python -m app.llm.adapters

    Requiert OPENROUTER_API_KEY dans .env.
    """
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    async def _test():
        provider = get_llm_provider()
        print(f"\n[TEST] Provider: {provider.provider_name}")
        print(f"[TEST] Modèle: {provider.model}\n")

        try:
            response = await provider.complete(
                prompt="En une phrase, qu'est-ce qu'un modèle de scoring churn bancaire ?",
                system="Tu es un expert data science. Réponds en français, concis.",
                max_tokens=100,
                temperature=0.3,
            )
            print("=" * 60)
            print(f"RÉPONSE  : {response.text}")
            print("=" * 60)
            print(f"Modèle   : {response.model}")
            print(f"Tokens   : prompt={response.prompt_tokens} completion={response.completion_tokens}")
            print(f"Coût     : {response.cost_usd} USD")
            print(f"Latence  : {response.latency_ms} ms")
            print("=" * 60)
        except LLMProviderError as e:
            print(f"\n[ERREUR] {type(e).__name__}: {e}", file=sys.stderr)
            sys.exit(1)
        finally:
            await close_llm_provider()

    asyncio.run(_test())
