"""
Common utilities for tests in block_structure module
"""
from contextlib import contextmanager
from mock import patch
from xmodule.modulestore.exceptions import ItemNotFoundError

from ..block_structure import BlockStructureBlockData
from ..transformer import BlockStructureTransformer, FilteringTransformerMixin


class MockXBlock(object):
    """
    A mock XBlock to be used in unit tests, thereby decoupling the
    implementation of the block cache framework from the xBlock
    implementation.  This class provides only the minimum xBlock
    capabilities needed by the block cache framework.
    """
    def __init__(self, location, field_map=None, children=None, modulestore=None):
        self.location = location
        self.field_map = field_map or {}

        self.children = children or []
        self.modulestore = modulestore

    def __getattr__(self, attr):
        try:
            return self.field_map[attr]
        except KeyError:
            raise AttributeError

    def get_children(self):
        """
        Returns the children of the mock XBlock.
        """
        return [self.modulestore.get_item(child) for child in self.children]


class MockModulestore(object):
    """
    A mock Modulestore to be used in unit tests, providing only the
    minimum methods needed by the block cache framework.
    """
    def __init__(self):
        self.get_items_call_count = 0
        self.blocks = None

    def set_blocks(self, blocks):
        """
        Updates the mock modulestore with a dictionary of blocks.

        Arguments:
            blocks ({block key, MockXBlock}) - A map of block_key
            to its mock xBlock.
        """
        self.blocks = blocks

    def get_item(self, block_key, depth=None, lazy=False):  # pylint: disable=unused-argument
        """
        Returns the mock XBlock (MockXBlock) associated with the
        given block_key.

        Raises ItemNotFoundError if the item is not found.
        """
        self.get_items_call_count += 1
        item = self.blocks.get(block_key)
        if not item:
            raise ItemNotFoundError
        return item

    @contextmanager
    def bulk_operations(self, ignore):  # pylint: disable=unused-argument
        """
        A context manager for notifying the store of bulk operations.
        """
        yield


class MockCache(object):
    """
    A mock Cache object, providing only the minimum features needed
    by the block cache framework.
    """
    def __init__(self):
        # An in-memory map of cache keys to cache values.
        self.map = {}
        self.set_call_count = 0
        self.timeout_from_last_call = 0

    def set(self, key, val, timeout):
        """
        Associates the given key with the given value in the cache.
        """
        self.set_call_count += 1
        self.map[key] = val
        self.timeout_from_last_call = timeout

    def get(self, key, default=None):
        """
        Returns the value associated with the given key in the cache;
        returns default if not found.
        """
        return self.map.get(key, default)

    def delete(self, key):
        """
        Deletes the given key from the cache.
        """
        del self.map[key]


class MockModulestoreFactory(object):
    """
    A factory for creating MockModulestore objects.
    """
    @classmethod
    def create(cls, children_map):
        """
        Creates and returns a MockModulestore from the given
        children_map.

        Arguments:
            children_map ({block_key: [block_key]}) - A dictionary
                mapping a block key to a list of block keys of the
                block's corresponding children.
        """
        modulestore = MockModulestore()
        modulestore.set_blocks({
            block_key: MockXBlock(block_key, children=children, modulestore=modulestore)
            for block_key, children in enumerate(children_map)
        })
        return modulestore


class MockTransformer(BlockStructureTransformer):
    """
    A mock BlockStructureTransformer class.
    """
    VERSION = 1

    @classmethod
    def name(cls):
        # Use the class' name for Mock transformers.
        return cls.__name__

    def transform(self, usage_info, block_structure):
        pass


class MockFilteringTransformer(FilteringTransformerMixin, BlockStructureTransformer):
    """
    A mock FilteringTransformerMixin class.
    """
    VERSION = 1

    @classmethod
    def name(cls):
        # Use the class' name for Mock transformers.
        return cls.__name__

    def transform_block_filters(self, usage_info, block_structure):
        return [block_structure.create_universal_filter()]


@contextmanager
def mock_registered_transformers(transformers):
    """
    Context manager for mocking the transformer registry to return the given transformers.
    """
    with patch(
        'openedx.core.lib.block_structure.transformer_registry.TransformerRegistry.get_registered_transformers'
    ) as mock_available_transforms:
        mock_available_transforms.return_value = {transformer for transformer in transformers}
        yield


class ChildrenMapTestMixin(object):
    """
    A Test Mixin with utility methods for testing with block structures
    created and manipulated using children_map and parents_map.
    """

    #     0
    #    / \
    #   1  2
    #  / \
    # 3   4
    SIMPLE_CHILDREN_MAP = [[1, 2], [3, 4], [], [], []]

    #       0
    #      /
    #     1
    #    /
    #   2
    #  /
    # 3
    LINEAR_CHILDREN_MAP = [[1], [2], [3], []]

    #     0
    #    / \
    #   1  2
    #   \ / \
    #    3  4
    #   / \
    #  5  6
    DAG_CHILDREN_MAP = [[1, 2], [3], [3, 4], [5, 6], [], [], []]

    def create_block_structure(self, children_map, block_structure_cls=BlockStructureBlockData):
        """
        Factory method for creating and returning a block structure
        for the given children_map.
        """
        # create empty block structure
        block_structure = block_structure_cls(root_block_usage_key=0)

        # _add_relation
        for parent, children in enumerate(children_map):
            for child in children:
                block_structure._add_relation(parent, child)  # pylint: disable=protected-access
        return block_structure

    def get_parents_map(self, children_map):
        """
        Converts and returns the given children_map to a parents_map.
        """
        parent_map = [[] for _ in children_map]
        for parent, children in enumerate(children_map):
            for child in children:
                parent_map[child].append(parent)
        return parent_map

    def assert_block_structure(self, block_structure, children_map, missing_blocks=None):
        """
        Verifies that the relations in the given block structure
        equate the relations described in the children_map. Use the
        missing_blocks parameter to pass in any blocks that were removed
        from the block structure but still have a positional entry in
        the children_map.
        """
        if not missing_blocks:
            missing_blocks = []

        for block_key, children in enumerate(children_map):
            # Verify presence
            self.assertEquals(
                block_key in block_structure,
                block_key not in missing_blocks,
                'Expected presence in block_structure for block_key {} to match absence in missing_blocks.'.format(
                    unicode(block_key)
                ),
            )

            # Verify children
            if block_key not in missing_blocks:
                self.assertEquals(
                    set(block_structure.get_children(block_key)),
                    set(children),
                )

        # Verify parents
        parents_map = self.get_parents_map(children_map)
        for block_key, parents in enumerate(parents_map):
            if block_key not in missing_blocks:
                self.assertEquals(
                    set(block_structure.get_parents(block_key)),
                    set(parents),
                )
