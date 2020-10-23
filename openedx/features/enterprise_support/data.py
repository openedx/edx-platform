"""
A module for managing cache- and request-scoped data about enterprise customers.
"""
from django.conf import settings
from django.core.cache import cache as django_cache
from django.utils.functional import cached_property
from edx_django_utils.cache import TieredCache, get_cache_key


ENTERPRISE_CUSTOMER_KEY_NAME = 'enterprise_customer'
# See https://open-edx-proposals.readthedocs.io/en/latest/oep-0022-bp-django-caches.html#common-caching-defect-and-fix
_CACHE_MISS = '__CACHE_MISS__'


class EnterpriseCache:
    def __init__(self, request):
        self._cookies = request.COOKIES
        self._session = request.session
        self._query_params = request.GET

    @staticmethod
    def _django_cache_get(key):
        return django_cache.get(key, _CACHE_MISS)

    @staticmethod
    def _django_cache_set(key, value):
        django_cache.set(key, value, settings.ENTERPRISE_API_CACHE_TIMEOUT)

    @staticmethod
    def _django_customer_cache_key(uuid, username=settings.ENTERPRISE_SERVICE_WORKER_USERNAME):
        """The cache key used to get cached Enterprise Customer data."""
        return get_cache_key(
            resource='enterprise-customer',
            resource_id=uuid,
            username=username,
        )

    def cache_customer_data(self, enterprise_customer_data):
        """Add this customer's data to the Django cache."""
        cache_key = self._django_customer_cache_key(enterprise_customer_data['uuid'])
        self._django_cache_set(cache_key, enterprise_customer_data)

    def enterprise_customer_from_cache(self, uuid):
        """
        Retrieve enterprise customer data associated with the given ``uuid`` from the Django cache,
        returning a ``__CACHE_MISS__`` if absent.
        """
        cache_key = self._django_customer_cache_key(uuid)
        return self._django_cache_get(cache_key)

    def add_enterprise_customer_to_session(self, enterprise_customer):
        """ Add the given enterprise_customer data to the request's session. """
        self._session[ENTERPRISE_CUSTOMER_KEY_NAME] = enterprise_customer

    def enterprise_customer_from_session(self):
        """
        Retrieve enterprise_customer data from the request's session,
        returning a ``__CACHE_MISS__`` if absent.
        """
        return self._session.get(ENTERPRISE_CUSTOMER_KEY_NAME, _CACHE_MISS)

    def enterprise_customer_uuid_from_session(self):
        """
        Retrieve an enterprise customer UUID from the request's session,
        returning a ``__CACHE_MISS__`` if absent.  Note that this may
        return ``None``, which indicates that we've previously looked
        for an associated customer for this request's user, and
        none was present.
        """
        customer_data = self.enterprise_customer_from_session()
        if customer_data is not _CACHE_MISS:
            customer_data = customer_data or {}
            return customer_data.get('uuid')
        return _CACHE_MISS

    def enterprise_customer_uuid_from_query_param(self):
        """
        Returns an enterprise customer UUID from the given request's GET data,
        or ``__CACHE_MISS__`` if not present.
        """
        return self._query_params.get(ENTERPRISE_CUSTOMER_KEY_NAME, _CACHE_MISS)

    def add_enterprise_customer_uuid_to_cookie(self, uuid):
        """ Add the given customer uuid to the request's cookies. """
        self._cookies[settings.ENTERPRISE_CUSTOMER_COOKIE_NAME] = uuid

    def enterprise_customer_uuid_from_cookie(self):
        """
        Returns an enterprise customer UUID from the given request's cookies,
        or ``__CACHE_MISS__`` if not present.
        """
        return self._cookies.get(settings.ENTERPRISE_CUSTOMER_COOKIE_NAME, _CACHE_MISS)


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
 
