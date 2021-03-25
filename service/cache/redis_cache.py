import logging

from redis import Redis

from .interface.cache import Cache


class RedisCache(Cache):

    def __init__(self, connection_str):
        self._logger = logging.getLogger(__name__)
        try:
            self._redis = Redis(connection_str)
        except Exception as e:
            self._logger.fatal('Error in creating redis connection: {}'.format(e))

    def get(self, redis_key):
        try:
            redis_value = self._redis.get(redis_key)
        except Exception:
            redis_value = None
        return redis_value

    def add(self, key, data, ttl=86400):
        try:
            self._redis.set(key, data)
            self._redis.expire(key, ttl)
        except Exception as e:
            self._logger.error("Error in setting the redis value for {} : {}".format(key.decode('utf-8'), e))
