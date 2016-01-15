"""
Module for factory class for BlockStructure objects.
"""
from .block_structure import BlockStructureModulestoreData


class BlockStructureFactory(object):
    """
    Factory class for BlockStructure objects.
    """
    @classmethod
    def create_from_modulestore(cls, root_block_usage_key, modulestore):
        """
        Creates and returns a block structure from the modulestore
        starting at the given root_block_usage_key.

        Arguments:
            root_block_usage_key (UsageKey) - The usage_key for the root
                of the block structure that is to be created.

            modulestore (ModuleStoreRead) - The modulestore that
                contains the data for the xBlocks within the block
                structure starting at root_block_usage_key.

        Returns:
            BlockStructureModulestoreData - The created block structure
                with instantiated xBlocks from the given modulestore
                starting at root_block_usage_key.

        Raises:
            xmodule.modulestore.exceptions.ItemNotFoundError if a block for
                root_block_usage_key is not found in the modulestore.
        """
        block_structure = BlockStructureModulestoreData(root_block_usage_key)
        blocks_visited = set()

        def build_block_structure(xblock):
            """
            Recursively update the block structure with the given xBlock
            and its descendants.
            """
            # Check if the xblock was already visited (can happen in
            # DAGs).
            if xblock.location in blocks_visited:
                return

            # Add the xBlock.
            blocks_visited.add(xblock.location)
            block_structure._add_xblock(xblock.location, xblock)  # pylint: disable=protected-access

            # Add relations with its children and recurse.
            for child in xblock.get_children():
                block_structure._add_relation(xblock.location, child.location)  # pylint: disable=protected-access
                build_block_structure(child)

        root_xblock = modulestore.get_item(root_block_usage_key, depth=None)
        build_block_structure(root_xblock)
        return block_structure

    @classmethod
    def create_from_cache(cls, root_block_usage_key, block_structure_cache):
        """
        Deserializes and returns the block structure starting at
        root_block_usage_key from the given cache, if it's found in the cache.

        The given root_block_usage_key must equate the root_block_usage_key
        previously passed to serialize_to_cache.

        Arguments:
            root_block_usage_key (UsageKey) - The usage_key for the root
                of the block structure that is to be deserialized from
                the given cache.

            block_structure_cache (BlockStructureCache) - The
                cache from which the block structure is to be
                deserialized.

        Returns:
            BlockStructure - The deserialized block structure starting
            at root_block_usage_key, if found in the cache.

            NoneType - If the root_block_usage_key is not found in the cache.
        """
        return block_structure_cache.get(root_block_usage_key)
