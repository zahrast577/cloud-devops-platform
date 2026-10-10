"""Cache Redis avec dégradation gracieuse.

Si Redis est absent ou en panne, l'API continue de fonctionner :
elle lit simplement la base de données à chaque requête.
C'est pour cela que Redis n'est PAS dans la sonde de disponibilité (/ready).
"""
import json
from typing import Any, Optional

import redis

from .config import CACHE_TTL_SECONDS, REDIS_HOST, REDIS_PORT


class Cache:
    def __init__(self) -> None:
        self._client: Optional[redis.Redis] = None
        if REDIS_HOST:
            self._client = redis.Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                socket_connect_timeout=1,
                socket_timeout=1,
                decode_responses=True,
            )

    def get_json(self, key: str) -> Optional[Any]:
        if self._client is None:
            return None
        try:
            raw = self._client.get(key)
        except redis.RedisError:
            return None
        return json.loads(raw) if raw else None

    def set_json(self, key: str, value: Any, ttl: int = CACHE_TTL_SECONDS) -> None:
        if self._client is None:
            return
        try:
            self._client.set(key, json.dumps(value), ex=ttl)
        except redis.RedisError:
            pass

    def delete(self, key: str) -> None:
        if self._client is None:
            return
        try:
            self._client.delete(key)
        except redis.RedisError:
            pass


cache = Cache()
