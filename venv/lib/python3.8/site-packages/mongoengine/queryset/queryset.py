from mongoengine.errors import OperationError
from mongoengine.queryset.base import (
    CASCADE,
    DENY,
    DO_NOTHING,
    NULLIFY,
    PULL,
    BaseQuerySet,
)

__all__ = (
    "QuerySet",
    "QuerySetNoCache",
    "DO_NOTHING",
    "NULLIFY",
    "CASCADE",
    "DENY",
    "PULL",
)

# The maximum number of items to display in a QuerySet.__repr__
REPR_OUTPUT_SIZE = 20
ITER_CHUNK_SIZE = 100


class QuerySet(BaseQuerySet):
    """The default queryset, that builds queries and handles a set of results
    returned from a query.

    Wraps a MongoDB cursor, providing :class:`~mongoengine.Document` objects as
    the results.
    """

    _has_more = True
    _len = None
    _result_cache = None

    def __iter__(self):
        """Iteration utilises a results cache which iterates the cursor
        in batches of ``ITER_CHUNK_SIZE``.

        If ``self._has_more`` the cursor hasn't been exhausted so cache then
        batch. Otherwise iterate the result_cache.
        """
        self._iter = True

        if self._has_more:
            return self._iter_results()

        # iterating over the cache.
        return iter(self._result_cache)

    def __len__(self):
        """Since __len__ is called quite frequently (for example, as part of
        list(qs)), we populate the result cache and cache the length.
        """
        if self._len is not None:
            return self._len

        # Populate the result cache with *all* of the docs in the cursor
        if self._has_more:
            list(self._iter_results())

        # Cache the length of the complete result cache and return it
        self._len = len(self._result_cache)
        return self._len

    def __repr__(self):
        """Provide a string representation of the QuerySet"""
        if self._iter:
            return ".. queryset mid-iteration .."

        self._populate_cache()
        data = self._result_cache[: REPR_OUTPUT_SIZE + 1]
        if len(data) > REPR_OUTPUT_SIZE:
            data[-1] = "...(remaining elements truncated)..."
        return repr(data)

    def _iter_results(self):
        """A generator for iterating over the result cache.

        Also populates the cache if there are more possible results to
        yield. Raises StopIteration when there are no more results.
        """
        if self._result_cache is None:
            self._result_cache = []

        pos = 0
        while True:

            # For all positions lower than the length of the current result
            # cache, serve the docs straight from the cache w/o hitting the
            # database.
            # XXX it's VERY important to compute the len within the `while`
            # condition because the result cache might expand mid-iteration
            # (e.g. if we call len(qs) inside a loop that iterates over the
            # queryset). Fortunately len(list) is O(1) in Python, so this
            # doesn't cause performance issues.
            while pos < len(self._result_cache):
                yield self._result_cache[pos]
                pos += 1

            # return if we already established there were no more
            # docs in the db cursor.
            if not self._has_more:
                return

            # Otherwise, populate more of the cache and repeat.
            if len(self._result_cache) <= pos:
                self._populate_cache()

    def _populate_cache(self):
        """
        Populates the result cache with ``ITER_CHUNK_SIZE`` more entries
        (until the cursor is exhausted).
        """
        if self._result_cache is None:
            self._result_cache = []

        # Skip populating the cache if we already established there are no
        # more docs to pull from the database.
        if not self._has_more:
            return

        # Pull in ITER_CHUNK_SIZE docs from the database and store them in
        # the result cache.
        try:
            for _ in range(ITER_CHUNK_SIZE):
                self._result_cache.append(next(self))
        except StopIteration:
            # Getting this exception means there are no more docs in the
            # db cursor. Set _has_more to False so that we can use that
            # information in other places.
            self._has_more = False

    def count(self, with_limit_and_skip=False):
        """Count the selected elements in the query.

        :param with_limit_and_skip (optional): take any :meth:`limit` or
            :meth:`skip` that has been applied to this cursor into account when
            getting the count
        """
        if with_limit_and_skip is False:
            return super().count(with_limit_and_skip)

        if self._len is None:
            # cache the length
            self._len = super().count(with_limit_and_skip)

        return self._len

    def no_cache(self):
        """Convert to a non-caching queryset"""
        if self._result_cache is not None:
            raise OperationError("QuerySet already cached")

        return self._clone_into(QuerySetNoCache(self._document, self._collection))


class QuerySetNoCache(BaseQuerySet):
    """A non caching QuerySet"""

    def cache(self):
        """Convert to a caching queryset"""
        return self._clone_into(QuerySet(self._document, self._collection))

    def __repr__(self):
        """Provides the string representation of the QuerySet"""
        if self._iter:
            return ".. queryset mid-iteration .."

        data = []
        for _ in range(REPR_OUTPUT_SIZE + 1):
            try:
                data.append(next(self))
            except StopIteration:
                break

        if len(data) > REPR_OUTPUT_SIZE:
            data[-1] = "...(remaining elements truncated)..."

        self.rewind()
        return repr(data)

    def __iter__(self):
        queryset = self
        if queryset._iter:
            queryset = self.clone()
        queryset.rewind()
        return queryset
