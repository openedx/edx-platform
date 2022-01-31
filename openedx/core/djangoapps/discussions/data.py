"""
Data classes for discussions
"""
from typing import List

import attr
from opaque_keys.edx.keys import CourseKey, UsageKey

# TODO: These data models will be moved to openedx_events. They are currently here to simplify the PR.


@attr.s(frozen=True)
class DiscussionTopicContext:
    """
    Context for linking the external id for a discussion topic to its associated usage key.

    The ``title`` is cached to improve the performance, since otherwise we'd
    need to look it up in the course structure each time.

    The ``group_id`` can be used for providers that don't internally support
    cohorting but we can emulate that wuth different contexts for different groups.
    """
    title = attr.ib(type=str)
    usage_key = attr.ib(type=UsageKey, default=None)
    group_id = attr.ib(type=int, default=None)
    external_id = attr.ib(type=str, default=None)
    ordering = attr.ib(type=int, default=None)


@attr.s(frozen=True)
class CourseDiscussionConfigurationData:
    """
    Course configuration information for discussions.

    Contains all the metadata needed to configure discussions for a course.

    The ``contexts`` field contains all the contexts for which discussion
    is to be enabled.
    """
    course_key = attr.ib(type=CourseKey)
    provider_type = attr.ib(type=str)
    enable_in_context = attr.ib(type=bool, default=True)
    enable_graded_units = attr.ib(type=bool, default=False)
    unit_level_visibility = attr.ib(type=bool, default=False)
    plugin_configuration = attr.ib(type=dict, default={})
    contexts = attr.ib(type=List[DiscussionTopicContext], factory=list)
