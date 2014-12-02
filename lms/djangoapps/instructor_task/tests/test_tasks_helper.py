"""
Unit tests for LMS instructor-initiated background tasks helper functions.

Tests that CSV grade report generation works with unicode emails.

"""
import os
import shutil
from datetime import datetime
import urllib

import ddt
from mock import Mock, patch

from django.conf import settings
from django.test.testcases import TestCase
from pytz import UTC

from xmodule.modulestore.tests.factories import CourseFactory

from student.tests.factories import CourseEnrollmentFactory, UserFactory

from instructor_task.tasks_helper import (
    push_grades_to_s3,
    push_ora2_responses_to_s3,
    UPDATE_STATUS_FAILED,
    UPDATE_STATUS_SUCCEEDED,
)


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


class TestInstructorOra2Report(TestCase):
    """
    Tests that ORA2 response report generation works.
    """
    def setUp(self):
        self.course = CourseFactory.create(org=TEST_COURSE_ORG,
                                           number=TEST_COURSE_NUMBER,
                                           display_name=TEST_COURSE_NAME)

        self.current_task = Mock()
        self.current_task.update_state = Mock()

    def tearDown(self):
        if os.path.exists(settings.ORA2_RESPONSES_DOWNLOAD['ROOT_PATH']):
            shutil.rmtree(settings.ORA2_RESPONSES_DOWNLOAD['ROOT_PATH'])

    def test_report_fails_if_error(self):
        with patch('instructor_task.tasks_helper.collect_ora2_data') as mock_collect_data:
            mock_collect_data.side_effect = KeyError

            with patch('instructor_task.tasks_helper._get_current_task') as mock_current_task:
                mock_current_task.return_value = self.current_task

                self.assertEqual(push_ora2_responses_to_s3(None, None, self.course.id, None, 'generated'), UPDATE_STATUS_FAILED)

    @patch('instructor_task.tasks_helper.datetime')
    def test_report_stores_results(self, mock_time):
        start_time = datetime.now(UTC)
        mock_time.now.return_value = start_time

        test_header = ['field1', 'field2']
        test_rows = [['row1_field1', 'row1_field2'], ['row2_field1', 'row2_field2']]

        with patch('instructor_task.tasks_helper._get_current_task') as mock_current_task:
            mock_current_task.return_value = self.current_task

            with patch('instructor_task.tasks_helper.collect_ora2_data') as mock_collect_data:
                mock_collect_data.return_value = (test_header, test_rows)

                with patch('instructor_task.models.LocalFSReportStore.store_rows') as mock_store_rows:
                    return_val = push_ora2_responses_to_s3(None, None, self.course.id, None, 'generated')

                    timestamp_str = start_time.strftime('%Y-%m-%d-%H%M')
                    course_id_string = urllib.quote(self.course.id.to_deprecated_string().replace('/', '_'))
                    filename = u'{}_ORA2_responses_{}.csv'.format(course_id_string, timestamp_str)

                    self.assertEqual(return_val, UPDATE_STATUS_SUCCEEDED)
                    mock_store_rows.assert_called_once_with(self.course.id, filename, [test_header] + test_rows)
