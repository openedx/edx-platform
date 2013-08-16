from xblock.core import Scope

# A list of metadata that this module can inherit from its parent module
INHERITABLE_METADATA = (
    'graded', 'start', 'due', 'graceperiod', 'showanswer', 'rerandomize',
    # TODO (ichuang): used for Fall 2012 xqa server access
    'xqa_key',
    # How many days early to show a course element to beta testers (float)
    # intended to be set per-course, but can be overridden in for specific
    # elements.  Can be a float.
    'days_early_for_beta',
    'giturl'  # for git edit link
)


def compute_inherited_metadata(descriptor):
    """Given a descriptor, traverse all of its descendants and do metadata
    inheritance.  Should be called on a CourseDescriptor after importing a
    course.

    NOTE: This means that there is no such thing as lazy loading at the
    moment--this accesses all the children."""
    for child in descriptor.get_children():
        inherit_metadata(
            child,
            {
                attr: descriptor._model_data.get(attr)
                for attr in INHERITABLE_METADATA
                if descriptor._model_data.has(attr)
            }
        )
        compute_inherited_metadata(child)


def inherit_metadata(descriptor, inherited_data):
    """
    Updates this module with metadata inherited from a containing module.
    Only metadata specified in self.inheritable_metadata will
    be inherited

    `inherited_data`: A dictionary mapping field names to the values that
        they should inherit
    """
    # The inherited values that are actually being used.
    if not hasattr(descriptor, '_inherited_metadata'):
        setattr(descriptor, '_inherited_metadata', {})

    # All inheritable metadata values (for which a value exists in model_data).
    if not hasattr(descriptor, '_inheritable_metadata'):
        setattr(descriptor, '_inheritable_metadata', {})

    # Set all inheritable metadata from kwargs that are
    # in self.inheritable_metadata and aren't already set in metadata
    for attr in INHERITABLE_METADATA:
        if attr in inherited_data:
            descriptor._inheritable_metadata[attr] = inherited_data[attr]
            if not descriptor._model_data.has(attr):
                descriptor._inherited_metadata[attr] = inherited_data[attr]
                descriptor._model_data.set(attr, inherited_data[attr])


def own_metadata(module):
    # IN SPLIT MONGO this is just ['metadata'] as it keeps ['_inherited_metadata'] separate!
    # FIXME move into kvs? will that work for xml mongo?
    """
    Return a dictionary that contains only non-inherited field keys,
    mapped to their values
    """
    inherited_metadata = getattr(module, '_inherited_metadata', {})
    metadata = {}
    for field in module.fields + module.lms.fields:
        # Only save metadata that wasn't inherited
        if field.scope != Scope.settings:
            continue

        if not module._model_data.has(field.name):
            continue

        if field.name in inherited_metadata and module._model_data.get(field.name) == inherited_metadata.get(field.name):
            continue

        try:
            metadata[field.name] = module._model_data.get(field.name)
        except KeyError:
            # Ignore any missing keys in _model_data
            pass

    return metadata
