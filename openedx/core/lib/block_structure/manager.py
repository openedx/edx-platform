"""
Top-level module for the Block Structure framework with a class for managing
BlockStructures.
"""
from .factory import BlockStructureFactory
from .cache import BlockStructureCache
from .transformers import BlockStructureTransformers


class BlockStructureManager(object):
    """
    Top-level class for managing Block Structures.
    """

    def __init__(self, root_block_usage_key, modulestore, cache):
        """
        Arguments:
            root_block_usage_key (UsageKey) - The usage_key for the root
                of the block structure that is being accessed.

            modulestore (ModuleStoreRead) - The modulestore that
                contains the data for the xBlock objects corresponding to
                the block structure.

            cache (django.core.cache.backends.base.BaseCache) - The
                cache to use for storing/retrieving the block structure's
                collected data.
        """
        self.root_block_usage_key = root_block_usage_key
        self.modulestore = modulestore
        self.block_structure_cache = BlockStructureCache(cache)

    def get_transformed(self, transformers):
        """
        Returns the transformed Block Structure for the root_block_usage_key,
        getting block data from the cache and modulestore, as needed.

        Details: Same as the get_collected method, except the transformers'
        transform methods are also called.

        Arguments:
            transformers (BlockStructureTransformers) - Collection of
                transformers to apply.

        Returns:
            BlockStructureBlockData - A transformed block structure,
                starting at self.root_block_usage_key.
        """
        block_structure = self.get_collected()
        transformers.transform(block_structure)
        return block_structure

    def get_collected(self):
        """
        Returns the collected Block Structure for the root_block_usage_key,
        getting block data from the cache and modulestore, as needed.

        Details: The cache is updated if needed (if outdated or empty),
        the modulestore is accessed if needed (at cache miss), and the
        transformers data is collected if needed.

        Returns:
            BlockStructureBlockData - A collected block structure,
                starting at root_block_usage_key, with collected data
                from each registered transformer.
        """
        block_structure = BlockStructureFactory.create_from_cache(
            self.root_block_usage_key,
            self.block_structure_cache
        )
        cache_miss = block_structure is None
        if cache_miss or BlockStructureTransformers.is_collected_outdated(block_structure):
            block_structure = BlockStructureFactory.create_from_modulestore(
                self.root_block_usage_key,
                self.modulestore
            )
            BlockStructureTransformers.collect(block_structure)
            self.block_structure_cache.add(block_structure)
        return block_structure

    def update_collected(self):
        """
        Updates the collected Block Structure for the root_block_usage_key.

        Details: The cache is cleared and updated by collecting transformers
        data from the modulestore.
        """
        self.clear()
        self.get_collected()

    def clear(self):
        """
        Removes cached data for the block structure associated with the given
        root block key.
        """
        self.block_structure_cache.delete(self.root_block_usage_key)
