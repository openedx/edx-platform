"""
Utility library containing operations used/shared by multiple courseware modules
"""


def yield_dynamic_descriptor_descendents(descriptor, module_creator):  # pylint: disable=invalid-name
    """
    This returns all of the descendants of a descriptor. If the descriptor
    has dynamic children, the module will be created using module_creator
    and the children (as descriptors) of that module will be returned.
    """
    def get_dynamic_descriptor_children(descriptor):
        """
        Internal recursive helper for traversing the child hierarchy
        """
        module_children = []
        if descriptor.has_dynamic_children():
            module = module_creator(descriptor)
            if module is not None:
                module_children = module.get_child_descriptors()
        else:
            module_children = descriptor.get_children()
        return module_children

    stack = [descriptor]

    while len(stack) > 0:
        next_descriptor = stack.pop()
        stack.extend(get_dynamic_descriptor_children(next_descriptor))
        yield next_descriptor
