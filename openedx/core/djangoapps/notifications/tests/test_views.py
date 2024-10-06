"""
Tests for the views in the notifications app.
"""
import json
from datetime import datetime, timedelta
from unittest import mock

import ddt
from django.conf import settings
from django.test.utils import override_settings
from django.urls import reverse
from edx_toggles.toggles.testutils import override_waffle_flag
from openedx_events.learning.data import CourseData, CourseEnrollmentData, UserData, UserPersonalData
from openedx_events.learning.signals import COURSE_ENROLLMENT_CREATED
from pytz import UTC
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from common.djangoapps.student.models import CourseEnrollment
from common.djangoapps.student.roles import CourseStaffRole
from common.djangoapps.student.tests.factories import UserFactory
from lms.djangoapps.discussion.django_comment_client.tests.factories import RoleFactory
from openedx.core.djangoapps.content.course_overviews.tests.factories import CourseOverviewFactory
from openedx.core.djangoapps.django_comment_common.models import (
    FORUM_ROLE_ADMINISTRATOR,
    FORUM_ROLE_COMMUNITY_TA,
    FORUM_ROLE_MODERATOR
)
from openedx.core.djangoapps.notifications.config.waffle import ENABLE_NOTIFICATIONS
from openedx.core.djangoapps.notifications.email_notifications import EmailCadence
from openedx.core.djangoapps.notifications.models import (
    CourseNotificationPreference,
    Notification,
    get_course_notification_preference_config_version
)
from openedx.core.djangoapps.notifications.serializers import NotificationCourseEnrollmentSerializer
from openedx.core.djangoapps.notifications.email.utils import encrypt_object, encrypt_string
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

from ..base_notification import COURSE_NOTIFICATION_APPS, COURSE_NOTIFICATION_TYPES, NotificationAppManager
from ..utils import get_notification_types_with_visibility_settings


@ddt.ddt
class CourseEnrollmentListViewTest(ModuleStoreTestCase):
    """
    Tests for the CourseEnrollmentListView.
    """

    def setUp(self):
        """
        Set up the test.
        """
        super().setUp()
        self.client = APIClient()
        self.user = UserFactory()
        course_1 = CourseFactory.create(
            org='testorg',
            number='testcourse',
            run='testrun'
        )
        course_2 = CourseFactory.create(
            org='testorg',
            number='testcourse_two',
            run='testrun'
        )
        course_overview_1 = CourseOverviewFactory.create(id=course_1.id, org='AwesomeOrg')
        course_overview_2 = CourseOverviewFactory.create(id=course_2.id, org='AwesomeOrg')

        self.enrollment1 = CourseEnrollment.objects.create(
            user=self.user,
            course=course_overview_1,
            is_active=True,
            mode='audit'
        )
        self.enrollment2 = CourseEnrollment.objects.create(
            user=self.user,
            course=course_overview_2,
            is_active=False,
            mode='honor'
        )

    @override_waffle_flag(ENABLE_NOTIFICATIONS, active=True)
    @ddt.unpack
    def test_course_enrollment_list_view(self):
        """
        Test the CourseEnrollmentListView.
        """
        self.client.login(username=self.user.username, password=self.TEST_PASSWORD)
        url = reverse('enrollment-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data['results']
        enrollments = CourseEnrollment.objects.filter(user=self.user, is_active=True)
        expected_data = NotificationCourseEnrollmentSerializer(enrollments, many=True).data

        self.assertEqual(len(data), 1)
        self.assertEqual(data, expected_data)
        self.assertEqual(response.data['show_preferences'], True)

    def test_course_enrollment_api_permission(self):
        """
        Calls api without login.
        Check is 401 is returned
        """
        url = reverse('enrollment-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


@override_waffle_flag(ENABLE_NOTIFICATIONS, active=True)
class CourseEnrollmentPostSaveTest(ModuleStoreTestCase):
    """
    Tests for the post_save signal for CourseEnrollment.
    """

    def setUp(self):
        """
        Set up the test.
        """
        super().setUp()
        self.user = UserFactory()
        self.course = CourseFactory.create(
            org='testorg',
            number='testcourse',
            run='testrun'
        )

        course_overview = CourseOverviewFactory.create(id=self.course.id, org='AwesomeOrg')
        self.course_enrollment = CourseEnrollment.objects.create(
            user=self.user,
            course=course_overview,
            is_active=True,
            mode='audit'
        )

    def test_course_enrollment_post_save(self):
        """
        Test the post_save signal for CourseEnrollment.
        """
        # Emit post_save signal
        enrollment_data = CourseEnrollmentData(
            user=UserData(
                pii=UserPersonalData(
                    username=self.user.username,
                    email=self.user.email,
                    name=self.user.profile.name,
                ),
                id=self.user.id,
                is_active=self.user.is_active,
            ),
            course=CourseData(
                course_key=self.course.id,
                display_name=self.course.display_name,
            ),
            mode=self.course_enrollment.mode,
            is_active=self.course_enrollment.is_active,
            creation_date=self.course_enrollment.created,
        )
        COURSE_ENROLLMENT_CREATED.send_event(
            enrollment=enrollment_data
        )

        # Assert that CourseNotificationPreference object was created with correct attributes
        notification_preferences = CourseNotificationPreference.objects.all()

        self.assertEqual(notification_preferences.count(), 1)
        self.assertEqual(notification_preferences[0].user, self.user)


@override_waffle_flag(ENABLE_NOTIFICATIONS, active=True)
@ddt.ddt
class UserNotificationPreferenceAPITest(ModuleStoreTestCase):
    """
    Test for user notification preference API.
    """

    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.course = CourseFactory.create(
            org='testorg',
            number='testcourse',
            run='testrun'
        )

        course_overview = CourseOverviewFactory.create(id=self.course.id, org='AwesomeOrg')
        self.course_enrollment = CourseEnrollment.objects.create(
            user=self.user,
            course=course_overview,
            is_active=True,
            mode='audit'
        )
        self.client = APIClient()
        self.path = reverse('notification-preferences', kwargs={'course_key_string': self.course.id})

        enrollment_data = CourseEnrollmentData(
            user=UserData(
                pii=UserPersonalData(
                    username=self.user.username,
                    email=self.user.email,
                    name=self.user.profile.name,
                ),
                id=self.user.id,
                is_active=self.user.is_active,
            ),
            course=CourseData(
                course_key=self.course.id,
                display_name=self.course.display_name,
            ),
            mode=self.course_enrollment.mode,
            is_active=self.course_enrollment.is_active,
            creation_date=self.course_enrollment.created,
        )
        COURSE_ENROLLMENT_CREATED.send_event(
            enrollment=enrollment_data
        )

    def _expected_api_response(self, course=None):
        """
        Helper method to return expected API response.
        """
        if course is None:
            course = self.course
        response = {
            'id': 1,
            'course_name': 'course-v1:testorg+testcourse+testrun Course',
            'course_id': 'course-v1:testorg+testcourse+testrun',
            'notification_preference_config': {
                'discussion': {
                    'enabled': True,
                    'core_notification_types': [
                        'new_comment_on_response',
                        'new_comment',
                        'new_response',
                        'response_on_followed_post',
                        'comment_on_followed_post',
                        'response_endorsed_on_thread',
                        'response_endorsed'
                    ],
                    'notification_types': {
                        'new_discussion_post': {
                            'web': False,
                            'email': False,
                            'push': False,
                            'email_cadence': 'Daily',
                            'info': ''
                        },
                        'new_question_post': {
                            'web': False,
                            'email': False,
                            'push': False,
                            'email_cadence': 'Daily',
                            'info': ''
                        },
                        'core': {
                            'web': True,
                            'email': True,
                            'push': True,
                            'email_cadence': 'Daily',
                            'info': 'Notifications for responses and comments on your posts, and the ones you’re '
                                    'following, including endorsements to your responses and on your posts.'
                        },
                        'content_reported': {
                            'web': True,
                            'email': True,
                            'push': True,
                            'info': '',
                            'email_cadence': 'Daily',
                        },
                    },
                    'non_editable': {
                        'core': ['web']
                    }
                },
                'updates': {
                    'enabled': True,
                    'core_notification_types': [],
                    'notification_types': {
                        'course_updates': {
                            'web': True,
                            'email': False,
                            'push': True,
                            'email_cadence': 'Daily',
                            'info': ''
                        },
                        'core': {
                            'web': True,
                            'email': True,
                            'push': True,
                            'email_cadence': 'Daily',
                            'info': 'Notifications for new announcements and updates from the course team.'
                        }
                    },
                    'non_editable': {}
                },
                'grading': {
                    'enabled': True,
                    'core_notification_types': [],
                    'notification_types': {
                        'ora_staff_notification': {
                            'web': False,
                            'email': False,
                            'push': False,
                            'email_cadence': 'Daily',
                            'info': ''
                        },
                        'core': {
                            'web': True,
                            'email': True,
                            'push': True,
                            'email_cadence': 'Daily',
                            'info': 'Notifications for submission grading.'
                        },
                        'ora_grade_assigned': {
                            'web': True,
                            'email': True,
                            'push': False,
                            'email_cadence': 'Daily',
                            'info': ''
                        },
                    },
                    'non_editable': {}
                }
            }
        }
        return response

    def test_get_user_notification_preference_without_login(self):
        """
        Test get user notification preference without login.
        """
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @mock.patch("eventtracking.tracker.emit")
    def test_get_user_notification_preference(self, mock_emit):
        """
        Test get user notification preference.
        """
        self.client.login(username=self.user.username, password=self.TEST_PASSWORD)
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_response = self._expected_api_response()
        expected_response = remove_notifications_with_visibility_settings(expected_response)
        self.assertEqual(response.data, expected_response)
        event_name, event_data = mock_emit.call_args[0]
        self.assertEqual(event_name, 'edx.notifications.preferences.viewed')

    @mock.patch("eventtracking.tracker.emit")
    @mock.patch.dict(COURSE_NOTIFICATION_TYPES, {
        **COURSE_NOTIFICATION_TYPES,
        **{
            'content_reported': {
                'name': 'content_reported',
                'visible_to': [FORUM_ROLE_MODERATOR, FORUM_ROLE_COMMUNITY_TA, FORUM_ROLE_ADMINISTRATOR]
            }
        }
    })
    @ddt.data(
        FORUM_ROLE_MODERATOR,
        FORUM_ROLE_COMMUNITY_TA,
        FORUM_ROLE_ADMINISTRATOR,
        None
    )
    def test_get_user_notification_preference_with_visibility_settings(self, role, mock_emit):
        """
        Test get user notification preference.
        """
        if role:
            CourseStaffRole(self.course.id).add_users(self.user)
        self.client.login(username=self.user.username, password=self.TEST_PASSWORD)

        role_instance = None
        if role:
            role_instance = RoleFactory(name=role, course_id=self.course.id)
            role_instance.users.add(self.user)

        response = self.client.get(self.path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        expected_response = self._expected_api_response()

        if not role:
            expected_response = remove_notifications_with_visibility_settings(expected_response)

        self.assertEqual(response.data, expected_response)
        event_name, event_data = mock_emit.call_args[0]
        self.assertEqual(event_name, 'edx.notifications.preferences.viewed')
        if role_instance:
            role_instance.users.clear()

    @ddt.data(
        ('discussion', None, None, True, status.HTTP_200_OK, 'app_update'),
        ('discussion', None, None, False, status.HTTP_200_OK, 'app_update'),
        ('invalid_notification_app', None, None, True, status.HTTP_400_BAD_REQUEST, None),

        ('discussion', 'core', 'email', True, status.HTTP_200_OK, 'type_update'),
        ('discussion', 'core', 'email', False, status.HTTP_200_OK, 'type_update'),

        # Test for email cadence update
        ('discussion', 'core', 'email_cadence', 'Daily', status.HTTP_200_OK, 'type_update'),
        ('discussion', 'core', 'email_cadence', 'Weekly', status.HTTP_200_OK, 'type_update'),

        # Test for app-wide channel update
        ('discussion', None, 'email', True, status.HTTP_200_OK, 'app-wide-channel-update'),
        ('discussion', None, 'email', False, status.HTTP_200_OK, 'app-wide-channel-update'),

        ('discussion', 'invalid_notification_type', 'email', True, status.HTTP_400_BAD_REQUEST, None),
        ('discussion', 'new_comment', 'invalid_notification_channel', False, status.HTTP_400_BAD_REQUEST, None),
    )
    @ddt.unpack
    @mock.patch("eventtracking.tracker.emit")
    def test_patch_user_notification_preference(
        self, notification_app, notification_type, notification_channel, value, expected_status, update_type, mock_emit,
    ):
        """
        Test update of user notification preference.
        """
        self.client.login(username=self.user.username, password=self.TEST_PASSWORD)
        payload = {
            'notification_app': notification_app,
            'value': value,
        }
        if notification_type:
            payload['notification_type'] = notification_type
        if notification_channel:
            payload['notification_channel'] = notification_channel

        response = self.client.patch(self.path, json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, expected_status)
        expected_data = self._expected_api_response()

        if update_type == 'app_update':
            expected_data = self._expected_api_response()
            expected_data = remove_notifications_with_visibility_settings(expected_data)
            expected_data['notification_preference_config'][notification_app]['enabled'] = value
            self.assertEqual(response.data, expected_data)

        elif update_type == 'type_update':
            expected_data = self._expected_api_response()
            expected_data = remove_notifications_with_visibility_settings(expected_data)
            expected_data['notification_preference_config'][notification_app][
                'notification_types'][notification_type][notification_channel] = value
            self.assertEqual(response.data, expected_data)

        elif update_type == 'app-wide-channel-update':
            expected_data = remove_notifications_with_visibility_settings(expected_data)
            app_prefs = expected_data['notification_preference_config'][notification_app]
            for notification_type_name, notification_type_preferences in app_prefs['notification_types'].items():
                non_editable_channels = app_prefs['non_editable'].get(notification_type_name, [])
                if notification_channel not in non_editable_channels:
                    app_prefs['notification_types'][notification_type_name][notification_channel] = value
            self.assertEqual(response.data, expected_data)

        if expected_status == status.HTTP_200_OK:
            event_name, event_data = mock_emit.call_args[0]
            self.assertEqual(event_name, 'edx.notifications.preferences.updated')
            self.assertEqual(event_data['notification_app'], notification_app)
            self.assertEqual(event_data['notification_type'], notification_type or '')
            self.assertEqual(event_data['notification_channel'], notification_channel or '')
            self.assertEqual(event_data['value'], value)

    def test_info_is_not_saved_in_json(self):
        default_prefs = NotificationAppManager().get_notification_app_preferences()
        for notification_app, app_prefs in default_prefs.items():
            for _, type_prefs in app_prefs.get('notification_types', {}).items():
                assert 'info' not in type_prefs.keys()


@ddt.ddt
class NotificationListAPIViewTest(APITestCase):
    """
    Tests suit for the NotificationListAPIView.
    """

    def setUp(self):
        self.TEST_PASSWORD = 'Password1234'
        self.user = UserFactory(password=self.TEST_PASSWORD)
        self.url = reverse('notifications-list')

    def test_list_notifications(self):
        """
        Test that the view can list notifications.
        """
        # Create a notification for the user.
        Notification.objects.create(
            user=self.user,
            app_name='discussion',
            notification_type='new_response',
            content_context={
                'replier_name': 'test_user',
                'post_title': 'This is a test post.',
            }
        )
        self.client.login(username=self.user.username, password=self.TEST_PASSWORD)

        # Make a request to the view.
        response = self.client.get(self.url)

        # Assert that the response is successful.

        self.assertEqual(response.status_code, 200)
        data = response.data['results']
        # Assert that the response contains the notification.
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['app_name'], 'discussion')
        self.assertEqual(data[0]['notification_type'], 'new_response')
        self.assertEqual(
            data[0]['content'],
            '<p><strong>test_user</strong> responded to your post <strong>This is a test post.</strong></p>'
        )

    def test_list_notifications_with_app_name_filter(self):
        """
        Test that the view can filter notifications by app name.
        """
        # Create two notifications for the user, one for each app name.
        Notification.objects.create(
            user=self.user,
            app_name='discussion',
            notification_type='new_response',
            content_context={
                'replier_name': 'test_user',
                'post_title': 'This is a test post.',
            }
        )
        Notification.objects.create(
            user=self.user,
            app_name='app2',
            notification_type='info',
        )
        self.client.login(username=self.user.username, password=self.TEST_PASSWORD)

        # Make a request to the view with the app_name query parameter set to 'app1'.
        response = self.client.get(self.url + "?app_name=discussion")

        # Assert that the response is successful.
        self.assertEqual(response.status_code, 200)

        # Assert that the response contains only the notification for app1.
        data = response.data['results']
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['app_name'], 'discussion')
        self.assertEqual(data[0]['notification_type'], 'new_response')
        self.assertEqual(
            data[0]['content'],
            '<p><strong>test_user</strong> responded to your post <strong>This is a test post.</strong></p>'
        )

    @ddt.data(
        ([], 0),
        (['web'], 1),
        (['email'], 0),
        (['web', 'email'], 1),
        (['web', 'email', 'push'], 1),
    )
    @ddt.unpack
    def test_list_notifications_with_channels(self, channels, expected_count):
        """
        Test that the view can filter notifications by app name and channels.
        """

        Notification.objects.create(
            user=self.user,
            app_name='discussion',
            notification_type='new_response',
            content_context={
                'replier_name': 'test_user',
                'post_title': 'This is a test post.',
            },
            web='web' in channels,
            email='email' in channels
        )

        self.client.login(username=self.user.username, password=self.TEST_PASSWORD)

        # Make a request to the view with the app_name query parameter set to 'app1'.
        response = self.client.get(self.url + "?app_name=discussion")

        # Assert that the response is successful.
        self.assertEqual(response.status_code, 200)

        # Assert that the response contains expected results i.e. channels contains web or is null.
        data = response.data['results']
        self.assertEqual(len(data), expected_count)

    @mock.patch("eventtracking.tracker.emit")
    def test_list_notifications_with_tray_opened_param(self, mock_emit):
        """
        Test event emission with tray_opened param is provided.
        """
        self.client.login(username=self.user.username, password=self.TEST_PASSWORD)

        # Make a request to the view with the tray_opened query parameter set to True.
        response = self.client.get(self.url + "?tray_opened=True")

        # Assert that the response is successful.
        self.assertEqual(response.status_code, 200)

        event_name, event_data = mock_emit.call_args[0]
        self.assertEqual(event_name, 'edx.notifications.tray_opened')
        self.assertEqual(event_data['user_id'], self.user.id)
        self.assertEqual(event_data['unseen_notifications_count'], 0)

    def test_list_notifications_without_authentication(self):
        """
        Test that the view returns 401 if the user is not authenticated.
        """
        # Make a request to the view without authenticating.
        response = self.client.get(self.url)

        # Assert that the response is unauthorized.
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_notifications_with_expiry_date(self):
        """
        Test that the view can filter notifications by expiry date.
        """
        today = datetime.now(UTC)

        # Create two notifications for the user, one with current date and other with expiry date.
        Notification.objects.create(
            user=self.user,
            notification_type='info',
            created=today
        )
        Notification.objects.create(
            user=self.user,
            notification_type='info',
            created=today - timedelta(days=settings.NOTIFICATIONS_EXPIRY)
        )
        self.client.login(username=self.user.username, password=self.TEST_PASSWORD)

        # Make a request to the view
        response = self.client.get(self.url)

        # Assert that the response is successful.
        self.assertEqual(response.status_code, 200)

        # Assert that the response contains only the notification for current date.
        data = response.data['results']
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['created'], today.strftime('%Y-%m-%dT%H:%M:%S.%fZ'))

    def test_list_notifications_with_order_by_reverse_id(self):
        """
        Test that the view can filter notifications and order by reverse id.
        """

        # Create two notifications for the user
        notification1 = Notification.objects.create(
            user=self.user,
            notification_type='info',
        )
        notification2 = Notification.objects.create(
            user=self.user,
            notification_type='info',
        )
        self.client.login(username=self.user.username, password=self.TEST_PASSWORD)

        # Make a request to the view
        response = self.client.get(self.url)

        # Assert that the response is successful.
        self.assertEqual(response.status_code, 200)

        # Assert that the response id list is in reverse order.
        data = response.data['results']
        self.assertEqual(len(data), 2)
        self.assertEqual([data[0]['id'], data[1]['id']], [notification2.id, notification1.id])


@ddt.ddt
class NotificationCountViewSetTestCase(ModuleStoreTestCase):
    """
    Tests for the NotificationCountViewSet.
    """

    def setUp(self):
        # Create a user.
        super().setUp()
        self.user = UserFactory()
        self.client = APIClient()

        course = CourseFactory.create(
            org='testorg',
            number='testcourse',
            run='testrun'
        )

        course_overview = CourseOverviewFactory.create(id=course.id, org='AwesomeOrg')
        self.enrollment = CourseEnrollment.objects.create(
            user=self.user,
            course=course_overview,
            is_active=True,
            mode='audit'
        )

        self.url = reverse('notifications-count')

        # Create some notifications for the user.
        Notification.objects.create(user=self.user, app_name='App Name 1', notification_type='Type A')
        Notification.objects.create(user=self.user, app_name='App Name 1', notification_type='Type B')
        Notification.objects.create(user=self.user, app_name='App Name 2', notification_type='Type A')
        Notification.objects.create(user=self.user, app_name='App Name 3', notification_type='Type C')

    @override_waffle_flag(ENABLE_NOTIFICATIONS, active=True)
    @ddt.unpack
    def test_get_unseen_notifications_count_with_show_notifications_tray(self):
        """
        Test that the endpoint returns the correct count of unseen notifications and show_notifications_tray value.
        """
        self.client.login(username=self.user.username, password=self.TEST_PASSWORD)
        # Make a request to the view
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 4)
        self.assertEqual(response.data['count_by_app_name'], {
            'App Name 1': 2, 'App Name 2': 1, 'App Name 3': 1, 'discussion': 0, 'updates': 0, 'grading': 0})
        self.assertEqual(response.data['show_notifications_tray'], True)

    def test_get_unseen_notifications_count_for_unauthenticated_user(self):
        """
        Test that the endpoint returns 401 for an unauthenticated user.
        """
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_unseen_notifications_count_for_user_with_no_notifications(self):
        """
        Test that the endpoint returns 0 for a user with no notifications.
        """
        # Create a user with no notifications.
        user = UserFactory()
        self.client.login(username=user.username, password=self.TEST_PASSWORD)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 0)
        self.assertEqual(response.data['count_by_app_name'], {'discussion': 0, 'updates': 0, 'grading': 0})

    def test_get_expiry_days_in_count_view(self):
        """
        Tests if "notification_expiry_days" exists in API response
        """
        user = UserFactory()
        self.client.login(username=user.username, password=self.TEST_PASSWORD)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['notification_expiry_days'], 60)


class MarkNotificationsSeenAPIViewTestCase(APITestCase):
    """
    Tests for the MarkNotificationsUnseenAPIView.
    """

    def setUp(self):
        self.TEST_PASSWORD = 'Password1234'
        self.user = UserFactory(password=self.TEST_PASSWORD)

        # Create some sample notifications for the user
        Notification.objects.create(user=self.user, app_name='App Name 1', notification_type='Type A')
        Notification.objects.create(user=self.user, app_name='App Name 1', notification_type='Type B')
        Notification.objects.create(user=self.user, app_name='App Name 2', notification_type='Type A')
        Notification.objects.create(user=self.user, app_name='App Name 3', notification_type='Type C')

    def test_mark_notifications_seen(self):
        # Create a POST request to mark notifications as seen for 'App Name 1'
        app_name = 'App Name 1'
        url = reverse('mark-notifications-seen', kwargs={'app_name': app_name})
        self.client.login(username=self.user.username, password=self.TEST_PASSWORD)
        response = self.client.put(url)
        # Assert the response status code is 200 (OK)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Assert the response data contains the expected message
        expected_data = {'message': 'Notifications marked as seen.'}
        self.assertEqual(response.data, expected_data)

        # Assert the notifications for 'App Name 1' are marked as seen for the user
        notifications = Notification.objects.filter(user=self.user, app_name=app_name, last_seen__isnull=False)
        self.assertEqual(notifications.count(), 2)


class NotificationReadAPIViewTestCase(APITestCase):
    """
    Tests for the NotificationReadAPIView.
    """

    def setUp(self):
        self.TEST_PASSWORD = 'Password1234'
        self.user = UserFactory(password=self.TEST_PASSWORD)
        self.url = reverse('notifications-read')
        self.client.login(username=self.user.username, password=self.TEST_PASSWORD)

        # Create some sample notifications for the user with already existing apps and with invalid app name
        Notification.objects.create(user=self.user, app_name='app_name_2', notification_type='Type A')
        for app_name in COURSE_NOTIFICATION_APPS:
            Notification.objects.create(user=self.user, app_name=app_name, notification_type='Type A')
            Notification.objects.create(user=self.user, app_name=app_name, notification_type='Type B')

    @mock.patch("eventtracking.tracker.emit")
    def test_mark_all_notifications_read_with_app_name(self, mock_emit):
        # Create a PATCH request to mark all notifications as read for already existing app e.g 'discussion'
        app_name = next(iter(COURSE_NOTIFICATION_APPS))
        data = {'app_name': app_name}

        response = self.client.patch(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {'message': 'Notifications marked read.'})
        notifications = Notification.objects.filter(user=self.user, app_name=app_name, last_read__isnull=False)
        self.assertEqual(notifications.count(), 2)
        event_name, event_data = mock_emit.call_args[0]
        self.assertEqual(event_name, 'edx.notifications.app_all_read')
        self.assertEqual(event_data['notification_app'], 'discussion')

    def test_mark_all_notifications_read_with_invalid_app_name(self):
        # Create a PATCH request to mark all notifications as read for 'app_name_1'
        app_name = 'app_name_1'
        data = {'app_name': app_name}

        response = self.client.patch(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'error': 'Invalid app_name or notification_id.'})

    @mock.patch("eventtracking.tracker.emit")
    def test_mark_notification_read_with_notification_id(self, mock_emit):
        # Create a PATCH request to mark notification as read for notification_id: 2
        notification_id = 2
        data = {'notification_id': notification_id}

        response = self.client.patch(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {'message': 'Notification marked read.'})
        notifications = Notification.objects.filter(user=self.user, id=notification_id, last_read__isnull=False)
        self.assertEqual(notifications.count(), 1)
        event_name, event_data = mock_emit.call_args[0]
        self.assertEqual(event_name, 'edx.notifications.read')
        self.assertEqual(event_data.get('notification_metadata').get('notification_id'), notification_id)
        self.assertEqual(event_data['notification_app'], 'discussion')
        self.assertEqual(event_data['notification_type'], 'Type A')
        self.assertEqual(event_data['first_read'], True)

    def test_mark_notification_read_with_other_user_notification_id(self):
        # Create a PATCH request to mark notification as read for notification_id: 2 through a different user
        self.client.logout()
        self.user = UserFactory()
        self.client.login(username=self.user.username, password=self.TEST_PASSWORD)

        notification_id = 2
        data = {'notification_id': notification_id}
        response = self.client.patch(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        notifications = Notification.objects.filter(user=self.user, id=notification_id, last_read__isnull=False)
        self.assertEqual(notifications.count(), 0)

    def test_mark_notification_read_with_invalid_notification_id(self):
        # Create a PATCH request to mark notification as read for notification_id: 23345
        notification_id = 23345
        data = {'notification_id': notification_id}

        response = self.client.patch(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["detail"], 'Not found.')

    def test_mark_notification_read_with_app_name_and_notification_id(self):
        # Create a PATCH request to mark notification as read for existing app e.g 'discussion' and notification_id: 2
        # notification_id has higher priority than app_name in this case app_name is ignored
        app_name = next(iter(COURSE_NOTIFICATION_APPS))
        notification_id = 2
        data = {'app_name': app_name, 'notification_id': notification_id}

        response = self.client.patch(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {'message': 'Notification marked read.'})
        notifications = Notification.objects.filter(
            user=self.user,
            id=notification_id,
            last_read__isnull=False
        )
        self.assertEqual(notifications.count(), 1)

    def test_mark_notification_read_without_app_name_and_notification_id(self):
        # Create a PATCH request to mark notification as read without app_name and notification_id
        response = self.client.patch(self.url, {})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'error': 'Invalid app_name or notification_id.'})


@ddt.ddt
class UpdatePreferenceFromEncryptedDataView(ModuleStoreTestCase):
    """
    Tests if preference is updated when encrypted url is hit
    """
    def setUp(self):
        """
        Setup test case
        """
        super().setUp()
        password = 'password'
        self.user = UserFactory(password=password)
        self.client.login(username=self.user.username, password=password)
        self.course = CourseFactory.create(display_name='test course 1', run="Testing_course_1")
        CourseNotificationPreference(course_id=self.course.id, user=self.user).save()

    @override_settings(LMS_BASE="")
    @ddt.data('get', 'post')
    def test_if_preference_is_updated(self, request_type):
        """
        Tests if preference is updated when url is hit
        """
        user_hash = encrypt_string(self.user.username)
        patch_hash = encrypt_object({'channel': 'email', 'value': False})
        url_params = {
            "username": user_hash,
            "patch": patch_hash
        }
        url = reverse("preference_update_from_encrypted_username_view", kwargs=url_params)
        func = getattr(self.client, request_type)
        response = func(url)
        assert response.status_code == status.HTTP_200_OK
        preference = CourseNotificationPreference.objects.get(user=self.user, course_id=self.course.id)
        config = preference.notification_preference_config
        for app_name, app_prefs in config.items():
            for type_prefs in app_prefs['notification_types'].values():
                assert type_prefs['email'] is False
                assert type_prefs['email_cadence'] == EmailCadence.NEVER

    def test_if_config_version_is_updated(self):
        """
        Tests if preference version is updated before applying patch data
        """
        preference = CourseNotificationPreference.objects.get(user=self.user, course_id=self.course.id)
        preference.config_version -= 1
        preference.save()
        user_hash = encrypt_string(self.user.username)
        patch_hash = encrypt_object({'channel': 'email', 'value': False})
        url_params = {
            "username": user_hash,
            "patch": patch_hash
        }
        url = reverse("preference_update_from_encrypted_username_view", kwargs=url_params)
        self.client.get(url)
        preference = CourseNotificationPreference.objects.get(user=self.user, course_id=self.course.id)
        assert preference.config_version == get_course_notification_preference_config_version()


def remove_notifications_with_visibility_settings(expected_response):
    """
    Remove notifications with visibility settings from the expected response.
    """
    not_visible = get_notification_types_with_visibility_settings()
    for expected_response_app in expected_response['notification_preference_config']:
        for notification_type, visibility_settings in not_visible.items():
            types = expected_response['notification_preference_config'][expected_response_app]['notification_types']
            if notification_type in types:
                expected_response['notification_preference_config'][expected_response_app]['notification_types'].pop(
                    notification_type
                )
    return expected_response
