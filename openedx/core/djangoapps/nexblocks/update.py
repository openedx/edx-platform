"""
Push instance data updates from upstream sources into this app's data models.
"""


def update_nex_block_instances_from_xblock_tree(root_block):
    """
    Given a root block (usually, a course), push any updates to NexBlock
    instance data down into the NexBlockInstance[Datum] models.
    """
    raise NotImplementedError
