import json
import random
from typing import Any, Optional

from flask import current_app
from redis.exceptions import RedisError

from . import extensions as _ext

ORDERS_LIST_VERSION_KEY = "orders:list:version"
ORDERS_DETAIL_KEY = "orders:detail:{order_id}"
TEMP_ORDER_KEY = "temp_order:{order_id}"


def _get_app():
    try:
        return current_app._get_current_object()
    except RuntimeError:
        return None


def _cache_enabled() -> bool:
    app = _get_app()
    if not app:
        return False
    if app.config.get("CACHE_DISABLED"):
        return False
    return app.extensions.get("redis") is not None


def _get_redis():
    app = _get_app()
    if app:
        client = app.extensions.get("redis")
        if client is not None:
            return client
    # Fallback to module variable for non-request contexts
    return getattr(_ext, "redis", None)


def cache_get(key: str) -> Optional[Any]:
    app = _get_app()
    if not _cache_enabled():
        return None

    client = _get_redis()
    try:
        payload = client.get(key) if client else None
    except (RedisError, OSError) as exc:
        if app:
            app.logger.warning("Cache read failed for %s (%s)", key, exc)
        return None

    if payload is None:
        return None

    try:
        return json.loads(payload)
    except json.JSONDecodeError:
        if app:
            app.logger.debug("Cache payload malformed for %s", key)
        return None


def cache_setex(key: str, obj: Any, ttl: Optional[int] = None) -> None:
    if not _cache_enabled():
        return

    app = _get_app()
    ttl = ttl or (app.config.get("ORDERS_CACHE_TTL", 30) if app else 30)
    if ttl <= 0:
        return

    jitter = max(1, int(round(ttl * random.uniform(0.9, 1.1))))

    client = _get_redis()
    try:
        if client:
            client.setex(key, jitter, json.dumps(obj))
    except (TypeError, ValueError) as exc:
        if app:
            app.logger.warning(
                "Failed to serialize cache payload for %s (%s)", key, exc
            )
    except (RedisError, OSError) as exc:
        if app:
            app.logger.warning("Cache write failed for %s (%s)", key, exc)


def cache_get_temp_order(order_id: str) -> Optional[Any]:
    """Return the cached temp order payload if present."""
    if not _cache_enabled():
        return None
    return cache_get(TEMP_ORDER_KEY.format(order_id=order_id))


def cache_set_temp_order(order_id: str, obj: Any, ttl: Optional[int] = None) -> None:
    """Write the temp order payload with a short TTL for read-your-own-writes."""
    if not _cache_enabled():
        return
    app = _get_app()
    effective_ttl = ttl or (app.config.get("TEMP_ORDER_CACHE_TTL", 60) if app else 60)
    if effective_ttl <= 0:
        return

    client = _get_redis()
    try:
        if client:
            client.setex(TEMP_ORDER_KEY.format(order_id=order_id), effective_ttl, json.dumps(obj))
    except (TypeError, ValueError) as exc:
        if app:
            app.logger.warning("Failed to serialize temp order cache for %s (%s)", order_id, exc)
    except (RedisError, OSError) as exc:
        if app:
            app.logger.warning("Temp order cache write failed for %s (%s)", order_id, exc)


def clear_temp_order_cache(order_id: str) -> None:
    """Drop any temp order cache entry."""
    if not _cache_enabled():
        return
    client = _get_redis()
    if not client:
        return
    try:
        client.delete(TEMP_ORDER_KEY.format(order_id=order_id))
    except (RedisError, OSError):
        pass


def get_list_version() -> int:
    """Return the current cached list version."""
    if not _cache_enabled():
        return 0

    client = _get_redis()
    try:
        value = client.get(ORDERS_LIST_VERSION_KEY) if client else None
    except (RedisError, OSError):
        return 0

    if value is None:
        return 0

    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def invalidate_orders_cache(order_id: Optional[str] = None) -> None:
    """Increment the list cache version and drop any order detail caches."""
    if not _cache_enabled():
        return

    client = _get_redis()
    try:
        if client:
            client.incr(ORDERS_LIST_VERSION_KEY)
    except (RedisError, OSError):
        pass

    if not order_id:
        return

    pattern = ORDERS_DETAIL_KEY.format(order_id=order_id)
    try:
        if client:
            for key in client.scan_iter(match=pattern):
                client.delete(key)
    except (RedisError, OSError):
        pass
