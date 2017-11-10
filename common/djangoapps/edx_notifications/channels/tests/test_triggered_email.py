"""
Test Triggered Emails
"""
from django.test import TestCase
from edx_notifications import startup
from edx_notifications.data import NotificationMessage
from edx_notifications.lib.publisher import bulk_publish_notification_to_users
from edx_notifications.scopes import register_user_scope_resolver, NotificationUserScopeResolver
from edx_notifications.stores.store import notification_store


class TestUserResolver(NotificationUserScopeResolver):
    """
    UserResolver for test purposes
    """
    def resolve(self, scope_name, scope_context, instance_context):
        """
        Implementation of interface method
        """
        user_id = scope_context.get('user_id')
        return [
            'testemail@sdc.com',
            {
                'user_id': user_id,
                'email': 'dummy@dummy.com',
                'first_name': 'Joe',
                'last_name': 'Smith'
            }
        ]


class TriggeredEmailTestCases(TestCase):
    """
    Unit tests for the TriggeredNotification Notifications Dispatch Channel
    """

    def setUp(self):
        """
        Test setup
        """
        startup.initialize()
        register_user_scope_resolver('user_email_resolver', TestUserResolver())
        self.store = notification_store()

        self.msg_type = self.store.get_notification_type(name='open-edx.lms.discussions.reply-to-thread')

        self.msg = NotificationMessage(
            namespace='test-runner',
            msg_type=self.msg_type,
            payload={
                '_schema_version': 1,
                '_click_link': 'http://localhost',
                'original_poster_id': 1,
                'action_username': 'testuser',
                'thread_title': 'A demo posting to the discussion forums',
            }
        )

    def test_bulk_dispatch_notification_count(self):  # pylint: disable=invalid-name
        """
        Test bulk dispatch notification using email channel count should be valid
        """
        count = bulk_publish_notification_to_users([1001, 1002], self.msg, preferred_channel='triggered-email')
        self.assertEqual(count, 2)
