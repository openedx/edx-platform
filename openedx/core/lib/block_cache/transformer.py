"""
...
"""
from abc import abstractmethod
from openedx.core.lib.api.plugins import PluginManager


class BlockStructureTransformer(object):
    """
    ...
    """
    # All Transformers are expected to update and maintain a VERSION class attribute
    VERSION = 0

    @classmethod
    def name(cls):
        return cls.__name__

    @classmethod
    def collect(self, block_structure):
        """
        Collects any information that's necessary to execute this transformer's
        transform method.
        """
        pass

    @abstractmethod
    def transform(self, user_info, block_structure):
        """
        Mutates block_structure based on the given user_info.
        """
        pass


class BlockStructureTransformers(PluginManager):
    """
    Manager for all of the block structure transformers that have been made available.

    All block structure transformers should implement `BlockStructureTransformer`.
    """
    NAMESPACE = 'openedx.block_structure_transformer'

    @classmethod
    def get_registered_transformers(cls):
        return set(cls.get_available_plugins().itervalues())

    @classmethod
    def are_all_registered(cls, transformers):
        registered_transformers = cls.get_registered_transformers()
        return all(
            any(transformer.name() == reg_trans.name() for reg_trans in registered_transformers)
            for transformer in transformers
        )
