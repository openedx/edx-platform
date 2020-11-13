"""
All tests for mailchimp pipeline signals
"""
import pytest
from django.test.utils import override_settings

from openedx.core.djangoapps.content.course_overviews.tests.factories import CourseOverviewFactory
from student.models import EnrollStatusChange
from student.tests.factories import UserFactory


@pytest.mark.django_db
def test_listen_for_auth_user_model(mocker):
    """
    Assert that `send_user_info_to_mailchimp` called with appropriate params
    """
    user = UserFactory()
    created = False

    with override_settings(SUSPEND_RECEIVERS=False):
        # Importing signals module inside test to override settings
        # Decorators are called when module is first imported
        from openedx.adg.common.mailchimp_pipeline import signals as mailchimp_signals
        mock_call = mocker.patch.object(mailchimp_signals, 'send_user_info_to_mailchimp')

        mailchimp_signals.listen_for_auth_user_model(sender=None, instance=user, created=created)

        mock_call.assert_called_once_with(user, created)


@pytest.mark.django_db
def test_listen_for_user_enrollments(mocker):
    """
    Assert that `send_user_enrollments_to_mailchimp` called with appropriate params
    """
    course = CourseOverviewFactory()
    event = EnrollStatusChange.enroll
    user = UserFactory()

    with override_settings(SUSPEND_RECEIVERS=False):
        # Importing signals module inside test to override settings
        # Decorators are called when module is first imported
        from openedx.adg.common.mailchimp_pipeline import signals as mailchimp_signals
        mock_call = mocker.patch.object(mailchimp_signals, 'send_user_enrollments_to_mailchimp')

        mailchimp_signals.listen_for_user_enrollments(sender=None, event=event, user=user, course_id=course.id)

        mock_call.assert_called_once_with(user, course)


@pytest.mark.django_db
@override_settings(SUSPEND_RECEIVERS=False)
def test_listen_for_user_enrollments_different_enrollment_event(mocker):
    """
    Assert that `send_user_enrollments_to_mailchimp` not called when signal event was different
    """
    from openedx.adg.common.mailchimp_pipeline import signals as mailchimp_signals
    mock_call = mocker.patch.object(mailchimp_signals, 'send_user_enrollments_to_mailchimp')

    mailchimp_signals.listen_for_user_enrollments(
        sender=None, event=EnrollStatusChange.upgrade_complete, user=None, kwargs={}
    )

    assert not mock_call.called
