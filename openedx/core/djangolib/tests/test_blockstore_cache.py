"""
Tests for BundleCache
"""
from unittest.mock import patch

from django.test import TestCase
from openedx.core.djangolib.blockstore_cache import BundleCache
from openedx.core.djangoapps.content_libraries.tests.base import (
    BlockstoreAppTestMixin,
    requires_blockstore,
    requires_blockstore_app,
)
from openedx.core.lib import blockstore_api as api


class TestWithBundleMixin:
    """
    Mixin that gives every test method access to a bundle + draft
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.collection = api.create_collection(title="Collection")
        cls.bundle = api.create_bundle(cls.collection.uuid, title="Test Bundle", slug="test")
        cls.draft = api.get_or_create_bundle_draft(cls.bundle.uuid, draft_name="test-draft")


@patch('openedx.core.djangolib.blockstore_cache.MAX_BLOCKSTORE_CACHE_DELAY', 0)
class BundleCacheTestMixin(TestWithBundleMixin):
    """
    Tests for BundleCache
    """

    def test_bundle_cache(self):
        """
        Test caching data related to a bundle (no draft)
        """
        cache = BundleCache(self.bundle.uuid)

        key1 = ("some", "key", "1")
        key2 = ("key2", )

        value1 = "value1"
        cache.set(key1, value1)
        value2 = {"this is": "a dict", "for": "key2"}
        cache.set(key2, value2)
        assert cache.get(key1) == value1
        assert cache.get(key2) == value2

        # Now publish a new version of the bundle:
        api.write_draft_file(self.draft.uuid, "test.txt", "we need a changed file in order to publish a new version")
        api.commit_draft(self.draft.uuid)

        # Now the cache should be invalidated
        # (immediately since we set MAX_BLOCKSTORE_CACHE_DELAY to 0)
        assert cache.get(key1) is None
        assert cache.get(key2) is None

    def test_bundle_draft_cache(self):
        """
        Test caching data related to a bundle draft
        """
        cache = BundleCache(self.bundle.uuid, draft_name=self.draft.name)

        key1 = ("some", "key", "1")
        key2 = ("key2", )

        value1 = "value1"
        cache.set(key1, value1)
        value2 = {"this is": "a dict", "for": "key2"}
        cache.set(key2, value2)
        assert cache.get(key1) == value1
        assert cache.get(key2) == value2

        # Now make a change to the draft (doesn't matter if we commit it or not)
        api.write_draft_file(self.draft.uuid, "test.txt", "we need a changed file in order to publish a new version")

        # Now the cache should be invalidated
        # (immediately since we set MAX_BLOCKSTORE_CACHE_DELAY to 0)
        assert cache.get(key1) is None
        assert cache.get(key2) is None


class BundleCacheClearTest(TestWithBundleMixin, TestCase):
    """
    Tests for BundleCache's clear() method.
    Requires MAX_BLOCKSTORE_CACHE_DELAY to be non-zero. This clear() method does
    not actually clear the cache but rather just means "a new bundle/draft
    version has been created, so immediately start reading/writing cache keys
    using the new version number.
    """

    def test_bundle_cache_clear(self):
        """
        Test the cache clear() method
        """
        cache = BundleCache(self.bundle.uuid)
        key1 = ("some", "key", "1")
        value1 = "value1"
        cache.set(key1, value1)
        assert cache.get(key1) == value1

        # Now publish a new version of the bundle:
        api.write_draft_file(self.draft.uuid, "test.txt", "we need a changed file in order to publish a new version")
        api.commit_draft(self.draft.uuid)

        # Now the cache will not be immediately invalidated; it takes up to MAX_BLOCKSTORE_CACHE_DELAY seconds.
        # Since this is a new bundle and we _just_ accessed the cache for the first time, we can be confident
        # it won't yet be automatically invalidated.
        assert cache.get(key1) == value1
        # Now "clear" the cache, forcing the check of the new version:
        cache.clear()
        assert cache.get(key1) is None


@requires_blockstore
class BundleCacheBlockstoreServiceTest(BundleCacheTestMixin, TestCase):
    """
    Tests BundleCache using the standalone Blockstore service.
    """


@requires_blockstore_app
class BundleCacheTest(BundleCacheTestMixin, BlockstoreAppTestMixin, TestCase):
    """
    Tests BundleCache using the installed Blockstore app.
    """
