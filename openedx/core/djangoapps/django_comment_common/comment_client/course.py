# pylint: disable=missing-docstring
"""Provides base Commentable model class"""
from __future__ import annotations

from typing import Dict, Optional

from edx_django_utils.monitoring import function_trace
from opaque_keys.edx.keys import CourseKey

from openedx.core.djangoapps.django_comment_common.comment_client import settings
from openedx.core.djangoapps.django_comment_common.comment_client.utils import perform_request


def get_course_commentable_counts(course_key: CourseKey) -> Dict[str, Dict[str, int]]:
    """
    Get stats about the count of different types of threads for each commentable (topic).

    Args:
        course_key (str|CourseKey): course key for which stats are needed.

    Returns:
        A mapping of topic ids to the number of question and discussion type posts in them.

        e.g.
            {
                "general": { "discussion": 22, "question": 15 },
                "topic-1": { "discussion": 2, "question": 1 },
                ...
            }

    """
    url = f"{settings.PREFIX}/commentables/{course_key}/counts"
    response = perform_request(
        'get',
        url,
        metric_tags=[
            f"course_key:{course_key}",
            "function:get_course_commentable_counts",
        ],
        metric_action='commentable_stats.retrieve',
    )
    return response


@function_trace("get_course_user_stats")
def get_course_user_stats(course_key: CourseKey, params: Optional[Dict] = None) -> Dict[str, Dict[str, int]]:
    """
    Get stats about a user's participation in a course.

    Args:
        course_key (str|CourseKey): course key for which stats are needed.
        params (Optional[Dict]): pagination and sorting query parameters.

    Returns:
        A mapping of user ids to stats about the user.

        e.g.
            {
                "user_stats" [
                    {
                        "active_flags": 2,
                        "inactive_flags": 0,
                        "replies": 3,
                        "responses": 2,
                        "threads": 7,
                        "username": "edx"
                    },
                    ...
                ],
                "num_pages": 12,
                "page": 3,
                "count": 124
                ...
            }

    """
    if params is None:
        params = {}
    url = f"{settings.PREFIX}/users/{course_key}/stats"
    return perform_request(
        'get',
        url,
        params,
        metric_action='user.course_stats',
        metric_tags=[
            f"course_key:{course_key}",
            "function:get_course_user_stats",
        ],
    )


@function_trace("update_course_users_stats")
def update_course_users_stats(course_key: CourseKey) -> Dict:
    """
    Update the user stats for all users for a particular course.

    Args:
        course_key (str|CourseKey): course key for which stats are needed.

    Returns:
        dict: data returned by API. Contains count of users updated.
    """
    url = f"{settings.PREFIX}/users/{course_key}/update_stats"
    return perform_request(
        'post',
        url,
        metric_action='user.update_course_stats',
        metric_tags=[
            f"course_key:{course_key}",
            "function:update_course_users_stats",
        ],
    )
