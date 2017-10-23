from django.test import TestCase
import mock

from django_comment_common import signals
from lms.djangoapps.discussion.config.waffle import waffle, FORUM_RESPONSE_NOTIFICATIONS


class SendMessageHandlerTestCase(TestCase):
    @mock.patch('lms.djangoapps.discussion.signals.handlers.send_message')
    def test_comment_created_signal_sends_message(self, mock_send_message):
        with waffle().override(FORUM_RESPONSE_NOTIFICATIONS):
            sender = mock.Mock()
            user = mock.Mock()
            post = mock.Mock()

            signals.comment_created.send(sender=sender, user=user, post=post)

            mock_send_message.assert_called_once_with(post)

    @mock.patch('lms.djangoapps.discussion.signals.handlers.send_message')
    def test_comment_created_signal_message_not_sent_without_waffle_switch(self, mock_send_message):
        with waffle().override(FORUM_RESPONSE_NOTIFICATIONS, active=False):
            sender = mock.Mock()
            user = mock.Mock()
            post = mock.Mock()

            signals.comment_created.send(sender=sender, user=user, post=post)

            self.assertFalse(mock_send_message.called)
