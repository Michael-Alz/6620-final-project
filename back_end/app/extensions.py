from __future__ import annotations

from typing import Optional

import redis as redis_lib
from flask_sqlalchemy import SQLAlchemy
from redis.exceptions import RedisError

db = SQLAlchemy()
redis: Optional[redis_lib.Redis] = None


def init_redis(app) -> None:
    """Initialise the Redis client with a soft-fail fallback."""
    global redis
    # If caching is explicitly disabled, do not attempt to connect
    if app.config.get("CACHE_DISABLED"):
        app.logger.info("Caching disabled via CACHE_DISABLED=true; skipping Redis connection.")
        redis = None
        app.extensions["redis_client"] = None
        app.extensions["redis"] = None
        return

    redis_url = app.config.get("REDIS_URL")
    if not redis_url:
        app.logger.warning("REDIS_URL not configured; caching disabled.")
        redis = None
        return

    try:
        client = redis_lib.Redis.from_url(redis_url, decode_responses=True)
        client.ping()
    except (RedisError, OSError) as exc:
        app.logger.warning("Redis unavailable (%s); running without cache.", exc)
        redis = None
    else:
        redis = client
        app.logger.info("Redis connected at %s", redis_url)

    # Expose on the app for easier debugging if needed.
    app.extensions["redis_client"] = redis
    app.extensions["redis"] = redis
