"""
Common utilities for tests in block_cache module
"""

from ..transformer import BlockStructureTransformer


class MockXBlock(object):
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
        return [self.modulestore.get_item(child) for child in self.children]


class MockModulestore(object):
    def set_blocks(self, blocks):
        self.blocks = blocks

    def get_item(self, block_key, depth=None):
         return self.blocks.get(block_key)


class MockCache(object):
    def __init__(self):
        self.map = {}

    def set(self, key, val):
        self.map[key] = val

    def get(self, key, default):
        return self.map.get(key, default)

    def set_many(self, map):
        for key, val in map.iteritems():
            self.set(key, val)

    def get_many(self, keys):
        return {key: self.map[key] for key in keys if key in self.map}

    def delete(self, key):
        del self.map[key]


class MockModulestoreFactory(object):
    @classmethod
    def create(cls, children_map):
        modulestore = MockModulestore()
        modulestore.set_blocks({
            block_key: MockXBlock(block_key, children=children, modulestore=modulestore)
            for block_key, children in enumerate(children_map)
        })
        return modulestore


class MockUserInfo(object):
    def has_staff_access(self):
        return False


class MockTransformer(BlockStructureTransformer):
    VERSION = 1
    def transform(self, user_info, block_structure):
        pass


class ChildrenMapTestMixin(object):
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

    def create_block_structure(self, block_structure_cls, children_map):
        # create block structure
        block_structure = block_structure_cls(root_block_key=0)

        # add_relation
        for parent, children in enumerate(children_map):
            for child in children:
               block_structure.add_relation(parent, child)
        return block_structure

    def get_parents_map(self, children_map):
        parent_map = [[] for _ in children_map]
        for parent, children in enumerate(children_map):
            for child in children:
                parent_map[child].append(parent)
        return parent_map

    def assert_block_structure(self, block_structure, children_map, missing_blocks=None):
        if not missing_blocks:
            missing_blocks = []

        for block_key, children in enumerate(children_map):
            self.assertEquals(
                block_structure.has_block(block_key),
                block_key not in missing_blocks,
            )
            if block_key not in missing_blocks:
                self.assertEquals(
                    set(block_structure.get_children(block_key)),
                    set(children),
                )

        parents_map = self.get_parents_map(children_map)
        for block_key, parents in enumerate(parents_map):
            if block_key not in missing_blocks:
                self.assertEquals(
                    set(block_structure.get_parents(block_key)),
                    set(parents),
                )
