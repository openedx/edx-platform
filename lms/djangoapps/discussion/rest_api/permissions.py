"""
Discussion API permission logic
"""
from typing import Dict, Set, Union

from opaque_keys.edx.keys import CourseKey
from rest_framework import permissions

from common.djangoapps.student.models import CourseEnrollment
from common.djangoapps.student.roles import (
    CourseInstructorRole,
    CourseStaffRole,
    GlobalStaff,
)
from lms.djangoapps.discussion.django_comment_client.utils import (
    get_user_role_names,
    has_discussion_privileges,
)
from openedx.core.djangoapps.django_comment_common.comment_client.comment import Comment
from openedx.core.djangoapps.django_comment_common.comment_client.thread import Thread
from openedx.core.djangoapps.django_comment_common.models import (
    FORUM_ROLE_ADMINISTRATOR, FORUM_ROLE_COMMUNITY_TA, FORUM_ROLE_MODERATOR
)


def _is_author(cc_content, context):
    """
    Return True if the requester authored the given content, False otherwise
    """
    return context["cc_requester"]["id"] == cc_content["user_id"]


def _is_author_or_privileged(cc_content, context):
    """
    Return True if the requester authored the given content or is a privileged
    user, False otherwise
    """
    return context["has_moderation_privilege"] or _is_author(cc_content, context)


NON_UPDATABLE_THREAD_FIELDS = {"course_id"}
NON_UPDATABLE_COMMENT_FIELDS = {"thread_id", "parent_id"}


def get_initializable_thread_fields(context):
    """
    Return the set of fields that the requester can initialize for a thread

    Any field that is editable by the author should also be initializable.
    """
    ret = get_editable_fields(
        Thread(user_id=context["cc_requester"]["id"], type="thread"),
        context
    )
    ret |= NON_UPDATABLE_THREAD_FIELDS
    return ret


def get_initializable_comment_fields(context):
    """
    Return the set of fields that the requester can initialize for a comment

    Any field that is editable by the author should also be initializable.
    """
    ret = get_editable_fields(
        Comment(user_id=context["cc_requester"]["id"], type="comment"),
        context
    )
    ret |= NON_UPDATABLE_COMMENT_FIELDS
    return ret


def _filter_fields(editable_fields: Dict[str, bool]) -> Set[str]:
    """
    Helper function that returns only the keys marked as True.
    Args:
        editable_fields (Dict[str, bool]): A mapping of strings to a bool value
            that indicates whether they should be in the output set

    Returns:
        Set[str] a set of fields that have a true value.
    """
    return {field for field, is_editable in editable_fields.items() if is_editable}


def get_editable_fields(cc_content: Union[Thread, Comment], context: Dict) -> Set[str]:
    """
    Return the set of fields that the requester can edit on the given content
    """
    # For closed thread:
    # no edits, except 'abuse_flagged' and 'read' are allowed for thread
    # no edits, except 'abuse_flagged' is allowed for comment

    is_thread = cc_content["type"] == "thread"
    is_comment = cc_content["type"] == "comment"
    has_moderation_privilege = context["has_moderation_privilege"]
    is_staff_or_admin = context["is_staff_or_admin"]

    if is_thread:
        is_thread_closed = cc_content["closed"]
    elif context.get("thread"):
        is_thread_closed = context["thread"]["closed"]
    else:
        # Flagging/un-flagging is always available.
        return {"abuse_flagged"}

    # Map each field to the condition in which it's editable.
    editable_fields = {
        "abuse_flagged": True,
        "closed": is_thread and has_moderation_privilege,
        "close_reason_code": is_thread and has_moderation_privilege,
        "pinned": is_thread and (has_moderation_privilege or is_staff_or_admin),
        "read": is_thread,
    }
    if is_thread:
        editable_fields.update({"copy_link": True})

    if is_thread_closed:
        # Return only editable fields
        return _filter_fields(editable_fields)

    is_author = _is_author(cc_content, context)
    editable_fields.update({
        "voted": has_moderation_privilege or not is_author or is_staff_or_admin,
        "raw_body": has_moderation_privilege or is_author,
        "edit_reason_code": has_moderation_privilege and not is_author,
        "following": is_thread,
        "topic_id": is_thread and (is_author or has_moderation_privilege),
        "type": is_thread and (is_author or has_moderation_privilege),
        "title": is_thread and (is_author or has_moderation_privilege),
        "group_id": is_thread and has_moderation_privilege and context["discussion_division_enabled"],
        "endorsed": (
            (is_comment and cc_content.get("parent_id", None) is None) and
            (has_moderation_privilege or
             (_is_author(context["thread"], context) and context["thread"]["thread_type"] == "question"))
        ),
        "anonymous": is_author and context["course"].allow_anonymous,
        "anonymous_to_peers": is_author and context["course"].allow_anonymous_to_peers,
    })
    # Return only editable fields
    return _filter_fields(editable_fields)


def can_delete(cc_content, context):
    """
    Return True if the requester can delete the given content, False otherwise
    """
    return _is_author_or_privileged(cc_content, context)


class IsStaffOrCourseTeamOrEnrolled(permissions.BasePermission):
    """
    Permission that checks to see if the user is allowed to post or
    comment in the course.
    """

    def has_permission(self, request, view):
        """Returns true if the user is enrolled or is staff."""
        course_key = CourseKey.from_string(view.kwargs.get('course_id'))
        return (
            GlobalStaff().has_user(request.user) or
            CourseStaffRole(course_key).has_user(request.user) or
            CourseInstructorRole(course_key).has_user(request.user) or
            CourseEnrollment.is_enrolled(request.user, course_key) or
            has_discussion_privileges(request.user, course_key)
        )


class IsStaffOrAdmin(permissions.BasePermission):
    """
    Permission that checks if the user is staff or an admin.
    """

    def has_permission(self, request, view):
        """Returns true if the user is admin or staff and request method is GET."""
        course_key = CourseKey.from_string(view.kwargs.get('course_id'))
        user_roles = get_user_role_names(request.user, course_key)
        is_user_staff = bool(user_roles & {
            FORUM_ROLE_ADMINISTRATOR,
            FORUM_ROLE_MODERATOR,
            FORUM_ROLE_COMMUNITY_TA,
        })
        return (
            GlobalStaff().has_user(request.user) or
            request.user.is_staff or
            is_user_staff and request.method == "GET"
        )
