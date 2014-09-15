"""
Unit tests for LMS instructor-initiated background tasks helper functions.

Tests that CSV grade report generation works with unicode emails.

"""
import os
import shutil

import ddt
from mock import Mock, patch

from django.conf import settings
from django.test.testcases import TestCase

from xmodule.modulestore.tests.factories import CourseFactory

from student.tests.factories import CourseEnrollmentFactory, UserFactory

from instructor_task.tasks_helper import push_grades_to_s3


TEST_COURSE_ORG = 'edx'
TEST_COURSE_NAME = 'test_course'
TEST_COURSE_NUMBER = '1.23x'


@ddt.ddt
class TestInstructorGradeReport(TestCase):
    """
    Tests that CSV grade report generation works.
    """
    def setUp(self):
        self.course = CourseFactory.create(org=TEST_COURSE_ORG,
                                           number=TEST_COURSE_NUMBER,
                                           display_name=TEST_COURSE_NAME)

    def tearDown(self):
        if os.path.exists(settings.GRADES_DOWNLOAD['ROOT_PATH']):
            shutil.rmtree(settings.GRADES_DOWNLOAD['ROOT_PATH'])

    def create_student(self, username, email):
        student = UserFactory.create(username=username, email=email)
        CourseEnrollmentFactory.create(user=student, course_id=self.course.id)

    @ddt.data([u'student@example.com', u'ni\xf1o@example.com'])
    def test_unicode_emails(self, emails):
        """
        Test that students with unicode characters in emails is handled.
        """
        for i, email in enumerate(emails):
            self.create_student('student{0}'.format(i), email)

        self.current_task = Mock()
        self.current_task.update_state = Mock()
        with patch('instructor_task.tasks_helper._get_current_task') as mock_current_task:
            mock_current_task.return_value = self.current_task
            result = push_grades_to_s3(None, None, self.course.id, None, 'graded')
        #This assertion simply confirms that the generation completed with no errors
        self.assertEquals(result['succeeded'], result['attempted'])
