"""
Module for the Storage of BlockStructure objects.
"""
# pylint: disable=protected-access


from logging import getLogger

import six

from django.utils.encoding import python_2_unicode_compatible
from openedx.core.lib.cache_utils import zpickle, zunpickle

from . import config
from .block_structure import BlockStructureBlockData
from .exceptions import BlockStructureNotFound
from .factory import BlockStructureFactory
from .models import BlockStructureModel
from .transformer_registry import TransformerRegistry

logger = getLogger(__name__)  # pylint: disable=C0103


@python_2_unicode_compatible
class StubModel(object):
    """
    Stub model to use when storage backing is disabled.
    By using this stub, we eliminate the need for extra
    conditional statements in the code.
    """
    def __init__(self, root_block_usage_key):
        self.data_usage_key = root_block_usage_key

    def __str__(self):
        return six.text_type(self.data_usage_key)

    def delete(self):
        """
        Noop delete method.
        """
        pass


class BlockStructureStore(object):
    """
    Storage for BlockStructure objects.
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
        Stores and caches a compressed and pickled serialization of
        the given block structure.

        The data stored includes the structure's
        block relations, transformer data, and block data.

        Arguments:
            block_structure (BlockStructure) - The block structure
                that is to be cached and stored.
        """
        serialized_data = self._serialize(block_structure)

        bs_model = self._update_or_create_model(block_structure, serialized_data)
        self._add_to_cache(serialized_data, bs_model)

    def get(self, root_block_usage_key):
        """
        Deserializes and returns the block structure starting at
        root_block_usage_key, if found in the cache or storage.

        The given root_block_usage_key must equate the
        root_block_usage_key previously passed to the `add` method.

        Arguments:
            root_block_usage_key (UsageKey) - The usage_key for the
                root of the block structure that is to be retrieved
                from the store.

        Returns:
            BlockStructure - The deserialized block structure starting
            at root_block_usage_key, if found.

        Raises:
            BlockStructureNotFound if the root_block_usage_key is not
            found.
        """
        bs_model = self._get_model(root_block_usage_key)

        try:
            serialized_data = self._get_from_cache(bs_model)
        except BlockStructureNotFound:
            serialized_data = self._get_from_store(bs_model)
            self._add_to_cache(serialized_data, bs_model)

        return self._deserialize(serialized_data, root_block_usage_key)

    def delete(self, root_block_usage_key):
        """
        Deletes the block structure for the given root_block_usage_key
        from the cache and storage.

        Arguments:
            root_block_usage_key (UsageKey) - The usage_key for the root
                of the block structure that is to be removed.
        """
        bs_model = self._get_model(root_block_usage_key)
        self._cache.delete(self._encode_root_cache_key(bs_model))
        bs_model.delete()
        logger.info(u"BlockStructure: Deleted from cache and store; %s.", bs_model)

    def is_up_to_date(self, root_block_usage_key, modulestore):
        """
        Returns whether the data in storage for the given key is
        already up-to-date with the version in the given modulestore.
        """
        if _is_storage_backing_enabled():
            try:
                bs_model = self._get_model(root_block_usage_key)
                root_block = modulestore.get_item(root_block_usage_key)
                return self._version_data_of_model(bs_model) == self._version_data_of_block(root_block)
            except BlockStructureNotFound:
                pass

        return False

    def _get_model(self, root_block_usage_key):
        """
        Returns the model associated with the given key.
        """
        if _is_storage_backing_enabled():
            return BlockStructureModel.get(root_block_usage_key)
        else:
            return StubModel(root_block_usage_key)

    def _update_or_create_model(self, block_structure, serialized_data):
        """
        Updates or creates the model for the given block_structure
        and serialized_data.
        """
        if _is_storage_backing_enabled():
            root_block = block_structure[block_structure.root_block_usage_key]
            bs_model, _ = BlockStructureModel.update_or_create(
                serialized_data,
                data_usage_key=block_structure.root_block_usage_key,
                **self._version_data_of_block(root_block)
            )
            return bs_model
        else:
            return StubModel(block_structure.root_block_usage_key)

    def _add_to_cache(self, serialized_data, bs_model):
        """
        Adds the given serialized_data for the given BlockStructureModel
        to the cache.
        """
        cache_key = self._encode_root_cache_key(bs_model)
        self._cache.set(cache_key, serialized_data, timeout=config.cache_timeout_in_seconds())
        logger.info(u"BlockStructure: Added to cache; %s, size: %d", bs_model, len(serialized_data))

    def _get_from_cache(self, bs_model):
        """
        Returns the serialized data for the given BlockStructureModel
        from the cache.
        Raises:
             BlockStructureNotFound if not found.
        """
        cache_key = self._encode_root_cache_key(bs_model)
        serialized_data = self._cache.get(cache_key)

        if not serialized_data:
            logger.info(u"BlockStructure: Not found in cache; %s.", bs_model)
            raise BlockStructureNotFound(bs_model.data_usage_key)
        return serialized_data

    def _get_from_store(self, bs_model):
        """
        Returns the serialized data for the given BlockStructureModel
        from storage.
        Raises:
             BlockStructureNotFound if not found.
        """
        if not _is_storage_backing_enabled():
            raise BlockStructureNotFound(bs_model.data_usage_key)

        return bs_model.get_serialized_data()

    def _serialize(self, block_structure):
        """
        Serializes the data for the given block_structure.
        """
        data_to_cache = (
            block_structure._block_relations,
            block_structure.transformer_data,
            block_structure._block_data_map,
        )
        return zpickle(data_to_cache)

    def _deserialize(self, serialized_data, root_block_usage_key):
        """
        Deserializes the given data and returns the parsed block_structure.
        """

        try:
            block_relations, transformer_data, block_data_map = zunpickle(serialized_data)
        except Exception:
            # Somehow failed to de-serialized the data, assume it's corrupt.
            bs_model = self._get_model(root_block_usage_key)
            logger.exception(u"BlockStructure: Failed to load data from cache for %s", bs_model)
            raise BlockStructureNotFound(bs_model.data_usage_key)

        return BlockStructureFactory.create_new(
            root_block_usage_key,
            block_relations,
            transformer_data,
            block_data_map,
        )

    @staticmethod
    def _encode_root_cache_key(bs_model):
        """
        Returns the cache key to use for the given
        BlockStructureModel or StubModel.
        """
        if _is_storage_backing_enabled():
            return six.text_type(bs_model)

        else:
            return "v{version}.root.key.{root_usage_key}".format(
                version=six.text_type(BlockStructureBlockData.VERSION),
                root_usage_key=six.text_type(bs_model.data_usage_key),
            )

    @staticmethod
    def _version_data_of_block(root_block):
        """
        Returns the version-relevant data for the given block, including the
        current schema state of the Transformers and BlockStructure classes.
        """
        return dict(
            data_version=getattr(root_block, 'course_version', None),
            data_edit_timestamp=getattr(root_block, 'subtree_edited_on', None),
            transformers_schema_version=TransformerRegistry.get_write_version_hash(),
            block_structure_schema_version=six.text_type(BlockStructureBlockData.VERSION),
        )

    @staticmethod
    def _version_data_of_model(bs_model):
        """
        Returns the version-relevant data for the given BlockStructureModel.
        """
        return {
            field_name: getattr(bs_model, field_name, None)
            for field_name in BlockStructureModel.VERSION_FIELDS
        }


def _is_storage_backing_enabled():
    """
    Returns whether storage backing for Block Structures is enabled.
    """
    return config.waffle().is_enabled(config.STORAGE_BACKING_FOR_CACHE)
