"""
Discussion API internal interface
"""
from django.http import Http404

from collections import defaultdict

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
from openedx.core.djangoapps.course_groups.cohorts import get_cohort_id


def get_course_topics(course, user):
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


def _cc_thread_to_api_thread(thread, cc_user):
    """
    Convert a thread data dict from the comment_client format (which is a direct
    representation of the format returned by the comments service) to the format
    used in this API
    """
    ret = {
        key: thread[key]
        for key in [
            "id",
            "course_id",
            "created_at",
            "updated_at",
            "type",
            "title",
            "pinned",
            "closed",
        ]
    }
    ret.update({
        "topic_id": thread["commentable_id"],
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
    course_key: The key of the course to get discussion threads for
    page: The page number (1-indexed) to retrieve
    page_size: The number of threads to retrieve per page

    Returns:

    A paginated result containing a list of threads; see
    discussion_api.views.ThreadViewSet for more detail.
    """
    user_is_privileged = Role.objects.filter(
        course_id=course_key,
        name__in=[FORUM_ROLE_ADMINISTRATOR, FORUM_ROLE_MODERATOR, FORUM_ROLE_COMMUNITY_TA],
        users=request.user
    ).exists()
    cc_user = User.from_django_user(request.user).retrieve()
    threads, result_page, num_pages, _ = Thread.search({
        "course_id": unicode(course_key),
        "group_id": None if user_is_privileged else get_cohort_id(request.user, course_key),
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

    results = [_cc_thread_to_api_thread(thread, cc_user) for thread in threads]
    return get_paginated_data(request, results, page, num_pages)
