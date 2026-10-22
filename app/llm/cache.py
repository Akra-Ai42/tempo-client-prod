"""Cache en memoire avec LRU + TTL.

Pourquoi un cache maison plutot que functools.lru_cache ?
    - functools.lru_cache ne gere pas le TTL (seulement LRU)
    - On veut controler finement la cle (client_id + hash features + model)
    - On veut pouvoir inspecter / vider le cache depuis l'API

Design :
    - OrderedDict : garde l'ordre d'insertion ET l'ordre d'acces (move_to_end)
    - TTL : chaque entree stocke son timestamp d'expiration
    - Thread-safe via asyncio.Lock pour les appels concurrents FastAPI
    - Metriques exposees : hits, misses, evictions, size
"""

import asyncio
import hashlib
import json
import time
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class CacheStats:
    """Statistiques du cache pour monitoring."""
    hits: int = 0
    misses: int = 0
    evictions_lru: int = 0
    evictions_ttl: int = 0

    @property
    def total_requests(self) -> int:
        return self.hits + self.misses

    @property
    def hit_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.hits / self.total_requests


@dataclass
class _CacheEntry:
    """Entree interne du cache."""
    value: Any
    expires_at: float


class TTLCache:
    """Cache LRU avec TTL par entree. Thread-safe pour FastAPI async."""

    def __init__(
        self,
        max_size: int = 1000,
        default_ttl_seconds: int = 86400,
    ):
        if max_size <= 0:
            raise ValueError("max_size doit etre > 0")
        if default_ttl_seconds <= 0:
            raise ValueError("default_ttl_seconds doit etre > 0")

        self._max_size = max_size
        self._default_ttl = default_ttl_seconds
        self._store: OrderedDict[str, _CacheEntry] = OrderedDict()
        self._lock = asyncio.Lock()
        self._stats = CacheStats()

    async def get(self, key: str) -> Optional[Any]:
        """Recupere une valeur. None si absente OU expiree."""
        async with self._lock:
            entry = self._store.get(key)
            if entry is None:
                self._stats.misses += 1
                return None

            if time.time() >= entry.expires_at:
                del self._store[key]
                self._stats.evictions_ttl += 1
                self._stats.misses += 1
                return None

            self._store.move_to_end(key)
            self._stats.hits += 1
            return entry.value

    async def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: Optional[int] = None,
    ) -> None:
        """Stocke une valeur avec TTL. Si plein, vire LRU."""
        ttl = ttl_seconds if ttl_seconds is not None else self._default_ttl
        expires_at = time.time() + ttl

        async with self._lock:
            if key in self._store:
                self._store.move_to_end(key)
                self._store[key] = _CacheEntry(value=value, expires_at=expires_at)
                return

            if len(self._store) >= self._max_size:
                self._store.popitem(last=False)
                self._stats.evictions_lru += 1

            self._store[key] = _CacheEntry(value=value, expires_at=expires_at)

    async def delete(self, key: str) -> bool:
        async with self._lock:
            return self._store.pop(key, None) is not None

    async def clear(self) -> None:
        async with self._lock:
            self._store.clear()

    def size(self) -> int:
        return len(self._store)

    def stats(self) -> CacheStats:
        return CacheStats(
            hits=self._stats.hits,
            misses=self._stats.misses,
            evictions_lru=self._stats.evictions_lru,
            evictions_ttl=self._stats.evictions_ttl,
        )


def build_cache_key(
    client_id: int,
    top_features: list[dict],
    model: str,
) -> str:
    """Construit une cle de cache stable depuis client_id + features + modele.

    Format : "v1:client=42:model=meta-llama/...:feat=a1b2c3d4"
    """
    features_json = json.dumps(top_features, sort_keys=True)
    features_hash = hashlib.sha256(features_json.encode()).hexdigest()[:16]
    return f"v1:client={client_id}:model={model}:feat={features_hash}"
