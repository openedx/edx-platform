"""
Cache utilities.
"""
import hashlib
import threading

from django.core.cache import cache as django_cache
from django.core.cache.backends.base import DEFAULT_TIMEOUT
from django.utils.encoding import force_str

FORCE_CACHE_MISS_PARAM = 'force_cache_miss'
DEFAULT_NAMESPACE = 'edx_django_utils.cache'
DEFAULT_REQUEST_CACHE_NAMESPACE = f'{DEFAULT_NAMESPACE}.default'
SHOULD_FORCE_CACHE_MISS_KEY = 'edx_django_utils.cache.should_force_cache_miss'

_CACHE_MISS = object()


def get_cache_key(**kwargs):
    """
    Get MD5 encoded cache key for given arguments.

    **Note:** We convert keyword arguments to their string form to build the cache key. So do not pass
    arguments that can't be converted to strings.  Also, don't pass arguments that may not consistently
    be converted to the same string, like an unsorted dict.
    Here is the format of key before MD5 encryption.
        key1:value1__key2:value2 ...
    Example:
        >>> get_cache_key(site_domain="example.com", resource="catalogs")
        # Here is key format for above call
        # "site_domain:example.com__resource:catalogs"
        a54349175618ff1659dee0978e3149ca
    Arguments:
        **kwargs: Key word arguments that need to be present in cache key.
    Returns:
         An MD5 encoded key uniquely identified by the key word arguments.
    """
    key = '__'.join(['{}:{}'.format(k, force_str(v)) for k, v in sorted(kwargs.items())])

    return hashlib.md5(key.encode('utf-8')).hexdigest()


class _RequestCache(threading.local):
    """
    A thread-local for storing the per-request caches.

    The data is a dict of dicts, keyed by namespace.
    """
    def __init__(self):
        super().__init__()
        self._data = {}

    def clear(self):
        """
        Clears all data for all namespaces.
        """
        self._data = {}

    def data(self, namespace):
        """
        Gets the thread.local data (dict) for a given namespace.

        Args:
            namespace (string): The namespace, or key, of the data dict.

        Returns:
            (dict)

        """
        assert namespace

        if namespace in self._data:
            return self._data[namespace]

        new_data = {}
        self._data[namespace] = new_data
        return new_data


# Singleton with thread-local cache
_REQUEST_CACHE = _RequestCache()


class RequestCache:
    """
    A namespaced request cache for caching per-request data.
    """

    def __init__(self, namespace=None):
        """
        Creates a request cache with the provided namespace.

        Args:
            namespace (string): (optional) uses 'default' if not provided.
        """
        assert namespace != DEFAULT_REQUEST_CACHE_NAMESPACE,\
            f'Optional namespace can not be {DEFAULT_REQUEST_CACHE_NAMESPACE}.'
        self.namespace = namespace or DEFAULT_REQUEST_CACHE_NAMESPACE

    @classmethod
    def clear_all_namespaces(cls):
        """
        Clears the data for all namespaces.
        """
        _REQUEST_CACHE.clear()

    @property
    def data(self):
        """
        Returns the namespaced cached key/value pairs as a dict.
        """
        return _REQUEST_CACHE.data(self.namespace)

    def clear(self):
        """
        Clears data for the namespaced request cache.
        """
        self.data.clear()

    def get_cached_response(self, key):
        """
        Retrieves a CachedResponse for the provided key.

        Args:
            key (string)

        Returns:
            A CachedResponse with is_found status and value.

        """
        cached_value = self.data.get(key, _CACHE_MISS)
        is_found = cached_value is not _CACHE_MISS
        return CachedResponse(is_found, key, cached_value)

    def set(self, key, value):
        """
        Caches the value for the provided key.

        Args:
            key (string)
            value (object)

        """
        self.data[key] = value

    def setdefault(self, key, value):
        """
        Sets the value for the provided key if it has not yet been set.

        Args:
            key (string)
            value (object)

        """
        self.data.setdefault(key, value)

    def delete(self, key):
        """
        Deletes the cached value for the provided key.

        Args:
            key (string)

        """
        if key in self.data:
            del self.data[key]


DEFAULT_REQUEST_CACHE = RequestCache()


class TieredCache:
    """
    A two tiered caching object with a request cache backed by a django cache.
    """

    @classmethod
    def get_cached_response(cls, key):
        """
        Retrieves a CachedResponse for the provided key.

        Args:
            key (string)

        Returns:
            A CachedResponse with is_found status and value.

        """
        request_cached_response = DEFAULT_REQUEST_CACHE.get_cached_response(key)
        if not request_cached_response.is_found:
            django_cached_response = cls._get_cached_response_from_django_cache(key)
            cls._set_request_cache_if_django_cache_hit(key, django_cached_response)
            return django_cached_response

        return request_cached_response

    @staticmethod
    def set_all_tiers(key, value, django_cache_timeout=DEFAULT_TIMEOUT):
        """
        Caches the value for the provided key in both the request cache and the
        django cache.

        Args:
            key (string)
            value (object)
            django_cache_timeout (int): (Optional) Timeout used to determine
                if and for how long to cache in the django cache. A timeout of
                0 will skip the django cache. If timeout is provided, use that
                timeout for the key; otherwise use the default cache timeout.

        """
        DEFAULT_REQUEST_CACHE.set(key, value)
        django_cache.set(key, value, django_cache_timeout)

    @staticmethod
    def delete_all_tiers(key):
        """
        Deletes the cached value for the provided key in both the request cache and the
        django cache.

        Args:
            key (string)

        """
        DEFAULT_REQUEST_CACHE.delete(key)
        django_cache.delete(key)

    @staticmethod
    def dangerous_clear_all_tiers():
        """
        This clears both the default request cache and the entire django
        backing cache.

        Important: This should probably only be called for testing purposes.

        TODO: Move CacheIsolationMixin from edx-platform to edx-django-utils
        and kill this method.

        """
        DEFAULT_REQUEST_CACHE.clear()
        django_cache.clear()

    @staticmethod
    def _get_cached_response_from_django_cache(key):
        """
        Retrieves a CachedResponse for the given key from the django cache.

        If the request was set to force cache misses, then this will always
        return a cache miss response.

        Args:
            key (string)

        Returns:
            A CachedResponse with is_found status and value.

        """
        if TieredCache._should_force_django_cache_miss():
            return CachedResponse(is_found=False, key=key, value=None)

        cached_value = django_cache.get(key, _CACHE_MISS)
        is_found = cached_value is not _CACHE_MISS
        return CachedResponse(is_found, key, cached_value)

    @staticmethod
    def _set_request_cache_if_django_cache_hit(key, django_cached_response):
        """
        Sets the value in the request cache if the django cached response was a hit.

        Args:
            key (string)
            django_cached_response (CachedResponse)

        """
        if django_cached_response.is_found:
            DEFAULT_REQUEST_CACHE.set(key, django_cached_response.value)

    @staticmethod
    def _get_and_set_force_cache_miss(request):
        """
        Gets value for request query parameter FORCE_CACHE_MISS
        and sets it in the default request cache.

        This functionality is only available for staff.

        Example:
            http://clobert.com/api/v1/resource?force_cache_miss=true

        """
        if not (request.user and request.user.is_active and request.user.is_staff):
            force_cache_miss = False
        else:
            force_cache_miss = request.GET.get(FORCE_CACHE_MISS_PARAM, 'false').lower() == 'true'
        DEFAULT_REQUEST_CACHE.set(SHOULD_FORCE_CACHE_MISS_KEY, force_cache_miss)

    @classmethod
    def _should_force_django_cache_miss(cls):
        """
        Returns True if the tiered cache should force a cache miss for the
        django cache, and False otherwise.

        """
        cached_response = DEFAULT_REQUEST_CACHE.get_cached_response(SHOULD_FORCE_CACHE_MISS_KEY)
        return False if not cached_response.is_found else cached_response.value


class CachedResponseError(Exception):
    """
    Error used when CachedResponse is misused.
    """
    USAGE_MESSAGE = 'CachedResponse was misused. Try the attributes is_found, value or key.'

    def __init__(self, message=USAGE_MESSAGE):  # pylint: disable=useless-super-delegation
        super().__init__(message)


class CachedResponse:
    """
    Represents a cache response including is_found status and value.
    """
    def __init__(self, is_found, key, value):
        """
        Creates a cached response object.

        Args:
            is_found (bool): True if the key was found in the cache, False
                otherwise.
            key (string): The key originally used to retrieve the value.
            value (object)
        """
        self.key = key
        self.is_found = is_found
        if self.is_found:
            self.value = value

    def __repr__(self):
        # Important: Do not include the cached value to help avoid any security
        # leaks that could happen if these are logged.
        return f'''CachedResponse(is_found={self.is_found}, key={self.key}, value='*****')'''

    def get_value_or_default(self, default):
        """
        Returns value for a cache hit, or the passed default for a cache miss.

        This method is safe to use, even for a cache_miss.

        WARNING: Never pass None as the default and then test the return value
        of this method. Use is_found instead for any checks.

        """
        return default if not self.is_found else self.value

    def __bool__(self):
        raise CachedResponseError()

    def __eq__(self, other):
        if not isinstance(other, CachedResponse):
            raise CachedResponseError()
        if self.is_found != other.is_found:
            return False

        if self.is_found:
            return (self.key, self.value) == (other.key, other.value)
        else:
            return self.key == other.key  # cache misses have no value attribute

    def __ne__(self, other):
        """Overrides the default implementation (unnecessary in Python 3)"""
        return not self.__eq__(other)
