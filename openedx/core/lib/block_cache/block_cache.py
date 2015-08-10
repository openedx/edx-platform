"""
...
"""
from block_structure import BlockStructureFactory
from transformer import BlockStructureTransformers


def get_blocks(cache, modulestore, user_info, root_block_key, transformers):
    if not BlockStructureTransformers.are_all_registered(transformers):
        raise Exception("One or more requested transformers are not registered.")

    # Load the cached block structure.
    root_block_structure = BlockStructureFactory.create_from_cache(root_block_key, cache)

    if not root_block_structure:

        # Create the block structure from the modulestore
        root_block_structure = BlockStructureFactory.create_from_modulestore(root_block_key, modulestore)

        # Collect data from each registered transformer
        for transformer in BlockStructureTransformers.get_registered_transformers():
            root_block_structure.add_transformer(transformer)
            transformer.collect(root_block_structure)

        # Collect all fields that were requested by the transformers
        root_block_structure.collect_requested_xblock_fields()

        # Cache this information
        BlockStructureFactory.serialize_to_cache(root_block_structure, cache)

    # Execute requested transforms on block structure
    for transformer in transformers:
        transformer.transform(user_info, root_block_structure)

    # Prune block structure
    root_block_structure.prune()

    return root_block_structure


def clear_block_cache(cache, root_block_key):
    BlockStructureFactory.remove_from_cache(root_block_key, cache)
