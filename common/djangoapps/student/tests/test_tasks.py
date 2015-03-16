"""
Test for student tasks.
"""

from student.tasks import publish_course_notifications_task
from student.tests.factories import UserFactory, CourseEnrollmentFactory
from edx_notifications.data import NotificationMessage
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory
from edx_notifications.lib.publisher import get_notification_type
from xmodule.modulestore.django import modulestore
from edx_notifications.lib.consumer import get_notifications_count_for_user
from mock import patch
from lms import startup


class StudentTasksTestCase(ModuleStoreTestCase):
    """
    Tests of student.roles
    """

    def setUp(self):
        super(StudentTasksTestCase, self).setUp()
        self.course = CourseFactory.create()

    @patch.dict("django.conf.settings.FEATURES", {"ENABLE_NOTIFICATIONS": True})
    def test_course_bulk_notification_tests(self):
        # create new users and enroll them in the course.
        startup.startup_notification_subsystem()

        test_user_1 = UserFactory.create(password='test_pass')
        CourseEnrollmentFactory(user=test_user_1, course_id=self.course.id)
        test_user_2 = UserFactory.create(password='test_pass')
        CourseEnrollmentFactory(user=test_user_2, course_id=self.course.id)

        notification_type = get_notification_type(u'open-edx.studio.announcements.new-announcement')
        course = modulestore().get_course(self.course.id, depth=0)
        notification_msg = NotificationMessage(
            msg_type=notification_type,
            namespace=unicode(self.course.id),
            payload={
                '_schema_version': '1',
                'course_name': course.display_name,

            }
        )
        # Send the notification_msg to the Celery task
        publish_course_notifications_task.delay(self.course.id, notification_msg)

        # now the enrolled users should get notification about the
        # course update where they are enrolled as student.
        self.assertTrue(get_notifications_count_for_user(test_user_1.id), 1)
        self.assertTrue(get_notifications_count_for_user(test_user_2.id), 1)
