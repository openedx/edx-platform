# -*- coding: utf-8 -*-
"""
course_overview api tests
"""
from django.test import TestCase

from openedx.core.djangoapps.content.course_overviews.api import get_course_overviews
from openedx.core.djangoapps.content.course_overviews.tests.factories import CourseOverviewFactory

from ..models import CourseOverview


class TestCourseOverviewsApi(TestCase):
    """
    TestCourseOverviewsApi tests.
    """

    def setUp(self):
        super(TestCourseOverviewsApi, self).setUp()
        for _ in range(3):
            CourseOverviewFactory.create()

    def test_get_course_overviews(self):
        """
        get_course_overviews should return the expected CourseOverview data
        in serialized form (a list of dicts)
        """
        course_ids = []
        course_ids.append(str(CourseOverview.objects.first().id))
        course_ids.append(str(CourseOverview.objects.last().id))

        data = get_course_overviews(course_ids)
        assert len(data) == 2
        for overview in data:
            assert overview['id'] in course_ids

        fields = [
            'display_name_with_default',
            'has_started',
            'has_ended',
            'pacing',
        ]
        for field in fields:
            assert field in data[0]
