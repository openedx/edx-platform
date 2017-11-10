"""
Unit tests for the digests.py file
"""

import datetime
import pytz
from django.test import TestCase
from freezegun import freeze_time

from edx_notifications.namespaces import (
    NotificationNamespaceResolver,
    DefaultNotificationNamespaceResolver,
    register_namespace_resolver
)
from edx_notifications.data import (
    NotificationMessage,
    NotificationType,
)
from edx_notifications.scopes import (
    NotificationUserScopeResolver
)

from edx_notifications.digests import (
    send_notifications_digest,
    create_default_notification_preferences,
    register_digest_timers
)
from edx_notifications.stores.store import notification_store
from edx_notifications.lib.publisher import (
    publish_notification_to_user,
)
from edx_notifications.lib.consumer import (
    set_user_notification_preference,
    mark_notification_read,
)
from edx_notifications import const


class TestUserResolver(NotificationUserScopeResolver):
    """
    UserResolver for test purposes
    """
    def resolve(self, scope_name, scope_context, instance_context):
        """
        Implementation of interface method
        """
        return [
            {
                'id': 1001,
                'email': 'dummy@dummy.com',
                'first_name': 'Joe',
                'last_name': 'Smith'
            }
        ]


class TestNamespaceResolver(NotificationNamespaceResolver):
    """
    Namespace resolver for demo purposes
    """
    def resolve(self, namespace, instance_context):
        """
        Implementation of interface method
        """
        return {
            'namespace': namespace,
            'display_name': 'A Test Namespace',
            'features': {
                'digests': True,
            },
            'default_user_resolver': TestUserResolver()
        }


class TestNamespaceResolverNoUsers(NotificationNamespaceResolver):
    """
    Namespace resolver for demo purposes
    """
    def resolve(self, namespace, instance_context):
        """
        Implementation of interface method
        """
        return {
            'namespace': namespace,
            'display_name': 'A Test Namespace',
            'features': {
                'digests': True,
            },
            'default_user_resolver': None
        }


class DigestTestCases(TestCase):
    """
    Test cases for digests.py
    """

    def setUp(self):
        """
        Initialize tests, by creating users and populating some
        unread notifications
        """
        create_default_notification_preferences()
        self.store = notification_store()
        self.test_user_id = 1001
        self.from_timestamp = datetime.datetime.now(pytz.UTC) - datetime.timedelta(days=1)
        self.weekly_from_timestamp = datetime.datetime.now(pytz.UTC) - datetime.timedelta(days=7)
        self.to_timestamp = datetime.datetime.now(pytz.UTC)

        self.msg_type = self.store.save_notification_type(
            NotificationType(
                name='foo.bar',
                renderer='edx_notifications.renderers.basic.BasicSubjectBodyRenderer',
            )
        )

        self.msg_type_no_renderer = self.store.save_notification_type(
            NotificationType(
                name='foo.baz',
                renderer='foo',
            )
        )

        # create two notifications
        with freeze_time(self.to_timestamp):
            msg = self.store.save_notification_message(
                NotificationMessage(
                    msg_type=self.msg_type,
                    namespace='foo',
                    payload={'subject': 'foo', 'body': 'bar'},
                )
            )
            self.notification1 = publish_notification_to_user(self.test_user_id, msg)

        with freeze_time(self.to_timestamp):
            msg = self.store.save_notification_message(
                NotificationMessage(
                    msg_type=self.msg_type_no_renderer,
                    namespace='bar',
                    payload={'subject': 'foo', 'body': 'bar'},
                )
            )
            self.notification2 = publish_notification_to_user(self.test_user_id, msg)

    def test_no_namespace_resolver(self):
        """
        Assert no digests were sent if we don't have
        a namespace resolver
        """

        register_namespace_resolver(None)

        self.assertEqual(
            send_notifications_digest(
                self.from_timestamp,
                self.to_timestamp,
                const.NOTIFICATION_DAILY_DIGEST_PREFERENCE_NAME,
                'subject',
                'foo@bar.com'
            ),
            0
        )

    def test_default_namespace_resolver(self):
        """
        Assert no digests were sent if we just use the DefaultNotificationNamespaceResolver
        """

        register_namespace_resolver(DefaultNotificationNamespaceResolver())

        self.assertEqual(
            send_notifications_digest(
                self.from_timestamp,
                self.to_timestamp,
                const.NOTIFICATION_DAILY_DIGEST_PREFERENCE_NAME,
                'subject',
                'foo@bar.com'
            ),
            0
        )

    def test_no_user_resolver(self):
        """
        Asserts no digests were sent if we don't have a user resolver as part of the namespace
        """

        register_namespace_resolver(TestNamespaceResolverNoUsers())

        self.assertEqual(
            send_notifications_digest(
                self.from_timestamp,
                self.to_timestamp,
                const.NOTIFICATION_DAILY_DIGEST_PREFERENCE_NAME,
                'subject',
                'foo@bar.com'
            ),
            0
        )

    def test_user_preference_undefined(self):
        """
        Make sure we don't send a digest if the digest preference name is not found
        """
        register_namespace_resolver(TestNamespaceResolver())

        self.assertEqual(
            send_notifications_digest(
                self.from_timestamp,
                self.to_timestamp,
                const.NOTIFICATION_DAILY_DIGEST_PREFERENCE_NAME,
                'subject',
                'foo@bar.com'
            ),
            0
        )

    def test_user_preference_false(self):
        """
        Make sure we don't send a digest to a user that does not want digests
        """
        register_namespace_resolver(TestNamespaceResolver())

        set_user_notification_preference(self.test_user_id, const.NOTIFICATION_DAILY_DIGEST_PREFERENCE_NAME, 'false')

        self.assertEqual(
            send_notifications_digest(
                self.from_timestamp,
                self.to_timestamp,
                const.NOTIFICATION_DAILY_DIGEST_PREFERENCE_NAME,
                'subject',
                'foo@bar.com'
            ),
            0
        )

    def test_happy_path(self):
        """
        If all is good and enabled, in this test case, we should get two digests sent, one for each namespace
        """

        register_namespace_resolver(TestNamespaceResolver())

        set_user_notification_preference(self.test_user_id, const.NOTIFICATION_DAILY_DIGEST_PREFERENCE_NAME, 'true')

        self.assertEqual(
            send_notifications_digest(
                self.from_timestamp,
                self.to_timestamp,
                const.NOTIFICATION_DAILY_DIGEST_PREFERENCE_NAME,
                'subject',
                'foo@bar.com'
            ),
            2
        )

    def test_read_notifications(self):
        """
        Test to make sure that we can generate a notification for read notifications as well
        """

        register_namespace_resolver(TestNamespaceResolver())
        set_user_notification_preference(self.test_user_id, const.NOTIFICATION_DAILY_DIGEST_PREFERENCE_NAME, 'true')

        # mark the two test notifications as read
        mark_notification_read(self.test_user_id, self.notification1.id)
        mark_notification_read(self.test_user_id, self.notification2.id)

        # make sure read notifications do not generate digests when we only want unread notifications
        self.assertEqual(
            send_notifications_digest(
                self.from_timestamp,
                self.to_timestamp,
                const.NOTIFICATION_DAILY_DIGEST_PREFERENCE_NAME,
                'subject',
                'foo@bar.com',
                unread_only=True
            ),
            0
        )

        # make sure read notifications do generate digests when we want all notifications
        self.assertEqual(
            send_notifications_digest(
                self.from_timestamp,
                self.to_timestamp,
                const.NOTIFICATION_DAILY_DIGEST_PREFERENCE_NAME,
                'subject',
                'foo@bar.com',
                unread_only=False
            ),
            2
        )

    def test_happy_path_without_styling(self):
        """
        If all is good and enabled, but the css and image are not supplied,
        in this test case, we should still get two digests sent, one for each namespace,
        but the resulting emails would not have any css or images.
        """

        register_namespace_resolver(TestNamespaceResolver())

        const.NOTIFICATION_DIGEST_EMAIL_CSS = 'bad.css.file'
        const.NOTIFICATION_BRANDED_DEFAULT_LOGO = 'bad.image.file'

        set_user_notification_preference(self.test_user_id, const.NOTIFICATION_DAILY_DIGEST_PREFERENCE_NAME, 'true')

        self.assertEqual(
            send_notifications_digest(
                self.from_timestamp,
                self.to_timestamp,
                const.NOTIFICATION_DAILY_DIGEST_PREFERENCE_NAME,
                'subject',
                'foo@bar.com'
            ),
            2
        )

    def test_to_not_send_digest(self):
        """
        If there are no unread notifications for the user for given timestamps
        Then don't send digest emails to the user.
        """

        register_namespace_resolver(TestNamespaceResolver())

        set_user_notification_preference(self.test_user_id, const.NOTIFICATION_DAILY_DIGEST_PREFERENCE_NAME, 'true')

        # there will be no unread notifications to send for the digest.
        self.assertEqual(
            send_notifications_digest(
                self.from_timestamp + datetime.timedelta(days=2),
                self.to_timestamp + datetime.timedelta(days=1),
                const.NOTIFICATION_DAILY_DIGEST_PREFERENCE_NAME,
                'subject',
                'foo@bar.com'
            ),
            0
        )

    def test_weekly_preference_false(self):
        """
        If all is good and enabled, in this test case, we should get two digests sent, one for each namespace
        """

        register_namespace_resolver(TestNamespaceResolver())

        set_user_notification_preference(self.test_user_id, const.NOTIFICATION_WEEKLY_DIGEST_PREFERENCE_NAME, 'false')

        self.assertEqual(
            send_notifications_digest(
                self.weekly_from_timestamp,
                self.to_timestamp,
                const.NOTIFICATION_WEEKLY_DIGEST_PREFERENCE_NAME,
                'subject',
                'foo@bar.com'
            ),
            0
        )

    def test_happy_path_weekly(self):
        """
        If all is good and enabled, in this test case, we should get two digests sent, one for each namespace
        """

        register_namespace_resolver(TestNamespaceResolver())

        set_user_notification_preference(self.test_user_id, const.NOTIFICATION_WEEKLY_DIGEST_PREFERENCE_NAME, 'true')

        self.assertEqual(
            send_notifications_digest(
                self.weekly_from_timestamp,
                self.to_timestamp,
                const.NOTIFICATION_WEEKLY_DIGEST_PREFERENCE_NAME,
                'subject',
                'foo@bar.com'
            ),
            2
        )

    def test_default_group_mapping(self):
        """
        Test that adds the default notification type mapping
        """
        msg_type = self.store.save_notification_type(
            NotificationType(
                name='open-edx.lms.discussions.cohorted-thread-added',
                renderer='edx_notifications.openedx.forums.CohortedThreadAddedRenderer',
            )
        )
        # create cohort notification
        with freeze_time(self.to_timestamp):
            msg = self.store.save_notification_message(
                NotificationMessage(
                    msg_type=msg_type,
                    namespace='cohort-thread-added',
                    payload={
                        'subject': 'foo',
                        'body': 'bar',
                        'thread_title': 'A demo posting to the discussion forums'
                    },
                )
            )
            publish_notification_to_user(self.test_user_id, msg)

        register_namespace_resolver(TestNamespaceResolver())

        set_user_notification_preference(self.test_user_id, const.NOTIFICATION_DAILY_DIGEST_PREFERENCE_NAME, 'true')

        self.assertEqual(
            send_notifications_digest(
                self.from_timestamp,
                self.to_timestamp,
                const.NOTIFICATION_DAILY_DIGEST_PREFERENCE_NAME,
                'subject',
                'foo@bar.com'
            ),
            3
        )

    def test_wildcard_group_mapping(self):
        """
        Test that adds the default notification type mapping
        """
        msg_type = self.store.save_notification_type(
            NotificationType(
                name='open-edx.lms.discussions.new-discussion-added',
                renderer='open-edx.lms.discussions.new-discussion-added',
            )
        )
        # create cohort notification
        with freeze_time(self.to_timestamp):
            msg = self.store.save_notification_message(
                NotificationMessage(
                    msg_type=msg_type,
                    namespace='cohort-thread-added',
                    payload={'subject': 'foo', 'body': 'bar'},
                )
            )
            publish_notification_to_user(self.test_user_id, msg)

        register_namespace_resolver(TestNamespaceResolver())

        set_user_notification_preference(self.test_user_id, const.NOTIFICATION_DAILY_DIGEST_PREFERENCE_NAME, 'true')

        self.assertEqual(
            send_notifications_digest(
                self.from_timestamp,
                self.to_timestamp,
                const.NOTIFICATION_DAILY_DIGEST_PREFERENCE_NAME,
                'subject',
                'foo@bar.com'
            ),
            3
        )

    def test_preserve_execute_at(self):
        """
        Make sure the execute at timestamps don't get reset
        across system restarts
        """

        register_digest_timers(None)

        timer = notification_store().get_notification_timer(const.DAILY_DIGEST_TIMER_NAME)

        callback_at = timer.callback_at - datetime.timedelta(days=1)

        timer.callback_at = callback_at
        notification_store().save_notification_timer(timer)

        # restart
        register_digest_timers(None)

        timer = notification_store().get_notification_timer(const.DAILY_DIGEST_TIMER_NAME)

        # make sure the timestamp did not get reset
        self.assertEqual(timer.callback_at, callback_at)
