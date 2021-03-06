import base64
from datetime import datetime
from typing import List

import timeago
from orator import Model
from redis_lock import Lock

from news.lib.cache import cache
from news.lib.metrics import CACHE_HITS, CACHE_MISSES

CACHE_EXPIRE_TIME = 12 * 60 * 60


class Base(Model):
    """
    Base class for all models which handles queries and caching

    All models should use methods from this class to access and write to cache,
    If model-specific methods for cache access are needed be really careful
    when implementing them and try to use as much code from this class as possible
    """

    @property
    def b_id(self):
        return str(self.id).encode()

    @property
    def id64(self):
        return self.__class__._cache_prefix() + base64.b64encode(self.id)

    @classmethod
    def _cache_prefix(cls) -> str:
        """
        Cache prefix for model, must be unique to prevent conflicts
        :rtype: str
        :return: cache prefix
        """
        return cls.__name__ + "_"

    @property
    def _cache_key(self) -> str:
        """
        Cache key for model
        :return: cache key for object
        """
        prefix = self.__class__._cache_prefix()
        return "{prefix}{id}".format(prefix=prefix, id=self.id)

    @property
    def _lock_key(self) -> str:
        """
        Get lock key for given model
        Mainly used for read - modify - write procedures
        :return: lock key
        """
        return "lock:{}".format(self._cache_key)

    @classmethod
    def _cache_key_from_id(cls, id: str) -> str:
        """
        Generate cache key from thing id
        :param id: thing id
        :return: cache key
        """
        prefix = cls._cache_prefix()
        return "{prefix}{id}".format(prefix=prefix, id=id)

    def get_read_modify_write_lock(self) -> Lock:
        """
        Gets read/modify/write lock for given things
        Used when updating in cache or database
        :return: RedisLock
        """
        return Lock(cache.conn, self._lock_key, expire=3)

    def update_from_cache(self):
        """
        Update model from redis
        This is usually performed before updates or when updating for data consistency
        """
        data = cache.get(self._cache_key)
        if data is not None:
            self.set_raw_attributes(data)

    def update_with_cache(self):
        self.save()
        self.write_to_cache()

    def write_to_cache(self):
        """
        Write self to cache
        What should and what shouldn't be written can be modified by
        __hidden__ attribute on class (more in documentation of orator)
        """
        # save token to redis for limited time
        cache.set(self._cache_key, self.serialize())

    @classmethod
    def load_from_cache(cls, id: str) -> object:
        """
        Load model from cache
        :param id: id
        :return: model if found else None
        """
        data = cache.get(cls._cache_key_from_id(id))
        if data is None:
            return None
        obj = cls()
        obj.set_raw_attributes(data)
        obj.set_exists(True)
        return obj

    def incr(self, attr: str, amp: int = 1):
        """
        Increment given attribute
        Increments model in both database and redis
        :param attr: attribute
        :param amp: amplitude
        """
        with self.get_read_modify_write_lock():
            self.update_from_cache()
            new_val = getattr(self, attr) + amp
            self.set_attribute(attr, new_val)
            self.__class__.where("id", self.id).increment(attr, amp)
            self.write_to_cache()

    def decr(self, attr: str, amp: int = 1):
        """
        Decrement given attribute
        Decrements model in both database and redis
        :param attr: attribute
        :param amp: amplitude
        """
        with self.get_read_modify_write_lock():
            self.update_from_cache()
            new_val = getattr(self, attr) - amp
            self.set_attribute(attr, new_val)
            self.__class__.where("id", self.id).decrement(attr, amp)
            self.write_to_cache()

    def set(self, attr: str, val: object):
        """
        Decrement given attribute
        Decrements model in both database and redis
        :param attr: attribute
        :param amp: amplitude
        """
        with self.get_read_modify_write_lock():
            self.set_raw_attribute(attr, val)
            self.save()
            self.write_to_cache()

    def time_ago(self) -> str:
        return timeago.format(self.created_at, datetime.utcnow())

    @property
    def route(self):
        """
        Get items url for access
        All viewable items should implement this method
        """
        raise NotImplemented

    @classmethod
    def by_id(cls, id: str) -> object:
        """
        Tries to load the item from cache and if it fails from DB
        items that are permanently stored in cache should overwrite this method
        :param id:
        :return:
        """
        # try to load from cache
        item = cls.load_from_cache(id)
        if item is not None:
            CACHE_HITS.inc(1)
            return item

        CACHE_MISSES.inc(1)
        # check db on fail
        item = cls.where("id", int(id)).first()
        if item is not None:
            item.write_to_cache()

        return item

    @classmethod
    def by_id_slow(cls, id: str) -> object:
        return cls.where("id", id).first()

    @classmethod
    def by_ids(cls, ids: List[str]) -> List[object]:
        """
        Get items by ids
        Uses pipe which is faster then loading the items one by one
        :param ids: list of ids of items to get
        :return: items
        """
        items = cache.mget([cls._cache_key_from_id(id) for id in ids])

        # fetch missing items
        for idx, id in enumerate(ids):
            if items[idx] is None:
                items[idx] = cls.by_id(id)
            else:
                obj = cls()
                obj.set_raw_attributes(items[idx])
                obj.set_exists(True)
                items[idx] = obj

        return items

    def update(self, _attributes=None, **attributes):
        """
        Update the item in database but also write the changes to cache
        :param _attributes:
        :param attributes:
        """
        super().update(_attributes, **attributes)
        self.write_to_cache()

    def delete(self):
        """
        Delete self from cache and db
        """
        cache.delete(self._cache_key)
        super().delete()
