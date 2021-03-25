from abc import ABCMeta, abstractmethod


class Cache(metaclass=ABCMeta):
    """
    Abstract base class for caching data
    """

    @abstractmethod
    def add(self, key, data, ttl=86400):
        """
        Add the data associated with key to the cache for the given TTL (seconds)
        """

    @abstractmethod
    def get(self, key):
        """
        Get the data associated with key from the cache
        """
