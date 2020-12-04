"""
All tests for mailchimp pipeline handlers
"""
import pytest
from django.test.utils import override_settings

from openedx.adg.lms.applications.models import UserApplication
from openedx.adg.lms.registration_extension.models import ExtendedUserProfile
from student.models import EnrollStatusChange, UserProfile


# pylint: disable=redefined-outer-name
@pytest.fixture
@override_settings(SUSPEND_RECEIVERS=False)
def mailchimp_handlers(request):
    """
    A fixture for mailchimp handlers. Importing handler module inside test to override settings.
    """
    from openedx.adg.common.mailchimp_pipeline import handlers as mailchimp_handlers
    return mailchimp_handlers


@pytest.mark.django_db
@override_settings(SUSPEND_RECEIVERS=False)
def test_send_user_info_to_mailchimp_created_true(mocker, mailchimp_handlers):
    """
    Assert that `send_user_info_to_mailchimp` called with appropriate params and
    celery task for sync is called once as created is true.
    """
    mock_task = mocker.patch.object(mailchimp_handlers, 'task_send_user_info_to_mailchimp')
    sender = None
    instance = None
    dummy_kwargs = {'user': 'dummy'}

    mailchimp_handlers.send_user_info_to_mailchimp(sender=sender, created=True, instance=instance, **dummy_kwargs)
    mock_task.delay.assert_called_once_with(sender, instance)


@pytest.mark.django_db
@override_settings(SUSPEND_RECEIVERS=False)
def test_send_user_info_to_mailchimp_created_false(mocker, mailchimp_handlers):
    """
    Assert that `send_user_info_to_mailchimp` called with appropriate params and celery task for sync is not called
    as created is false, sender is `None` and `update_fields` are empty.
    """
    mock_task = mocker.patch.object(mailchimp_handlers, 'task_send_user_info_to_mailchimp')
    dummy_kwargs = {'user': 'dummy', 'update_fields': []}

    mailchimp_handlers.send_user_info_to_mailchimp(sender=None, created=False, instance=None, **dummy_kwargs)
    assert not mock_task.delay.called


@pytest.mark.django_db
@override_settings(SUSPEND_RECEIVERS=False)
def test_send_user_info_to_mailchimp_userprofile_updated(mocker, mailchimp_handlers):
    """
    Assert that `send_user_info_to_mailchimp` called with appropriate params and celery task for sync is called once
    as sender is `UserProfile`.
    """
    mock_task = mocker.patch.object(mailchimp_handlers, 'task_send_user_info_to_mailchimp')
    sender = UserProfile
    instance = None
    dummy_kwargs = {'user': 'dummy', 'update_fields': []}

    mailchimp_handlers.send_user_info_to_mailchimp(sender=sender, created=False, instance=instance, **dummy_kwargs)
    mock_task.delay.assert_called_once_with(sender, instance)


@pytest.mark.django_db
@override_settings(SUSPEND_RECEIVERS=False)
def test_send_user_info_to_mailchimp_application_fields_updated(mocker, mailchimp_handlers):
    """
    Assert that `send_user_info_to_mailchimp` called with appropriate params and sync with mailchimp task is called
    once when `update_fields` contains all UserApplication field which are required at mailchimp.
    """
    mock_task = mocker.patch.object(mailchimp_handlers, 'task_send_user_info_to_mailchimp')
    sender = UserApplication
    instance = None
    dummy_kwargs = {'user': 'dummy', 'update_fields': ['organization', 'status', 'business_line']}

    mailchimp_handlers.send_user_info_to_mailchimp(sender=sender, created=False, instance=instance, **dummy_kwargs)
    mock_task.delay.assert_called_once_with(sender, instance)


@pytest.mark.django_db
@override_settings(SUSPEND_RECEIVERS=False)
def test_send_user_info_to_mailchimp_application_status_updated(mocker, mailchimp_handlers):
    """
    Assert that `send_user_info_to_mailchimp` called with appropriate params and sync with mailchimp task is called
    once when `update_fields` contains one of the UserApplication fields which is required at mailchimp.
    """
    mock_task = mocker.patch.object(mailchimp_handlers, 'task_send_user_info_to_mailchimp')
    sender = UserApplication
    instance = None
    dummy_kwargs = {'user': 'dummy', 'update_fields': ['status']}

    mailchimp_handlers.send_user_info_to_mailchimp(sender=sender, created=False, instance=instance, **dummy_kwargs)
    mock_task.delay.assert_called_once_with(sender, instance)


@pytest.mark.django_db
@override_settings(SUSPEND_RECEIVERS=False)
def test_send_user_info_to_mailchimp_user_company_updated(mocker, mailchimp_handlers):
    """
    Assert that `send_user_info_to_mailchimp` called with appropriate params and sync with mailchimp task is called
    once when `update_fields` contains `company` and sender is `ExtendedUserProfile`.
    """
    mock_task = mocker.patch.object(mailchimp_handlers, 'task_send_user_info_to_mailchimp')
    sender = ExtendedUserProfile
    instance = None
    dummy_kwargs = {'user': 'dummy', 'update_fields': ['company']}

    mailchimp_handlers.send_user_info_to_mailchimp(sender=sender, created=False, instance=instance, **dummy_kwargs)
    mock_task.delay.assert_called_once_with(sender, instance)


@pytest.mark.django_db
@override_settings(SUSPEND_RECEIVERS=False)
def test_send_user_info_to_mailchimp_non_mailchimp_application_fields_updated(mocker, mailchimp_handlers):
    """
    Assert that `send_user_info_to_mailchimp` called with appropriate params and sync with mailchimp is not called
    as `update_fields` don't have application field which is required at mailchimp.
    """
    mock_task = mocker.patch.object(mailchimp_handlers, 'task_send_user_info_to_mailchimp')
    sender = UserApplication
    instance = None
    dummy_kwargs = {
        'user': 'dummy',
        'update_fields': ['reviewed_by', 'linkedin_url', 'resume', 'cover_letter_file', 'cover_letter']
    }

    mailchimp_handlers.send_user_info_to_mailchimp(sender=sender, created=False, instance=instance, **dummy_kwargs)
    assert not mock_task.delay.called


@pytest.mark.django_db
@override_settings(SUSPEND_RECEIVERS=False)
def test_send_user_info_to_mailchimp_non_mailchimp_ext_profile_fields_updated(mocker, mailchimp_handlers):
    """
    Assert that `send_user_info_to_mailchimp` called with appropriate params and sync with mailchimp is not called
    as `update_fields` don't have ExtendedProfile field which is required at mailchimp.
    """
    mock_task = mocker.patch.object(mailchimp_handlers, 'task_send_user_info_to_mailchimp')
    sender = ExtendedUserProfile
    instance = None
    dummy_kwargs = {
        'user': 'dummy',
        'update_fields': ['birth_date', 'saudi_national']
    }

    mailchimp_handlers.send_user_info_to_mailchimp(sender=sender, created=False, instance=instance, **dummy_kwargs)
    assert not mock_task.delay.called


@pytest.mark.django_db
@override_settings(SUSPEND_RECEIVERS=False)
def test_send_user_enrollments_to_mailchimp_with_valid_enrollment_event(mocker, mailchimp_handlers):
    """
    Assert that `send_user_enrollments_to_mailchimp` called with appropriate params
    """
    event = EnrollStatusChange.enroll
    dummy_kwargs = {'user': 'dummy', 'course': 'test_course'}
    mock_call = mocker.patch.object(mailchimp_handlers, 'task_send_user_enrollments_to_mailchimp')

    mailchimp_handlers.send_user_enrollments_to_mailchimp(sender=None, event=event, **dummy_kwargs)

    mock_call.delay.assert_called_once_with(**dummy_kwargs)


@pytest.mark.django_db
@override_settings(SUSPEND_RECEIVERS=False)
def test_send_user_enrollments_to_mailchimp_different_enrollment_event(mocker, mailchimp_handlers):
    """
    Assert that `send_user_enrollments_to_mailchimp` not called when signal event is other than enrollment
    or un-enrollment
    """
    mock_call = mocker.patch.object(mailchimp_handlers, 'task_send_user_enrollments_to_mailchimp')

    mailchimp_handlers.send_user_enrollments_to_mailchimp(sender=None, event=EnrollStatusChange.upgrade_complete)

    assert not mock_call.delay.called
