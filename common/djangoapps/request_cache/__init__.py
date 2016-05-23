"""
A cache that is cleared after every request.

This module requires that :class:`request_cache.middleware.RequestCache`
is installed in order to clear the cache after each request.
"""

import logging
from urlparse import urlparse

from django.core.cache import caches
from django.core.cache.backends.base import BaseCache
from django.conf import settings
from django.test.client import RequestFactory

from request_cache import middleware


log = logging.getLogger(__name__)


def get_cache(name):
    """
    Return the request cache named ``name``.

    Arguments:
        name (str): The name of the request cache to load

    Returns: dict
    """
    return middleware.RequestCache.get_request_cache(name)


def get_request():
    """
    Return the current request.
    """
    return middleware.RequestCache.get_current_request()


def get_request_or_stub():
    """
    Return the current request or a stub request.

    If called outside the context of a request, construct a fake
    request that can be used to build an absolute URI.

    This is useful in cases where we need to pass in a request object
    but don't have an active request (for example, in test cases).
    """
    request = get_request()

    if request is None:
        log.warning(
            "Could not retrieve the current request.  "
            "A stub request will be created instead using settings.SITE_NAME.  "
            "This should be used *only* in test cases, never in production!"
        )

        # The settings SITE_NAME may contain a port number, so we need to
        # parse the full URL.
        full_url = "http://{site_name}".format(site_name=settings.SITE_NAME)
        parsed_url = urlparse(full_url)

        # Construct the fake request.  This can be used to construct absolute
        # URIs to other paths.
        return RequestFactory(
            SERVER_NAME=parsed_url.hostname,
            SERVER_PORT=parsed_url.port or 80,
        ).get("/")

    else:
        return request


class RequestPlusRemoteCache(BaseCache):
    """
    This Django cache backend implements two layers of caching.

    The first layer is a threadlocal dictionary that is tied to the life of a
    given request. The second layer is another named Django cache -- e.g. the
    "default" entry in settings.CACHES, typically backed by memcached.

    Some baseline rules:

    1. Treat it as a global namespace, like any other cache. The per-request
       local cache is only going to live for the lifetime of one request, but
       the backing cache is going to something like Memcached, where key
       collision is possible.

    2. Timeouts are ignored for the purposes of the in-memory request cache, but
       do apply to the backing remote cache. One consequence of this is that
       sending an explicit timeout of 0 in `set` or `add` will cause that item
       to only be cached across the duration of the request and will not cause
       a write to the remote cache.

    3. If you're in a situation where key generation performance is actually a
       concern (many thousands of lookups), then just use the request cache
       directly instead of this hybrid.
    """
    def __init__(self, name, params):
        try:
            super(RequestPlusRemoteCache, self).__init__(params)
            self._remote_cache = caches[params['REMOTE_CACHE_NAME']]
        except Exception:
            log.exception(
                "DjangoRequestCache %s could not load backing remote cache.",
                name
            )
            raise

        # This is a threadlocal that will get wiped out for each request.
        self._local_dict = get_cache("DjangoRequestCache")

    def add(self, key, value, timeout=0, version=None):
        """
        Set a value in the cache if the key does not already exist. If
        timeout is given, that timeout will be used for the key; otherwise
        the timeout will default to 0, and the (key, value) will only be stored
        in the local in-memory request cache, not the backing remote cache.

        Returns True if the value was stored, False otherwise.
        """
        local_key = self.make_key(key, version)
        if local_key in self._local_dict:
            return False

        self._local_dict[local_key] = value
        if timeout != 0:
            self._remote_cache.add(key, value, timeout=timeout, version=version)

        return True

    def get(self, key, default=None, version=None):
        """
        Fetch a given key from the cache. If the key does not exist, return
        default, which itself defaults to None.
        """
        # Simple case: It's already in our local memory...
        local_key = self.make_key(key, version)
        if local_key in self._local_dict:
            return self._local_dict[local_key]

        # Now try looking it up in our backing cache...
        external_value = self._remote_cache.get(key, default=default, version=None)

        # This might be None, but we store it anyway to prevent repeated requests
        # to the same non-existent key during the course of the request.
        self._local_dict[local_key] = external_value

        return external_value

    def set(self, key, value, timeout=0, version=None):
        """
        Set a value in the cache. If timeout is given, that timeout will be used
        for the key when storing in the remote cache; otherwise the timeout will
        default to 0, and the (key, value) will only be stored in the local
        in-memory request cache.

        For example::

            # This will only be stored in the local request cache, and should
            # be used for items where there are potentially many, many keys.
            dj_req_cache.set('has_access:user1243:block3048', True, 0)

            # This value will be stored in both the local request cache and the
        """
        local_key = self.make_key(key, version)
        self._local_dict[local_key] = value
        if timeout != 0:
            self._remote_cache.set(key, value, timeout=timeout, version=version)

    def delete(self, key, version=None):
        """
        Delete a key from the cache, failing silently.

        Note that this *will* flow through to the backing remote cache.
        """
        local_key = self.make_key(key, version)
        if local_key in self._local_:
            del self._local_dict[local_key]
        self._remote_cache.delete(key, version=version)

    def get_many(self, keys, version=None):
        mapping = {}

        # First get all the keys that exist locally.
        for key in keys:
            local_key = self.make_key(key)
            if local_key in self._local_dict:
                mapping[key] = self._local_dict[local_key]

        # Now check the external cache for everything that we didn't find
        remaining_keys = set(keys) - set(mapping)
        external_mapping = self._remote_cache.get_many(remaining_keys, version=version)

        # Update both the mapping that we're returning as well as our local cache
        mapping.update(external_mapping)
        self._local_dict.update({
            self.make_key(key): value for key, value in external_mapping.items()
        })

        return mapping

    def set_many(self, data, timeout=0, version=None):
        self._local_dict.update({
            self.make_key(key): value for key, value in data.items()
        })
        self._remote_cache.set_many(data, timeout=timeout, version=version)

    def delete_many(self, keys, version=None):
        for key in keys:
            del self._local_dict[self.make_key(key)]
        self._remote_cache.delete_many(keys)

    def clear(self):
        self._local_dict.clear()
        self._remote_cache.clear()

    def close(self, **kwargs):
        self._local_dict.clear()
        self._remote_cache.close()
