from redis_lock import Lock
from rq.decorators import job

from news.lib.cache import cache
from news.clients.db.sorts import sorts
from news.lib.metrics import CACHE_MISSES, CACHE_HITS
from news.lib.sorts import sort_tuples
from news.lib.task_queue import redis_conn
from news.lib.utils.time_utils import epoch_seconds
from news.models.comment import CommentTree

PRECOMPUTE_LIMIT = 1000


def tuple_maker(sort):
    """
    Tuple maker returns function which transforms model to tuple of values base on sort
    These tuples are used to sort the models
    First element in tuple is always the ID of object
    :param sort:
    :return:
    """
    if sort == "new":
        return lambda x: [x.id, epoch_seconds(x.created_at)]
    if sort == "best":
        return lambda x: [x.id, x.score, epoch_seconds(x.created_at)]
    return lambda x: [x.id, x.hot]  # default to trending


class LinkQuery:
    """
    Access object for sorted links

    Should be handled as source of truth, uses redis as store
    """

    def __init__(self, feed_id, sort, time="all", filters=()):
        self.feed_id = feed_id
        self.sort = sort
        self.time = time
        self._tupler = tuple_maker(sort)
        self._fetched = False
        self._data = None
        self._filters = filters

    def __iter__(self):
        self.fetch()

        for x in self._data:
            yield x[0]

    def __repr__(self):
        return "<CachedQuery %s %s>" % (self.feed_id, self.sort)

    @property
    def _cache_key(self):
        return "cquery:{}.{}.{}".format(self.feed_id, self.sort, self.time)

    @property
    def _lock_key(self):
        return "lock:cquery:{}.{}.{}".format(self.feed_id, self.sort, self.time)

    def _save(self):
        """
        Save data to cache
        """
        assert self._fetched
        cache.set(self._cache_key, self._data)

    def _rebuild(self):
        """
        Rebuild link query from database
        """
        from news.models.link import Link

        q = (
            Link.where("feed_id", self.feed_id)
            .order_by_raw(sorts[self.sort])
            .limit(1000)
        )

        # cache needs array of objects, not a orator collection
        res = [self._tupler(l) for l in q.get()]
        self._data = sort_tuples(res)
        self._fetched = True
        self._save()

    def delete(self, links):
        """
        Delete given links from query
        :param links: links
        """
        with Lock(cache.conn, self._lock_key):
            # fetch fresh data from cache
            data = cache.get(self._cache_key) or []
            lids = set(x.id for x in links)

            data = [x for x in data if x[0] not in lids]
            self._data = data
            self._fetched = True
            self._save()

    def insert(self, links):
        """
        Insert links into the query
        :param links: links to insert
        :return: updated list of [id, sort value...] tuples
        """
        # read - write - modify
        with Lock(cache.conn, self._lock_key):
            self.fetch()
            data = self._data
            item_tuples = [self._tupler(link) for link in links] or []

            existing_fnames = {item[0] for item in data}
            new_fnames = {item[0] for item in item_tuples}

            mutated_length = len(existing_fnames.union(new_fnames))
            would_truncate = mutated_length >= PRECOMPUTE_LIMIT
            if would_truncate and data:
                # only insert items that are already stored or new items
                # that are large enough that they won't be immediately truncated
                # out of storage
                # item structure is (name, sortval1[, sortval2, ...])
                smallest = data[-1]
                item_tuples = [
                    item
                    for item in item_tuples
                    if (item[0] in existing_fnames or item[1:] >= smallest[1:])
                ]

            if not item_tuples:
                # nothing changes
                return self._data

            # insert the items, remove the duplicates (keeping the
            # one being inserted over the stored value if applicable),
            # and sort the result
            data = [x for x in data if x[0] not in new_fnames]
            data.extend(item_tuples)
            data.sort(reverse=True, key=lambda x: x[1:])
            if len(data) > PRECOMPUTE_LIMIT:
                data = data[:PRECOMPUTE_LIMIT]
            self._data = data
            self._fetched = True
            self._save()
        return True

    def fetch(self):
        """
        Fetch data from cache and return them
        Data are tuples in from [id, [sort value 1, [sort value 2, ...]]]
        :return: sorted and filtered list of [id, sort values...] tuples
        """
        self._data = cache.get(self._cache_key)

        if self._data is None:
            CACHE_MISSES.inc(1)
            self._rebuild()
        else:
            CACHE_HITS.inc(1)

        self._fetched = True

        for fnc in self._filters:
            self._data = filter(fnc, self._data)

        return self._data

    def fetch_ids(self) -> [str]:
        """
        Fetch data from cache but return only ids of things
        :return: sorted and filtered list of ids
        """
        return [r[0] for r in self.fetch()]


@job("medium", connection=redis_conn)
def JOB_add_to_queries(link):
    """
    Consumes add_to_queries queue
    :param link: link to add/update
    :return: nothing
    """
    for sort in ["trending", "best", "new"]:
        q = LinkQuery(feed_id=link.feed_id, sort=sort)
        q.insert([link])
    CommentTree(link.id).create()
    return None
