"""
THE TESTS IN THIS MODULE SHOULD BE RUN ON THE SAME PROCESS TO BE MEANINGFUL!!!

The tests in this module look kind of goofy, but the idea is to make sure that
cache values can't leak between different TestCase classes and methods. The need
for this will go away whenever Django merges the fix to reset the caches between
tests (https://code.djangoproject.com/ticket/11505).
"""
from django.core.cache import caches

from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase, SharedModuleStoreTestCase


class CacheCheckMixin(object):
    """Base mixin that does our cache check."""

    def check_caches(self, key):
        """Check that caches are empty, and add values."""
        for cache in caches.all():
            self.assertIsNone(cache.get(key))
            cache.set(key, "Not None")


class CacheModuleStoreTestCaseParent(ModuleStoreTestCase, CacheCheckMixin):
    """Make sure that we're clearing cache values between tests."""

    def test_cache_reset_1(self):
        """Check to make sure cache is empty, and add values to it."""
        self.check_caches("mstc_cache_test_key")

    def test_cache_reset_2(self):
        """Check to make sure cache is empty, and add values to it."""
        self.check_caches("mstc_cache_test_key")


class CacheModuleStoreTestCaseChild(CacheModuleStoreTestCaseParent):  # pylint: disable=test-inherits-tests
    """Make sure that we're clearing cache values between classes."""


class CacheSharedModuleStoreTestCaseParent(SharedModuleStoreTestCase, CacheCheckMixin):
    """Make sure that we're clearing cache values between tests."""

    def test_cache_reset_1(self):
        """Check to make sure cache is empty, and add values to it."""
        self.check_caches("smstc_cache_test_key")

    def test_cache_reset_2(self):
        """Check to make sure cache is empty, and add values to it."""
        self.check_caches("smstc_cache_test_key")


class CacheSharedModuleStoreTestCaseChild(CacheSharedModuleStoreTestCaseParent):  # pylint: disable=test-inherits-tests
    """Make sure that we're clearing cache values between classes."""
