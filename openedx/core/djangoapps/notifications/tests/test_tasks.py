"""
Tests for notifications tasks.
"""

import datetime
from unittest.mock import patch

import ddt
from django.conf import settings
from django.core.exceptions import ValidationError
from edx_toggles.toggles.testutils import override_waffle_flag

from common.djangoapps.student.models import CourseEnrollment
from common.djangoapps.student.tests.factories import UserFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

from ..config.waffle import ENABLE_NOTIFICATIONS, ENABLE_NOTIFICATION_GROUPING
from ..models import CourseNotificationPreference, Notification
from ..tasks import (
    create_notification_pref_if_not_exists,
    delete_notifications,
    send_notifications,
    update_user_preference
)
from .utils import create_notification


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
        with patch('openedx.core.djangoapps.notifications.tasks.notification_generated_event') as event_mock:
            send_notifications([self.user.id], str(self.course_1.id), app_name, notification_type, context, content_url)
            assert event_mock.called
            assert event_mock.call_args[0][0] == [self.user.id]
            assert event_mock.call_args[0][1] == app_name
            assert event_mock.call_args[0][2] == notification_type

        # Assert that `Notification` objects have been created for the users.
        notification = Notification.objects.filter(user_id=self.user.id).first()
        # Assert that the `Notification` objects have the correct properties.
        self.assertEqual(notification.user_id, self.user.id)
        self.assertEqual(notification.app_name, app_name)
        self.assertEqual(notification.notification_type, notification_type)
        self.assertEqual(notification.content_context, context)
        self.assertEqual(notification.content_url, content_url)
        self.assertEqual(notification.course_id, self.course_1.id)

    @ddt.data(True, False)
    def test_enable_notification_flag(self, flag_value):
        """
        Tests if notification is sent when flag is enabled and notification
        is not sent when flag is disabled
        """
        app_name = "discussion"
        notification_type = "new_response"
        context = {
            'post_title': 'Post title',
            'replier_name': 'replier name',
        }
        content_url = 'https://example.com/'
        with override_waffle_flag(ENABLE_NOTIFICATIONS, active=flag_value):
            send_notifications([self.user.id], str(self.course_1.id), app_name, notification_type, context, content_url)
        created_notifications_count = 1 if flag_value else 0
        self.assertEqual(len(Notification.objects.all()), created_notifications_count)

    @override_waffle_flag(ENABLE_NOTIFICATIONS, active=True)
    def test_notification_not_send_with_preference_disabled(self):
        """
        Tests notification not send if preference is disabled
        """
        app_name = "discussion"
        notification_type = "new_response"
        context = {
            'post_title': 'Post title',
            'replier_name': 'replier name',
        }
        content_url = 'https://example.com/'

        preference = CourseNotificationPreference.get_user_course_preference(self.user.id, self.course_1.id)
        app_prefs = preference.notification_preference_config[app_name]
        app_prefs['notification_types']['core']['web'] = False
        app_prefs['notification_types']['core']['email'] = False
        app_prefs['notification_types']['core']['push'] = False
        preference.save()

        send_notifications([self.user.id], str(self.course_1.id), app_name, notification_type, context, content_url)
        self.assertEqual(len(Notification.objects.all()), 0)

    @override_waffle_flag(ENABLE_NOTIFICATION_GROUPING, True)
    @override_waffle_flag(ENABLE_NOTIFICATIONS, active=True)
    def test_send_notification_with_grouping_enabled(self):
        """
        Test send_notifications with grouping enabled.
        """
        with patch('openedx.core.djangoapps.notifications.tasks.group_user_notifications') as user_notifications_mock:
            context = {
                'post_title': 'Post title',
                'author_name': 'author name',
                'replier_name': 'replier name',
                'group_by_id': 'group_by_id',
            }
            content_url = 'https://example.com/'
            send_notifications(
                [self.user.id],
                str(self.course_1.id),
                'discussion',
                'new_comment',
                {**context},
                content_url
            )
            send_notifications(
                [self.user.id],
                str(self.course_1.id),
                'discussion',
                'new_comment',
                {**context},
                content_url
            )
            self.assertEqual(Notification.objects.filter(user_id=self.user.id).count(), 1)
            user_notifications_mock.assert_called_once()

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

    @override_waffle_flag(ENABLE_NOTIFICATIONS, active=True)
    def test_notification_not_created_when_context_is_incomplete(self):
        try:
            send_notifications([self.user.id], str(self.course_1.id), "discussion", "new_comment", {}, "")
        except Exception as exc:  # pylint: disable=broad-except
            assert isinstance(exc, ValidationError)


@ddt.ddt
class SendBatchNotificationsTest(ModuleStoreTestCase):
    """
    Test that notification and notification preferences are created in batches
    """

    def setUp(self):
        """
        Setups test case
        """
        super().setUp()
        self.course = CourseFactory.create(
            org='test_org',
            number='test_course',
            run='test_run'
        )

    def _create_users(self, num_of_users):
        """
        Create users and enroll them in course
        """
        users = [
            UserFactory.create(username=f'user{i}', email=f'user{i}@example.com')
            for i in range(num_of_users)
        ]
        for user in users:
            CourseEnrollment.enroll(user=user, course_key=self.course.id)
        return users

    @override_waffle_flag(ENABLE_NOTIFICATIONS, active=True)
    @ddt.data(
        (settings.NOTIFICATION_CREATION_BATCH_SIZE, 10, 4),
        (settings.NOTIFICATION_CREATION_BATCH_SIZE + 10, 12, 7),
        (settings.NOTIFICATION_CREATION_BATCH_SIZE - 10, 10, 4),
    )
    @ddt.unpack
    def test_notification_is_send_in_batch(self, creation_size, prefs_query_count, notifications_query_count):
        """
        Tests notifications and notification preferences are created in batches
        """
        notification_app = "discussion"
        notification_type = "new_discussion_post"
        users = self._create_users(creation_size)
        user_ids = [user.id for user in users]
        context = {
            "post_title": "Test Post",
            "username": "Test Author"
        }

        # Creating preferences and asserting query count
        with self.assertNumQueries(prefs_query_count):
            send_notifications(user_ids, str(self.course.id), notification_app, notification_type,
                               context, "http://test.url")

        # Updating preferences for notification creation
        preferences = CourseNotificationPreference.objects.filter(
            user_id__in=user_ids,
            course_id=self.course.id
        )
        for preference in preferences:
            discussion_config = preference.notification_preference_config['discussion']
            discussion_config['notification_types'][notification_type]['web'] = True
            preference.save()

        # Creating notifications and asserting query count
        with self.assertNumQueries(notifications_query_count):
            send_notifications(user_ids, str(self.course.id), notification_app, notification_type,
                               context, "http://test.url")

    def test_preference_not_created_for_default_off_preference(self):
        """
        Tests if new preferences are NOT created when default preference for
        notification type is False
        """
        notification_app = "discussion"
        notification_type = "new_discussion_post"
        users = self._create_users(20)
        user_ids = [user.id for user in users]
        context = {
            "post_title": "Test Post",
            "username": "Test Author"
        }
        with override_waffle_flag(ENABLE_NOTIFICATIONS, active=True):
            with self.assertNumQueries(10):
                send_notifications(user_ids, str(self.course.id), notification_app, notification_type,
                                   context, "http://test.url")

    def test_preference_created_for_default_on_preference(self):
        """
        Tests if new preferences are created when default preference for
        notification type is True
        """
        notification_app = "discussion"
        notification_type = "new_comment"
        users = self._create_users(20)
        user_ids = [user.id for user in users]
        context = {
            "post_title": "Test Post",
            "author_name": "Test Author",
            "replier_name": "Replier Name"
        }
        with override_waffle_flag(ENABLE_NOTIFICATIONS, active=True):
            with self.assertNumQueries(12):
                send_notifications(user_ids, str(self.course.id), notification_app, notification_type,
                                   context, "http://test.url")

    def _update_user_preference(self, user_id, pref_exists):
        """
        Removes or creates user preference based on pref_exists
        """
        if pref_exists:
            CourseNotificationPreference.objects.get_or_create(user_id=user_id, course_id=self.course.id)
        else:
            CourseNotificationPreference.objects.filter(user_id=user_id, course_id=self.course.id).delete()

    @override_waffle_flag(ENABLE_NOTIFICATIONS, active=True)
    @ddt.data(
        ("new_response", True, True, 2),
        ("new_response", False, False, 2),
        ("new_response", True, False, 2),
        ("new_discussion_post", True, True, 0),
        ("new_discussion_post", False, False, 0),
        ("new_discussion_post", True, False, 0),
    )
    @ddt.unpack
    def test_preference_enabled_in_batch_audience(self, notification_type,
                                                  user_1_pref_exists, user_2_pref_exists, generated_count):
        """
        Tests if users with preference enabled in batch gets notification
        """
        users = self._create_users(2)
        user_ids = [user.id for user in users]
        self._update_user_preference(user_ids[0], user_1_pref_exists)
        self._update_user_preference(user_ids[1], user_2_pref_exists)

        app_name = "discussion"
        context = {
            'post_title': 'Post title',
            'username': 'Username',
            'replier_name': 'replier name',
            'author_name': 'Authorname'
        }
        content_url = 'https://example.com/'
        send_notifications(user_ids, str(self.course.id), app_name, notification_type, context, content_url)
        self.assertEqual(len(Notification.objects.all()), generated_count)


class TestDeleteNotificationTask(ModuleStoreTestCase):
    """
    Tests delete_notification_function
    """

    def setUp(self):
        """
        Setup
        """
        super().setUp()
        self.user = UserFactory()
        self.course_1 = CourseFactory.create(org='org', number='num', run='run_01')
        self.course_2 = CourseFactory.create(org='org', number='num', run='run_02')
        Notification.objects.all().delete()

    def test_app_name_param(self):
        """
        Tests if app_name parameter works as expected
        """
        assert not Notification.objects.all()
        create_notification(self.user, self.course_1.id, app_name='discussion', notification_type='new_comment')
        create_notification(self.user, self.course_1.id, app_name='updates', notification_type='course_updates')
        delete_notifications({'app_name': 'discussion'})
        assert not Notification.objects.filter(app_name='discussion')
        assert Notification.objects.filter(app_name='updates')

    def test_notification_type_param(self):
        """
        Tests if notification_type parameter works as expected
        """
        assert not Notification.objects.all()
        create_notification(self.user, self.course_1.id, app_name='discussion', notification_type='new_comment')
        create_notification(self.user, self.course_1.id, app_name='discussion', notification_type='new_response')
        delete_notifications({'notification_type': 'new_comment'})
        assert not Notification.objects.filter(notification_type='new_comment')
        assert Notification.objects.filter(notification_type='new_response')

    def test_created_param(self):
        """
        Tests if created parameter works as expected
        """
        assert not Notification.objects.all()
        create_notification(self.user, self.course_1.id, created=datetime.datetime(2024, 2, 10))
        create_notification(self.user, self.course_2.id, created=datetime.datetime(2024, 3, 12, 5))
        kwargs = {
            'created': {
                'created__gte': datetime.datetime(2024, 3, 12, 0, 0, 0),
                'created__lte': datetime.datetime(2024, 3, 12, 23, 59, 59),
            }
        }
        delete_notifications(kwargs)
        self.assertEqual(Notification.objects.all().count(), 1)

    def test_course_id_param(self):
        """
        Tests if course_id parameter works as expected
        """
        assert not Notification.objects.all()
        create_notification(self.user, self.course_1.id)
        create_notification(self.user, self.course_2.id)
        delete_notifications({'course_id': self.course_1.id})
        assert not Notification.objects.filter(course_id=self.course_1.id)
        assert Notification.objects.filter(course_id=self.course_2.id)


@ddt.ddt
class NotificationCreationOnChannelsTests(ModuleStoreTestCase):
    """
    Tests for notification creation and channels value.
    """

    def setUp(self):
        """
        Create a course and users for tests.
        """

        super().setUp()
        self.user = UserFactory()
        self.course = CourseFactory.create(
            org='testorg',
            number='testcourse',
            run='testrun'
        )

        self.preference = CourseNotificationPreference.objects.create(
            user_id=self.user.id,
            course_id=self.course.id,
            config_version=0,
        )

    @override_waffle_flag(ENABLE_NOTIFICATIONS, active=True)
    @ddt.data(
        (False, False, 0),
        (False, True, 1),
        (True, False, 1),
        (True, True, 1),
    )
    @ddt.unpack
    def test_notification_is_created_when_any_channel_is_enabled(self, web_value, email_value, generated_count):
        """
        Tests if notification is created if any preference is enabled
        """
        app_name = 'discussion'
        notification_type = 'new_discussion_post'
        app_prefs = self.preference.notification_preference_config[app_name]
        app_prefs['notification_types'][notification_type]['web'] = web_value
        app_prefs['notification_types'][notification_type]['email'] = email_value
        kwargs = {
            'user_ids': [self.user.id],
            'course_key': str(self.course.id),
            'app_name': app_name,
            'notification_type': notification_type,
            'content_url': 'https://example.com/',
            'context': {
                'post_title': 'Post title',
                'username': 'user name',
            },
        }
        self.preference.save()
        with patch('openedx.core.djangoapps.notifications.tasks.notification_generated_event') as event_mock:
            send_notifications(**kwargs)
            notifications = Notification.objects.all()
            assert len(notifications) == generated_count
            if notifications:
                notification = Notification.objects.all()[0]
                assert notification.web == web_value
                assert notification.email == email_value
