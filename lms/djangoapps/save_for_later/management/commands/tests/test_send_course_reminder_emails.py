""" Test the test_send_course_reminder_emails command line script."""

from unittest.mock import patch

import ddt
from django.core.management import call_command
from django.test.utils import override_settings
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase

from openedx.core.djangolib.testing.utils import skip_unless_lms
from common.djangoapps.student.tests.factories import UserFactory
from lms.djangoapps.save_for_later.tests.factories import SavedCourseFactory
from lms.djangoapps.save_for_later.models import SavedCourse
from openedx.core.djangoapps.content.course_overviews.tests.factories import CourseOverviewFactory


@ddt.ddt
@skip_unless_lms
class SavedCourseReminderEmailsTest(SharedModuleStoreTestCase):
    """
    Test the test_send_course_reminder_emails management command
    """

    def setUp(self):
        super().setUp()
        self.course_id = 'course-v1:edX+DemoX+Demo_Course'
        self.user = UserFactory(email='email@test.com', username='jdoe')
        self.saved_course = SavedCourseFactory.create(course_id=self.course_id, user_id=self.user.id)
        self.saved_course_1 = SavedCourseFactory.create(course_id=self.course_id)
        CourseOverviewFactory.create(id=self.saved_course.course_id)
        CourseOverviewFactory.create(id=self.saved_course_1.course_id)

    @override_settings(
        EDX_BRAZE_API_KEY='test-key',
        EDX_BRAZE_API_SERVER='http://test.url'
    )
    def test_send_reminder_emails(self):
        with patch('lms.djangoapps.utils.BrazeClient') as mock_task:
            call_command('send_course_reminder_emails', '--batch-size=1')
            mock_task.assert_called()

        saved_course = SavedCourse.objects.filter(course_id=self.course_id).first()
        assert saved_course.reminder_email_sent is True
        assert saved_course.email_sent_count > 0
