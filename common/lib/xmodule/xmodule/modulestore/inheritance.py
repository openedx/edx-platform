from datetime import datetime
from pytz import UTC

from xblock.fields import Scope, Boolean, String, Float, XBlockMixin
from xmodule.fields import Date, Timedelta


class InheritanceMixin(XBlockMixin):
    """Field definitions for inheritable fields"""

    graded = Boolean(
        help="Whether this module contributes to the final course grade",
        default=False,
        scope=Scope.settings
    )

    start = Date(
        help="Start time when this module is visible",
        default=datetime.fromtimestamp(0, UTC),
        scope=Scope.settings
    )
    due = Date(help="Date that this problem is due by", scope=Scope.settings)
    giturl = String(help="url root for course data git repository", scope=Scope.settings)
    xqa_key = String(help="DO NOT USE", scope=Scope.settings)
    graceperiod = Timedelta(
        help="Amount of time after the due date that submissions will be accepted",
        scope=Scope.settings
    )
    showanswer = String(
        help="When to show the problem answer to the student",
        scope=Scope.settings,
        default="finished"
    )
    rerandomize = String(
        help="When to rerandomize the problem",
        default="never",
        scope=Scope.settings
    )
    days_early_for_beta = Float(
        help="Number of days early to show content to beta users",
        default=None,
        scope=Scope.settings
    )
    static_asset_path = String(help="Path to use for static assets - overrides Studio c4x://", scope=Scope.settings, default='')


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
                name: field.read_from(descriptor)
                for name, field in InheritanceMixin.fields.items()
                if field.is_set_on(descriptor)
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

    # All inheritable metadata values (for which a value exists in field_data).
    if not hasattr(descriptor, '_inheritable_metadata'):
        setattr(descriptor, '_inheritable_metadata', {})

    # Set all inheritable metadata from kwargs that are
    # in self.inheritable_metadata and aren't already set in metadata
    for name, field in InheritanceMixin.fields.items():
        if name not in inherited_data:
            continue
        inherited_value = inherited_data[name]

        descriptor._inheritable_metadata[name] = inherited_value
        if not field.is_set_on(descriptor):
            descriptor._inherited_metadata[name] = inherited_value
            field.write_to(descriptor, inherited_value)
            # We've updated the fields on the descriptor, so we need to save it
            descriptor.save()


def own_metadata(module):
    # IN SPLIT MONGO this is just ['metadata'] as it keeps ['_inherited_metadata'] separate!
    # FIXME move into kvs? will that work for xml mongo?
    """
    Return a dictionary that contains only non-inherited field keys,
    mapped to their serialized values
    """
    inherited_metadata = getattr(module, '_inherited_metadata', {})
    metadata = {}
    for name, field in module.fields.items():
        # Only save metadata that wasn't inherited
        if field.scope != Scope.settings:
            continue

        if not field.is_set_on(module):
            continue

        if name in inherited_metadata and field.read_from(module) == inherited_metadata.get(name):
            continue

        try:
            metadata[name] = field.read_json(module)
        except KeyError:
            # Ignore any missing keys in _field_data
            pass

    return metadata
