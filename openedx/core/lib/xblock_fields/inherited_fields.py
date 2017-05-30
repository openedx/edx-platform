"""
Inherited fields for all XBlocks.
"""
from __future__ import absolute_import

from datetime import datetime

from django.conf import settings
from openedx.core.lib.partitions.partitions import UserPartition
from pytz import utc
from xblock.fields import Boolean, Dict, Float, Integer, List, Scope, String, XBlockMixin

from .fields import Date, Timedelta

DEFAULT_START_DATE = datetime(2030, 1, 1, tzinfo=utc)

# Make '_' a no-op so we can scrape strings
# Using lambda instead of `django.utils.translation.ugettext_noop` because Django cannot be imported in this file
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
        default=DEFAULT_START_DATE,
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
            # Translators: DO NOT translate the words in quotes here, they are
            # specific words for the acceptable values.
            'Specify when the Show Answer button appears for each problem. '
            'Valid values are "always", "answered", "attempted", "closed", '
            '"finished", "past_due", "correct_or_past_due", and "never".'
        ),
        scope=Scope.settings,
        default="finished",
    )

    show_correctness = String(
        display_name=_("Show Results"),
        help=_(
            # Translators: DO NOT translate the words in quotes here, they are
            # specific words for the acceptable values.
            'Specify when to show answer correctness and score to learners. '
            'Valid values are "always", "never", and "past_due".'
        ),
        scope=Scope.settings,
        default="always",
    )

    rerandomize = String(
        display_name=_("Randomization"),
        help=_(
            # Translators: DO NOT translate the words in quotes here, they are
            # specific words for the acceptable values.
            'Specify the default for how often variable values in a problem are randomized. '
            'This setting should be set to "never" unless you plan to provide a Python '
            'script to identify and randomize values in most of the problems in your course. '
            'Valid values are "always", "onreset", "never", and "per_student".'
        ),
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
            "Identify a video, 5-10 seconds in length, to play before course videos. Enter the video ID from "
            "the Video Uploads page and one or more transcript files in the following format: {format}. "
            "For example, an entry for a video with two transcripts looks like this: {example}"
        ).format(
            format='{"video_id": "ID", "transcripts": {"language": "/static/filename.srt"}}',
            example=(
                '{'
                '"video_id": "77cef264-d6f5-4cf2-ad9d-0178ab8c77be", '
                '"transcripts": {"en": "/static/DemoX-D01_1.srt", "uk": "/static/DemoX-D01_1_uk.srt"}'
                '}'
            ),
        ),
        scope=Scope.settings
    )

    # TODO: Remove this Django dependency! It really doesn't belong here.
    reset_key = "DEFAULT_SHOW_RESET_BUTTON"
    default_reset_button = getattr(settings, reset_key) if hasattr(settings, reset_key) else False
    show_reset_button = Boolean(
        display_name=_("Show Reset Button for Problems"),
        help=_(
            "Enter true or false. If true, problems in the course default to always displaying a 'Reset' button. "
            "You can override this in each problem's settings. All existing problems are affected when "
            "this course-wide setting is changed."
        ),
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

    self_paced = Boolean(
        display_name=_('Self Paced'),
        help=_(
            'Set this to "true" to mark this course as self-paced. Self-paced courses do not have '
            'due dates for assignments, and students can progress through the course at any rate before '
            'the course ends.'
        ),
        default=False,
        scope=Scope.settings
    )
