# pylint: disable=missing-docstring
"""Provides base Commentable model class"""
from __future__ import annotations

from typing import Dict

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
