from xmodule.model import Scope


def compute_inherited_metadata(descriptor):
    """Given a descriptor, traverse all of its descendants and do metadata
    inheritance.  Should be called on a CourseDescriptor after importing a
    course.

    NOTE: This means that there is no such thing as lazy loading at the
    moment--this accesses all the children."""
    for child in descriptor.get_children():
        inherit_metadata(child, descriptor._model_data)
        compute_inherited_metadata(child)


def inherit_metadata(descriptor, model_data):
    """
    Updates this module with metadata inherited from a containing module.
    Only metadata specified in self.inheritable_metadata will
    be inherited
    """
    if not hasattr(descriptor, '_inherited_metadata'):
        setattr(descriptor, '_inherited_metadata', set())

    # Set all inheritable metadata from kwargs that are
    # in self.inheritable_metadata and aren't already set in metadata
    for attr in descriptor.inheritable_metadata:
        if attr not in descriptor._model_data and attr in model_data:
            descriptor._inherited_metadata.add(attr)
            descriptor._model_data[attr] = model_data[attr]


def own_metadata(module):
    """
    Return a dictionary that contains only non-inherited field keys,
    mapped to their values
    """
    inherited_metadata = getattr(module, '_inherited_metadata', {})
    metadata = {}
    for field in module.fields + module.lms.fields:
        # Only save metadata that wasn't inherited
        if (field.scope == Scope.settings and
            field.name not in inherited_metadata and
            field.name in module._model_data):

            metadata[field.name] = module._model_data[field.name]

    return metadata
