"""
Block Structure Transformer Registry implemented using the platform's
PluginManager.
"""


from base64 import b64encode
from hashlib import sha1

from edx_django_utils.plugins import PluginManager

from openedx.core.lib.cache_utils import process_cached


class TransformerRegistry(PluginManager):
    """
    Registry for all of the block structure transformers that have been
    made available.

    All block structure transformers should implement
    `BlockStructureTransformer`.
    """
    NAMESPACE = 'openedx.block_structure_transformer'
    USE_PLUGIN_MANAGER = True

    @classmethod
    def get_registered_transformers(cls):
        """
        Returns a set of all registered transformers.

        Returns:
            {BlockStructureTransformer} - All transformers that are
                registered with the platform's PluginManager.
        """
        if cls.USE_PLUGIN_MANAGER:
            return set(cls.get_available_plugins().values())
        else:
            return set()

    @classmethod
    @process_cached
    def get_write_version_hash(cls):
        """
        Returns a deterministic hash value of the WRITE_VERSION of all
        registered transformers.
        """
        hash_obj = sha1()

        sorted_transformers = sorted(cls.get_registered_transformers(), key=lambda t: t.name())
        for transformer in sorted_transformers:
            hash_obj.update((transformer.name()).encode())
            hash_obj.update((str(transformer.WRITE_VERSION)).encode())

        return b64encode(hash_obj.digest()).decode('utf-8')

    @classmethod
    def find_unregistered(cls, transformers):
        """
        Find and returns the names of all the transformers from the
        given list that aren't registered with the platform's
        PluginManager.

        Arguments:
            transformers ([BlockStructureTransformer] - List of
                transformers to check in the registry.

        Returns:
            set([string]) - Set of names of a subset of the given
                transformers that weren't found in the registry.
        """
        registered_transformer_names = {reg_trans.name() for reg_trans in cls.get_registered_transformers()}
        requested_transformer_names = {transformer.name() for transformer in transformers}
        return requested_transformer_names - registered_transformer_names
