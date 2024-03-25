"""
Tests for serializers for the Mobile Course Info
"""

import ddt
from mock import patch
from django.test import TestCase

from common.djangoapps.student.tests.factories import (
    UserFactory,
)
from openedx.core.djangoapps.content.course_overviews.tests.factories import (
    CourseOverviewFactory,
)
from lms.djangoapps.mobile_api.course_info.serializers import CourseAccessSerializer


@ddt.ddt
class TestCourseAccessSerializer(TestCase):
    """Tests for the CourseAccessSerializer"""

    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.course = CourseOverviewFactory()

    @ddt.data(
        ([{"course_id": {}}], True),
        ([], False),
    )
    @ddt.unpack
    @patch('lms.djangoapps.mobile_api.course_info.serializers.get_pre_requisite_courses_not_completed')
    def test_has_unmet_prerequisites(self, mock_return_value, has_unmet_prerequisites, mock_get_prerequisites):
        mock_get_prerequisites.return_value = mock_return_value
        output_data = CourseAccessSerializer({
            "user": self.user,
            "course": self.course,
            "course_id": self.course.id,
        }).data

        self.assertEqual(output_data['hasUnmetPrerequisites'], has_unmet_prerequisites)

    @ddt.data(
        (True, False),
        (False, True),
    )
    @ddt.unpack
    @patch('lms.djangoapps.mobile_api.course_info.serializers.check_course_open_for_learner')
    def test_is_too_early(self, mock_return_value, is_too_early, mock_check_course_open):
        mock_check_course_open.return_value = mock_return_value
        output_data = CourseAccessSerializer({
            "user": self.user,
            "course": self.course,
            "course_id": self.course.id
        }).data

        self.assertEqual(output_data['isTooEarly'], is_too_early)

    @ddt.data(
        ((False, False, False), False),
        ((True, True, True), True),
        ((True, False, False), True),
    )
    @ddt.unpack
    @patch('lms.djangoapps.mobile_api.course_info.serializers.administrative_accesses_to_course_for_user')
    def test_is_staff(self, mock_return_value, is_staff, mock_administrative_access):
        mock_administrative_access.return_value = mock_return_value
        output_data = CourseAccessSerializer({
            "user": self.user,
            "course": self.course,
            "course_id": self.course.id
        }).data

        self.assertEqual(output_data['isStaff'], is_staff)
