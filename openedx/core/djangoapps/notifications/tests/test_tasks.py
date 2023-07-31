"""
Tests for notifications tasks.
"""

from unittest.mock import patch

import ddt
from edx_toggles.toggles.testutils import override_waffle_flag

from common.djangoapps.student.tests.factories import UserFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

from ..config.waffle import ENABLE_NOTIFICATIONS
from ..models import CourseNotificationPreference, Notification
from ..tasks import create_notification_pref_if_not_exists, send_notifications, update_user_preference


@patch('openedx.core.djangoapps.notifications.models.COURSE_NOTIFICATION_CONFIG_VERSION', 1)
class TestNotificationsTasks(ModuleStoreTestCase):
    """
    Tests for notifications tasks.
    """

    def setUp(self):
        """
        Create a course and users for the course.
        """

        super().setUp()
        self.user = UserFactory()
        self.user_1 = UserFactory()
        self.user_2 = UserFactory()
        self.course_1 = CourseFactory.create(
            org='testorg',
            number='testcourse',
            run='testrun'
        )
        self.course_2 = CourseFactory.create(
            org='testorg',
            number='testcourse_2',
            run='testrun'
        )
        self.preference_v1 = CourseNotificationPreference.objects.create(
            user_id=self.user.id,
            course_id=self.course_1.id,
            config_version=0,
        )
        self.preference_v2 = CourseNotificationPreference.objects.create(
            user_id=self.user.id,
            course_id=self.course_2.id,
            config_version=1,
        )

    def test_update_user_preference(self):
        """
        Test whether update_user_preference updates the preference with the latest config version.
        """
        # Test whether update_user_preference updates the preference with a different config version
        updated_preference = update_user_preference(self.preference_v1, self.user, self.course_1.id)
        self.assertEqual(updated_preference.config_version, 1)

        # Test whether update_user_preference does not update the preference if the config version is the same
        updated_preference = update_user_preference(self.preference_v2, self.user, self.course_2.id)
        self.assertEqual(updated_preference.config_version, 1)

    @override_waffle_flag(ENABLE_NOTIFICATIONS, active=True)
    def test_create_notification_pref_if_not_exists(self):
        """
        Test whether create_notification_pref_if_not_exists creates a new preference if it doesn't exist.
        """
        # Test whether create_notification_pref_if_not_exists creates a new preference if it doesn't exist
        user_ids = [self.user.id, self.user_1.id, self.user_2.id]
        preferences = [self.preference_v2]
        updated_preferences = create_notification_pref_if_not_exists(user_ids, preferences, self.course_2.id)
        self.assertEqual(len(updated_preferences), 3)  # Should have created two new preferences

        # Test whether create_notification_pref_if_not_exists doesn't create a new preference if it already exists
        updated_preferences = create_notification_pref_if_not_exists(user_ids, preferences, self.course_2.id)
        self.assertEqual(len(updated_preferences), 3)  # No new preferences should be created this time


@ddt.ddt
class SendNotificationsTest(ModuleStoreTestCase):
    """
    Tests for send_notifications.
    """

    def setUp(self):
        """
        Create a course and users for the course.
        """

        super().setUp()
        self.user = UserFactory()
        self.course_1 = CourseFactory.create(
            org='testorg',
            number='testcourse',
            run='testrun'
        )

        self.preference_v1 = CourseNotificationPreference.objects.create(
            user_id=self.user.id,
            course_id=self.course_1.id,
            config_version=0,
        )

    @override_waffle_flag(ENABLE_NOTIFICATIONS, active=True)
    @ddt.data(
        ('discussion', 'new_comment_on_response'),  # core notification
        ('discussion', 'new_response'),  # non core notification
    )
    @ddt.unpack
    def test_send_notifications(self, app_name, notification_type):
        """
        Test whether send_notifications creates a new notification.
        """
        context = {
            'post_title': 'Post title',
            'replier_name': 'replier name',
        }
        content_url = 'https://example.com/'

        # Call the `send_notifications` function.
        send_notifications([self.user.id], str(self.course_1.id), app_name, notification_type, context, content_url)

        # Assert that `Notification` objects have been created for the users.
        notification = Notification.objects.filter(user_id=self.user.id).first()
        # Assert that the `Notification` objects have the correct properties.
        self.assertEqual(notification.user_id, self.user.id)
        self.assertEqual(notification.app_name, app_name)
        self.assertEqual(notification.notification_type, notification_type)
        self.assertEqual(notification.content_context, context)
        self.assertEqual(notification.content_url, content_url)
        self.assertEqual(notification.course_id, self.course_1.id)

    @override_waffle_flag(ENABLE_NOTIFICATIONS, active=True)
    @ddt.data(
        ('discussion', 'new_comment_on_response'),  # core notification
        ('discussion', 'new_response'),  # non core notification
    )
    @ddt.unpack
    def test_send_with_app_disabled_notifications(self, app_name, notification_type):
        """
        Test send_notifications does not create a new notification if the app is disabled.
        """
        self.preference_v1.notification_preference_config['discussion']['enabled'] = False
        self.preference_v1.save()

        context = {
            'post_title': 'Post title',
            'replier_name': 'replier name',
        }
        content_url = 'https://example.com/'

        # Call the `send_notifications` function.
        send_notifications([self.user.id], str(self.course_1.id), app_name, notification_type, context, content_url)

        # Assert that `Notification` objects are not created for the users.
        notification = Notification.objects.filter(user_id=self.user.id).first()
        self.assertIsNone(notification)
