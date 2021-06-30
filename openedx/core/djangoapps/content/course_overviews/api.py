"""
CourseOverview api
"""
import logging

from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.content.course_overviews.serializers import (
    CourseOverviewBaseSerializer,
)

log = logging.getLogger(__name__)


def get_course_overview(course_id):
    """
    Retrieve and return course overview data for the provided course id.
    """
    return CourseOverview.get_from_id(course_id)


def get_course_overview_or_none(course_id):
    """
    Retrieve and return course overview data for the provided course id.

    If the course overview does not exist, return None.
    """
    try:
        return get_course_overview(course_id)
    except CourseOverview.DoesNotExist:
        log.warning(f"Course overview does not exist for {course_id}")
        return None


def get_course_overviews(course_ids):
    """
    Return course_overview data for a given list of opaque_key course_ids.
    """
    overviews = CourseOverview.objects.filter(id__in=course_ids)
    return CourseOverviewBaseSerializer(overviews, many=True).data
