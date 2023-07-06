"""
Tests for notifications tasks.
"""
from unittest.mock import patch

from common.djangoapps.student.tests.factories import UserFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

from ..models import CourseNotificationPreference
from ..tasks import create_notification_pref_if_not_exists, update_user_preference


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

    def test_create_notification_pref_if_not_exists(self):
        """
        Test whether create_notification_pref_if_not_exists creates a new preference if it doesn't exist.
        """
        # Test whether create_notification_pref_if_not_exists creates a new preference if it doesn't exist
        user_ids = [self.user.id, self.user_1.id, self.user_2.id]
        preferences = [self.preference_v2]
        updated_preferences = create_notification_pref_if_not_exists(user_ids, preferences)
        self.assertEqual(len(updated_preferences), 3)  # Should have created two new preferences

        # Test whether create_notification_pref_if_not_exists doesn't create a new preference if it already exists
        updated_preferences = create_notification_pref_if_not_exists(user_ids, preferences)
        self.assertEqual(len(updated_preferences), 3)  # No new preferences should be created this time
