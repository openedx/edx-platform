from __future__ import absolute_import

from tempfile import NamedTemporaryFile

from django.core.management import call_command
from testfixtures import LogCapture

from openedx.core.djangoapps.course_modes.tests.factories import CourseModeFactory
from student.models import CourseEnrollment
from student.tests.factories import UserFactory
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

LOGGER_NAME = 'student.management.commands.bulk_unenroll'


class BulkUnenrollTests(SharedModuleStoreTestCase):
    """Test Bulk un-enroll command works fine for all test cases."""
    def setUp(self):
        super(BulkUnenrollTests, self).setUp()
        self.course = CourseFactory.create()
        self.audit_mode = CourseModeFactory.create(
            course_id=self.course.id,
            mode_slug='audit',
            mode_display_name='Audit',
        )

        self.user_info = [
            ('amy', 'amy@pond.com', 'password'),
            ('rory', 'rory@theroman.com', 'password'),
            ('river', 'river@song.com', 'password')
        ]
        self.enrollments = []
        self.users = []

        for username, email, password in self.user_info:
            user = UserFactory.create(username=username, email=email, password=password)
            self.users.append(user)
            self.enrollments.append(CourseEnrollment.enroll(user, self.course.id, mode='audit'))

    def _write_test_csv(self, csv, lines=None):
        """Write a test csv file with the lines procided"""
        csv.write("user_id,username,email,course_id\n")
        csv.writelines(lines)
        csv.seek(0)
        return csv

    def test_user_not_exist(self):
        """Verify that warning user not exist is logged for non existing user."""
        with NamedTemporaryFile() as csv:
            csv = self._write_test_csv(csv, lines="111,test,test@example.com,course-v1:edX+DemoX+Demo_Course\n")

            with LogCapture(LOGGER_NAME) as log:
                call_command("bulk_unenroll", "--csv_path={}".format(csv.name))
                log.check(
                    (
                        LOGGER_NAME,
                        'WARNING',
                        'User with username {} or email {} does not exist'.format('test', 'test@example.com')
                    )
                )

    def test_invalid_course_key(self):
        """Verify in case of invalid course key warning is logged."""
        with NamedTemporaryFile() as csv:
            csv = self._write_test_csv(csv, lines="111,amy,amy@pond.com,test_course\n")

            with LogCapture(LOGGER_NAME) as log:
                call_command("bulk_unenroll", "--csv_path={}".format(csv.name))
                log.check(
                    (
                        LOGGER_NAME,
                        'WARNING',
                        'Invalid course id {}, skipping un-enrollement for {}, {}'.format(
                            'test_course', 'amy', 'amy@pond.com')
                    )
                )

    def test_user_not_enrolled(self):
        """Verify in case of user not enrolled in course warning is logged."""
        with NamedTemporaryFile() as csv:
            csv = self._write_test_csv(csv, lines="111,amy,amy@pond.com,course-v1:edX+DemoX+Demo_Course\n")

            with LogCapture(LOGGER_NAME) as log:
                call_command("bulk_unenroll", "--csv_path={}".format(csv.name))
                log.check(
                    (
                        LOGGER_NAME,
                        'INFO',
                        'Enrollment for the user {} in course {} does not exist!'.format(
                            'amy', 'course-v1:edX+DemoX+Demo_Course')
                    )
                )

    def test_bulk_un_enroll(self):
        """Verify users are unenrolled using the command."""
        lines = (str(enrollment.user.id) + "," + enrollment.user.username + "," +
                 enrollment.user.email + "," + str(enrollment.course.id) + "\n"
                 for enrollment in self.enrollments)
        with NamedTemporaryFile() as csv:
            csv = self._write_test_csv(csv, lines=lines)\

            call_command("bulk_unenroll", "--csv_path={}".format(csv.name))
            for enrollment in CourseEnrollment.objects.all():
                self.assertEqual(enrollment.is_active, False)
