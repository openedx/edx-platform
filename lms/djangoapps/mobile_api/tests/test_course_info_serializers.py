"""
Tests for serializers for the Mobile Course Info
"""

import ddt
from django.test import TestCase
from mock import MagicMock, Mock, patch
from typing import Dict, List, Tuple, Union

from common.djangoapps.student.tests.factories import UserFactory
from lms.djangoapps.mobile_api.course_info.serializers import (
    CourseAccessSerializer,
    CourseInfoOverviewSerializer,
)
from openedx.core.djangoapps.content.course_overviews.tests.factories import CourseOverviewFactory


@ddt.ddt
class TestCourseAccessSerializer(TestCase):
    """
    Tests for the CourseAccessSerializer.
    """

    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.course = CourseOverviewFactory()

    @ddt.data(
        ([{'course_id': {}}], True),
        ([], False),
    )
    @ddt.unpack
    @patch('lms.djangoapps.mobile_api.course_info.serializers.get_pre_requisite_courses_not_completed')
    def test_has_unmet_prerequisites(
        self,
        mock_return_value: List[Dict],
        has_unmet_prerequisites: bool,
        mock_get_prerequisites: MagicMock,
    ) -> None:
        mock_get_prerequisites.return_value = mock_return_value

        output_data = CourseAccessSerializer({
            'user': self.user,
            'course': self.course,
            'course_id': self.course.id,
        }).data

        self.assertEqual(output_data['has_unmet_prerequisites'], has_unmet_prerequisites)
        mock_get_prerequisites.assert_called_once_with(self.user, [self.course.id])

    @ddt.data(
        (True, False),
        (False, True),
    )
    @ddt.unpack
    @patch('lms.djangoapps.mobile_api.course_info.serializers.check_course_open_for_learner')
    def test_is_too_early(
        self,
        mock_return_value: bool,
        is_too_early: bool,
        mock_check_course_open: MagicMock,
    ) -> None:
        mock_check_course_open.return_value = mock_return_value

        output_data = CourseAccessSerializer({
            'user': self.user,
            'course': self.course,
            'course_id': self.course.id
        }).data

        self.assertEqual(output_data['is_too_early'], is_too_early)
        mock_check_course_open.assert_called_once_with(self.user, self.course)

    @ddt.data(
        ((False, False, False), False),
        ((True, True, True), True),
        ((True, False, False), True),
    )
    @ddt.unpack
    @patch('lms.djangoapps.mobile_api.course_info.serializers.administrative_accesses_to_course_for_user')
    def test_is_staff(
        self,
        mock_return_value: Tuple[bool],
        is_staff: bool,
        mock_administrative_access: MagicMock,
    ) -> None:
        mock_administrative_access.return_value = mock_return_value

        output_data = CourseAccessSerializer({
            'user': self.user,
            'course': self.course,
            'course_id': self.course.id
        }).data

        self.assertEqual(output_data['is_staff'], is_staff)
        mock_administrative_access.assert_called_once_with(self.user, self.course.id)

    @ddt.data(None, 'mocked_user_course_expiration_date')
    @patch('lms.djangoapps.mobile_api.course_info.serializers.get_user_course_expiration_date')
    def test_get_audit_access_expires(
        self,
        mock_return_value: Union[str, None],
        mock_get_user_course_expiration_date: MagicMock,
    ) -> None:
        mock_get_user_course_expiration_date.return_value = mock_return_value

        output_data = CourseAccessSerializer({
            'user': self.user,
            'course': self.course,
            'course_id': self.course.id
        }).data

        self.assertEqual(output_data['audit_access_expires'], mock_return_value)
        mock_get_user_course_expiration_date.assert_called_once_with(self.user, self.course)

    @patch('lms.djangoapps.mobile_api.course_info.serializers.has_access')
    def test_get_courseware_access(self, mock_has_access: MagicMock) -> None:
        mocked_access = {
            'has_access': True,
            'error_code': None,
            'developer_message': None,
            'user_message': None,
            'additional_context_user_message': None,
            'user_fragment': None
        }
        mock_has_access.return_value = Mock(to_json=Mock(return_value=mocked_access))

        output_data = CourseAccessSerializer({
            'user': self.user,
            'course': self.course,
            'course_id': self.course.id
        }).data

        self.assertDictEqual(output_data['courseware_access'], mocked_access)
        mock_has_access.assert_called_once_with(self.user, 'load_mobile', self.course)
        mock_has_access.return_value.to_json.assert_called_once_with()


class TestCourseInfoOverviewSerializer(TestCase):
    """
    Tests for the CourseInfoOverviewSerializer.
    """

    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.course_overview = CourseOverviewFactory()

    def test_get_media(self):
        output_data = CourseInfoOverviewSerializer(self.course_overview, context={'user': self.user}).data

        self.assertIn('media', output_data)
        self.assertIn('image', output_data['media'])
        self.assertIn('raw', output_data['media']['image'])
        self.assertIn('small', output_data['media']['image'])
        self.assertIn('large', output_data['media']['image'])

    @patch('lms.djangoapps.mobile_api.course_info.serializers.get_link_for_about_page', return_value='mock_about_link')
    def test_get_course_sharing_utm_parameters(self, mock_get_link_for_about_page: MagicMock) -> None:
        output_data = CourseInfoOverviewSerializer(self.course_overview, context={'user': self.user}).data

        self.assertEqual(output_data['course_about'], mock_get_link_for_about_page.return_value)
        mock_get_link_for_about_page.assert_called_once_with(self.course_overview)

    def test_get_course_modes(self):
        expected_course_modes = [{'slug': 'audit', 'sku': None, 'android_sku': None, 'ios_sku': None, 'min_price': 0}]

        output_data = CourseInfoOverviewSerializer(self.course_overview, context={'user': self.user}).data

        self.assertListEqual(output_data['course_modes'], expected_course_modes)
