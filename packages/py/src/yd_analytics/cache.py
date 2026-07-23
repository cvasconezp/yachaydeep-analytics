"""
yd.analytics.cache — Caché por clave versionada.

Demo: caché en memoria con TTL. En producción: Redis (flag ENABLE_RATE_LIMIT ya
trae Redis a la casa). La clave incluye la versión de la métrica: subir la versión
invalida su caché automáticamente.
"""
from __future__ import annotations

import hashlib
import json
import time

from .schemas import MetricQuery, MetricSpec


class _Cache:
    def __init__(self) -> None:
        self._store: dict[str, tuple[float, list]] = {}

    def key(self, spec: MetricSpec, query: MetricQuery) -> str:
        raw = json.dumps(
            {
                "id": spec.id,
                "v": spec.version,
                "dims": query.dimensions,
                "filters": [f.model_dump() for f in query.filters],
                "params": query.params,
                "limit": query.limit,
            },
            sort_keys=True, default=str,
        )
        return hashlib.sha256(raw.encode()).hexdigest()

    def get(self, key: str):
        hit = self._store.get(key)
        if not hit:
            return None
        expires, value = hit
        if expires < time.monotonic():
            self._store.pop(key, None)
            return None
        return value

    def set(self, key: str, value: list, ttl: float) -> None:
        self._store[key] = (time.monotonic() + ttl, value)

    @staticmethod
    def ttl_for(cadencia: str) -> float:
        return {"hourly": 3600.0, "daily": 86400.0}.get(cadencia, 0.0)


cache = _Cache()
