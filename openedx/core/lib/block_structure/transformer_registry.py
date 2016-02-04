"""
Block Structure Transformer Registry implemented using the platform's
PluginManager.
"""
from openedx.core.lib.api.plugins import PluginManager


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
            return set(cls.get_available_plugins().itervalues())
        else:
            return set()

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
        registered_transformer_names = set(reg_trans.name() for reg_trans in cls.get_registered_transformers())
        requested_transformer_names = set(transformer.name() for transformer in transformers)
        return requested_transformer_names - registered_transformer_names
