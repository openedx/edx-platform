"""
Tests for block_structure/cache.py
"""
import ddt

from openedx.core.djangolib.testing.utils import CacheIsolationTestCase

from ..config import STORAGE_BACKING_FOR_CACHE, waffle
from ..config.models import BlockStructureConfiguration
from ..exceptions import BlockStructureNotFound
from ..store import BlockStructureStore
from .helpers import ChildrenMapTestMixin, UsageKeyFactoryMixin, MockCache, MockTransformer


@ddt.ddt
class TestBlockStructureStore(UsageKeyFactoryMixin, ChildrenMapTestMixin, CacheIsolationTestCase):
    """
    Tests for BlockStructureStore
    """
    ENABLED_CACHES = ['default']
    shard = 2

    def setUp(self):
        super(TestBlockStructureStore, self).setUp()

        self.children_map = self.SIMPLE_CHILDREN_MAP
        self.block_structure = self.create_block_structure(self.children_map)
        self.add_transformers()

        self.mock_cache = MockCache()
        self.store = BlockStructureStore(self.mock_cache)

    def add_transformers(self):
        """
        Add each registered transformer to the block structure.
        Mimic collection by setting test transformer block data.
        """
        for transformer in [MockTransformer]:
            self.block_structure._add_transformer(transformer)  # pylint: disable=protected-access
            self.block_structure.set_transformer_block_field(
                self.block_key_factory(0),
                transformer,
                key='test',
                value='{} val'.format(transformer.name()),
            )

    @ddt.data(True, False)
    def test_get_none(self, with_storage_backing):
        with waffle().override(STORAGE_BACKING_FOR_CACHE, active=with_storage_backing):
            with self.assertRaises(BlockStructureNotFound):
                self.store.get(self.block_structure.root_block_usage_key)

    @ddt.data(True, False)
    def test_add_and_get(self, with_storage_backing):
        with waffle().override(STORAGE_BACKING_FOR_CACHE, active=with_storage_backing):
            self.store.add(self.block_structure)
            stored_value = self.store.get(self.block_structure.root_block_usage_key)
            self.assertIsNotNone(stored_value)
            self.assert_block_structure(stored_value, self.children_map)

    @ddt.data(True, False)
    def test_delete(self, with_storage_backing):
        with waffle().override(STORAGE_BACKING_FOR_CACHE, active=with_storage_backing):
            self.store.add(self.block_structure)
            self.store.delete(self.block_structure.root_block_usage_key)
            with self.assertRaises(BlockStructureNotFound):
                self.store.get(self.block_structure.root_block_usage_key)

    def test_uncached_without_storage(self):
        self.store.add(self.block_structure)
        self.mock_cache.map.clear()
        with self.assertRaises(BlockStructureNotFound):
            self.store.get(self.block_structure.root_block_usage_key)

    def test_uncached_with_storage(self):
        with waffle().override(STORAGE_BACKING_FOR_CACHE, active=True):
            self.store.add(self.block_structure)
            self.mock_cache.map.clear()
            stored_value = self.store.get(self.block_structure.root_block_usage_key)
            self.assert_block_structure(stored_value, self.children_map)

    @ddt.data(1, 5, None)
    def test_cache_timeout(self, timeout):
        if timeout is not None:
            BlockStructureConfiguration.objects.create(enabled=True, cache_timeout_in_seconds=timeout)
        else:
            timeout = BlockStructureConfiguration.DEFAULT_CACHE_TIMEOUT_IN_SECONDS

        self.assertEquals(self.mock_cache.timeout_from_last_call, 0)
        self.store.add(self.block_structure)
        self.assertEquals(self.mock_cache.timeout_from_last_call, timeout)
