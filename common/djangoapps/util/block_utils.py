"""
Utility library containing operations used/shared by multiple CourseBlocks.
"""


def yield_dynamic_descriptor_descendants(descriptor, user_id, block_creator=None):
    """
    This returns all of the descendants of a descriptor. If the descriptor
    has dynamic children, the block will be created using block_creator
    and the children (as descriptors) of that module will be returned.
    """
    stack = [descriptor]

    while len(stack) > 0:
        next_descriptor = stack.pop()
        stack.extend(get_dynamic_descriptor_children(next_descriptor, user_id, block_creator))
        yield next_descriptor


def get_dynamic_descriptor_children(descriptor, user_id, block_creator=None, usage_key_filter=None):
    """
    Returns the children of the given descriptor, while supporting descriptors with dynamic children.
    """
    block_children = []
    if descriptor.has_dynamic_children():
        block = None
        if descriptor.scope_ids.user_id and user_id == descriptor.scope_ids.user_id:
            # do not rebind the block if it's already bound to a user.
            block = descriptor
        elif block_creator:
            block = block_creator(descriptor)
        if block:
            block_children = block.get_child_descriptors()
    else:
        block_children = descriptor.get_children(usage_key_filter)
    return block_children
