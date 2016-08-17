"""
Module with family of classes for block structures.
    BlockStructure - responsible for block existence and relations.
    BlockStructureBlockData - responsible for block & transformer data.
    BlockStructureModulestoreData - responsible for xBlock data.

The following internal data structures are implemented:
    _BlockRelations - Data structure for a single block's relations.
    _BlockData - Data structure for a single block's data.
"""
from collections import defaultdict
from logging import getLogger

from openedx.core.lib.graph_traversals import traverse_topologically, traverse_post_order

from .exceptions import TransformerException


logger = getLogger(__name__)  # pylint: disable=invalid-name


# A dictionary key value for storing a transformer's version number.
TRANSFORMER_VERSION_KEY = '_version'


class _BlockRelations(object):
    """
    Data structure to encapsulate relationships for a single block,
    including its children and parents.
    """
    def __init__(self):

        # List of usage keys of this block's parents.
        # list [UsageKey]
        self.parents = []

        # List of usage keys of this block's children.
        # list [UsageKey]
        self.children = []


class BlockStructure(object):
    """
    Base class for a block structure.  BlockStructures are constructed
    using the BlockStructureFactory and then used as the currency across
    Transformers.

    This base class keeps track of the block structure's root_block_usage_key,
    the existence of the blocks, and their parents and children
    relationships (graph nodes and edges).
    """
    def __init__(self, root_block_usage_key):

        # The usage key of the root block for this structure.
        # UsageKey
        self.root_block_usage_key = root_block_usage_key

        # Map of a block's usage key to its block relations. The
        # existence of a block in the structure is determined by its
        # presence in this map.
        # defaultdict {UsageKey: _BlockRelations}
        self._block_relations = defaultdict(_BlockRelations)

        # Add the root block.
        self._add_block(self._block_relations, root_block_usage_key)

    def __iter__(self):
        """
        The default iterator for a block structure is a topological
        traversal since it's the more common case and we currently
        need to support DAGs.
        """
        return self.topological_traversal()

    #--- Block structure relation methods ---#

    def get_parents(self, usage_key):
        """
        Returns the parents of the block identified by the given
        usage_key.

        Arguments:
            usage_key - The usage key of the block whose parents
                are to be returned.

        Returns:
            [UsageKey] - A list of usage keys of the block's parents.
        """
        return self._block_relations[usage_key].parents if self.has_block(usage_key) else []

    def get_children(self, usage_key):
        """
        Returns the children of the block identified by the given
        usage_key.

        Arguments:
            usage_key - The usage key of the block whose children
                are to be returned.

        Returns:
            [UsageKey] - A list of usage keys of the block's children.
        """
        return self._block_relations[usage_key].children if self.has_block(usage_key) else []

    def has_block(self, usage_key):
        """
        Returns whether a block with the given usage_key is in this
        block structure.

        Arguments:
            usage_key - The usage key of the block whose children
                are to be returned.

        Returns:
            bool - Whether or not a block with the given usage_key
                is present in this block structure.
        """
        return usage_key in self._block_relations

    def get_block_keys(self):
        """
        Returns the block keys in the block structure.

        Returns:
            iterator(UsageKey) - An iterator of the usage
            keys of all the blocks in the block structure.
        """
        return self._block_relations.iterkeys()

    #--- Block structure traversal methods ---#

    def topological_traversal(
            self,
            filter_func=None,
            yield_descendants_of_unyielded=False,
    ):
        """
        Performs a topological sort of the block structure and yields
        the usage_key of each block as it is encountered.

        Arguments:
            See the description in
            openedx.core.lib.graph_traversals.traverse_topologically.

        Returns:
            generator - A generator object created from the
                traverse_topologically method.
        """
        return traverse_topologically(
            start_node=self.root_block_usage_key,
            get_parents=self.get_parents,
            get_children=self.get_children,
            filter_func=filter_func,
            yield_descendants_of_unyielded=yield_descendants_of_unyielded,
        )

    def post_order_traversal(
            self,
            filter_func=None,
    ):
        """
        Performs a post-order sort of the block structure and yields
        the usage_key of each block as it is encountered.

        Arguments:
            See the description in
            openedx.core.lib.graph_traversals.traverse_post_order.

        Returns:
            generator - A generator object created from the
                traverse_post_order method.
        """
        return traverse_post_order(
            start_node=self.root_block_usage_key,
            get_children=self.get_children,
            filter_func=filter_func,
        )

    #--- Internal methods ---#
    # To be used within the block_cache framework or by tests.

    def _prune_unreachable(self):
        """
        Mutates this block structure by removing any unreachable blocks.
        """

        # Create a new block relations map to store only those blocks
        # that are still linked
        pruned_block_relations = defaultdict(_BlockRelations)
        old_block_relations = self._block_relations

        # Build the structure from the leaves up by doing a post-order
        # traversal of the old structure, thereby encountering only
        # reachable blocks.
        for block_key in self.post_order_traversal():
            # If the block is in the old structure,
            if block_key in old_block_relations:
                # Add it to the new pruned structure
                self._add_block(pruned_block_relations, block_key)

                # Add a relationship to only those old children that
                # were also added to the new pruned structure.
                for child in old_block_relations[block_key].children:
                    if child in pruned_block_relations:
                        self._add_to_relations(pruned_block_relations, block_key, child)

        # Replace this structure's relations with the newly pruned one.
        self._block_relations = pruned_block_relations

    def _add_relation(self, parent_key, child_key):
        """
        Adds a parent to child relationship in this block structure.

        Arguments:
            parent_key (UsageKey) - Usage key of the parent block.
            child_key (UsageKey) - Usage key of the child block.
        """
        self._add_to_relations(self._block_relations, parent_key, child_key)

    @staticmethod
    def _add_to_relations(block_relations, parent_key, child_key):
        """
        Adds a parent to child relationship in the given block
        relations map.

        Arguments:
            block_relations (defaultdict({UsageKey: _BlockRelations})) -
                Internal map of a block's usage key to its
                parents/children relations.

            parent_key (UsageKey) - Usage key of the parent block.

            child_key (UsageKey) - Usage key of the child block.
        """
        block_relations[child_key].parents.append(parent_key)
        block_relations[parent_key].children.append(child_key)

    @staticmethod
    def _add_block(block_relations, usage_key):
        """
        Adds the given usage_key to the given block_relations map.

        Arguments:
            block_relations (defaultdict({UsageKey: _BlockRelations})) -
                Internal map of a block's usage key to its
                parents/children relations.

            usage_key (UsageKey) - Usage key of the block that is to
                be added to the given block_relations.
        """
        block_relations[usage_key] = _BlockRelations()


class _BlockData(object):
    """
    Data structure to encapsulate collected data for a single block.
    """
    def __init__(self):
        # Map of xblock field name to the field's value for this block.
        # dict {string: any picklable type}
        self.xblock_fields = {}

        # Map of transformer name to the transformer's data for this
        # block.
        # defaultdict {string: dict}
        self.transformer_data = defaultdict(dict)


class BlockStructureBlockData(BlockStructure):
    """
    Subclass of BlockStructure that is responsible for managing block
    and transformer data.
    """
    def __init__(self, root_block_usage_key):
        super(BlockStructureBlockData, self).__init__(root_block_usage_key)

        # Map of a block's usage key to its collected data, including
        # its xBlock fields and block-specific transformer data.
        # defaultdict {UsageKey: _BlockData}
        self._block_data_map = defaultdict(_BlockData)

        # Map of a transformer's name to its non-block-specific data.
        # defaultdict {string: dict}
        self._transformer_data = defaultdict(dict)

    def get_xblock_field(self, usage_key, field_name, default=None):
        """
        Returns the collected value of the xBlock field for the
        requested block for the requested field_name; returns default if
        not found.

        Arguments:
            usage_key (UsageKey) - Usage key of the block whose xBlock
                field is requested.

            field_name (string) - The name of the field that is
                requested.

            default (any type) - The value to return if a field value is
                not found.
        """
        block_data = self._block_data_map.get(usage_key)
        return block_data.xblock_fields.get(field_name, default) if block_data else default

    def get_transformer_data(self, transformer, key, default=None):
        """
        Returns the value associated with the given key from the given
        transformer's data dictionary; returns default if not found.

        Arguments:
            transformer (BlockStructureTransformer) - The transformer
                whose collected data is requested.

            key (string) - A dictionary key to the transformer's data
                that is requested.
        """
        return self._transformer_data.get(transformer.name(), {}).get(key, default)

    def set_transformer_data(self, transformer, key, value):
        """
        Updates the given transformer's data dictionary with the given
        key and value.

        Arguments:
            transformer (BlockStructureTransformer) - The transformer
                whose data is to be updated.

            key (string) - A dictionary key to the transformer's data.

            value (any picklable type) - The value to associate with the
                given key for the given transformer's data.
        """
        self._transformer_data[transformer.name()][key] = value

    def get_transformer_block_field(self, usage_key, transformer, key, default=None):
        """
        Returns the value associated with the given key for the given
        transformer for the block identified by the given usage_key;
        returns default if not found.

        Arguments:
            usage_key (UsageKey) - Usage key of the block whose
                transformer data is requested.

            transformer (BlockStructureTransformer) - The transformer
                whose dictionary data is requested.

            key (string) - A dictionary key to the transformer's data
                that is requested.

            default (any type) - The value to return if a dictionary
                entry is not found.
        """
        transformer_data = self.get_transformer_block_data(usage_key, transformer)
        return transformer_data.get(key, default)

    def set_transformer_block_field(self, usage_key, transformer, key, value):
        """
        Updates the given transformer's data dictionary with the given
        key and value for the block identified by the given usage_key.

        Arguments:
            usage_key (UsageKey) - Usage key of the block whose
                transformer data is to be updated.

            transformer (BlockStructureTransformer) - The transformer
                whose data is to be updated.

            key (string) - A dictionary key to the transformer's data.

            value (any picklable type) - The value to associate with the
                given key for the given transformer's data for the
                requested block.
        """
        self._block_data_map[usage_key].transformer_data[transformer.name()][key] = value

    def get_transformer_block_data(self, usage_key, transformer):
        """
        Returns the entire transformer data dict for the given
        transformer for the block identified by the given usage_key;
        returns an empty dict {} if not found.

        Arguments:
            usage_key (UsageKey) - Usage key of the block whose
                transformer data is requested.

            transformer (BlockStructureTransformer) - The transformer
                whose dictionary data is requested.

            key (string) - A dictionary key to the transformer's data
                that is requested.
        """
        default = {}
        block_data = self._block_data_map.get(usage_key)
        if not block_data:
            return default
        else:
            return block_data.transformer_data.get(transformer.name(), default)

    def remove_transformer_block_field(self, usage_key, transformer, key):
        """
        Deletes the given transformer's entire data dict for the
        block identified by the given usage_key.

        Arguments:
            usage_key (UsageKey) - Usage key of the block whose
                transformer data is to be deleted.

            transformer (BlockStructureTransformer) - The transformer
                whose data entry is to be deleted.
        """
        transformer_block_data = self.get_transformer_block_data(usage_key, transformer)
        transformer_block_data.pop(key, None)

    def remove_block(self, usage_key, keep_descendants):
        """
        Removes the block identified by the usage_key and all of its
        related data from the block structure.  If descendants of the
        removed block are to be kept, the structure's relations are
        updated to reconnect the block's parents with its children.

        Note: While the immediate relations of the block are updated
        (removed), all descendants of the block will remain in the
        structure unless the _prune_unreachable method is called.

        Arguments:
            usage_key (UsageKey) - Usage key of the block that is to be
                removed.

            keep_descendants (bool) - If True, the block structure's
                relations (graph edges) are updated such that the
                removed block's children become children of the
                removed block's parents.
        """
        children = self._block_relations[usage_key].children
        parents = self._block_relations[usage_key].parents

        # Remove block from its children.
        for child in children:
            self._block_relations[child].parents.remove(usage_key)

        # Remove block from its parents.
        for parent in parents:
            self._block_relations[parent].children.remove(usage_key)

        # Remove block.
        self._block_relations.pop(usage_key, None)
        self._block_data_map.pop(usage_key, None)

        # Recreate the graph connections if descendants are to be kept.
        if keep_descendants:
            for child in children:
                for parent in parents:
                    self._add_relation(parent, child)

    def remove_block_if(self, removal_condition, keep_descendants=False, **kwargs):
        """
        A higher-order function that traverses the block structure
        using topological sort and removes any blocks encountered that
        satisfy the removal_condition.

        Arguments:
            removal_condition ((usage_key)->bool) - A function that
                takes a block's usage key as input and returns whether
                or not to remove that block from the block structure.

            keep_descendants (bool) - See the description in
                remove_block.

            kwargs (dict) - Optional keyword arguments to be forwarded
                to topological_traversal.
        """
        def filter_func(block_key):
            """
            Filter function for removing blocks that satisfy the
            removal_condition.
            """
            if removal_condition(block_key):
                self.remove_block(block_key, keep_descendants)
                return False
            return True

        # Note: For optimization, we remove blocks using the filter
        # function, since the graph traversal method can skip over
        # descendants that are unyielded.  However, note that the
        # optimization is not currently present because of DAGs,
        # but it will be as soon as we remove support for DAGs.
        for _ in self.topological_traversal(filter_func=filter_func, **kwargs):
            pass

    def get_block_keys(self):
        """
        Returns the block keys in the block structure.

        Returns:
            iterator(UsageKey) - An iterator of the usage
            keys of all the blocks in the block structure.
        """
        return self._block_relations.iterkeys()

    #--- Internal methods ---#
    # To be used within the block_cache framework or by tests.

    def _get_transformer_data_version(self, transformer):
        """
        Returns the version number stored for the given transformer.

        Arguments:
            transformer (BlockStructureTransformer) - The transformer
                whose stored version is requested.
        """

        return self.get_transformer_data(transformer, TRANSFORMER_VERSION_KEY, 0)

    def _add_transformer(self, transformer):
        """
        Adds the given transformer to the block structure by recording
        its current version number.
        """
        if transformer.VERSION == 0:
            raise TransformerException('VERSION attribute is not set on transformer {0}.', transformer.name())
        self.set_transformer_data(transformer, TRANSFORMER_VERSION_KEY, transformer.VERSION)


class BlockStructureModulestoreData(BlockStructureBlockData):
    """
    Subclass of BlockStructureBlockData that is responsible for managing
    xBlocks and corresponding functionality that should only be called
    during the Collect phase.

    Note: Although this class interface uses xBlock terminology, it is
    designed and implemented generically so it can work with any
    interface and implementation of an xBlock.
    """
    def __init__(self, root_block_usage_key):
        super(BlockStructureModulestoreData, self).__init__(root_block_usage_key)

        # Map of a block's usage key to its instantiated xBlock.
        # dict {UsageKey: XBlock}
        self._xblock_map = {}

        # Set of xBlock field names that have been requested for
        # collection.
        # set(string)
        self._requested_xblock_fields = set()

    def request_xblock_fields(self, *field_names):
        """
        Records request for collecting data for the given xBlock fields.

        A Transformer should call this method when it needs to collect
        data for a common xBlock field that may also be used by other
        transformers.  This minimizes storage usage across transformers.
        Contrast this with each transformer collecting the same xBlock
        data within its own transformer data storage.

        Arguments:
            field_names (list(string)) - A list of names of common
                xBlock fields whose values should be collected.
        """
        self._requested_xblock_fields.update(set(field_names))

    def get_xblock(self, usage_key):
        """
        Returns the instantiated xBlock for the given usage key.

        Arguments:
            usage_key (UsageKey) - Usage key of the block whose
                xBlock object is to be returned.
        """
        return self._xblock_map[usage_key]

    #--- Internal methods ---#
    # To be used within the block_cache framework or by tests.

    def _add_xblock(self, usage_key, xblock):
        """
        Associates the given xBlock object with the given usage_key.

        Arguments:
            usage_key (UsageKey) - Usage key of the given xBlock.  This
                value is passed in separately as opposed to retrieving
                it from the given xBlock since this interface is
                agnostic to and decoupled from the xBlock interface.

            xblock (XBlock) - An instantiated XBlock object that is
                to be stored for later access.
        """
        self._xblock_map[usage_key] = xblock

    def _collect_requested_xblock_fields(self):
        """
        Iterates through all instantiated xBlocks that were added and
        collects all xBlock fields that were requested.
        """
        if not self._requested_xblock_fields:
            return

        for xblock_usage_key, xblock in self._xblock_map.iteritems():
            for field_name in self._requested_xblock_fields:
                self._set_xblock_field(xblock_usage_key, xblock, field_name)

    def _set_xblock_field(self, usage_key, xblock, field_name):
        """
        Updates the given block's xBlock fields data with the xBlock
        value for the given field name.

        Arguments:
            usage_key (UsageKey) - Usage key of the given xBlock.  This
                value is passed in separately as opposed to retrieving
                it from the given xBlock since this interface is
                agnostic to and decoupled from the xBlock interface.

            xblock (XBlock) - An instantiated XBlock object whose
                field is being accessed and collected for later
                retrieval.

            field_name (string) - The name of the xBlock field that is
                being collected and stored.
        """
        if hasattr(xblock, field_name):
            self._block_data_map[usage_key].xblock_fields[field_name] = getattr(xblock, field_name)
