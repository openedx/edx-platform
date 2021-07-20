"""
Test the enterprise support utils.
"""

from unittest import mock
from unittest.case import TestCase

from django.core.exceptions import ObjectDoesNotExist
from opaque_keys.edx.keys import CourseKey

from common.djangoapps.student.tests.factories import UserFactory
from openedx.core.djangoapps.course_groups.cohorts import CourseUserGroup
from openedx.core.djangoapps.enrollments.errors import CourseEnrollmentError, CourseEnrollmentExistsError
from openedx.core.djangolib.testing.utils import skip_unless_lms
from openedx.features.enterprise_support.enrollments.exceptions import (
    CourseIdMissingException,
    UserDoesNotExistException
)
from openedx.features.enterprise_support.enrollments.utils import lms_enroll_user_in_course

COURSE_STRING = 'course-v1:OpenEdX+OutlineCourse+Run3'


@skip_unless_lms
class EnrollmentUtilsTest(TestCase):
    """
    Test enterprise support utils.
    """

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory.create(password='password')
        super().setUpTestData()

    def test_validation_of_inputs_course_id(self):
        with self.assertRaises(CourseIdMissingException):
            lms_enroll_user_in_course('user', None, 'verified')

    def test_validation_of_inputs_user_not_provided(self):
        with self.assertRaises(UserDoesNotExistException):
            lms_enroll_user_in_course(
                None,
                CourseKey.from_string(COURSE_STRING),
                'verified'
            )

    @mock.patch('openedx.features.enterprise_support.enrollments.utils.User')
    def test_validation_of_inputs_user_not_found(self, mock_user_model):
        mock_user_model.return_value.objects.return_value.get.side_effect = ObjectDoesNotExist
        with self.assertRaises(UserDoesNotExistException):
            lms_enroll_user_in_course(
                None,
                CourseKey.from_string(COURSE_STRING),
                'verified'
            )

    @mock.patch('openedx.features.enterprise_support.enrollments.utils.api.add_enrollment')
    @mock.patch('openedx.features.enterprise_support.enrollments.utils.api.get_enrollment')
    @mock.patch('openedx.features.enterprise_support.enrollments.utils.add_user_to_course_cohort')
    @mock.patch('openedx.features.enterprise_support.enrollments.utils.User')
    @mock.patch('openedx.features.enterprise_support.enrollments.utils.transaction')
    def test_course_enrollment_error_raises(self,
                                            mock_tx,
                                            mock_user_model,
                                            mock_add_user_to_course_cohort,
                                            mock_get_enrollment_api,
                                            mock_add_enrollment_api,
                                            ):
        enrollment_response = {'mode': 'verified', 'is_active': True}
        username = 'test'
        course_id = CourseKey.from_string(COURSE_STRING)
        mode = "verified"

        mock_add_enrollment_api.side_effect = CourseEnrollmentError("test")
        mock_tx.return_value.atomic.side_effect = None

        mock_get_enrollment_api.return_value = enrollment_response

        a_user = {'id': 1223, 'username': username}
        mock_user_model.return_value.objects.return_value.get.return_value = a_user

        with self.assertRaises(CourseEnrollmentError):
            lms_enroll_user_in_course(username, course_id, mode)
            mock_add_user_to_course_cohort.assert_not_called()
            mock_get_enrollment_api.assert_called_once()

    @mock.patch('openedx.features.enterprise_support.enrollments.utils.api.add_enrollment')
    @mock.patch('openedx.features.enterprise_support.enrollments.utils.api.get_enrollment')
    @mock.patch('openedx.features.enterprise_support.enrollments.utils.add_user_to_course_cohort')
    @mock.patch('openedx.features.enterprise_support.enrollments.utils.User')
    @mock.patch('openedx.features.enterprise_support.enrollments.utils.transaction')
    def test_course_group_error_raises(self,
                                       mock_tx,
                                       mock_user_model,
                                       mock_add_user_to_course_cohort,
                                       mock_get_enrollment_api,
                                       mock_add_enrollment_api,
                                       ):
        enrollment_response = {'mode': 'verified', 'is_active': True}
        username = 'test'
        course_id = CourseKey.from_string(COURSE_STRING)
        mode = "verified"

        mock_add_enrollment_api.side_effect = CourseUserGroup.DoesNotExist()
        mock_tx.return_value.atomic.side_effect = None

        mock_get_enrollment_api.return_value = enrollment_response

        a_user = {'id': 1223, 'username': username}
        mock_user_model.return_value.objects.return_value.get.return_value = a_user

        with self.assertRaises(CourseUserGroup.DoesNotExist):
            lms_enroll_user_in_course(username, course_id, mode)
            mock_add_user_to_course_cohort.assert_not_called()
            mock_get_enrollment_api.assert_called_once()

    @mock.patch('openedx.features.enterprise_support.enrollments.utils.api.add_enrollment')
    @mock.patch('openedx.features.enterprise_support.enrollments.utils.api.get_enrollment')
    @mock.patch('openedx.features.enterprise_support.enrollments.utils.add_user_to_course_cohort')
    @mock.patch('openedx.features.enterprise_support.enrollments.utils.User')
    @mock.patch('openedx.features.enterprise_support.enrollments.utils.transaction')
    def test_calls_enrollment_and_cohort_apis(
        self,
        mock_tx,
        mock_user_model,
        mock_add_user_to_course_cohort,
        mock_get_enrollment_api,
        mock_add_enrollment_api,
    ):

        expected_response = {'a': 'value'}
        enrollment_response = {'mode': 'verified', 'is_active': True}
        username = 'test'
        course_id = CourseKey.from_string(COURSE_STRING)
        mode = "verified"

        mock_add_enrollment_api.return_value = expected_response
        mock_tx.return_value.atomic.side_effect = None

        mock_get_enrollment_api.return_value = enrollment_response

        a_user = {'id': 1223, 'username': username}
        mock_user_model.return_value.objects.return_value.get.return_value = a_user

        response = lms_enroll_user_in_course(username, course_id, mode)

        assert response == expected_response
        mock_add_enrollment_api.assert_called_once_with(
            username,
            str(course_id),
            mode=mode,
            is_active=True,
            enrollment_attributes=None
        )

        mock_add_user_to_course_cohort.assert_called_once()
        mock_get_enrollment_api.assert_called_once_with(username, str(course_id))

    @mock.patch('openedx.features.enterprise_support.enrollments.utils.api.add_enrollment')
    @mock.patch('openedx.features.enterprise_support.enrollments.utils.api.get_enrollment')
    @mock.patch('openedx.features.enterprise_support.enrollments.utils.add_user_to_course_cohort')
    @mock.patch('openedx.features.enterprise_support.enrollments.utils.User')
    @mock.patch('openedx.features.enterprise_support.enrollments.utils.transaction')
    def test_existing_enrollment_does_not_fail(
        self,
        mock_tx,
        mock_user_model,
        mock_add_user_to_course_cohort,
        mock_get_enrollment_api,
        mock_add_enrollment_api,
    ):

        expected_response = None
        enrollment_response = {'mode': 'verified', 'is_active': True}
        username = 'test'
        course_id = CourseKey.from_string(COURSE_STRING)
        mode = "verified"

        mock_add_enrollment_api.side_effect = CourseEnrollmentExistsError("test", {})
        mock_tx.return_value.atomic.side_effect = None

        mock_get_enrollment_api.return_value = enrollment_response

        a_user = {'id': 1223, 'username': username}
        mock_user_model.return_value.objects.return_value.get.return_value = a_user

        response = lms_enroll_user_in_course(username, course_id, mode)

        assert response == expected_response
        mock_add_enrollment_api.assert_called_once_with(
            username,
            str(course_id),
            mode=mode,
            is_active=True,
            enrollment_attributes=None
        )

        mock_add_user_to_course_cohort.assert_not_called()
        mock_get_enrollment_api.assert_called_once()
