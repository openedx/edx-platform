"""
Utility classes for testing django applications.

:py:class:`CacheIsolationMixin`
    A mixin helping to write tests which are isolated from cached data.

:py:class:`CacheIsolationTestCase`
    A TestCase baseclass that has per-test isolated caches.
"""


import copy
import re
from unittest import skipUnless

import crum
from django.conf import settings
from django.contrib import sites
from django.core.cache import caches
from django.db import DEFAULT_DB_ALIAS, connections
from django.test import RequestFactory, TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from edx_django_utils.cache import RequestCache


class CacheIsolationMixin(object):
    """
    This class can be used to enable specific django caches for
    the specific TestCase that it's mixed into.

    Usage:

    Use the ENABLED_CACHES to list the names of caches that should
    be enabled in the context of this TestCase. These caches will
    use a loc_mem_cache with the default settings.

    Set the class variable CACHES to explicitly specify the cache settings
    that should be overridden. This class will insert those values into
    django.conf.settings, and will reset all named caches before each
    test.

    If both CACHES and ENABLED_CACHES are not None, raises an error.
    """

    CACHES = None
    ENABLED_CACHES = None

    __settings_overrides = []
    __old_settings = []

    @classmethod
    def setUpClass(cls):
        super(CacheIsolationMixin, cls).setUpClass()
        cls.start_cache_isolation()

    @classmethod
    def tearDownClass(cls):
        cls.end_cache_isolation()
        super(CacheIsolationMixin, cls).tearDownClass()

    def setUp(self):
        super(CacheIsolationMixin, self).setUp()

        self.clear_caches()
        self.addCleanup(self.clear_caches)

    @classmethod
    def start_cache_isolation(cls):
        """
        Start cache isolation by overriding the settings.CACHES and
        flushing the cache.
        """
        cache_settings = None
        if cls.CACHES is not None and cls.ENABLED_CACHES is not None:
            raise Exception(
                "Use either CACHES or ENABLED_CACHES, but not both"
            )

        if cls.CACHES is not None:
            cache_settings = cls.CACHES
        elif cls.ENABLED_CACHES is not None:
            cache_settings = {
                'default': {
                    'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
                }
            }

            cache_settings.update({
                cache_name: {
                    'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
                    'LOCATION': cache_name,
                    'KEY_FUNCTION': 'common.djangoapps.util.memcache.safe_key',
                    'OPTIONS': {
                        'MAX_ENTRIES': 1000,
                    },
                } for cache_name in cls.ENABLED_CACHES
            })

        if cache_settings is None:
            return

        cls.__old_settings.append(copy.deepcopy(settings.CACHES))
        override = override_settings(CACHES=cache_settings)
        override.__enter__()
        cls.__settings_overrides.append(override)

        assert settings.CACHES == cache_settings

        # Start with empty caches
        cls.clear_caches()

    @classmethod
    def end_cache_isolation(cls):
        """
        End cache isolation by flushing the cache and then returning
        settings.CACHES to its original state.
        """
        # Make sure that cache contents don't leak out after the isolation is ended
        cls.clear_caches()

        if cls.__settings_overrides:
            cls.__settings_overrides.pop().__exit__(None, None, None)
            assert settings.CACHES == cls.__old_settings.pop()

    @classmethod
    def clear_caches(cls):
        """
        Clear all of the caches defined in settings.CACHES.
        """
        # N.B. As of 2016-04-20, Django won't return any caches
        # from django.core.cache.caches.all() that haven't been
        # accessed using caches[name] previously, so we loop
        # over our list of overridden caches, instead.
        for cache in settings.CACHES:
            caches[cache].clear()

        # The sites framework caches in a module-level dictionary.
        # Clear that.
        sites.models.SITE_CACHE.clear()

        RequestCache.clear_all_namespaces()


class CacheIsolationTestCase(CacheIsolationMixin, TestCase):
    """
    A TestCase that isolates caches (as described in
    :py:class:`CacheIsolationMixin`) at class setup, and flushes the cache
    between every test.
    """


class _AssertNumQueriesContext(CaptureQueriesContext):
    """
    This is a copy of Django's internal class of the same name, with the
    addition of being able to provide a table_blacklist used to filter queries
    before comparing the count.
    """
    def __init__(self, test_case, num, connection, table_blacklist=None):
        """
        Same as Django's _AssertNumQueriesContext __init__, with the addition of
        the following argument:
            table_blacklist (List): A list of table names to filter out of the
                set of queries that get counted.
        """
        self.test_case = test_case
        self.num = num
        self.table_blacklist = table_blacklist
        super(_AssertNumQueriesContext, self).__init__(connection)

    def __exit__(self, exc_type, exc_value, traceback):
        def is_unfiltered_query(query):
            """
            Returns True if the query does not contain a blacklisted table, and
            False otherwise.

            Note: This is a simple naive implementation that makes no attempt
            to parse the query.
            """
            if self.table_blacklist:
                for table in self.table_blacklist:
                    # SQL contains the following format for columns:
                    # "table_name"."column_name".  The regex ensures there is no
                    # "." before the name to avoid matching columns.
                    if re.search(r'[^.]"{}"'.format(table), query['sql']):
                        return False
            return True

        super(_AssertNumQueriesContext, self).__exit__(exc_type, exc_value, traceback)
        if exc_type is not None:
            return
        filtered_queries = [query for query in self.captured_queries if is_unfiltered_query(query)]
        executed = len(filtered_queries)
        self.test_case.assertEqual(
            executed, self.num,
            u"%d queries executed, %d expected\nCaptured queries were:\n%s" % (
                executed, self.num,
                '\n'.join(
                    query['sql'] for query in filtered_queries
                )
            )
        )


class FilteredQueryCountMixin(object):
    """
    Mixin to add to any subclass of Django's TestCase that replaces
    assertNumQueries with one that accepts a blacklist of tables to filter out
    of the count.
    """
    def assertNumQueries(self, num, func=None, table_blacklist=None, *args, **kwargs):
        """
        Used to replace Django's assertNumQueries with the same capability, with
        the addition of the following argument:
            table_blacklist (List): A list of table names to filter out of the
                set of queries that get counted.
        """
        using = kwargs.pop("using", DEFAULT_DB_ALIAS)
        conn = connections[using]

        context = _AssertNumQueriesContext(self, num, conn, table_blacklist=table_blacklist)
        if func is None:
            return context

        with context:
            func(*args, **kwargs)


def get_mock_request(user=None):
    """
    Create a request object for the user, if specified.
    """
    # Import is placed here to avoid model import at project startup.
    from django.contrib.auth.models import AnonymousUser
    request = RequestFactory().get('/')
    if user is not None:
        request.user = user
    else:
        request.user = AnonymousUser()
    request.is_secure = lambda: True
    request.get_host = lambda: "edx.org"
    crum.set_current_request(request)
    return request


def skip_unless_cms(func):
    """
    Only run the decorated test in the CMS test suite
    """
    return skipUnless(settings.ROOT_URLCONF == 'cms.urls', 'Test only valid in CMS')(func)


def skip_unless_lms(func):
    """
    Only run the decorated test in the LMS test suite
    """
    return skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in LMS')(func)
