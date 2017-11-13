from django.test import TestCase
import mock

from opaque_keys.edx.keys import CourseKey

from django_comment_common import signals
from lms.djangoapps.discussion.config.waffle import waffle, FORUM_RESPONSE_NOTIFICATIONS, SEND_NOTIFICATIONS_FOR_COURSE
from lms.djangoapps.discussion.signals.handlers import ENABLE_FORUM_NOTIFICATIONS_FOR_SITE_KEY
from openedx.core.djangoapps.site_configuration.tests.factories import SiteFactory, SiteConfigurationFactory
from openedx.core.djangoapps.waffle_utils.testutils import override_waffle_flag


class SendMessageHandlerTestCase(TestCase):
    def setUp(self):
        self.sender = mock.Mock()
        self.user = mock.Mock()
        self.post = mock.Mock()
        self.post.thread.course_id = 'course-v1:edX+DemoX+Demo_Course'

        self.site = SiteFactory.create()

    @mock.patch('lms.djangoapps.discussion.signals.handlers.get_current_site')
    @mock.patch('lms.djangoapps.discussion.signals.handlers.send_message')
    @override_waffle_flag(SEND_NOTIFICATIONS_FOR_COURSE, True)
    def test_comment_created_signal_sends_message(self, mock_send_message, mock_get_current_site):
        site_config = SiteConfigurationFactory.create(site=self.site)
        site_config.values[ENABLE_FORUM_NOTIFICATIONS_FOR_SITE_KEY] = True
        site_config.save()
        mock_get_current_site.return_value = self.site
        with waffle().override(FORUM_RESPONSE_NOTIFICATIONS):
            signals.comment_created.send(sender=self.sender, user=self.user, post=self.post)

            mock_send_message.assert_called_once_with(self.post, mock_get_current_site.return_value)

    @mock.patch('lms.djangoapps.discussion.signals.handlers.send_message')
    @override_waffle_flag(SEND_NOTIFICATIONS_FOR_COURSE, True)
    def test_comment_created_signal_message_not_sent_without_waffle_switch(self, mock_send_message):
        with waffle().override(FORUM_RESPONSE_NOTIFICATIONS, active=False):
            signals.comment_created.send(sender=self.sender, user=self.user, post=self.post)

            self.assertFalse(mock_send_message.called)

    @mock.patch('lms.djangoapps.discussion.signals.handlers.send_message')
    def test_comment_created_signal_message_not_sent_without_course_waffle_flag(self, mock_send_message):
        with waffle().override(FORUM_RESPONSE_NOTIFICATIONS, active=True):
            signals.comment_created.send(sender=self.sender, user=self.user, post=self.post)

            self.assertFalse(mock_send_message.called)

    @mock.patch('lms.djangoapps.discussion.signals.handlers.get_current_site', return_value=None)
    @mock.patch('lms.djangoapps.discussion.signals.handlers.send_message')
    @override_waffle_flag(SEND_NOTIFICATIONS_FOR_COURSE, True)
    def test_comment_created_signal_message_not_sent_without_site(self, mock_send_message, mock_get_current_site):
        with waffle().override(FORUM_RESPONSE_NOTIFICATIONS, active=True):
            signals.comment_created.send(sender=self.sender, user=self.user, post=self.post)

            self.assertFalse(mock_send_message.called)

    @mock.patch('lms.djangoapps.discussion.signals.handlers.get_current_site')
    @mock.patch('lms.djangoapps.discussion.signals.handlers.send_message')
    @override_waffle_flag(SEND_NOTIFICATIONS_FOR_COURSE, True)
    def test_comment_created_signal_msg_not_sent_without_site_config(self, mock_send_message, mock_get_current_site):
        mock_get_current_site.return_value = self.site
        with waffle().override(FORUM_RESPONSE_NOTIFICATIONS):
            signals.comment_created.send(sender=self.sender, user=self.user, post=self.post)

            self.assertFalse(mock_send_message.called)

    @mock.patch('lms.djangoapps.discussion.signals.handlers.get_current_site')
    @mock.patch('lms.djangoapps.discussion.signals.handlers.send_message')
    @override_waffle_flag(SEND_NOTIFICATIONS_FOR_COURSE, True)
    def test_comment_created_signal_msg_not_sent_with_site_config_disabled(
            self, mock_send_message, mock_get_current_site
    ):
        site_config = SiteConfigurationFactory.create(site=self.site)
        site_config.values[ENABLE_FORUM_NOTIFICATIONS_FOR_SITE_KEY] = False
        site_config.save()
        mock_get_current_site.return_value = self.site
        with waffle().override(FORUM_RESPONSE_NOTIFICATIONS):
            signals.comment_created.send(sender=self.sender, user=self.user, post=self.post)

            self.assertFalse(mock_send_message.called)
