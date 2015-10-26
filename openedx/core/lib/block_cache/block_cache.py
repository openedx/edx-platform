"""
Top-level module for the Block Cache framework with higher order
functions for getting and clearing cached blocks.
"""
from .block_structure_factory import BlockStructureFactory
from .exceptions import TransformerException
from .transformer_registry import TransformerRegistry


def get_blocks(cache, modulestore, user_info, root_block_key, transformers):
    """
    Top-level function in the Block Cache framework that manages
    the cache (populating it and updating it when needed), calls the
    transformers as appropriate (collect and transform methods), and
    accessing the modulestore when needed (at cache miss).

    Arguments:
        cache (django.core.cache.backends.base.BaseCache) - The
            cache to use for storing/retrieving the block structure's
            collected data.

        modulestore (ModuleStoreRead) - The modulestore that
            contains the data for the xBlock objects corresponding to
            the block structure.

        root_block_key (UsageKey) - The usage_key for the root
            of the block structure that is being accessed.

        transformers ([BlockStructureTransformer]) - The list of
            transformers whose transform methods are to be called.
            This list should be a subset of the list of registered
            transformers in the Transformer Registry.
    """

    # Verify that all requested transformers are registered in the
    # Transformer Registry.
    unregistered_transformers = TransformerRegistry.find_unregistered(transformers)
    if unregistered_transformers:
        raise TransformerException(
            "The following requested transformers are not registered: {}".format(unregistered_transformers)
        )

    # Load the cached block structure.
    root_block_structure = BlockStructureFactory.create_from_cache(root_block_key, cache, transformers)

    # On cache miss, execute the collect phase and update the cache.
    if not root_block_structure:

        # Create the block structure from the modulestore.
        root_block_structure = BlockStructureFactory.create_from_modulestore(root_block_key, modulestore)

        # Collect data from each registered transformer.
        for transformer in TransformerRegistry.get_registered_transformers():
            root_block_structure._add_transformer(transformer)
            transformer.collect(root_block_structure)

        # Collect all fields that were requested by the transformers.
        root_block_structure._collect_requested_xblock_fields()

        # Cache this information.
        BlockStructureFactory.serialize_to_cache(root_block_structure, cache)

    # Execute requested transforms on block structure.
    for transformer in transformers:
        transformer.transform(user_info, root_block_structure)

    # Prune the block structure to remove any unreachable blocks.
    root_block_structure._prune()

    return root_block_structure


def clear_block_cache(cache, root_block_key):
    """
    Removes the block structure associated with the given root block
    key.
    """
    BlockStructureFactory.remove_from_cache(root_block_key, cache)
