"""
Test for generate_notification_preferences management command.
"""

from unittest import mock

from django.core.management import call_command

from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase


class GenerateCourseNotificationPreferencesTests(ModuleStoreTestCase):
    """
    Tests for generate_course_notification_preferences management command.
    """

    def setUp(self):
        super().setUp()
        self.course_ids = ['course-v1:edX+DemoX.1+2T2017', 'course-v1:edX+DemoX.1+2T2018']

    @mock.patch(
        'openedx.core.djangoapps.notifications.tasks.create_course_notification_preferences_for_courses'
    )
    def test_generate_course_notification_preferences(self, mock_task):
        """
        Test generate_course_notification_preferences command.
        """
        call_command(
            'generate_course_notification_preferences',
            self.course_ids,
        )
        mock_task.delay.assert_called_once_with(self.course_ids)
