"""
Module for a collection of BlockStructureTransformers.
"""
from logging import getLogger

from .exceptions import TransformerException
from .transformer import OptimizedTransformer
from .transformer_registry import TransformerRegistry


logger = getLogger(__name__)  # pylint: disable=C0103


class BlockStructureTransformers(object):
    """
    The BlockStructureTransformers class encapsulates an ordered list of block
    structure transformers.  It uses the Transformer Registry to verify the
    the registration status of added transformers and to collect their data.
    It provides aggregate functionality for collection and ordered
    transformation of the transformers.

    Clients are expected to access the list of transformers through the
    class' interface rather than directly.
    """
    def __init__(self, transformers=None, usage_info=None):
        """
        Arguments:
            transformers ([BlockStructureTransformer]) - List of transformers
                to add to the collection.

            usage_info (any negotiated type) - A usage-specific object
                that is passed to the block_structure and forwarded to all
                requested Transformers in order to apply a
                usage-specific transform. For example, an instance of
                usage_info would contain a user object for which the
                transform should be applied.

        Raises:
            TransformerException - if any transformer is not registered in the
                Transformer Registry.
        """
        self.usage_info = usage_info
        self._transformers = {'optimized': [], 'nonoptimized': []}
        if transformers:
            self.__iadd__(transformers)

    def __iadd__(self, transformers):
        """
        Adds the given transformers to the collection.

        Args:
            transformers ([BlockStructureTransformer]) - List of transformers
                to add to the collection.

        Raises:
            TransformerException - if any transformer is not registered in the
                Transformer Registry.
        """
        unregistered_transformers = TransformerRegistry.find_unregistered(transformers)
        if unregistered_transformers:
            raise TransformerException(
                "The following requested transformers are not registered: {}".format(unregistered_transformers)
            )

        for transformer in transformers:
            if isinstance(transformer, OptimizedTransformer):
                self._transformers['optimized'].append(transformer)
            else:
                self._transformers['nonoptimized'].append(transformer)
        return self

    @classmethod
    def collect(cls, block_structure):
        """
        Collects data for each registered transformer.
        """
        for transformer in TransformerRegistry.get_registered_transformers():
            block_structure._add_transformer(transformer)  # pylint: disable=protected-access
            transformer.collect(block_structure)

        # Collect all fields that were requested by the transformers.
        block_structure._collect_requested_xblock_fields()  # pylint: disable=protected-access

    def transform(self, block_structure):
        """
        The given block structure is transformed by each transformer in the
        collection, in the order that the transformers were added.
        """
        self._transform_optimized(self._transformers['optimized'], block_structure)
        self._transform_nonoptimized(self._transformers['nonoptimized'], block_structure)

        # Prune the block structure to remove any unreachable blocks.
        block_structure._prune_unreachable()  # pylint: disable=protected-access

    @classmethod
    def is_collected_outdated(cls, block_structure):
        """
        Returns whether the collected data in the block structure is outdated.
        """
        outdated_transformers = []
        for transformer in TransformerRegistry.get_registered_transformers():
            version_in_block_structure = block_structure._get_transformer_data_version(transformer)  # pylint: disable=protected-access
            if transformer.VERSION != version_in_block_structure:
                outdated_transformers.append(transformer)

        if outdated_transformers:
            logger.info(
                "Collected Block Structure data for the following transformers is outdated: '%s'.",
                [(transformer.name(), transformer.VERSION) for transformer in outdated_transformers],
            )

        return bool(outdated_transformers)

    def _transform_optimized(self, transformers, block_structure):
        """
        Transforms the given block_structure using the transform_block_filter
        method from the given transformers.
        """
        if not transformers:
            return

        removal_filters = []
        for removal in [t.transform_block_filter(self.usage_info, block_structure) for t in transformers]:
            if isinstance(removal, list):
                removal_filters.extend(removal)
            else:
                removal_filters.append(removal)

        combined_filters = reduce(
            lambda t1_filter, t2_filter: self._filter_chain(t1_filter, t2_filter),
            removal_filters,
            block_structure.create_universal_filter()
        )
        block_structure.filter_topological_traversal(combined_filters)

    def _filter_chain(self, t1_filter, t2_filter):
        """
        Given two functions that take a block_key and return a boolean, yield
        a function that takes a block key, and 'ands' the functions together
        """
        return lambda block_key: t1_filter(block_key) and t2_filter(block_key)

    def _transform_nonoptimized(self, transformers, block_structure):
        """
        Transforms the given block_structure using the transform
        method from the given transformers.
        """
        for transformer in transformers:
            transformer.transform(self.usage_info, block_structure)
