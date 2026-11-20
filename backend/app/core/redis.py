import logging
from typing import Optional
import redis
from app.core.config import settings

logger = logging.getLogger("sentinelai.redis")

_redis_client: Optional[redis.Redis] = None


def get_redis_client() -> Optional[redis.Redis]:
    """
    Returns an active Redis client if REDIS_ENABLED and reachable.
    Gracefully returns None on connection failure to allow fallback.
    """
    global _redis_client
    if not settings.REDIS_ENABLED:
        return None

    if _redis_client is not None:
        try:
            _redis_client.ping()
            return _redis_client
        except (redis.ConnectionError, redis.TimeoutError, Exception) as e:
            logger.warning(f"[SentinelRedis] Cached Redis connection failed: {e}. Reconnecting...")
            _redis_client = None

    try:
        client = redis.from_url(
            settings.REDIS_URL,
            socket_timeout=2.0,
            socket_connect_timeout=2.0,
            decode_responses=True
        )
        client.ping()
        _redis_client = client
        return _redis_client
    except (redis.ConnectionError, redis.TimeoutError, Exception) as e:
        logger.warning(f"[SentinelRedis] Unable to connect to Redis at {settings.REDIS_URL}: {e}. Falling back to memory.")
        return None


def close_redis_client():
    global _redis_client
    if _redis_client:
        try:
            _redis_client.close()
        except Exception:
            pass
        _redis_client = None
