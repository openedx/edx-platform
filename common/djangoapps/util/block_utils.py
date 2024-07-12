"""
Utility library containing operations used/shared by multiple CourseBlocks.
"""


def yield_dynamic_block_descendants(block, user_id, block_creator=None):
    """
    This returns all of the descendants of a block. If the block
    has dynamic children, the block will be created using block_creator
    and the children (as blocks) of that module will be returned.
    """
    stack = [block]

    while len(stack) > 0:
        next_block = stack.pop()
        stack.extend(get_dynamic_block_children(next_block, user_id, block_creator))
        yield next_block


def get_dynamic_block_children(block, user_id, block_creator=None, usage_key_filter=None):
    """
    Returns the children of the given block, while supporting blocks with dynamic children.
    """
    block_children = []
    if block.has_dynamic_children():
        parent_block = None
        if block.scope_ids.user_id and user_id == block.scope_ids.user_id:
            # do not rebind the block if it's already bound to a user.
            parent_block = block
        elif block_creator:
            parent_block = block_creator(block)
        if parent_block:
            block_children = parent_block.get_child_blocks()
    else:
        block_children = block.get_children(usage_key_filter)
    return block_children
