"""
Module for the Cache class for BlockStructure objects.
"""
# pylint: disable=protected-access
from logging import getLogger

from openedx.core.lib.cache_utils import zpickle, zunpickle

from .block_structure import BlockStructureBlockData
from .factory import BlockStructureFactory


logger = getLogger(__name__)  # pylint: disable=C0103


class BlockStructureCache(object):
    """
    Cache for BlockStructure objects.
    """
    def __init__(self, cache):
        """
        Arguments:
            cache (django.core.cache.backends.base.BaseCache) - The
                cache into which cacheable data of the block structure
                is to be serialized.
        """
        self._cache = cache

    def add(self, block_structure):
        """
        Store a compressed and pickled serialization of the given
        block structure into the given cache.

        The key in the cache is 'root.key.<root_block_usage_key>'.
        The data stored in the cache includes the structure's
        block relations, transformer data, and block data.

        Arguments:
            block_structure (BlockStructure) - The block structure
                that is to be serialized to the given cache.
        """
        data_to_cache = (
            block_structure._block_relations,
            block_structure.transformer_data,
            block_structure._block_data_map,
        )
        zp_data_to_cache = zpickle(data_to_cache)

        # Set the timeout value for the cache to 1 day as a fail-safe
        # in case the signal to invalidate the cache doesn't come through.
        timeout_in_seconds = 60 * 60 * 24
        self._cache.set(
            self._encode_root_cache_key(block_structure.root_block_usage_key),
            zp_data_to_cache,
            timeout=timeout_in_seconds,
        )

        logger.info(
            "Wrote BlockStructure %s to cache, size: %s",
            block_structure.root_block_usage_key,
            len(zp_data_to_cache),
        )

    def get(self, root_block_usage_key):
        """
        Deserializes and returns the block structure starting at
        root_block_usage_key from the given cache, if it's found in the cache.

        The given root_block_usage_key must equate the root_block_usage_key
        previously passed to serialize_to_cache.

        Arguments:
            root_block_usage_key (UsageKey) - The usage_key for the root
                of the block structure that is to be deserialized from
                the given cache.

        Returns:
            BlockStructure - The deserialized block structure starting
            at root_block_usage_key, if found in the cache.

            NoneType - If the root_block_usage_key is not found in the cache.
        """

        # Find root_block_usage_key in the cache.
        zp_data_from_cache = self._cache.get(self._encode_root_cache_key(root_block_usage_key))
        if not zp_data_from_cache:
            logger.info(
                "Did not find BlockStructure %r in the cache.",
                root_block_usage_key,
            )
            return None
        else:
            logger.info(
                "Read BlockStructure %r from cache, size: %s",
                root_block_usage_key,
                len(zp_data_from_cache),
            )

        # Deserialize and construct the block structure.
        block_relations, transformer_data, block_data_map = zunpickle(zp_data_from_cache)
        return BlockStructureFactory.create_new(
            root_block_usage_key,
            block_relations,
            transformer_data,
            block_data_map,
        )

    def delete(self, root_block_usage_key):
        """
        Deletes the block structure for the given root_block_usage_key
        from the given cache.

        Arguments:
            root_block_usage_key (UsageKey) - The usage_key for the root
                of the block structure that is to be removed from
                the cache.
        """
        self._cache.delete(self._encode_root_cache_key(root_block_usage_key))
        logger.info(
            "Deleted BlockStructure %r from the cache.",
            root_block_usage_key,
        )

    @classmethod
    def _encode_root_cache_key(cls, root_block_usage_key):
        """
        Returns the cache key to use for storing the block structure
        for the given root_block_usage_key.
        """
        return "v{version}.root.key.{root_usage_key}".format(
            version=unicode(BlockStructureBlockData.VERSION),
            root_usage_key=unicode(root_block_usage_key),
        )
