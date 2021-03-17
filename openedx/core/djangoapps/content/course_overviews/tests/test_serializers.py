"""
CourseOverviewSerializer tests
"""
from django.test import TestCase

from openedx.core.djangoapps.content.course_overviews.serializers import CourseOverviewBaseSerializer
from openedx.core.djangoapps.content.course_overviews.tests.factories import CourseOverviewFactory

from ..models import CourseOverview


class TestCourseOverviewSerializer(TestCase):
    """
    TestCourseOverviewSerializer tests.
    """

    def setUp(self):
        super().setUp()
        CourseOverviewFactory.create()

    def test_get_course_overview_serializer(self):
        """
        CourseOverviewBaseSerializer should add additional fields in the
        to_representation method that is overridden.
        """
        overview = CourseOverview.objects.first()
        data = CourseOverviewBaseSerializer(overview).data

        fields = [
            'display_name_with_default',
            'has_started',
            'has_ended',
            'pacing',
        ]
        for field in fields:
            assert field in data

        assert isinstance(data['has_started'], bool)
        assert isinstance(data['has_ended'], bool)
