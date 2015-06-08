"""
Support for inheritance of fields down an XBlock hierarchy.
"""
from __future__ import absolute_import

from datetime import datetime
from pytz import UTC
from xmodule.partitions.partitions import UserPartition
from xblock.fields import Scope, Boolean, String, Float, XBlockMixin, Dict, Integer, List
from xblock.runtime import KeyValueStore, KvsFieldData
from xmodule.fields import Date, Timedelta
from django.conf import settings


# Make '_' a no-op so we can scrape strings
_ = lambda text: text


class UserPartitionList(List):
    """Special List class for listing UserPartitions"""
    def from_json(self, values):
        return [UserPartition.from_json(v) for v in values]

    def to_json(self, values):
        return [user_partition.to_json()
                for user_partition in values]


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
        display_name=_("Due Date"),
        help=_("Enter the default date by which problems are due."),
        scope=Scope.settings,
    )
    visible_to_staff_only = Boolean(
        help=_("If true, can be seen only by course staff, regardless of start date."),
        default=False,
        scope=Scope.settings,
    )
    course_edit_method = String(
        display_name=_("Course Editor"),
        help=_("Enter the method by which this course is edited (\"XML\" or \"Studio\")."),
        default="Studio",
        scope=Scope.settings,
        deprecated=True  # Deprecated because user would not change away from Studio within Studio.
    )
    giturl = String(
        display_name=_("GIT URL"),
        help=_("Enter the URL for the course data GIT repository."),
        scope=Scope.settings
    )
    xqa_key = String(
        display_name=_("XQA Key"),
        help=_("This setting is not currently supported."), scope=Scope.settings,
        deprecated=True
    )
    annotation_storage_url = String(
        help=_("Enter the location of the annotation storage server. The textannotation, videoannotation, and imageannotation advanced modules require this setting."),
        scope=Scope.settings,
        default="http://your_annotation_storage.com",
        display_name=_("URL for Annotation Storage")
    )
    annotation_token_secret = String(
        help=_("Enter the secret string for annotation storage. The textannotation, videoannotation, and imageannotation advanced modules require this string."),
        scope=Scope.settings,
        default="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
        display_name=_("Secret Token String for Annotation")
    )
    graceperiod = Timedelta(
        help="Amount of time after the due date that submissions will be accepted",
        scope=Scope.settings,
    )
    group_access = Dict(
        help=_("Enter the ids for the content groups this problem belongs to."),
        scope=Scope.settings,
    )
    showanswer = String(
        display_name=_("Show Answer"),
        help=_(
            'Specify when the Show Answer button appears for each problem. '
            'Valid values are "always", "answered", "attempted", "closed", '
            '"finished", "past_due", "correct_or_past_due", and "never".'
        ),
        scope=Scope.settings,
        default="finished",
    )
    rerandomize = String(
        display_name=_("Randomization"),
        help=_("Specify how often variable values in a problem are randomized when a student loads the problem. Valid values are \"always\", \"onreset\", \"never\", and \"per_student\". This setting only applies to problems that have randomly generated numeric values."),
        scope=Scope.settings,
        default="never",
    )
    days_early_for_beta = Float(
        display_name=_("Days Early for Beta Users"),
        help=_("Enter the number of days before the start date that beta users can access the course."),
        scope=Scope.settings,
        default=None,
    )
    static_asset_path = String(
        display_name=_("Static Asset Path"),
        help=_("Enter the path to use for files on the Files & Uploads page. This value overrides the Studio default, c4x://."),
        scope=Scope.settings,
        default='',
    )
    text_customization = Dict(
        display_name=_("Text Customization"),
        help=_("Enter string customization substitutions for particular locations."),
        scope=Scope.settings,
    )
    use_latex_compiler = Boolean(
        display_name=_("Enable LaTeX Compiler"),
        help=_("Enter true or false. If true, you can use the LaTeX templates for HTML components and advanced Problem components."),
        default=False,
        scope=Scope.settings
    )
    max_attempts = Integer(
        display_name=_("Maximum Attempts"),
        help=_("Enter the maximum number of times a student can try to answer problems. By default, Maximum Attempts is set to null, meaning that students have an unlimited number of attempts for problems. You can override this course-wide setting for individual problems. However, if the course-wide setting is a specific number, you cannot set the Maximum Attempts for individual problems to unlimited."),
        values={"min": 0}, scope=Scope.settings
    )
    matlab_api_key = String(
        display_name=_("Matlab API key"),
        help=_("Enter the API key provided by MathWorks for accessing the MATLAB Hosted Service. "
               "This key is granted for exclusive use in this course for the specified duration. "
               "Do not share the API key with other courses. Notify MathWorks immediately "
               "if you believe the key is exposed or compromised. To obtain a key for your course, "
               "or to report an issue, please contact moocsupport@mathworks.com"),
        scope=Scope.settings
    )
    # This is should be scoped to content, but since it's defined in the policy
    # file, it is currently scoped to settings.
    user_partitions = UserPartitionList(
        display_name=_("Group Configurations"),
        help=_("Enter the configurations that govern how students are grouped together."),
        default=[],
        scope=Scope.settings
    )
    video_speed_optimizations = Boolean(
        display_name=_("Enable video caching system"),
        help=_("Enter true or false. If true, video caching will be used for HTML5 videos."),
        default=True,
        scope=Scope.settings
    )
    video_bumper = Dict(
        display_name=_("Video Pre-Roll"),
        help=_(
            """Identify a video, 5-10 seconds in length, to play before course videos. Enter the video ID from"""
            """ the Video Uploads page and one or more transcript files in the following format:"""
            """ {"video_id": "ID", "transcripts": {"language": "/static/filename.srt"}}."""
            """ For example, an entry for a video with two transcripts looks like this:"""
            """ {"video_id": "77cef264-d6f5-4cf2-ad9d-0178ab8c77be","""
            """ "transcripts": {"en": "/static/DemoX-D01_1.srt", "uk": "/static/DemoX-D01_1_uk.srt"}}"""
        ),
        scope=Scope.settings
    )

    reset_key = "DEFAULT_SHOW_RESET_BUTTON"
    default_reset_button = getattr(settings, reset_key) if hasattr(settings, reset_key) else False
    show_reset_button = Boolean(
        display_name=_("Show Reset Button for Problems"),
        help=_("Enter true or false. If true, problems in the course default to always displaying a 'Reset' button. You can "
               "override this in each problem's settings. All existing problems are affected when this course-wide setting is changed."),
        scope=Scope.settings,
        default=default_reset_button
    )
    edxnotes = Boolean(
        display_name=_("Enable Student Notes"),
        help=_("Enter true or false. If true, students can use the Student Notes feature."),
        default=False,
        scope=Scope.settings
    )
    edxnotes_visibility = Boolean(
        display_name="Student Notes Visibility",
        help=_("Indicates whether Student Notes are visible in the course. "
               "Students can also show or hide their notes in the courseware."),
        default=True,
        scope=Scope.user_info
    )

    in_entrance_exam = Boolean(
        display_name=_("Tag this module as part of an Entrance Exam section"),
        help=_("Enter true or false. If true, answer submissions for problem modules will be "
               "considered in the Entrance Exam scoring/gating algorithm."),
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
    Return a JSON-friendly dictionary that contains only non-inherited field
    keys, mapped to their serialized values
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
        if name in self.inheritable_names:
            # Walk up the content tree to find the first ancestor
            # that this field is set on. Use the field from the current
            # block so that if it has a different default than the root
            # node of the tree, the block's default will be used.
            field = block.fields[name]
            ancestor = block.get_parent()
            while ancestor is not None:
                if field.is_set_on(ancestor):
                    return field.read_json(ancestor)
                else:
                    ancestor = ancestor.get_parent()
        return super(InheritingFieldData, self).default(block, name)


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
        Check to see if the default should be from inheritance. If not
        inheriting, this will raise KeyError which will cause the caller to use
        the field's global default.
        """
        return self.inherited_settings[key.field_name]
