"""
All tests for mailchimp pipeline tasks
"""
import pytest
from django.contrib.auth.models import User

from openedx.adg.common.mailchimp_pipeline import tasks as mailchimp_tasks
from openedx.adg.lms.applications.models import UserApplication
from openedx.adg.lms.applications.test.factories import UserApplicationFactory
from openedx.adg.lms.registration_extension.models import ExtendedUserProfile
from openedx.adg.lms.registration_extension.tests.factories import ExtendedUserProfileFactory
from openedx.core.djangoapps.content.course_overviews.tests.factories import CourseOverviewFactory
from openedx.core.djangolib.testing.utils import skip_unless_lms
from student.models import UserProfile
from student.tests.factories import UserFactory


@pytest.mark.django_db
@pytest.mark.mute_signals
def test_task_send_user_info_to_mailchimp_user_created(mocker):
    """
    Assert that mailchimp client is called with valid data when User is created.
    """
    mock_mailchimp_client = mocker.patch.object(mailchimp_tasks, 'MailchimpClient', autospec=True)
    mock_create_or_update_list_member = mock_mailchimp_client().create_or_update_list_member

    user = UserFactory()
    mailchimp_tasks.task_send_user_info_to_mailchimp(User, user)

    user_json = {
        'email_address': user.email,
        'status_if_new': 'subscribed',
        'merge_fields': {
            'DATEREGIS': str(user.date_joined.strftime('%m/%d/%Y')),
            'USERNAME': user.username
        },
    }
    mock_create_or_update_list_member.assert_called_once_with(email=user.email, data=user_json)


@pytest.mark.django_db
@pytest.mark.mute_signals
def test_task_send_user_info_to_mailchimp_profile_created(mocker):
    """
    Assert that mailchimp client is called with valid data when UserProfile is created.
    """
    mock_mailchimp_client = mocker.patch.object(mailchimp_tasks, 'MailchimpClient', autospec=True)
    mock_create_or_update_list_member = mock_mailchimp_client().create_or_update_list_member

    profile = UserFactory().profile
    mailchimp_tasks.task_send_user_info_to_mailchimp(UserProfile, profile)

    user_json = {
        'email_address': profile.user.email,  # pylint: disable=no-member
        'status_if_new': 'subscribed',
        'merge_fields': {
            'LOCATION': profile.city,  # pylint: disable=no-member
            'FULLNAME': profile.name
        },
    }
    mock_create_or_update_list_member.assert_called_once_with(email=profile.user.email, data=user_json)  # pylint: disable=no-member


@pytest.mark.django_db
@pytest.mark.mute_signals
@skip_unless_lms
def test_task_send_user_info_to_mailchimp_user_application_created(mocker):
    """
    Assert that mailchimp client is called with valid data when User is created.
    """
    mock_mailchimp_client = mocker.patch.object(mailchimp_tasks, 'MailchimpClient', autospec=True)
    mock_create_or_update_list_member = mock_mailchimp_client().create_or_update_list_member

    application = UserApplicationFactory()
    mailchimp_tasks.task_send_user_info_to_mailchimp(UserApplication, application)

    user_json = {
        'email_address': application.user.email,
        'status_if_new': 'subscribed',
        'merge_fields': {
            'ORG_NAME': application.organization or '',
            'APP_STATUS': application.status,
            'B_LINE': application.business_line.title or ''
        }
    }
    mock_create_or_update_list_member.assert_called_once_with(email=application.user.email, data=user_json)


@pytest.mark.django_db
@pytest.mark.mute_signals
@skip_unless_lms
def test_task_send_user_info_to_mailchimp_extended_profile_created(mocker):
    """
    Assert that mailchimp client is called with valid data when ExtendedUserProfile is created.
    """
    mock_mailchimp_client = mocker.patch.object(mailchimp_tasks, 'MailchimpClient', autospec=True)
    mock_create_or_update_list_member = mock_mailchimp_client().create_or_update_list_member
    extended_profile = ExtendedUserProfileFactory()
    mailchimp_tasks.task_send_user_info_to_mailchimp(ExtendedUserProfile, extended_profile)

    user_json = {
        'email_address': extended_profile.user.email,
        'status_if_new': 'subscribed',
        'merge_fields': {
            'COMPANY': extended_profile.company.title or ''
        },
    }
    mock_create_or_update_list_member.assert_called_once_with(email=extended_profile.user.email, data=user_json)


@pytest.mark.django_db
@pytest.mark.mute_signals
def test_task_send_user_enrollments_to_mailchimp(mocker):
    """
    Assert that mailchimp client is called with valid data for syncing user enrollment (and un-enrolment)
    """
    mock_get_or_create = mocker.patch.object(mailchimp_tasks.CourseMeta.objects, 'get_or_create')
    mock_enrolls = mocker.patch.object(mailchimp_tasks, 'get_enrollment_course_names_and_short_ids_by_user')
    mock_enrolls.return_value = '100, 101, 102', 'course1, course2, course3'
    mock_mailchimp_client = mocker.patch.object(mailchimp_tasks, 'MailchimpClient', autospec=True)
    mock_create_or_update_list_member = mock_mailchimp_client().create_or_update_list_member
    user = UserFactory()
    course = CourseOverviewFactory()

    mailchimp_tasks.task_send_user_enrollments_to_mailchimp(user, course.id)

    user_json = {
        "email_address": user.email,
        "status_if_new": "subscribed",
        "merge_fields": {
            "ENROLLS": 'course1, course2, course3',
            "ENROLL_IDS": '100, 101, 102',
        }
    }

    mock_get_or_create.assert_called_once_with(course=course)
    mock_create_or_update_list_member.assert_called_once_with(email=user.email, data=user_json)


@pytest.mark.django_db
@pytest.mark.mute_signals
def test_task_send_user_enrollments_to_mailchimp_invalid_course_id(mocker):
    """
    Assert that mailchimp client is not called due to invalid course id
    """
    mock_log_error = mocker.patch.object(mailchimp_tasks.log, 'error')
    mock_get_or_create = mocker.patch.object(mailchimp_tasks.CourseMeta.objects, 'get_or_create')

    mailchimp_tasks.task_send_user_enrollments_to_mailchimp(UserFactory(), 'course/test/123')

    mock_log_error.assert_called_once_with(mocker.ANY)
    assert not mock_get_or_create.called
