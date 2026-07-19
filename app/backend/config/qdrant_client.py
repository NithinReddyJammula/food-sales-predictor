"""
qdrant_client.py
─────────────────
Instrumented wrapper around QdrantClient.
Logs every upsert / search / delete to the OTLP logger so operations
are visible in New Relic Logs under service.name='food-sales-predictor'.

Usage — import this instead of qdrant_client directly:
    from app.backend.config.qdrant_client import get_qdrant_client
    client = get_qdrant_client()
"""

import logging
import time
import os
from typing import Any, Optional

logger = logging.getLogger("food-sales-predictor.qdrant")


def _try_init_observability():
    """Ensure the OTLP logger is initialised before the first Qdrant call."""
    try:
        from app.backend.config.monitoring import Observability
        Observability.initialize()
    except Exception:
        pass  # Silently degrade; basic Python logging still works


class InstrumentedQdrantClient:
    """
    Thin proxy around QdrantClient that emits structured log records
    for every mutating or querying operation.
    """

    def __init__(self, *args, **kwargs):
        from qdrant_client import QdrantClient as _QdrantClient  # lazy import
        _try_init_observability()
        self._client = _QdrantClient(*args, **kwargs)
        logger.info("Qdrant client initialised", extra={
            "qdrant.host": kwargs.get("host") or (args[0] if args else "localhost"),
            "qdrant.port": kwargs.get("port", 6333),
        })

    # ── Search ────────────────────────────────────────────────────────────────
    def search(self, collection_name: str, *args, **kwargs):
        t0 = time.perf_counter()
        try:
            result = self._client.search(collection_name, *args, **kwargs)
            elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
            logger.info("Qdrant search completed", extra={
                "qdrant.operation": "search",
                "qdrant.collection": collection_name,
                "qdrant.result_count": len(result),
                "qdrant.latency_ms": elapsed_ms,
            })
            return result
        except Exception as exc:
            elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
            logger.error("Qdrant search failed", extra={
                "qdrant.operation": "search",
                "qdrant.collection": collection_name,
                "qdrant.latency_ms": elapsed_ms,
                "error": str(exc),
            })
            raise

    # ── Upsert ────────────────────────────────────────────────────────────────
    def upsert(self, collection_name: str, *args, **kwargs):
        points = kwargs.get("points") or (args[0] if args else [])
        point_count = len(points) if hasattr(points, "__len__") else "?"
        t0 = time.perf_counter()
        try:
            result = self._client.upsert(collection_name, *args, **kwargs)
            elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
            logger.info("Qdrant upsert completed", extra={
                "qdrant.operation": "upsert",
                "qdrant.collection": collection_name,
                "qdrant.point_count": point_count,
                "qdrant.latency_ms": elapsed_ms,
            })
            return result
        except Exception as exc:
            elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
            logger.error("Qdrant upsert failed", extra={
                "qdrant.operation": "upsert",
                "qdrant.collection": collection_name,
                "qdrant.point_count": point_count,
                "qdrant.latency_ms": elapsed_ms,
                "error": str(exc),
            })
            raise

    # ── Delete ────────────────────────────────────────────────────────────────
    def delete(self, collection_name: str, *args, **kwargs):
        t0 = time.perf_counter()
        try:
            result = self._client.delete(collection_name, *args, **kwargs)
            elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
            logger.info("Qdrant delete completed", extra={
                "qdrant.operation": "delete",
                "qdrant.collection": collection_name,
                "qdrant.latency_ms": elapsed_ms,
            })
            return result
        except Exception as exc:
            elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
            logger.error("Qdrant delete failed", extra={
                "qdrant.operation": "delete",
                "qdrant.collection": collection_name,
                "qdrant.latency_ms": elapsed_ms,
                "error": str(exc),
            })
            raise

    # ── Pass-through all other methods unchanged ──────────────────────────────
    def __getattr__(self, name: str):
        return getattr(self._client, name)


_qdrant_client: Optional[InstrumentedQdrantClient] = None


def get_qdrant_client(
    host: str = "localhost",
    port: int = 6333,
    url: Optional[str] = None,
    api_key: Optional[str] = None,
) -> InstrumentedQdrantClient:
    """
    Returns a singleton InstrumentedQdrantClient.
    Connection params default to environment variables if not supplied.
    """
    global _qdrant_client
    if _qdrant_client is None:
        _host = url or os.getenv("QDRANT_URL") or host
        _api_key = api_key or os.getenv("QDRANT_API_KEY")
        kwargs = {"url": _host} if "://" in _host else {"host": _host, "port": port}
        if _api_key:
            kwargs["api_key"] = _api_key
        _qdrant_client = InstrumentedQdrantClient(**kwargs)
    return _qdrant_client
