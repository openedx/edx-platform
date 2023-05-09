"""
Tests for the views in the notifications app.
"""
import json

from django.dispatch import Signal
from django.urls import reverse
from edx_toggles.toggles.testutils import override_waffle_flag
from rest_framework import status
from rest_framework.test import APIClient

from common.djangoapps.student.models import CourseEnrollment
from common.djangoapps.student.tests.factories import UserFactory
from openedx.core.djangoapps.content.course_overviews.tests.factories import CourseOverviewFactory
from openedx.core.djangoapps.notifications.config.waffle import ENABLE_NOTIFICATIONS
from openedx.core.djangoapps.notifications.models import NotificationPreference
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
