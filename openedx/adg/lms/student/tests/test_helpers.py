"""
Unit test for student helpers
"""
import pytest
from django.conf import settings
from django.test.client import RequestFactory
from mock import patch

from common.djangoapps.student.tests.factories import RegistrationFactory, UserFactory, UserProfileFactory
from openedx.adg.lms.helpers import get_user_first_name
from openedx.adg.lms.student import helpers as student_helpers
from openedx.core.djangoapps.content.course_overviews.tests.factories import CourseOverviewFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


@pytest.fixture(name='mock_mandrill_client')
def mandrill_client(request, mocker):
    """
    A fixture to create patched Mandrill client for tests. This client does not need API key.
    """
    mock_mandrill = mocker.patch.object(student_helpers, 'MandrillClient')

    return mock_mandrill


@pytest.fixture(name='mock_task_send_mandrill_email')
def task_send_mandrill_email(request, mocker):
    """
    A fixture to create patched Mandrill client for tests. This client does not need API key.
    """
    mock_task = mocker.patch.object(student_helpers, 'task_send_mandrill_email')

    return mock_task


@pytest.mark.django_db
def test_compose_and_send_adg_activation_email(
    mocker, user_with_profile, mock_mandrill_client, mock_task_send_mandrill_email
):
    """
    Test `compose_and_send_adg_activation_email` helper method of student
    """

    mock_get_configuration_value = mocker.patch.object(student_helpers.configuration_helpers, 'get_value')
    mock_get_configuration_value.return_value = settings.LMS_ROOT_URL

    activation_key = 'some_activation_key'
    expected_context = {
        'first_name': user_with_profile.profile.name.split()[0],
        'activation_link': '{root_url}/activate/{activation_key}'.format(
            root_url=mock_get_configuration_value.return_value,
            activation_key=activation_key)
    }

    student_helpers.compose_and_send_adg_activation_email(user_with_profile, activation_key)
    mock_task_send_mandrill_email.assert_called_once_with(
        mock_mandrill_client.USER_ACCOUNT_ACTIVATION, [user_with_profile.email], expected_context
    )


@pytest.mark.django_db
@pytest.mark.parametrize('fake_request', [RequestFactory().put("/dummy", secure=True),
                                          RequestFactory().put("/dummy", secure=False)])
def test_compose_and_send_adg_password_reset_email(
    mocker, user_with_profile, mock_mandrill_client, mock_task_send_mandrill_email, fake_request
):
    """
    Test `compose_and_send_adg_password_reset_email` helper method of student
    """

    mocker.patch.object(student_helpers, 'int_to_base36')
    mocker.patch.object(student_helpers, 'default_token_generator')
    mock_reverse = mocker.patch.object(student_helpers, 'reverse')
    mock_get_configuration_value = mocker.patch.object(student_helpers.configuration_helpers, 'get_value')

    mock_get_configuration_value.return_value = settings.SITE_NAME
    mock_reverse.return_value = 'password_reset_confirm'

    expected_context = {
        'first_name': user_with_profile.profile.name.split()[0],
        'reset_link': '{protocol}://{site}{link}?track=pwreset'.format(
            protocol='https' if fake_request.is_secure() else 'http',
            site=mock_get_configuration_value.return_value,
            link=mock_reverse.return_value
        )
    }

    student_helpers.compose_and_send_adg_password_reset_email(user_with_profile, fake_request)
    mock_task_send_mandrill_email.assert_called_once_with(
        mock_mandrill_client.PASSWORD_RESET, [user_with_profile.email], expected_context
    )


@pytest.mark.django_db
def test_compose_and_send_adg_update_email_verification(
    mocker, user_with_profile, mock_mandrill_client, mock_task_send_mandrill_email
):
    """
    Test `compose_and_send_adg_update_email_verification` helper method of student
    """
    mock_get_configuration_value = mocker.patch.object(student_helpers.configuration_helpers, 'get_value')
    mock_get_configuration_value.return_value = settings.SITE_NAME

    confirmation_link = 'some_confirmation_link'
    expected_context = {
        'update_email_link': '{protocol}://{site}{link}'.format(
            protocol='https',
            site=mock_get_configuration_value.return_value,
            link=confirmation_link
        )
    }

    student_helpers.compose_and_send_adg_update_email_verification(user_with_profile.email, True, confirmation_link)
    mock_task_send_mandrill_email.assert_called_once_with(
        mock_mandrill_client.CHANGE_USER_EMAIL_ALERT, [user_with_profile.email], expected_context
    )


@pytest.mark.django_db
def test_compose_and_send_adg_update_email_confirmation(
    user_with_profile, mock_mandrill_client, mock_task_send_mandrill_email
):
    """
    Test `compose_and_send_adg_update_email_confirmation` helper method of student
    """
    context = {
        'dummy_key': 'some_dummy_data'
    }

    student_helpers.compose_and_send_adg_update_email_confirmation(user_with_profile, context)
    mock_task_send_mandrill_email.assert_called_once_with(
        mock_mandrill_client.VERIFY_CHANGE_USER_EMAIL, [user_with_profile.email], context
    )


@pytest.mark.django_db
def test_send_account_activation_email(user_with_profile, mocker):
    """
    Test `compose_and_send_adg_activation_email` is called for non-test environments.
    """
    mock_is_test_env = mocker.patch('openedx.adg.lms.student.helpers.is_testing_environment')
    mock_is_test_env.return_value = False

    mock_compose_and_send_adg_activation_email = mocker.patch.object(
        student_helpers, 'compose_and_send_adg_activation_email'
    )

    RegistrationFactory(user=user_with_profile)
    student_helpers.send_account_activation_email(user_with_profile, user_with_profile.profile)

    mock_compose_and_send_adg_activation_email.assert_called_once()


@pytest.mark.django_db
def test_compose_and_send_password_reset_success_email(
    user_with_profile, request, mocker, mock_mandrill_client, mock_task_send_mandrill_email
):
    mock_is_test_env = mocker.patch('openedx.adg.lms.student.helpers.is_testing_environment')
    mock_is_test_env.return_value = False

    mock_get_configuration_value = mocker.patch.object(student_helpers.configuration_helpers, 'get_value')
    mock_get_configuration_value.return_value = settings.LMS_ROOT_URL

    root_url = mock_get_configuration_value.return_value

    expected_context = {
        'first_name': get_user_first_name(user_with_profile),
        'signin_link': '{}/login'.format(root_url),
    }

    student_helpers.send_adg_password_reset_success_email(user_with_profile, request)
    mock_task_send_mandrill_email.assert_called_once_with(
        mock_mandrill_client.PASSWORD_RESET_SUCCESS, [user_with_profile.email], expected_context
    )


# pylint: disable=no-member
class MandrillCourseEnrollmentEmails(ModuleStoreTestCase):
    """
    Class contains tests related to course enrollments and course invitation emails
    """

    def setUp(self):
        """
        Create data that will be used in all tests of MandrillCourseEnrollmentEmails class
        """

        super(MandrillCourseEnrollmentEmails, self).setUp()
        self.user = UserFactory()
        UserProfileFactory(user=self.user)
        self.course = CourseFactory()
        self.course_overview = CourseOverviewFactory.create(id=self.course.id)

    @patch('openedx.adg.lms.student.helpers.configuration_helpers.get_value')
    @patch('openedx.adg.lms.student.helpers.task_send_mandrill_email')
    @patch('openedx.adg.lms.student.helpers.MandrillClient')
    def test_compose_and_send_adg_course_enrollment_confirmation_email(
        self, mock_mandrill_client, mock_task_send_mandrill_email, mock_get_configuration_value
    ):
        """
        Test `compose_and_send_adg_course_enrollment_confirmation_email` helper method of student
        """

        mock_get_configuration_value.return_value = settings.LMS_ROOT_URL

        course_url = '{root_url}/courses/{course_id}'.format(
            root_url=settings.LMS_ROOT_URL,
            course_id=self.course_overview.id
        )
        expected_context = {
            'course_name': self.course_overview.display_name,
            'course_url': course_url
        }
        student_helpers.compose_and_send_adg_course_enrollment_confirmation_email(self.user, self.course.id)
        mock_task_send_mandrill_email.delay.assert_called_once_with(
            mock_mandrill_client.ENROLLMENT_CONFIRMATION, [self.user.email], expected_context
        )

    @patch('openedx.adg.lms.student.helpers.task_send_mandrill_email')
    @patch('openedx.adg.lms.student.helpers.MandrillClient')
    def test_compose_and_send_adg_course_invitation_email_with_display_name_and_user(
        self, mock_mandrill_client, mock_task_send_mandrill_email
    ):
        """
        Test `compose_and_send_adg_course_enrollment_invitation_email` helper method of
        student with registered user and course's display_name in context
        """

        expected_context = {
            'course_name': self.course.display_name,
            'display_name': self.course.display_name,
            'full_name': self.user.profile.name
        }
        student_helpers.compose_and_send_adg_course_enrollment_invitation_email(
            self.user.email, {'display_name': self.course.display_name, 'course': 'dummy_obj'}
        )
        mock_task_send_mandrill_email.delay.assert_called_once_with(
            mock_mandrill_client.COURSE_ENROLLMENT_INVITATION, [self.user.email], expected_context
        )

    @patch('openedx.adg.lms.student.helpers.task_send_mandrill_email')
    @patch('openedx.adg.lms.student.helpers.MandrillClient')
    def test_compose_and_send_adg_course_invitation_email_without_display_name_and_user(
        self, mock_mandrill_client, mock_task_send_mandrill_email
    ):
        """
        Test `compose_and_send_adg_course_enrollment_invitation_email` helper method of
        student with non registered user and course's data in context
        """

        expected_context = {
            'course_name': self.course.display_name,
            'full_name': self.user.profile.name
        }
        student_helpers.compose_and_send_adg_course_enrollment_invitation_email(
            self.user.email, {'course': self.course}
        )
        mock_task_send_mandrill_email.delay.assert_called_once_with(
            mock_mandrill_client.COURSE_ENROLLMENT_INVITATION, [self.user.email], expected_context
        )
