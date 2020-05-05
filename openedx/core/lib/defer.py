"""
This module creates a default ThreadPoolExecutor for the process
and exposes some convenience functions for using the executor.
"""
from concurrent.futures import ThreadPoolExecutor, wait

from django.utils.functional import cached_property

# on python 3.5, max_workers defaults to (number of cpu cores * 5)
# which is probably too high, considering every process will have a threadpool
_POOL = ThreadPoolExecutor(max_workers=4)

NOT_DONE = object()

__all__ = ('defer', 'wait', 'PrefetchCachedProperties', 'FutureProxy')


def defer(func, *args, **kwargs):
    """
    Execute a function using the global threadpool.
    If `proxy_result=True`, returns a FutureProxy,
    otherwise, returns a Future
    """
    proxy_result = kwargs.pop('proxy_result', False)
    fut = _POOL.submit(func, *args, **kwargs)
    if proxy_result:
        fut = FutureProxy(fut)
    return fut


class PrefetchCachedProperties:
    """
    Mixin class that will asynchronously prefetch all cached_properties on the object
    """
    def __init__(self, *args, **kwargs):  # pylint: disable=unused-argument
        to_prefetch = []
        klass = self.__class__
        for attr in dir(self):
            if isinstance(getattr(klass, attr), cached_property):
                to_prefetch.append(attr)
        self._to_prefetch = to_prefetch

    def prefetch(self):
        """
        Prefetch cached properties, using the global threadpool.
        """
        results = []
        for attr in self._to_prefetch:
            results.append(_POOL.submit(getattr, self, attr))
        wait(results)


class FutureProxy:
    """
    Object that wraps a future and automatically waits for the result
    """
    def __init__(self, fut):
        self.fut = fut
        self._result = NOT_DONE

    def _check_done(self):
        if self._result is NOT_DONE:
            self._result = self.fut.result()

    def __getattr__(self, attr):
        self._check_done()
        return getattr(self._result, attr)

    def __getitem__(self, item):
        self._check_done()
        return self._result[item]

    def __contains__(self, item):
        self._check_done()
        return item in self._result

    def __iter__(self):
        self._check_done()
        return iter(self._result)

    def __bool__(self):
        self._check_done()
        return bool(self._result)
