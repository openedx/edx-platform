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

from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

from student.tests.factories import CourseEnrollmentFactory, UserFactory

from instructor_task.models import ReportStore
from instructor_task.tasks_helper import push_grades_to_s3, push_students_csv_to_s3, UPDATE_STATUS_SUCCEEDED


class TestReport(ModuleStoreTestCase):
    """
    Base class for testing CSV download tasks.
    """
    def setUp(self):
        self.course = CourseFactory.create()

    def tearDown(self):
        if os.path.exists(settings.GRADES_DOWNLOAD['ROOT_PATH']):
            shutil.rmtree(settings.GRADES_DOWNLOAD['ROOT_PATH'])

    def create_student(self, username, email):
        student = UserFactory.create(username=username, email=email)
        CourseEnrollmentFactory.create(user=student, course_id=self.course.id)


@ddt.ddt
class TestInstructorGradeReport(TestReport):
    """
    Tests that CSV grade report generation works.
    """
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


@ddt.ddt
class TestStudentReport(TestReport):
    """
    Tests that CSV student profile report generation works.
    """
    def test_success(self):
        task_input = {'features': []}
        with patch('instructor_task.tasks_helper._get_current_task'):
            result = push_students_csv_to_s3(None, None, self.course.id, task_input, 'calculated')
        report_store = ReportStore.from_config()
        links = report_store.links_for(self.course.id)

        self.assertEquals(len(links), 1)
        self.assertEquals(result, UPDATE_STATUS_SUCCEEDED)

    @ddt.data([u'student', u'student\xec'])
    def test_unicode_usernames(self, students):
        """
        Test that students with unicode characters in their usernames
        are handled.
        """
        for i, student in enumerate(students):
            self.create_student(username=student, email='student{0}@example.com'.format(i))

        self.current_task = Mock()
        self.current_task.update_state = Mock()
        task_input = {
            'features': [
                'id', 'username', 'name', 'email', 'language', 'location',
                'year_of_birth', 'gender', 'level_of_education', 'mailing_address',
                'goals'
            ]
        }
        with patch('instructor_task.tasks_helper._get_current_task') as mock_current_task:
            mock_current_task.return_value = self.current_task
            result = push_students_csv_to_s3(None, None, self.course.id, task_input, 'calculated')
        #This assertion simply confirms that the generation completed with no errors
        self.assertEquals(result, UPDATE_STATUS_SUCCEEDED)
