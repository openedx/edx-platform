"""
Support for inheritance of fields down an XBlock hierarchy.
"""

from datetime import datetime
from pytz import UTC

from xblock.fields import Scope, Boolean, String, Float, XBlockMixin, Dict, Integer
from xblock.runtime import KeyValueStore, KvsFieldData

from xmodule.fields import Date, Timedelta


class InheritanceMixin(XBlockMixin):
    """Field definitions for inheritable fields."""

    graded = Boolean(
        help="Whether this module contributes to the final course grade",
        scope=Scope.settings,
        default=False,
    )
    start = Date(
        help="Start time when this module is visible",
        default=datetime(2030, 1, 1, tzinfo=UTC),
        scope=Scope.settings
    )
    due = Date(
        help="Date that this problem is due by",
        scope=Scope.settings,
    )
    extended_due = Date(
        help="Date that this problem is due by for a particular student. This "
             "can be set by an instructor, and will override the global due "
             "date if it is set to a date that is later than the global due "
             "date.",
        default=None,
        scope=Scope.user_state,
    )
    course_edit_method = String(
        help="Method with which this course is edited.",
        default="Studio", scope=Scope.settings
    )
    giturl = String(
        help="url root for course data git repository",
        scope=Scope.settings,
    )
    xqa_key = String(help="DO NOT USE", scope=Scope.settings)
    annotation_storage_url = String(help="Location of Annotation backend", scope=Scope.settings, default="http://your_annotation_storage.com", display_name="Url for Annotation Storage")
    annotation_token_secret = String(help="Secret string for annotation storage", scope=Scope.settings, default="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx", display_name="Secret Token String for Annotation")
    graceperiod = Timedelta(
        help="Amount of time after the due date that submissions will be accepted",
        scope=Scope.settings,
    )
    showanswer = String(
        help="When to show the problem answer to the student",
        scope=Scope.settings,
        default="finished",
    )
    rerandomize = String(
        help="When to rerandomize the problem",
        scope=Scope.settings,
        default="never",
    )
    days_early_for_beta = Float(
        help="Number of days early to show content to beta users",
        scope=Scope.settings,
        default=None,
    )
    static_asset_path = String(
        help="Path to use for static assets - overrides Studio c4x://",
        scope=Scope.settings,
        default='',
    )
    text_customization = Dict(
        help="String customization substitutions for particular locations",
        scope=Scope.settings,
    )
    use_latex_compiler = Boolean(
        help="Enable LaTeX templates?",
        default=False,
        scope=Scope.settings
    )
    max_attempts = Integer(
        display_name="Maximum Attempts",
        help=("Defines the number of times a student can try to answer this problem. "
              "If the value is not set, infinite attempts are allowed."),
        values={"min": 0}, scope=Scope.settings
    )
    grade_videos = Boolean(
        help="pass",
        display_name='Grade videos',
        scope=Scope.settings,
        default=False
    )



def compute_inherited_metadata(descriptor):
    """Given a descriptor, traverse all of its descendants and do metadata
    inheritance.  Should be called on a CourseDescriptor after importing a
    course.

    NOTE: This means that there is no such thing as lazy loading at the
    moment--this accesses all the children."""
    if descriptor.has_children:
        parent_metadata = descriptor.xblock_kvs.inherited_settings.copy()
        # add any of descriptor's explicitly set fields to the inheriting list
        for field in InheritanceMixin.fields.values():
            if field.is_set_on(descriptor):
                # inherited_settings values are json repr
                parent_metadata[field.name] = field.read_json(descriptor)

        for child in descriptor.get_children():
            inherit_metadata(child, parent_metadata)
            compute_inherited_metadata(child)


def inherit_metadata(descriptor, inherited_data):
    """
    Updates this module with metadata inherited from a containing module.
    Only metadata specified in self.inheritable_metadata will
    be inherited

    `inherited_data`: A dictionary mapping field names to the values that
        they should inherit
    """
    try:
        descriptor.xblock_kvs.inherited_settings = inherited_data
    except AttributeError:  # the kvs doesn't have inherited_settings probably b/c it's an error module
        pass


def own_metadata(module):
    """
    Return a dictionary that contains only non-inherited field keys,
    mapped to their serialized values
    """
    return module.get_explicitly_set_fields_by_scope(Scope.settings)


class InheritingFieldData(KvsFieldData):
    """A `FieldData` implementation that can inherit value from parents to children."""

    def __init__(self, inheritable_names, **kwargs):
        """
        `inheritable_names` is a list of names that can be inherited from
        parents.

        """
        super(InheritingFieldData, self).__init__(**kwargs)
        self.inheritable_names = set(inheritable_names)

    def default(self, block, name):
        """
        The default for an inheritable name is found on a parent.
        """
        if name in self.inheritable_names and block.parent is not None:
            parent = block.get_parent()
            if parent:
                return getattr(parent, name)
        super(InheritingFieldData, self).default(block, name)


def inheriting_field_data(kvs):
    """Create an InheritanceFieldData that inherits the names in InheritanceMixin."""
    return InheritingFieldData(
        inheritable_names=InheritanceMixin.fields.keys(),
        kvs=kvs,
    )


class InheritanceKeyValueStore(KeyValueStore):
    """
    Common superclass for kvs's which know about inheritance of settings. Offers simple
    dict-based storage of fields and lookup of inherited values.

    Note: inherited_settings is a dict of key to json values (internal xblock field repr)
    """
    def __init__(self, initial_values=None, inherited_settings=None):
        super(InheritanceKeyValueStore, self).__init__()
        self.inherited_settings = inherited_settings or {}
        self._fields = initial_values or {}

    def get(self, key):
        return self._fields[key.field_name]

    def set(self, key, value):
        # xml backed courses are read-only, but they do have some computed fields
        self._fields[key.field_name] = value

    def delete(self, key):
        del self._fields[key.field_name]

    def has(self, key):
        return key.field_name in self._fields

    def default(self, key):
        """
        Check to see if the default should be from inheritance rather than from the field's global default
        """
        return self.inherited_settings[key.field_name]
