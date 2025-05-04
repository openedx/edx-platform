"""
Test the notification app models
"""
import unittest
from unittest import mock

import pytest

from common.djangoapps.student.tests.factories import UserFactory
from openedx.core.djangoapps.notifications.base_notification import NotificationAppManager
from openedx.core.djangoapps.notifications.models import CourseNotificationPreference, \
    COURSE_NOTIFICATION_CONFIG_VERSION


@pytest.mark.django_db
class TestPreferenceModel(unittest.TestCase):
    """
    Test the CourseNotificationPreference model.
    """

    def test_get_user_notification_preferences_method(self):
        """
        Test the get_user_notification_preferences method. and check if version is updated properly.
        """
        # Create a mock user and notification preference
        user = UserFactory()
        CourseNotificationPreference.objects.create(
            user_id=user.id,
            course_id='course-v1:edX+DemoX+Demo_Course',
            is_active=True,
            notification_preference_config=NotificationAppManager().get_notification_app_preferences(True)
        )
        # Check if the notification preference is created
        preference = CourseNotificationPreference.objects.get(user_id=user.id)
        self.assertIsNotNone(preference)
        self.assertTrue(preference.is_active)

        with mock.patch(
            'openedx.core.djangoapps.notifications.models.COURSE_NOTIFICATION_CONFIG_VERSION',
            COURSE_NOTIFICATION_CONFIG_VERSION + 1
        ):
            updated_preferences = preference.get_user_notification_preferences(user)
            for updated_preference in updated_preferences:
                assert updated_preference.config_version == COURSE_NOTIFICATION_CONFIG_VERSION + 1
