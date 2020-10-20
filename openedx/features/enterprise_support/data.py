"""
A module for managing cache- and request-scoped data about enterprise customers.
"""
from django.conf import settings
from django.core.cache import cache as django_cache
from django.utils.functional import cached_property


class EnterpriseCache:
    def __init__(self, request):
        self._cookies = request.COOKIES
        self._session = request.session
        self._query_params = request.GET

    @staticmethod
    def _django_cache_get(key):
        return django_cache.get(key)

    @staticmethod
    def _django_cache_set(key, value):
        django_cache.set(key, value, settings.ENTERPRISE_API_CACHE_TIMEOUT)


class EnterpriseData:
    """
    Abstract away where data about a user's associated enterprise customer might be stored,
    and just give the client the data it wants.
    """
    def __init__(self, request):
        self._request = request
        self._cache = EnterpriseCache(request)

    def __enter__(self):
        return self

    def __exit__(self, _type, value, traceback):
        """
        Sets things in the cache, if appropriate.
        """

    @cached_property
    def customer_uuid(self):
        """
        Returns a UUID of the Enterprise Customer associated with this request's user, or None.
        """
        pass

    @cached_property
    def customer_data(self):
        pass

    @cached_property
    def learner_portal_data(self):
        pass
