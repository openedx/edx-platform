"""
Unit tests for LMS instructor-initiated background tasks helper functions.

Tests that CSV grade report generation works with unicode emails.

"""
import ddt
from mock import Mock, patch
import tempfile

from xmodule.modulestore.tests.factories import CourseFactory

from course_groups.tests.helpers import CohortFactory
from instructor_task.models import ReportStore
from instructor_task.tasks_helper import cohort_students_and_upload, upload_grades_csv, upload_students_csv
from instructor_task.tests.test_base import InstructorTaskCourseTestCase, TestReportMixin


@ddt.ddt
class TestInstructorGradeReport(TestReportMixin, InstructorTaskCourseTestCase):
    """
    Tests that CSV grade report generation works.
    """
    def setUp(self):
        self.course = CourseFactory.create()

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
            result = upload_grades_csv(None, None, self.course.id, None, 'graded')
        num_students = len(emails)
        self.assertDictContainsSubset({'attempted': num_students, 'succeeded': num_students, 'failed': 0}, result)

    @patch('instructor_task.tasks_helper._get_current_task')
    @patch('instructor_task.tasks_helper.iterate_grades_for')
    def test_grading_failure(self, mock_iterate_grades_for, _mock_current_task):
        """
        Test that any grading errors are properly reported in the
        progress dict and uploaded to the report store.
        """
        # mock an error response from `iterate_grades_for`
        mock_iterate_grades_for.return_value = [
            (self.create_student('username', 'student@example.com'), {}, 'Cannot grade student')
        ]
        result = upload_grades_csv(None, None, self.course.id, None, 'graded')
        self.assertDictContainsSubset({'attempted': 1, 'succeeded': 0, 'failed': 1}, result)

        report_store = ReportStore.from_config()
        self.assertTrue(any('grade_report_err' in item[0] for item in report_store.links_for(self.course.id)))


@ddt.ddt
class TestStudentReport(TestReportMixin, InstructorTaskCourseTestCase):
    """
    Tests that CSV student profile report generation works.
    """
    def setUp(self):
        self.course = CourseFactory.create()

    def test_success(self):
        self.create_student('student', 'student@example.com')
        task_input = {'features': []}
        with patch('instructor_task.tasks_helper._get_current_task'):
            result = upload_students_csv(None, None, self.course.id, task_input, 'calculated')
        report_store = ReportStore.from_config()
        links = report_store.links_for(self.course.id)

        self.assertEquals(len(links), 1)
        self.assertDictContainsSubset({'attempted': 1, 'succeeded': 1, 'failed': 0}, result)

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
            result = upload_students_csv(None, None, self.course.id, task_input, 'calculated')
        #This assertion simply confirms that the generation completed with no errors
        num_students = len(students)
        self.assertDictContainsSubset({'attempted': num_students, 'succeeded': num_students, 'failed': 0}, result)


class TestCohortStudents(TestReportMixin, InstructorTaskCourseTestCase):
    """
    Tests that bulk student cohorting works.
    """
    def setUp(self):
        self.course = CourseFactory.create()
        self.cohort_1 = CohortFactory(course_id=self.course.id, name='Cohort 1')
        self.cohort_2 = CohortFactory(course_id=self.course.id, name='Cohort 2')
        self.student_1 = self.create_student(username='student_1', email='student_1@example.com')
        self.student_2 = self.create_student(username='student_2', email='student_2@example.com')

    def _cohort_students_and_upload(self, csv_rows):
        """
        Call `cohort_students_and_upload` with a file generated from `csv_rows`.
        """
        with tempfile.NamedTemporaryFile() as fp:
            fp.write(('\n'.join([','.join(row) for row in csv_rows])).encode('utf-8'))
            fp.flush()
            with patch('instructor_task.tasks_helper._get_current_task'):
                return cohort_students_and_upload(None, None, self.course.id, {'file_name': fp.name}, 'cohorted')

    @patch('instructor_task.tasks_helper.DefaultStorage')
    def test_success(self, mock_default_storage):
        # Mock out DefaultStorage's scoped `open` method with standard python
        # `open` so that we can read from /tmp/
        mock_default_storage.return_value = Mock()
        mock_default_storage.return_value.open = open

        result = self._cohort_students_and_upload(
            [
                ['username', 'cohort'],
                ['student_1', 'Cohort 1'],
                ['student_2', 'Cohort 2']
            ]
        )
        self.assertDictContainsSubset({'attempted': 2, 'succeeded': 2, 'failed': 0}, result)
