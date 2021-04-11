"""
Unit tests for user messages.
"""


import ddt
from django.contrib.messages.middleware import MessageMiddleware
from django.test import RequestFactory, TestCase

from common.test.utils import normalize_repr
from openedx.core.djangolib.markup import HTML, Text
from common.djangoapps.student.tests.factories import UserFactory

from ..user_messages import PageLevelMessages, UserMessageType

TEST_MESSAGE = 'Test message'


@ddt.ddt
class UserMessagesTestCase(TestCase):
    """
    Unit tests for page level user messages.
    """
    def setUp(self):
        super(UserMessagesTestCase, self).setUp()
        self.student = UserFactory.create()
        self.request = RequestFactory().request()
        self.request.session = {}
        self.request.user = self.student
        MessageMiddleware().process_request(self.request)

    @ddt.data(
        ('Rock & Roll', '<div class="message-content">Rock &amp; Roll</div>'),
        (Text('Rock & Roll'), '<div class="message-content">Rock &amp; Roll</div>'),
        (HTML('<p>Hello, world!</p>'), '<div class="message-content"><p>Hello, world!</p></div>')
    )
    @ddt.unpack
    def test_message_escaping(self, message, expected_message_html):
        """
        Verifies that a user message is escaped correctly.
        """
        PageLevelMessages.register_user_message(self.request, UserMessageType.INFO, message)
        messages = list(PageLevelMessages.user_messages(self.request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].message_html, expected_message_html)

    @ddt.data(
        (UserMessageType.ERROR, 'alert-danger', 'fa fa-warning'),
        (UserMessageType.INFO, 'alert-info', 'fa fa-bullhorn'),
        (UserMessageType.SUCCESS, 'alert-success', 'fa fa-check-circle'),
        (UserMessageType.WARNING, 'alert-warning', 'fa fa-warning'),
    )
    @ddt.unpack
    def test_message_icon(self, message_type, expected_css_class, expected_icon_class):
        """
        Verifies that a user message returns the correct CSS and icon classes.
        """
        PageLevelMessages.register_user_message(self.request, message_type, TEST_MESSAGE)
        messages = list(PageLevelMessages.user_messages(self.request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].css_class, expected_css_class)
        self.assertEqual(messages[0].icon_class, expected_icon_class)

    @ddt.data(
        (normalize_repr(PageLevelMessages.register_error_message), UserMessageType.ERROR),
        (normalize_repr(PageLevelMessages.register_info_message), UserMessageType.INFO),
        (normalize_repr(PageLevelMessages.register_success_message), UserMessageType.SUCCESS),
        (normalize_repr(PageLevelMessages.register_warning_message), UserMessageType.WARNING),
    )
    @ddt.unpack
    def test_message_type(self, register_message_function, expected_message_type):
        """
        Verifies that each user message function returns the correct type.
        """
        register_message_function(self.request, TEST_MESSAGE)
        messages = list(PageLevelMessages.user_messages(self.request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].type, expected_message_type)
