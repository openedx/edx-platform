"""
Discussion API internal interface
"""
from django.http import Http404

from collections import defaultdict

from courseware.courses import get_course_with_access
from discussion_api.pagination import get_paginated_data
from discussion_api.serializers import ThreadSerializer, get_context
from django_comment_client.utils import get_accessible_discussion_modules
from lms.lib.comment_client.thread import Thread
from openedx.core.djangoapps.course_groups.cohorts import get_cohort_id
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

    course_key: The key of the course to get topics for
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
    course = _get_course_or_404(course_key, request.user)
    context = get_context(course, request.user)
    threads, result_page, num_pages, _ = Thread.search({
        "course_id": unicode(course.id),
        "group_id": (
            None if context["is_requester_privileged"] else
            get_cohort_id(request.user, course.id)
        ),
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

    results = [ThreadSerializer(thread, context=context).data for thread in threads]
    return get_paginated_data(request, results, page, num_pages)
