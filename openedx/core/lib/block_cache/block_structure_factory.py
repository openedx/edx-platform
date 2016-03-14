"""
Module for factory class for BlockStructure objects.
"""
# pylint: disable=protected-access
from logging import getLogger

from openedx.core.lib.cache_utils import zpickle, zunpickle

from .block_structure import BlockStructureBlockData, BlockStructureModulestoreData


logger = getLogger(__name__)  # pylint: disable=C0103


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
        """
        # Create block structure.
        block_structure = BlockStructureModulestoreData(root_block_usage_key)

        # Create internal set of blocks visited to use when recursing.
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
            block_structure._add_xblock(xblock.location, xblock)

            # Add relations with its children and recurse.
            for child in xblock.get_children():
                block_structure._add_relation(xblock.location, child.location)
                build_block_structure(child)

        root_xblock = modulestore.get_item(root_block_usage_key, depth=None)
        build_block_structure(root_xblock)
        return block_structure

    @classmethod
    def serialize_to_cache(cls, block_structure, cache):
        """
        Store a compressed and pickled serialization of the given
        block structure into the given cache.

        The key in the cache is 'root.key.<root_block_usage_key>'.
        The data stored in the cache includes the structure's
        block relations, transformer data, and block data.

        Arguments:
            block_structure (BlockStructure) - The block structure
                that is to be serialized to the given cache.

            cache (django.core.cache.backends.base.BaseCache) - The
                cache into which cacheable data of the block structure
                is to be serialized.
        """
        data_to_cache = (
            block_structure._block_relations,
            block_structure._transformer_data,
            block_structure._block_data_map
        )
        zp_data_to_cache = zpickle(data_to_cache)
        cache.set(
            cls._encode_root_cache_key(block_structure.root_block_usage_key),
            zp_data_to_cache
        )
        logger.debug(
            "Wrote BlockStructure %s to cache, size: %s",
            block_structure.root_block_usage_key,
            len(zp_data_to_cache),
        )

    @classmethod
    def create_from_cache(cls, root_block_usage_key, cache, transformers):
        """
        Deserializes and returns the block structure starting at
        root_block_usage_key from the given cache, if it's found in the cache.

        The given root_block_usage_key must equate the root_block_usage_key
        previously passed to serialize_to_cache.

        Arguments:
            root_block_usage_key (UsageKey) - The usage_key for the root
                of the block structure that is to be deserialized from
                the given cache.

            cache (django.core.cache.backends.base.BaseCache) - The
                cache from which the block structure is to be
                deserialized.

            transformers ([BlockStructureTransformer]) - A list of
                transformers for which the block structure will be
                transformed.

        Returns:
            BlockStructure - The deserialized block structure starting
            at root_block_usage_key, if found in the cache.

            NoneType - If the root_block_usage_key is not found in the cache
            or if the cached data is outdated for one or more of the
            given transformers.
        """

        # Find root_block_usage_key in the cache.
        zp_data_from_cache = cache.get(cls._encode_root_cache_key(root_block_usage_key))
        if not zp_data_from_cache:
            logger.debug(
                "BlockStructure %r not found in the cache.",
                root_block_usage_key,
            )
            return None
        else:
            logger.debug(
                "Read BlockStructure %r from cache, size: %s",
                root_block_usage_key,
                len(zp_data_from_cache),
            )

        # Deserialize and construct the block structure.
        block_relations, transformer_data, block_data_map = zunpickle(zp_data_from_cache)
        block_structure = BlockStructureBlockData(root_block_usage_key)
        block_structure._block_relations = block_relations
        block_structure._transformer_data = transformer_data
        block_structure._block_data_map = block_data_map

        # Verify that the cached data for all the given transformers are
        # for their latest versions.
        outdated_transformers = {}
        for transformer in transformers:
            cached_transformer_version = block_structure._get_transformer_data_version(transformer)
            if transformer.VERSION != cached_transformer_version:
                outdated_transformers[transformer.name()] = "version: {}, cached: {}".format(
                    transformer.VERSION,
                    cached_transformer_version,
                )
        if outdated_transformers:
            logger.info(
                "Collected data for the following transformers are outdated:\n%s.",
                '\n'.join([t_name + ": " + t_value for t_name, t_value in outdated_transformers.iteritems()]),
            )
            return None

        return block_structure

    @classmethod
    def remove_from_cache(cls, root_block_usage_key, cache):
        """
        Removes the block structure for the given root_block_usage_key
        from the given cache.

        Arguments:
            root_block_usage_key (UsageKey) - The usage_key for the root
                of the block structure that is to be removed from
                the given cache.

            cache (django.core.cache.backends.base.BaseCache) - The
                cache from which the block structure is to be
                removed.
        """
        cache.delete(cls._encode_root_cache_key(root_block_usage_key))
        # TODO also remove all block data?

    @classmethod
    def _encode_root_cache_key(cls, root_block_usage_key):
        """
        Returns the cache key to use for storing the block structure
        for the given root_block_usage_key.
        """
        return "root.key." + unicode(root_block_usage_key)
