import abc


class Cache(object):
    """
    Abstract base class for caching data
    """
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def add(self, key, data, ttl=86400):
        '''
        Add the data associated with key to the cache for the given TTL (seconds)
        '''

    @abc.abstractmethod
    def get(self, key):
        '''
        Get the data associated with key from the cache
        '''
