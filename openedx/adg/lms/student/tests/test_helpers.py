"""
Unit test for student helpers
"""

import pytest
from django.conf import settings
from django.test.client import RequestFactory
from mock import patch

from openedx.adg.common.lib.mandrill_client.client import MandrillClient
from openedx.adg.lms.student import helpers as student_helpers
from openedx.core.djangoapps.content.course_overviews.tests.factories import CourseOverviewFactory
from student.tests.factories import UserFactory, UserProfileFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


@pytest.fixture
def user_with_profile(request):
    """
    Create user with profile, this fixture will be passed as a parameter to all pytests
    """
    user = UserFactory()
    UserProfileFactory(user=user)
    return user


@pytest.mark.django_db
def test_compose_and_send_adg_activation_email(mocker, user_with_profile):  # pylint: disable=redefined-outer-name
    """
    Test `compose_and_send_adg_activation_email` helper method of student
    """

    mock_send_email = mocker.patch.object(student_helpers, 'send_mandrill_email')

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
    mock_send_email.assert_called_once_with(
        MandrillClient.USER_ACCOUNT_ACTIVATION, user_with_profile.email, expected_context
    )


@pytest.mark.django_db
@pytest.mark.parametrize('fake_request', [RequestFactory().put("/dummy", secure=True),
                                          RequestFactory().put("/dummy", secure=False)])
def test_compose_and_send_adg_password_reset_email(
    mocker, user_with_profile, fake_request  # pylint: disable=redefined-outer-name
):
    """
    Test `compose_and_send_adg_password_reset_email` helper method of student
    """

    mocker.patch.object(student_helpers, 'int_to_base36')
    mocker.patch.object(student_helpers, 'default_token_generator')
    mock_reverse = mocker.patch.object(student_helpers, 'reverse')
    mock_send_email = mocker.patch.object(student_helpers, 'send_mandrill_email')
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
    mock_send_email.assert_called_once_with(MandrillClient.PASSWORD_RESET, user_with_profile.email, expected_context)


@pytest.mark.django_db
def test_compose_and_send_adg_update_email_verification(
    mocker, user_with_profile  # pylint: disable=redefined-outer-name
):
    """
    Test `compose_and_send_adg_update_email_verification` helper method of student
    """

    mock_send_email = mocker.patch.object(student_helpers, 'send_mandrill_email')

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

    student_helpers.compose_and_send_adg_update_email_verification(user_with_profile, True, confirmation_link)
    mock_send_email.assert_called_once_with(
        MandrillClient.CHANGE_USER_EMAIL_ALERT, user_with_profile.email, expected_context
    )


@pytest.mark.django_db
def test_compose_and_send_adg_update_email_confirmation(
    mocker, user_with_profile  # pylint: disable=redefined-outer-name
):
    """
    Test `compose_and_send_adg_update_email_confirmation` helper method of student
    """

    mock_send_email = mocker.patch.object(student_helpers, 'send_mandrill_email')

    context = {
        'dummy_key': 'some_dummy_data'
    }

    student_helpers.compose_and_send_adg_update_email_confirmation(user_with_profile, context)
    mock_send_email.assert_called_once_with(MandrillClient.VERIFY_CHANGE_USER_EMAIL, user_with_profile.email, context)


@pytest.mark.django_db
def test_send_mandrill_email(mocker, user_with_profile):  # pylint: disable=redefined-outer-name
    """
    Test `send_mandrill_email` helper method of student
    """

    mock_email_data = mocker.patch.object(student_helpers, 'EmailData')
    mock_mandrill_email = mocker.patch.object(student_helpers.MandrillClient, 'send_mail')

    template_name = 'some_template_slug'
    context = {'dummy_key': 'some_dummy_data'}

    mock_email_data.return_value = 'dummy_email_data'
    student_helpers.send_mandrill_email(template_name, user_with_profile.email, context)

    mock_email_data.assert_called_once_with(template_name, user_with_profile.email, context)
    mock_mandrill_email.assert_called_once_with('dummy_email_data')


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
    @patch('openedx.adg.lms.student.helpers.send_mandrill_email')
    def test_compose_and_send_adg_course_enrollment_confirmation_email(
        self, mock_send_email, mock_get_configuration_value
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
        mock_send_email.assert_called_once_with(
            MandrillClient.ENROLLMENT_CONFIRMATION, self.user.email, expected_context
        )

    @patch('openedx.adg.lms.student.helpers.send_mandrill_email')
    def test_compose_and_send_adg_course_invitation_email_with_display_name_and_user(self, mock_send_email):
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
        mock_send_email.assert_called_once_with(
            MandrillClient.COURSE_ENROLLMENT_INVITATION, self.user.email, expected_context
        )

    @patch('openedx.adg.lms.student.helpers.send_mandrill_email')
    def test_compose_and_send_adg_course_invitation_email_without_display_name_and_user(self, mock_send_email):
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
        mock_send_email.assert_called_once_with(
            MandrillClient.COURSE_ENROLLMENT_INVITATION, self.user.email, expected_context
        )
