"""
...
"""
from collections import defaultdict
from graph_traversals import traverse_topologically, traverse_post_order
from logging import getLogger

from transformer import BlockStructureTransformers


logger = getLogger(__name__)  # pylint: disable=C0103

TRANSFORMER_VERSION_KEY = '_version'


class BlockStructure(object):
    """
    A class to encapsulate a structure of blocks, a directed acyclic graph of blocks.
    """
    class BlockRelations(object):
        def __init__(self):
            self.parents = []
            self.children = []

    def __init__(self, root_block_key):
        self.root_block_key = root_block_key
        self._block_relations = defaultdict(self.BlockRelations)
        self._add_block(self._block_relations, root_block_key)

    def __iter__(self):
        return self.topological_traversal()

    def add_relation(self, parent_key, child_key):
        self._add_relation(self._block_relations, parent_key, child_key)

    def get_parents(self, usage_key):
        return self._block_relations.get(usage_key).parents if self.has_block(usage_key) else []

    def get_children(self, usage_key):
        return self._block_relations[usage_key].children if self.has_block(usage_key) else []

    def has_block(self, usage_key):
        return usage_key in self._block_relations

    def get_block_keys(self):
        return self._block_relations.iterkeys()

    def topological_traversal(self, get_result=None, predicate=None):
        return traverse_topologically(
            start_node=self.root_block_key,
            get_parents=self.get_parents,
            get_children=self.get_children,
            get_result=get_result,
            predicate=predicate,
        )

    def post_order_traversal(self, get_result=None, predicate=None):
        return traverse_post_order(
            start_node=self.root_block_key,
            get_children=self.get_children,
            get_result=get_result,
            predicate=predicate,
        )

    def prune(self):
        # create a new block relations map with only those blocks that are still linked
        pruned_block_relations = defaultdict(self.BlockRelations)
        old_block_relations = self._block_relations

        # def do_for_each_block(block_key):
        #     if block_key in old_block_relations:
        #         self._add_block(pruned_block_relations, block_key)
        #
        #         for parent in old_block_relations[block_key].parents:
        #             if parent in pruned_block_relations:
        #                 self._add_relation(pruned_block_relations, parent, block_key)

        def do_for_each_block(block_key):
            if block_key in old_block_relations:
                self._add_block(pruned_block_relations, block_key)

                for child in old_block_relations[block_key].children:
                    if child in pruned_block_relations:
                        self._add_relation(pruned_block_relations, block_key, child)

        list(self.post_order_traversal(get_result=do_for_each_block))
        self._block_relations = pruned_block_relations

    @classmethod
    def _add_relation(cls, block_relations, parent_key, child_key):
        block_relations[child_key].parents.append(parent_key)
        block_relations[parent_key].children.append(child_key)

    @classmethod
    def _add_block(cls, block_relations, block_key):
        _ = block_relations[block_key]


class BlockStructureBlockData(BlockStructure):
    """
    A sub-class of BlockStructure that encapsulates data captured about the blocks.
    """
    class BlockData(object):
        def __init__(self):
            # dictionary mapping xblock field names to their values.
            self._xblock_fields = {}

            # dictionary mapping transformers' IDs to their collected data.
            self._transformer_data = defaultdict(dict)

    def __init__(self, root_block_key):
        super(BlockStructureBlockData, self).__init__(root_block_key)

        # dictionary mapping usage keys to BlockData
        self._block_data_map = defaultdict(self.BlockData)

        # dictionary mapping transformer IDs to block-structure-wide transformer data
        self._transformer_data = defaultdict(dict)

    def get_xblock_field(self, usage_key, field_name, default=None):
        block_data = self._block_data_map.get(usage_key)
        return block_data._xblock_fields.get(field_name, default) if block_data else default

    def get_transformer_data(self, transformer, key, default=None):
        return self._transformer_data.get(transformer.name(), {}).get(key, default)

    def set_transformer_data(self, transformer, key, value):
        self._transformer_data[transformer.name()][key] = value

    def get_transformer_data_version(self, transformer):
        return self.get_transformer_data(transformer, TRANSFORMER_VERSION_KEY, 0)

    def get_transformer_block_data(self, usage_key, transformer, key=None, default=None):
        block_data = self._block_data_map.get(usage_key)
        if not block_data:
            return default
        else:
            transformer_data = block_data._transformer_data.get(transformer.name(), {})
            return transformer_data.get(key, default) if key else transformer_data

    def set_transformer_block_data(self, usage_key, transformer, key, value):
        self._block_data_map[usage_key]._transformer_data[transformer.name()][key] = value

    def remove_transformer_block_data(self, usage_key, transformer, key):
        self._block_data_map[usage_key]._transformer_data.get(transformer.name(), {}).pop(key, None)

    def remove_block(self, usage_key):
        # Remove block from its children.
        for child in self._block_relations[usage_key].children:
            self._block_relations[child].parents.remove(usage_key)

        # Remove block from its parents.
        for parent_key in self._block_relations[usage_key].parents:
            self._block_relations[parent_key].children.remove(usage_key)

        # Remove block.
        self._block_relations.pop(usage_key, None)
        self._block_data_map.pop(usage_key, None)

    def remove_block_if(self, removal_condition):
        def predicate(block_key):
            if removal_condition(block_key):
                self.remove_block(block_key)
                return False
            return True
        list(self.topological_traversal(predicate=predicate))


class BlockStructureCollectedData(BlockStructureBlockData):
    """
    A sub-class of BlockStructure that encapsulates information about the blocks during the collect phase.
    """
    def __init__(self, root_block_key):
        super(BlockStructureCollectedData, self).__init__(root_block_key)

        self._xblock_map = {}  # dict[UsageKey: XBlock]
        self._requested_xblock_fields = set()

    def request_xblock_fields(self, *field_names):
        self._requested_xblock_fields.update(set(field_names))

    def collect_requested_xblock_fields(self):
        if not self._requested_xblock_fields:
            return

        for xblock in self._xblock_map.itervalues():
            for field_name in self._requested_xblock_fields:
                self._set_xblock_field(xblock, field_name)

    def _set_xblock_field(self, xblock, field_name):
        if hasattr(xblock, field_name):
            self._block_data_map[xblock.location]._xblock_fields[field_name] = getattr(xblock, field_name)

    def add_xblock(self, xblock):
        self._xblock_map[xblock.location] = xblock

    def get_xblock(self, usage_key):
        return self._xblock_map[usage_key]

    def add_transformer(self, transformer):
        if transformer.VERSION == 0:
            raise Exception('VERSION attribute is not set on transformer {0}.', transformer.name())
        self.set_transformer_data(transformer, TRANSFORMER_VERSION_KEY, transformer.VERSION)


class BlockStructureFactory(object):
    @classmethod
    def create_from_modulestore(cls, root_block_key, modulestore):
        block_structure = BlockStructureCollectedData(root_block_key)

        def build_block_structure(xblock):
            """
            Helper function to recursively walk block structure
            """
            block_structure.add_xblock(xblock)
            for child in xblock.get_children():
                block_structure.add_relation(xblock.location, child.location)
                build_block_structure(child)

        root_xblock = modulestore.get_item(root_block_key, depth=None)
        build_block_structure(root_xblock)
        return block_structure

    @classmethod
    def serialize_to_cache(cls, block_structure, cache):
        cache.set(
            cls._encode_root_cache_key(block_structure.root_block_key),
            (block_structure._block_relations, block_structure._transformer_data)
        )
        cache.set_many({
            unicode(usage_key): block_data
            for usage_key, block_data
            in block_structure._block_data_map.iteritems()
        })

    @classmethod
    def create_from_cache(cls, root_block_key, cache):
        """
        Returns:
            BlockStructure, if the block structure is in the cache, and
            NoneType otherwise.
        """
        block_relations, transformer_data = cache.get(cls._encode_root_cache_key(root_block_key), (None, None))
        if block_relations:
            block_structure = BlockStructureBlockData(root_block_key)
            block_structure._block_relations = block_relations
            block_structure._transformer_data = transformer_data

            if all(
                transformer.VERSION == block_structure.get_transformer_data_version(transformer)
                for transformer in BlockStructureTransformers.get_registered_transformers()
            ):
                block_structure._block_data_map = cache.get_many(block_relations.iterkeys())
                return block_structure
            else:
                logger.info("Collected data for transformer is outdated.")

        return None

    @classmethod
    def remove_from_cache(cls, root_block_key, cache):
        cache.delete(cls._encode_root_cache_key(root_block_key))
        # TODO also remove all block data?

    @classmethod
    def _encode_root_cache_key(cls, root_block_key):
        return "root.key." + unicode(root_block_key)
