"""
Test cases for notifications/email/tasks.py
"""
import datetime
import ddt

from unittest.mock import patch

from edx_toggles.toggles.testutils import override_waffle_flag

from common.djangoapps.student.tests.factories import UserFactory
from openedx.core.djangoapps.notifications.config.waffle import ENABLE_NOTIFICATIONS, ENABLE_EMAIL_NOTIFICATIONS
from openedx.core.djangoapps.notifications.tasks import send_notifications
from openedx.core.djangoapps.notifications.email_notifications import EmailCadence
from openedx.core.djangoapps.notifications.email.tasks import (
    get_audience_for_cadence_email,
    send_digest_email_to_all_users,
    send_digest_email_to_user
)
from openedx.core.djangoapps.notifications.email.utils import get_start_end_date
from openedx.core.djangoapps.notifications.models import CourseNotificationPreference
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

from .utils import create_notification


@ddt.ddt
class TestEmailDigestForUser(ModuleStoreTestCase):
    """
    Tests email notification for a specific user
    """

    def setUp(self):
        """
        Setup
        """
        super().setUp()
        self.user = UserFactory()
        self.course = CourseFactory.create(display_name='test course', run="Testing_course")

    @patch('edx_ace.ace.send')
    def test_email_is_not_sent_if_no_notifications(self, mock_func):
        """
        Tests email is sent iff waffle flag is enabled
        """
        start_date, end_date = get_start_end_date(EmailCadence.DAILY)
        with override_waffle_flag(ENABLE_EMAIL_NOTIFICATIONS, True):
            send_digest_email_to_user(self.user, EmailCadence.DAILY, start_date, end_date)
        assert not mock_func.called

    @ddt.data(True, False)
    @patch('edx_ace.ace.send')
    def test_email_is_sent_iff_flag_enabled(self, flag_value, mock_func):
        """
        Tests email is sent iff waffle flag is enabled
        """
        created_date = datetime.datetime.now() - datetime.timedelta(days=1)
        create_notification(self.user, self.course.id, created=created_date)
        start_date, end_date = get_start_end_date(EmailCadence.DAILY)
        with override_waffle_flag(ENABLE_EMAIL_NOTIFICATIONS, flag_value):
            send_digest_email_to_user(self.user, EmailCadence.DAILY, start_date, end_date)
        assert mock_func.called is flag_value

    @patch('edx_ace.ace.send')
    def test_notification_not_send_if_created_on_next_day(self, mock_func):
        """
        Tests email is not sent if notification is created on next day
        """
        start_date, end_date = get_start_end_date(EmailCadence.DAILY)
        create_notification(self.user, self.course.id, created=end_date + datetime.timedelta(minutes=2))
        with override_waffle_flag(ENABLE_EMAIL_NOTIFICATIONS, True):
            send_digest_email_to_user(self.user, EmailCadence.DAILY, start_date, end_date)
        assert not mock_func.called

    @ddt.data(True, False)
    @patch('edx_ace.ace.send')
    def test_email_not_send_to_disable_user(self, value, mock_func):
        """
        Tests email is not sent to disabled user
        """
        created_date = datetime.datetime.now() - datetime.timedelta(days=1)
        create_notification(self.user, self.course.id, created=created_date)
        start_date, end_date = get_start_end_date(EmailCadence.DAILY)
        if value:
            self.user.set_password("12345678")
        else:
            self.user.set_unusable_password()
        with override_waffle_flag(ENABLE_EMAIL_NOTIFICATIONS, True):
            send_digest_email_to_user(self.user, EmailCadence.DAILY, start_date, end_date)
        assert mock_func.called is value

    @patch('edx_ace.ace.send')
    def test_notification_not_send_if_created_day_before_yesterday(self, mock_func):
        """
        Tests email is not sent if notification is created day before yesterday
        """
        start_date, end_date = get_start_end_date(EmailCadence.DAILY)
        created_date = datetime.datetime.now() - datetime.timedelta(days=1, minutes=18)
        create_notification(self.user, self.course.id, created=created_date)
        with override_waffle_flag(ENABLE_EMAIL_NOTIFICATIONS, True):
            send_digest_email_to_user(self.user, EmailCadence.DAILY, start_date, end_date)
        assert not mock_func.called

    @ddt.data(
        (EmailCadence.DAILY, datetime.datetime.now() - datetime.timedelta(days=1, minutes=30), False),
        (EmailCadence.DAILY, datetime.datetime.now() - datetime.timedelta(minutes=10), True),
        (EmailCadence.DAILY, datetime.datetime.now() - datetime.timedelta(days=1), True),
        (EmailCadence.DAILY, datetime.datetime.now() + datetime.timedelta(minutes=20), False),
        (EmailCadence.WEEKLY, datetime.datetime.now() - datetime.timedelta(days=7, minutes=30), False),
        (EmailCadence.WEEKLY, datetime.datetime.now() - datetime.timedelta(days=7), True),
        (EmailCadence.WEEKLY, datetime.datetime.now() - datetime.timedelta(minutes=20), True),
        (EmailCadence.WEEKLY, datetime.datetime.now() + datetime.timedelta(minutes=20), False),
    )
    @ddt.unpack
    @patch('edx_ace.ace.send')
    def test_notification_content(self, cadence_type, created_time, notification_created, mock_func):
        """
        Tests email only contains notification created within date
        """
        start_date, end_date = get_start_end_date(cadence_type)
        create_notification(self.user, self.course.id, created=created_time)
        with override_waffle_flag(ENABLE_EMAIL_NOTIFICATIONS, True):
            send_digest_email_to_user(self.user, EmailCadence.DAILY, start_date, end_date)
        assert mock_func.called is notification_created


@ddt.ddt
class TestEmailDigestAudience(ModuleStoreTestCase):
    """
    Tests audience for notification digest email
    """

    def setUp(self):
        """
        Setup
        """
        super().setUp()
        self.user = UserFactory()
        self.course = CourseFactory.create(display_name='test course', run="Testing_course")

    @patch('openedx.core.djangoapps.notifications.email.tasks.send_digest_email_to_user')
    def test_email_func_not_called_if_no_notification(self, mock_func):
        """
        Tests email sending function is not called if user has no notifications
        """
        with override_waffle_flag(ENABLE_EMAIL_NOTIFICATIONS, True):
            send_digest_email_to_all_users(EmailCadence.DAILY)
        assert not mock_func.called

    @patch('openedx.core.djangoapps.notifications.email.tasks.send_digest_email_to_user')
    def test_email_func_called_if_user_has_notification(self, mock_func):
        """
        Tests email sending function is called if user has notification
        """
        created_date = datetime.datetime.now() - datetime.timedelta(days=1)
        create_notification(self.user, self.course.id, created=created_date)
        with override_waffle_flag(ENABLE_EMAIL_NOTIFICATIONS, True):
            send_digest_email_to_all_users(EmailCadence.DAILY)
        assert mock_func.called

    @patch('openedx.core.djangoapps.notifications.email.tasks.send_digest_email_to_user')
    def test_email_func_not_called_if_user_notification_is_not_duration(self, mock_func):
        """
        Tests email sending function is not called if user has notification
        which is not in duration
        """
        created_date = datetime.datetime.now() - datetime.timedelta(days=10)
        create_notification(self.user, self.course.id, created=created_date)
        with override_waffle_flag(ENABLE_EMAIL_NOTIFICATIONS, True):
            send_digest_email_to_all_users(EmailCadence.DAILY)
        assert not mock_func.called

    @patch('edx_ace.ace.send')
    def test_email_is_sent_to_user_when_task_is_called(self, mock_func):
        created_date = datetime.datetime.now() - datetime.timedelta(days=1)
        create_notification(self.user, self.course.id, created=created_date)
        with override_waffle_flag(ENABLE_EMAIL_NOTIFICATIONS, True):
            send_digest_email_to_all_users(EmailCadence.DAILY)
        assert mock_func.called
        assert mock_func.call_count == 1

    def test_audience_query_count(self):
        with self.assertNumQueries(1):
            audience = get_audience_for_cadence_email(EmailCadence.DAILY)
            list(audience)   # evaluating queryset

    @ddt.data(True, False)
    @patch('edx_ace.ace.send')
    def test_digest_should_contain_email_enabled_notifications(self, email_value, mock_func):
        """
        Tests email is sent only when notifications with email=True exists
        """
        start_date, end_date = get_start_end_date(EmailCadence.DAILY)
        created_date = datetime.datetime.now() - datetime.timedelta(hours=23, minutes=59)
        create_notification(self.user, self.course.id, created=created_date, email=email_value)
        with override_waffle_flag(ENABLE_EMAIL_NOTIFICATIONS, True):
            send_digest_email_to_user(self.user, EmailCadence.DAILY, start_date, end_date)
            assert mock_func.called is email_value


@ddt.ddt
class TestPreferences(ModuleStoreTestCase):
    """
    Tests preferences
    """
    def setUp(self):
        """
        Setup
        """
        super().setUp()
        self.user = UserFactory()
        self.course = CourseFactory.create(display_name='test course', run="Testing_course")
        self.preference = CourseNotificationPreference.objects.create(user=self.user, course_id=self.course.id)
        created_date = datetime.datetime.now() - datetime.timedelta(hours=23)
        create_notification(self.user, self.course.id, notification_type='new_discussion_post', created=created_date)

    @patch('edx_ace.ace.send')
    def test_email_send_for_digest_preference(self, mock_func):
        """
        Tests email is send for digest notification preference
        """
        start_date, end_date = get_start_end_date(EmailCadence.DAILY)
        config = self.preference.notification_preference_config
        types = config['discussion']['notification_types']
        types['new_discussion_post']['email_cadence'] = EmailCadence.DAILY
        types['new_discussion_post']['email'] = True
        self.preference.save()
        with override_waffle_flag(ENABLE_EMAIL_NOTIFICATIONS, True):
            send_digest_email_to_user(self.user, EmailCadence.DAILY, start_date, end_date)
        assert mock_func.called

    @ddt.data(True, False)
    @patch('edx_ace.ace.send')
    def test_email_send_for_email_preference_value(self, pref_value, mock_func):
        """
        Tests email is sent iff preference value is True
        """
        start_date, end_date = get_start_end_date(EmailCadence.DAILY)
        config = self.preference.notification_preference_config
        types = config['discussion']['notification_types']
        types['new_discussion_post']['email_cadence'] = EmailCadence.DAILY
        types['new_discussion_post']['email'] = pref_value
        self.preference.save()
        with override_waffle_flag(ENABLE_EMAIL_NOTIFICATIONS, True):
            send_digest_email_to_user(self.user, EmailCadence.DAILY, start_date, end_date)
        assert mock_func.called is pref_value

    @patch('edx_ace.ace.send')
    def test_email_not_send_if_different_digest_preference(self, mock_func):
        """
        Tests email is not send if digest notification preference doesnot match
        """
        start_date, end_date = get_start_end_date(EmailCadence.DAILY)
        config = self.preference.notification_preference_config
        types = config['discussion']['notification_types']
        types['new_discussion_post']['email_cadence'] = EmailCadence.WEEKLY
        self.preference.save()
        with override_waffle_flag(ENABLE_EMAIL_NOTIFICATIONS, True):
            send_digest_email_to_user(self.user, EmailCadence.DAILY, start_date, end_date)
        assert not mock_func.called


class TestImmediateEmail(ModuleStoreTestCase):
    """
    Tests immediate email
    """

    def setUp(self):
        """
        Setup
        """
        super().setUp()
        self.user = UserFactory()
        self.course = CourseFactory.create(display_name='test course', run="Testing_course")

    @patch('edx_ace.ace.send')
    def test_email_sent_when_cadence_is_immediate(self, mock_func):
        """
        Tests email is sent when cadence is immediate
        """
        preference = CourseNotificationPreference.objects.create(user=self.user, course_id=self.course.id)
        app_prefs = preference.notification_preference_config['discussion']['notification_types']
        app_prefs['new_discussion_post']['email'] = True
        app_prefs['new_discussion_post']['email_cadence'] = EmailCadence.IMMEDIATELY
        preference.save()
        context = {
            'username': 'User',
            'post_title': 'title'
        }
        with override_waffle_flag(ENABLE_NOTIFICATIONS, True):
            with override_waffle_flag(ENABLE_EMAIL_NOTIFICATIONS, True):
                send_notifications([self.user.id], str(self.course.id), 'discussion',
                                   'new_discussion_post', context, 'http://test.url')
        assert mock_func.call_count == 1

    @patch('edx_ace.ace.send')
    def test_email_not_sent_when_cadence_is_not_immediate(self, mock_func):
        """
        Tests email is not sent when cadence is not immediate
        """
        CourseNotificationPreference.objects.create(user=self.user, course_id=self.course.id)
        context = {
            'replier_name': 'User',
            'post_title': 'title'
        }
        with override_waffle_flag(ENABLE_NOTIFICATIONS, True):
            with override_waffle_flag(ENABLE_EMAIL_NOTIFICATIONS, True):
                send_notifications([self.user.id], str(self.course.id), 'discussion',
                                   'new_response', context, 'http://test.url')
        assert mock_func.call_count == 0
