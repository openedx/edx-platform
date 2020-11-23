"""
All tests for mailchimp pipeline handlers
"""
import pytest
from django.test.utils import override_settings

from student.models import EnrollStatusChange


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
    Assert that `send_user_info_to_mailchimp` called with appropriate params
    """
    dummy_kwargs = {'user': 'dummy'}
    mock_task = mocker.patch.object(mailchimp_handlers, 'task_send_user_info_to_mailchimp')

    mailchimp_handlers.send_user_info_to_mailchimp(sender=None, created=True, kwargs=dummy_kwargs)
    mock_task.assert_called_once_with(kwargs=dummy_kwargs)


@pytest.mark.django_db
@override_settings(SUSPEND_RECEIVERS=False)
def test_send_user_enrollments_to_mailchimp_with_valid_enrollment_event(mocker, mailchimp_handlers):
    """
    Assert that `send_user_enrollments_to_mailchimp` called with appropriate params
    """
    event = EnrollStatusChange.enroll
    dummy_kwargs = {'user': 'dummy', 'course': 'test_course'}
    mock_call = mocker.patch.object(mailchimp_handlers, 'task_send_user_enrollments_to_mailchimp')

    mailchimp_handlers.send_user_enrollments_to_mailchimp(sender=None, event=event, kwargs=dummy_kwargs)

    mock_call.assert_called_once_with(kwargs=dummy_kwargs)


@pytest.mark.django_db
@override_settings(SUSPEND_RECEIVERS=False)
def test_send_user_enrollments_to_mailchimp_different_enrollment_event(mocker, mailchimp_handlers):
    """
    Assert that `send_user_enrollments_to_mailchimp` not called when signal event is other than enrollment
    or un-enrollment
    """
    mock_call = mocker.patch.object(mailchimp_handlers, 'task_send_user_enrollments_to_mailchimp')

    mailchimp_handlers.send_user_enrollments_to_mailchimp(sender=None, event=EnrollStatusChange.upgrade_complete)

    assert not mock_call.called
