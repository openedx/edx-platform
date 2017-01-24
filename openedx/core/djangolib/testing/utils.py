"""
Utility classes for testing django applications.

:py:class:`CacheIsolationMixin`
    A mixin helping to write tests which are isolated from cached data.

:py:class:`CacheIsolationTestCase`
    A TestCase baseclass that has per-test isolated caches.
"""

import copy
from unittest import skipUnless

import crum
from django import db
from django.contrib.auth.models import AnonymousUser
from django.core.cache import caches
from django.test import RequestFactory, TestCase, override_settings
from django.conf import settings
from django.contrib import sites
from nose.plugins import Plugin
from waffle.models import Switch

from request_cache.middleware import RequestCache


class CacheIsolationMixin(object):
    """
    This class can be used to enable specific django caches for
    specific the TestCase that it's mixed into.

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
                    'KEY_FUNCTION': 'util.memcache.safe_key',
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

        RequestCache.clear_request_cache()


class CacheIsolationTestCase(CacheIsolationMixin, TestCase):
    """
    A TestCase that isolates caches (as described in
    :py:class:`CacheIsolationMixin`) at class setup, and flushes the cache
    between every test.
    """
    @classmethod
    def setUpClass(cls):
        super(CacheIsolationTestCase, cls).setUpClass()
        cls.start_cache_isolation()

    @classmethod
    def tearDownClass(cls):
        cls.end_cache_isolation()
        super(CacheIsolationTestCase, cls).tearDownClass()

    def setUp(self):
        super(CacheIsolationTestCase, self).setUp()

        self.clear_caches()
        self.addCleanup(self.clear_caches)


class NoseDatabaseIsolation(Plugin):
    """
    nosetest plugin that resets django databases before any tests begin.

    Used to make sure that tests running in multi processes aren't sharing
    a database connection.
    """
    name = "database-isolation"

    def begin(self):
        """
        Before any tests start, reset all django database connections.
        """
        for db_ in db.connections.all():
            db_.close()


def get_mock_request(user=None):
    """
    Create a request object for the user, if specified.
    """
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


def toggle_switch(name, active=True):
    """
    Activate or deactivate a Waffle switch. The switch is created if it does not exist.

    Arguments:
        name (str): Name of the switch to be toggled.

    Keyword Arguments:
        active (bool): Whether a newly created switch should be on or off.

    Returns:
        Switch
    """
    switch, created = Switch.objects.get_or_create(name=name, defaults={'active': active})

    if not created:
        switch.active = not switch.active
        switch.save()

    return switch
