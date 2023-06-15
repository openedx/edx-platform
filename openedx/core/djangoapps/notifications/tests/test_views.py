"""
Tests for the views in the notifications app.
"""
import json
from datetime import datetime, timedelta

import ddt
from django.conf import settings
from django.dispatch import Signal
from django.urls import reverse
from edx_toggles.toggles.testutils import override_waffle_flag
from pytz import UTC
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from common.djangoapps.student.models import CourseEnrollment
from common.djangoapps.student.tests.factories import UserFactory
from openedx.core.djangoapps.content.course_overviews.tests.factories import CourseOverviewFactory
from openedx.core.djangoapps.notifications.config.waffle import ENABLE_NOTIFICATIONS, SHOW_NOTIFICATIONS_TRAY
from openedx.core.djangoapps.notifications.models import (
    Notification,
    CourseNotificationPreference,
)
from openedx.core.djangoapps.notifications.serializers import NotificationCourseEnrollmentSerializer
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

from ..base_notification import COURSE_NOTIFICATION_APPS


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
    def test_course_enrollment_list_view(self):
        """
        Test the CourseEnrollmentListView.
        """
        self.client.login(username=self.user.username, password='test')
        url = reverse('enrollment-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        enrollments = CourseEnrollment.objects.filter(user=self.user, is_active=True)
        expected_data = NotificationCourseEnrollmentSerializer(enrollments, many=True).data
        self.assertEqual(response.data, expected_data)

    def test_course_enrollment_api_permission(self):
        """
        Calls api without login.
        Check is 403 is returned
        """
        url = reverse('enrollment-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


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
        self.post_save_signal = Signal()

    def test_course_enrollment_post_save(self):
        """
        Test the post_save signal for CourseEnrollment.
        """
        # Emit post_save signal

        self.post_save_signal.send(
            sender=self.course_enrollment.__class__,
            instance=self.course_enrollment,
            created=True
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
        self.post_save_signal = Signal()
        self.client = APIClient()
        self.path = reverse('notification-preferences', kwargs={'course_key_string': self.course.id})
        self.post_save_signal.send(
            sender=self.course_enrollment.__class__,
            instance=self.course_enrollment,
            created=True
        )

    def _expected_api_response(self):
        """
        Helper method to return expected API response.
        """
        return {
            'id': 1,
            'course_name': 'course-v1:testorg+testcourse+testrun Course',
            'course_id': 'course-v1:testorg+testcourse+testrun',
            'notification_preference_config': {
                'discussion': {
                    'enabled': True,
                    'core_notification_types': ['new_comment_on_response'],
                    'notification_types': {
                        'new_comment': {
                            'web': True,
                            'email': True,
                            'push': True,
                            'info': 'Comment on post'
                        },
                        'new_response': {
                            'web': True,
                            'email': True,
                            'push': True,
                            'info': 'Response on post'
                        },
                        'core': {
                            'web': True,
                            'email': True,
                            'push': True,
                            'info': ''
                        }
                    },
                    'non_editable': {
                        'new_comment': ['web', 'email']
                    }
                }
            }
        }

    def test_get_user_notification_preference_without_login(self):
        """
        Test get user notification preference without login.
        """
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_user_notification_preference(self):
        """
        Test get user notification preference.
        """
        self.client.login(username=self.user.username, password='test')
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, self._expected_api_response())

    @ddt.data(
        ('discussion', None, None, True, status.HTTP_200_OK, 'app_update'),
        ('discussion', None, None, False, status.HTTP_200_OK, 'app_update'),
        ('invalid_notification_app', None, None, True, status.HTTP_400_BAD_REQUEST, None),

        ('discussion', 'new_comment', 'web', True, status.HTTP_200_OK, 'type_update'),
        ('discussion', 'new_response', 'web', False, status.HTTP_200_OK, 'type_update'),

        ('discussion', 'core', 'email', True, status.HTTP_200_OK, 'type_update'),
        ('discussion', 'core', 'email', False, status.HTTP_200_OK, 'type_update'),

        ('discussion', 'invalid_notification_type', 'email', True, status.HTTP_400_BAD_REQUEST, None),
        ('discussion', 'new_comment', 'invalid_notification_channel', False, status.HTTP_400_BAD_REQUEST, None),
    )
    @ddt.unpack
    def test_patch_user_notification_preference(
        self, notification_app, notification_type, notification_channel, value, expected_status, update_type,
    ):
        """
        Test update of user notification preference.
        """
        self.client.login(username=self.user.username, password='test')
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

        if update_type == 'app_update':
            expected_data = self._expected_api_response()
            expected_data['notification_preference_config'][notification_app]['enabled'] = value
            self.assertEqual(response.data, expected_data)

        elif update_type == 'type_update':
            expected_data = self._expected_api_response()
            expected_data['notification_preference_config'][notification_app][
                'notification_types'][notification_type][notification_channel] = value
            self.assertEqual(response.data, expected_data)


class NotificationListAPIViewTest(APITestCase):
    """
    Tests suit for the NotificationListAPIView.
    """

    def setUp(self):
        self.user = UserFactory()
        self.url = reverse('notifications-list')

    def test_list_notifications(self):
        """
        Test that the view can list notifications.
        """
        # Create a notification for the user.
        Notification.objects.create(
            user=self.user,
            app_name='app1',
            notification_type='info',
        )
        self.client.login(username=self.user.username, password='test')

        # Make a request to the view.
        response = self.client.get(self.url)

        # Assert that the response is successful.

        self.assertEqual(response.status_code, 200)
        data = response.data['results']
        # Assert that the response contains the notification.
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['app_name'], 'app1')
        self.assertEqual(data[0]['notification_type'], 'info')

    def test_list_notifications_with_app_name_filter(self):
        """
        Test that the view can filter notifications by app name.
        """
        # Create two notifications for the user, one for each app name.
        Notification.objects.create(
            user=self.user,
            app_name='app1',
            notification_type='info',
        )
        Notification.objects.create(
            user=self.user,
            app_name='app2',
            notification_type='info',
        )
        self.client.login(username=self.user.username, password='test')

        # Make a request to the view with the app_name query parameter set to 'app1'.
        response = self.client.get(self.url + "?app_name=app1")

        # Assert that the response is successful.
        self.assertEqual(response.status_code, 200)

        # Assert that the response contains only the notification for app1.
        data = response.data['results']
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['app_name'], 'app1')
        self.assertEqual(data[0]['notification_type'], 'info')

    def test_list_notifications_without_authentication(self):
        """
        Test that the view returns 403 if the user is not authenticated.
        """
        # Make a request to the view without authenticating.
        response = self.client.get(self.url)

        # Assert that the response is unauthorized.
        self.assertEqual(response.status_code, 403)

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
        self.client.login(username=self.user.username, password='test')

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
        self.client.login(username=self.user.username, password='test')

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

    @ddt.data((False,), (True,))
    @ddt.unpack
    def test_get_unseen_notifications_count_with_show_notifications_tray(self, show_notifications_tray_enabled):
        """
        Test that the endpoint returns the correct count of unseen notifications and show_notifications_tray value.
        """
        self.client.login(username=self.user.username, password='test')

        # Enable or disable the waffle flag based on the test case data
        with override_waffle_flag(SHOW_NOTIFICATIONS_TRAY, active=show_notifications_tray_enabled):

            # Make a request to the view
            response = self.client.get(self.url)

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data['count'], 4)
            self.assertEqual(response.data['count_by_app_name'], {'App Name 1': 2, 'App Name 2': 1, 'App Name 3': 1})
            self.assertEqual(response.data['show_notifications_tray'], show_notifications_tray_enabled)

    def test_get_unseen_notifications_count_for_unauthenticated_user(self):
        """
        Test that the endpoint returns 403 for an unauthenticated user.
        """
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_get_unseen_notifications_count_for_user_with_no_notifications(self):
        """
        Test that the endpoint returns 0 for a user with no notifications.
        """
        # Create a user with no notifications.
        user = UserFactory()
        self.client.login(username=user.username, password='test')
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 0)
        self.assertEqual(response.data['count_by_app_name'], {})


class MarkNotificationsUnseenAPIViewTestCase(APITestCase):
    """
    Tests for the MarkNotificationsUnseenAPIView.
    """

    def setUp(self):
        self.user = UserFactory()

        # Create some sample notifications for the user
        Notification.objects.create(user=self.user, app_name='App Name 1', notification_type='Type A')
        Notification.objects.create(user=self.user, app_name='App Name 1', notification_type='Type B')
        Notification.objects.create(user=self.user, app_name='App Name 2', notification_type='Type A')
        Notification.objects.create(user=self.user, app_name='App Name 3', notification_type='Type C')

    def test_mark_notifications_unseen(self):
        # Create a POST request to mark notifications as unseen for 'App Name 1'
        app_name = 'App Name 1'
        url = reverse('mark-notifications-unseen', kwargs={'app_name': app_name})
        self.client.login(username=self.user.username, password='test')
        response = self.client.put(url)
        # Assert the response status code is 200 (OK)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Assert the response data contains the expected message
        expected_data = {'message': 'Notifications marked unseen.'}
        self.assertEqual(response.data, expected_data)

        # Assert the notifications for 'App Name 1' are marked as unseen for the user
        notifications = Notification.objects.filter(user=self.user, app_name=app_name, last_seen__isnull=False)
        self.assertEqual(notifications.count(), 2)


class NotificationReadAPIViewTestCase(APITestCase):
    """
    Tests for the NotificationReadAPIView.
    """

    def setUp(self):
        self.user = UserFactory()
        self.url = reverse('notifications-read')
        self.client.login(username=self.user.username, password='test')

        # Create some sample notifications for the user with already existing apps and with invalid app name
        Notification.objects.create(user=self.user, app_name='app_name_2', notification_type='Type A')
        for app_name in COURSE_NOTIFICATION_APPS:
            Notification.objects.create(user=self.user, app_name=app_name, notification_type='Type A')
            Notification.objects.create(user=self.user, app_name=app_name, notification_type='Type B')

    def test_mark_all_notifications_read_with_app_name(self):
        # Create a PATCH request to mark all notifications as read for already existing app e.g 'discussion'
        app_name = next(iter(COURSE_NOTIFICATION_APPS))
        data = {'app_name': app_name}

        response = self.client.patch(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {'message': 'Notifications marked read.'})
        notifications = Notification.objects.filter(user=self.user, app_name=app_name, last_read__isnull=False)
        self.assertEqual(notifications.count(), 2)

    def test_mark_all_notifications_read_with_invalid_app_name(self):
        # Create a PATCH request to mark all notifications as read for 'app_name_1'
        app_name = 'app_name_1'
        data = {'app_name': app_name}

        response = self.client.patch(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'message': 'Invalid app name.'})

    def test_mark_notification_read_with_notification_id(self):
        # Create a PATCH request to mark notification as read for notification_id: 2
        notification_id = 2
        data = {'notification_id': notification_id}

        response = self.client.patch(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {'message': 'Notifications marked read.'})
        notifications = Notification.objects.filter(user=self.user, id=notification_id, last_read__isnull=False)
        self.assertEqual(notifications.count(), 1)

    def test_mark_notification_read_with_invalid_notification_id(self):
        # Create a PATCH request to mark notification as read for notification_id: 23345
        notification_id = 23345
        data = {'notification_id': notification_id}

        response = self.client.patch(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, {'message': 'Notification not found.'})

    def test_mark_notification_read_with_app_name_and_notification_id(self):
        # Create a PATCH request to mark notification as read for existing app e.g 'discussion' and notification_id: 2
        app_name = next(iter(COURSE_NOTIFICATION_APPS))
        notification_id = 2
        data = {'app_name': app_name, 'notification_id': notification_id}

        response = self.client.patch(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {'message': 'Notifications marked read.'})
        notifications = Notification.objects.filter(
            user=self.user,
            app_name=app_name,
            id=notification_id,
            last_read__isnull=False
        )
        self.assertEqual(notifications.count(), 1)

    def test_mark_notification_read_without_app_name_and_notification_id(self):
        # Create a PATCH request to mark notification as read without app_name and notification_id
        response = self.client.patch(self.url, {})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'message': 'Invalid app name or notification id.'})
