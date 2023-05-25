"""
Tests for the views in the notifications app.
"""
import json

from django.dispatch import Signal
from django.urls import reverse
from edx_toggles.toggles.testutils import override_waffle_flag
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from common.djangoapps.student.models import CourseEnrollment
from common.djangoapps.student.tests.factories import UserFactory
from openedx.core.djangoapps.content.course_overviews.tests.factories import CourseOverviewFactory
from openedx.core.djangoapps.notifications.config.waffle import ENABLE_NOTIFICATIONS
from openedx.core.djangoapps.notifications.models import Notification, NotificationPreference
from openedx.core.djangoapps.notifications.serializers import NotificationCourseEnrollmentSerializer
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


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
        # self.client.force_authenticate(user=self.user)
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

        # Assert that NotificationPreference object was created with correct attributes
        notification_preferences = NotificationPreference.objects.all()

        self.assertEqual(notification_preferences.count(), 1)
        self.assertEqual(notification_preferences[0].user, self.user)


@override_waffle_flag(ENABLE_NOTIFICATIONS, active=True)
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

    def _expected_api_response(self, overrides=None):
        """
        Helper method to return expected API response.
        """
        expected_response = {
            'id': 1,
            'course_name': 'course-v1:testorg+testcourse+testrun Course',
            'course_id': 'course-v1:testorg+testcourse+testrun',
            'notification_preference_config': {
                'discussion': {
                    'new_post': {
                        'web': False,
                        'push': False,
                        'email': False
                    }
                }
            }
        }
        if overrides:
            expected_response.update(overrides)
        return expected_response

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

    def test_patch_user_notification_preference(self):
        """
        Test update of user notification preference.
        """
        self.client.login(username=self.user.username, password='test')
        updated_notification_config_data = {
            "notification_preference_config": {
                "discussion": {
                    "new_post": {
                        "web": True,
                        "push": False,
                        "email": False,
                    },
                },
            },
        }
        response = self.client.patch(
            self.path, json.dumps(updated_notification_config_data), content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_data = self._expected_api_response(overrides=updated_notification_config_data)
        self.assertEqual(response.data, expected_data)


class NotificationListAPIViewTest(APITestCase):
    """
    Tests suit for the NotificationListAPIView.
    """

    def setUp(self):
        self.user = self.user = UserFactory()
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
            content='This is a notification.',
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
        self.assertEqual(data[0]['content'], 'This is a notification.')

    def test_list_notifications_with_app_name_filter(self):
        """
        Test that the view can filter notifications by app name.
        """
        # Create two notifications for the user, one for each app name.
        Notification.objects.create(
            user=self.user,
            app_name='app1',
            notification_type='info',
            content='This is a notification for app1.',
        )
        Notification.objects.create(
            user=self.user,
            app_name='app2',
            notification_type='info',
            content='This is a notification for app2.',
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
        self.assertEqual(data[0]['content'], 'This is a notification for app1.')

    def test_list_notifications_without_authentication(self):
        """
        Test that the view returns 403 if the user is not authenticated.
        """
        # Make a request to the view without authenticating.
        response = self.client.get(self.url)

        # Assert that the response is unauthorized.
        self.assertEqual(response.status_code, 403)


class NotificationCountViewSetTestCase(APITestCase):
    """
    Tests for the NotificationCountViewSet.
    """

    def setUp(self):
        # Create a user.
        self.user = UserFactory()
        self.url = reverse('notifications-count')
        # Create some notifications for the user.
        Notification.objects.create(user=self.user, app_name='App Name 1', notification_type='Type A')
        Notification.objects.create(user=self.user, app_name='App Name 1', notification_type='Type B')
        Notification.objects.create(user=self.user, app_name='App Name 2', notification_type='Type A')
        Notification.objects.create(user=self.user, app_name='App Name 3', notification_type='Type C')

    def test_get_unseen_notifications_count(self):
        """
        Test that the endpoint returns the correct count of unseen notifications.
        """
        self.client.login(username=self.user.username, password='test')
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 4)
        self.assertEqual(response.data['count_by_app_name'], {'App Name 1': 2, 'App Name 2': 1, 'App Name 3': 1})

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
