"""
Discussion API internal interface
"""
from django.http import Http404

from collections import defaultdict

from courseware.courses import get_course_with_access
from discussion_api.pagination import get_paginated_data
from django_comment_client.utils import get_accessible_discussion_modules
from django_comment_common.models import (
    FORUM_ROLE_ADMINISTRATOR,
    FORUM_ROLE_COMMUNITY_TA,
    FORUM_ROLE_MODERATOR,
    Role,
)
from lms.lib.comment_client.thread import Thread
from lms.lib.comment_client.user import User
from openedx.core.djangoapps.course_groups.cohorts import get_cohort_id, get_cohort_names
from xmodule.tabs import DiscussionTab


def _get_course_or_404(course_key, user):
    """
    Get the course descriptor, raising Http404 if the course is not found,
    the user cannot access forums for the course, or the discussion tab is
    disabled for the course.
    """
    course = get_course_with_access(user, 'load_forum', course_key)
    if not any([isinstance(tab, DiscussionTab) for tab in course.tabs]):
        raise Http404
    return course


def get_course_topics(course_key, user):
    """
    Return the course topic listing for the given course and user.

    Parameters:

    course: The course to get topics for
    user: The requesting user, for access control

    Returns:

    A course topic listing dictionary; see discussion_api.views.CourseTopicViews
    for more detail.
    """
    def get_module_sort_key(module):
        """
        Get the sort key for the module (falling back to the discussion_target
        setting if absent)
        """
        return module.sort_key or module.discussion_target

    course = _get_course_or_404(course_key, user)
    discussion_modules = get_accessible_discussion_modules(course, user)
    modules_by_category = defaultdict(list)
    for module in discussion_modules:
        modules_by_category[module.discussion_category].append(module)
    courseware_topics = [
        {
            "id": None,
            "name": category,
            "children": [
                {
                    "id": module.discussion_id,
                    "name": module.discussion_target,
                    "children": [],
                }
                for module in sorted(modules_by_category[category], key=get_module_sort_key)
            ],
        }
        for category in sorted(modules_by_category.keys())
    ]

    non_courseware_topics = [
        {
            "id": entry["id"],
            "name": name,
            "children": [],
        }
        for name, entry in sorted(
            course.discussion_topics.items(),
            key=lambda item: item[1].get("sort_key", item[0])
        )
    ]

    return {
        "courseware_topics": courseware_topics,
        "non_courseware_topics": non_courseware_topics,
    }


def _cc_thread_to_api_thread(thread, cc_user, staff_user_ids, ta_user_ids, group_ids_to_names):
    """
    Convert a thread data dict from the comment_client format (which is a direct
    representation of the format returned by the comments service) to the format
    used in this API

    Arguments:
      thread (comment_client.thread.Thread): The thread to convert
      cc_user (comment_client.user.User): The comment_client representation of
        the requesting user
      staff_user_ids (set): The set of user ids for users with the Moderator or
        Administrator role in the course
      ta_user_ids (set): The set of user ids for users with the Community TA
        role in the course
      group_ids_to_names (dict): A mapping of group ids to names

    Returns:
      dict: The discussion_api format representation of the thread.
    """
    is_anonymous = (
        thread["anonymous"] or
        (
            thread["anonymous_to_peers"] and
            int(cc_user["id"]) not in (staff_user_ids | ta_user_ids)
        )
    )
    ret = {
        key: thread[key]
        for key in [
            "id",
            "course_id",
            "group_id",
            "created_at",
            "updated_at",
            "title",
            "pinned",
            "closed",
        ]
    }
    ret.update({
        "topic_id": thread["commentable_id"],
        "group_name": group_ids_to_names.get(thread["group_id"]),
        "author": None if is_anonymous else thread["username"],
        "author_label": (
            None if is_anonymous else
            "staff" if int(thread["user_id"]) in staff_user_ids else
            "community_ta" if int(thread["user_id"]) in ta_user_ids else
            None
        ),
        "type": thread["thread_type"],
        "raw_body": thread["body"],
        "following": thread["id"] in cc_user["subscribed_thread_ids"],
        "abuse_flagged": cc_user["id"] in thread["abuse_flaggers"],
        "voted": thread["id"] in cc_user["upvoted_ids"],
        "vote_count": thread["votes"]["up_count"],
        "comment_count": thread["comments_count"],
        "unread_comment_count": thread["unread_comments_count"],
    })
    return ret


def get_thread_list(request, course_key, page, page_size):
    """
    Return the list of all discussion threads pertaining to the given course

    Parameters:

    request: The django request objects used for build_absolute_uri
    course: The course to get discussion threads for
    page: The page number (1-indexed) to retrieve
    page_size: The number of threads to retrieve per page

    Returns:

    A paginated result containing a list of threads; see
    discussion_api.views.ThreadViewSet for more detail.
    """
    course = _get_course_or_404(course_key, request.user)
    user_is_privileged = Role.objects.filter(
        course_id=course.id,
        name__in=[FORUM_ROLE_ADMINISTRATOR, FORUM_ROLE_MODERATOR, FORUM_ROLE_COMMUNITY_TA],
        users=request.user
    ).exists()
    cc_user = User.from_django_user(request.user).retrieve()
    threads, result_page, num_pages, _ = Thread.search({
        "course_id": unicode(course.id),
        "group_id": None if user_is_privileged else get_cohort_id(request.user, course.id),
        "sort_key": "date",
        "sort_order": "desc",
        "page": page,
        "per_page": page_size,
    })
    # The comments service returns the last page of results if the requested
    # page is beyond the last page, but we want be consistent with DRF's general
    # behavior and return a 404 in that case
    if result_page != page:
        raise Http404
    # TODO: cache staff_user_ids and ta_user_ids if we need to improve perf
    staff_user_ids = {
        user.id
        for role in Role.objects.filter(
            name__in=[FORUM_ROLE_ADMINISTRATOR, FORUM_ROLE_MODERATOR],
            course_id=course.id
        )
        for user in role.users.all()
    }
    ta_user_ids = {
        user.id
        for role in Role.objects.filter(name=FORUM_ROLE_COMMUNITY_TA, course_id=course.id)
        for user in role.users.all()
    }
    # For now, the only groups are cohorts
    group_ids_to_names = get_cohort_names(course)

    results = [
        _cc_thread_to_api_thread(thread, cc_user, staff_user_ids, ta_user_ids, group_ids_to_names)
        for thread in threads
    ]
    return get_paginated_data(request, results, page, num_pages)
