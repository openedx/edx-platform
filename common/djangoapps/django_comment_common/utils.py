"""
Common comment client utility functions.
"""
import logging
from django_comment_common.models import (
    FORUM_ROLE_ADMINISTRATOR,
    FORUM_ROLE_COMMUNITY_TA,
    FORUM_ROLE_GROUP_MODERATOR,
    FORUM_ROLE_MODERATOR,
    FORUM_ROLE_STUDENT,
    Role
)
from openedx.core.djangoapps.course_groups.cohorts import get_legacy_discussion_settings
from openedx.core.djangoapps.request_cache import get_cache
from xmodule.modulestore.django import modulestore

from .models import CourseDiscussionSettings

log = logging.getLogger(__name__)


class ThreadContext(object):
    """ An enumeration that represents the context of a thread. Used primarily by the comments service. """
    STANDALONE = 'standalone'
    COURSE = 'course'


STUDENT_ROLE_PERMISSIONS = ["vote", "update_thread", "follow_thread", "unfollow_thread",
                            "update_comment", "create_sub_comment", "unvote", "create_thread",
                            "follow_commentable", "unfollow_commentable", "create_comment", ]

MODERATOR_ROLE_PERMISSIONS = ["edit_content", "delete_thread", "openclose_thread",
                              "endorse_comment", "delete_comment", "see_all_cohorts"]

GROUP_MODERATOR_ROLE_PERMISSIONS = ["group_edit_content", "group_delete_thread", "group_openclose_thread",
                                    "group_endorse_comment", "group_delete_comment"]

ADMINISTRATOR_ROLE_PERMISSIONS = ["manage_moderator"]


def _save_forum_role(course_key, name):
    """
    Save and Update 'course_key' for all roles which are already created to keep course_id same
    as actual passed course key
    """
    role, created = Role.objects.get_or_create(name=name, course_id=course_key)
    if created is False:
        role.course_id = course_key
        role.save()

    return role


def seed_permissions_roles(course_key):
    """
    Create and assign permissions for forum roles
    """
    administrator_role = _save_forum_role(course_key, FORUM_ROLE_ADMINISTRATOR)
    moderator_role = _save_forum_role(course_key, FORUM_ROLE_MODERATOR)
    group_moderator_role = _save_forum_role(course_key, FORUM_ROLE_GROUP_MODERATOR)
    community_ta_role = _save_forum_role(course_key, FORUM_ROLE_COMMUNITY_TA)
    student_role = _save_forum_role(course_key, FORUM_ROLE_STUDENT)

    for per in STUDENT_ROLE_PERMISSIONS:
        student_role.add_permission(per)

    for per in MODERATOR_ROLE_PERMISSIONS:
        moderator_role.add_permission(per)

    for per in GROUP_MODERATOR_ROLE_PERMISSIONS:
        group_moderator_role.add_permission(per)

    for per in ADMINISTRATOR_ROLE_PERMISSIONS:
        administrator_role.add_permission(per)

    moderator_role.inherit_permissions(student_role)
    group_moderator_role.inherit_permissions(student_role)
    # For now, Community TA == Moderator, except for the styling.
    community_ta_role.inherit_permissions(moderator_role)

    administrator_role.inherit_permissions(moderator_role)


def are_permissions_roles_seeded(course_id):
    """
    Returns whether the forums permissions for a course have been provisioned in
    the database
    """
    try:
        administrator_role = Role.objects.get(name=FORUM_ROLE_ADMINISTRATOR, course_id=course_id)
        moderator_role = Role.objects.get(name=FORUM_ROLE_MODERATOR, course_id=course_id)
        group_moderator_role = Role.objects.get(name=FORUM_ROLE_GROUP_MODERATOR, course_id=course_id)
        student_role = Role.objects.get(name=FORUM_ROLE_STUDENT, course_id=course_id)
    except:
        return False

    for per in STUDENT_ROLE_PERMISSIONS:
        if not student_role.has_permission(per):
            return False

    for per in MODERATOR_ROLE_PERMISSIONS + STUDENT_ROLE_PERMISSIONS:
        if not moderator_role.has_permission(per):
            return False

    for per in GROUP_MODERATOR_ROLE_PERMISSIONS + STUDENT_ROLE_PERMISSIONS:
        if not group_moderator_role.has_permission(per):
            return False

    for per in ADMINISTRATOR_ROLE_PERMISSIONS + MODERATOR_ROLE_PERMISSIONS + STUDENT_ROLE_PERMISSIONS:
        if not administrator_role.has_permission(per):
            return False

    return True


def get_course_discussion_settings(course_key):
    cache = get_cache('get_course_discussion_settings')
    if course_key in cache:
        return cache[course_key]

    try:
        course_discussion_settings = CourseDiscussionSettings.objects.get(course_id=course_key)
    except CourseDiscussionSettings.DoesNotExist:
        legacy_discussion_settings = get_legacy_discussion_settings(course_key)
        course_discussion_settings, _ = CourseDiscussionSettings.objects.get_or_create(
            course_id=course_key,
            defaults={
                'always_divide_inline_discussions': legacy_discussion_settings['always_cohort_inline_discussions'],
                'divided_discussions': legacy_discussion_settings['cohorted_discussions'],
                'division_scheme': CourseDiscussionSettings.COHORT if legacy_discussion_settings['is_cohorted']
                else CourseDiscussionSettings.NONE
            }
        )

    cache[course_key] = course_discussion_settings

    return course_discussion_settings


def set_course_discussion_settings(course_key, **kwargs):
    """
    Set discussion settings for a course.

    Arguments:
        course_key: CourseKey
        always_divide_inline_discussions (bool): If inline discussions should always be divided.
        divided_discussions (list): List of discussion ids.
        division_scheme (str): `CourseDiscussionSettings.NONE`, `CourseDiscussionSettings.COHORT`,
            or `CourseDiscussionSettings.ENROLLMENT_TRACK`
        discussions_id_map (dict): Dict containing discussion IDs as keys and the associated discussion
            XBlock usage keys as values.

    Returns:
        A CourseDiscussionSettings object.
    """
    fields = {
        'division_scheme': basestring,
        'always_divide_inline_discussions': bool,
        'divided_discussions': list,
        'discussions_id_map': dict,
    }
    course_discussion_settings = get_course_discussion_settings(course_key)
    for field, field_type in fields.items():
        if field in kwargs:
            if not isinstance(kwargs[field], field_type):
                raise ValueError("Incorrect field type for `{}`. Type must be `{}`".format(field, field_type.__name__))
            setattr(course_discussion_settings, field, kwargs[field])

    course_discussion_settings.save()
    cache = get_cache('get_course_discussion_settings')
    cache.pop(course_key, None)  # Remove settings cache entry

    return course_discussion_settings


def get_discussion_xblocks_by_course_id(course_id):  # pylint: disable=invalid-name
    """
    Return a list of all valid discussion xblocks in this course.
    """
    all_xblocks = modulestore().get_items(
        course_id, qualifiers={'category': 'discussion'}, include_orphans=False
    )
    return [xblock for xblock in all_xblocks if has_required_keys(xblock)]


def has_required_keys(xblock):
    """
    Returns True iff xblock has the proper attributes for generating metadata
    with get_discussion_id_map_entry()
    """
    for key in ('discussion_id', 'discussion_category', 'discussion_target'):
        if getattr(xblock, key, None) is None:
            log.debug(
                "Required key '%s' not in discussion %s, leaving out of category map",
                key,
                xblock.location
            )
            return False
    return True
