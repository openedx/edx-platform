"""
Test the enterprise support utils.
"""

from unittest import mock
from unittest.case import TestCase

from django.core.exceptions import ObjectDoesNotExist
from opaque_keys.edx.keys import CourseKey

from openedx.core.djangoapps.course_groups.cohorts import CourseUserGroup
from openedx.core.djangoapps.enrollments.errors import CourseEnrollmentError, CourseEnrollmentExistsError
from openedx.core.djangolib.testing.utils import skip_unless_lms
from openedx.features.enterprise_support.enrollments.exceptions import (
    CourseIdMissingException,
    UserDoesNotExistException
)
from openedx.features.enterprise_support.enrollments.utils import lms_enroll_user_in_course

COURSE_STRING = 'course-v1:OpenEdX+OutlineCourse+Run3'
ENTERPRISE_UUID = 'enterprise_uuid'
COURSE_ID = CourseKey.from_string(COURSE_STRING)
USERNAME = 'test'
USER_ID = 1223
COURSE_MODE = 'verified'


@skip_unless_lms
class EnrollmentUtilsTest(TestCase):
    """
    Test enterprise support utils.
    """

    def setUp(self):
        super().setUp()
        self.a_user = mock.MagicMock()
        self.a_user.id = USER_ID
        self.a_user.username = USERNAME

    def test_validation_of_inputs_course_id(self):
        with self.assertRaises(CourseIdMissingException):
            lms_enroll_user_in_course(USERNAME, None, COURSE_MODE, ENTERPRISE_UUID)

    def test_validation_of_inputs_user_not_provided(self):
        with self.assertRaises(UserDoesNotExistException):
            lms_enroll_user_in_course(
                None,
                COURSE_ID,
                COURSE_MODE,
                ENTERPRISE_UUID,
            )

    @mock.patch('openedx.features.enterprise_support.enrollments.utils.User.objects.get')
    @mock.patch('openedx.features.enterprise_support.enrollments.utils.transaction')
    def test_validation_of_inputs_user_not_found(self, mock_tx, mock_user_model):
        mock_tx.return_value.atomic.side_effect = None
        mock_user_model.side_effect = ObjectDoesNotExist()
        with self.assertRaises(UserDoesNotExistException):
            lms_enroll_user_in_course(
                USERNAME,
                COURSE_ID,
                COURSE_MODE,
                ENTERPRISE_UUID,
            )

    @mock.patch('openedx.features.enterprise_support.enrollments.utils.enrollment_api.add_enrollment')
    @mock.patch('openedx.features.enterprise_support.enrollments.utils.enrollment_api.get_enrollment')
    @mock.patch('openedx.features.enterprise_support.enrollments.utils.User.objects.get')
    @mock.patch('openedx.features.enterprise_support.enrollments.utils.transaction')
    def test_course_enrollment_error_raises(
        self,
        mock_tx,
        mock_user_model,
        mock_get_enrollment_api,
        mock_add_enrollment_api,
    ):
        enrollment_response = {'mode': COURSE_MODE, 'is_active': True}

        mock_add_enrollment_api.side_effect = CourseEnrollmentError("test")
        mock_tx.return_value.atomic.side_effect = None

        mock_get_enrollment_api.return_value = enrollment_response

        mock_user_model.return_value = self.a_user

        with self.assertRaises(CourseEnrollmentError):
            lms_enroll_user_in_course(USERNAME, COURSE_ID, COURSE_MODE, ENTERPRISE_UUID)
            mock_get_enrollment_api.assert_called_once()

    @mock.patch('openedx.features.enterprise_support.enrollments.utils.enrollment_api.add_enrollment')
    @mock.patch('openedx.features.enterprise_support.enrollments.utils.enrollment_api.get_enrollment')
    @mock.patch('openedx.features.enterprise_support.enrollments.utils.User.objects.get')
    @mock.patch('openedx.features.enterprise_support.enrollments.utils.transaction')
    def test_course_group_error_raises(
        self,
        mock_tx,
        mock_user_model,
        mock_get_enrollment_api,
        mock_add_enrollment_api,
    ):
        enrollment_response = {'mode': COURSE_MODE, 'is_active': True}

        mock_add_enrollment_api.side_effect = CourseUserGroup.DoesNotExist()
        mock_tx.return_value.atomic.side_effect = None

        mock_get_enrollment_api.return_value = enrollment_response

        mock_user_model.return_value = self.a_user

        with self.assertRaises(CourseUserGroup.DoesNotExist):
            lms_enroll_user_in_course(USERNAME, COURSE_ID, COURSE_MODE, ENTERPRISE_UUID)
            mock_get_enrollment_api.assert_called_once()

    @mock.patch('openedx.features.enterprise_support.enrollments.utils.enrollment_api.add_enrollment')
    @mock.patch('openedx.features.enterprise_support.enrollments.utils.enrollment_api.get_enrollment')
    @mock.patch('openedx.features.enterprise_support.enrollments.utils.User.objects.get')
    @mock.patch('openedx.features.enterprise_support.enrollments.utils.transaction')
    def test_calls_enrollment_and_cohort_apis(
        self,
        mock_tx,
        mock_user_model,
        mock_get_enrollment_api,
        mock_add_enrollment_api,
    ):

        expected_response = {'a': 'value'}
        enrollment_response = {'mode': COURSE_MODE, 'is_active': True}

        mock_add_enrollment_api.return_value = expected_response
        mock_tx.return_value.atomic.side_effect = None

        mock_get_enrollment_api.return_value = enrollment_response

        mock_user_model.return_value = self.a_user

        response = lms_enroll_user_in_course(USERNAME, COURSE_ID, COURSE_MODE, ENTERPRISE_UUID)

        assert response == expected_response
        mock_add_enrollment_api.assert_called_once_with(
            USERNAME,
            str(COURSE_ID),
            mode=COURSE_MODE,
            is_active=True,
            enrollment_attributes=None,
            enterprise_uuid=ENTERPRISE_UUID,
        )

        mock_get_enrollment_api.assert_called_once_with(USERNAME, str(COURSE_ID))

    @mock.patch('openedx.features.enterprise_support.enrollments.utils.enrollment_api.add_enrollment')
    @mock.patch('openedx.features.enterprise_support.enrollments.utils.enrollment_api.get_enrollment')
    @mock.patch('openedx.features.enterprise_support.enrollments.utils.User.objects.get')
    @mock.patch('openedx.features.enterprise_support.enrollments.utils.transaction')
    def test_existing_enrollment_does_not_fail(
        self,
        mock_tx,
        mock_user_model,
        mock_get_enrollment_api,
        mock_add_enrollment_api,
    ):

        expected_response = None
        enrollment_response = {'mode': COURSE_MODE, 'is_active': True}

        mock_add_enrollment_api.side_effect = CourseEnrollmentExistsError("test", {})
        mock_tx.return_value.atomic.side_effect = None

        mock_get_enrollment_api.return_value = enrollment_response

        mock_user_model.return_value = self.a_user

        response = lms_enroll_user_in_course(USERNAME, COURSE_ID, COURSE_MODE, ENTERPRISE_UUID)

        assert response == expected_response
        mock_add_enrollment_api.assert_called_once_with(
            USERNAME,
            str(COURSE_ID),
            mode=COURSE_MODE,
            is_active=True,
            enrollment_attributes=None,
            enterprise_uuid=ENTERPRISE_UUID,
        )

        mock_get_enrollment_api.assert_called_once()
