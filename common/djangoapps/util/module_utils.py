"""
Utility library containing operations used/shared by multiple courseware modules
"""


def yield_dynamic_descriptor_descendents(descriptor, module_creator):  # pylint: disable=invalid-name
    """
    This returns all of the descendants of a descriptor. If the descriptor
    has dynamic children, the module will be created using module_creator
    and the children (as descriptors) of that module will be returned.
    """
    stack = [descriptor]

    while len(stack) > 0:
        next_descriptor = stack.pop()
        stack.extend(get_dynamic_descriptor_children(next_descriptor, module_creator))
        yield next_descriptor


def get_dynamic_descriptor_children(descriptor, module_creator, usage_key_filter=None):
    """
    Returns the children of the given descriptor, while supporting descriptors with dynamic children.
    """
    module_children = []
    if descriptor.has_dynamic_children():
        module = module_creator(descriptor)
        if module is not None:
            module_children = module.get_child_descriptors()
    else:
        module_children = descriptor.get_children(usage_key_filter)
    return module_children
