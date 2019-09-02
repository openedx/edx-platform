# -*- coding: utf-8 -*-
"""
CourseOverview internal api
"""
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview

from openedx.core.djangoapps.content.course_overviews.serializers import (
    CourseOverviewBaseSerializer,
)


def get_course_overviews(course_ids):
    """
    Return course_overview data for a given list of opaque_key course_ids.
    """
    overviews = CourseOverview.objects.filter(id__in=course_ids)
    return CourseOverviewBaseSerializer(overviews, many=True).data
