"""
Unit tests for LMS instructor-initiated background tasks helper functions.

Tests that CSV grade report generation works with unicode emails.

"""
import ddt
from mock import Mock, patch
import tempfile

from xmodule.modulestore.tests.factories import CourseFactory

from openedx.core.djangoapps.course_groups.tests.helpers import CohortFactory
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


class MockDefaultStorage(object):
    """Mock django's DefaultStorage"""
    def __init__(self):
        pass

    def open(self, file_name):
        """Mock out DefaultStorage.open with standard python open"""
        return open(file_name)


@patch('instructor_task.tasks_helper.DefaultStorage', new=MockDefaultStorage)
class TestCohortStudents(TestReportMixin, InstructorTaskCourseTestCase):
    """
    Tests that bulk student cohorting works.
    """
    def setUp(self):
        self.course = CourseFactory.create()
        self.cohort_1 = CohortFactory(course_id=self.course.id, name='Cohort 1')
        self.cohort_2 = CohortFactory(course_id=self.course.id, name='Cohort 2')
        self.student_1 = self.create_student(username=u'student_1\xec', email='student_1@example.com')
        self.student_2 = self.create_student(username='student_2', email='student_2@example.com')
        self.csv_header_row = ['Cohort Name', 'Exists', 'Students Added', 'Students Not Found']

    def _cohort_students_and_upload(self, csv_data):
        """
        Call `cohort_students_and_upload` with a file generated from `csv_data`.
        """
        with tempfile.NamedTemporaryFile() as temp_file:
            temp_file.write(csv_data.encode('utf-8'))
            temp_file.flush()
            with patch('instructor_task.tasks_helper._get_current_task'):
                return cohort_students_and_upload(None, None, self.course.id, {'file_name': temp_file.name}, 'cohorted')

    def test_username(self):
        result = self._cohort_students_and_upload(
            u'username,email,cohort\n'
            u'student_1\xec,,Cohort 1\n'
            u'student_2,,Cohort 2'
        )
        self.assertDictContainsSubset({'total': 2, 'attempted': 2, 'succeeded': 2, 'failed': 0}, result)
        self.verify_rows_in_csv(
            [
                dict(zip(self.csv_header_row, ['Cohort 1', 'True', '1', ''])),
                dict(zip(self.csv_header_row, ['Cohort 2', 'True', '1', ''])),
            ],
            verify_order=False
        )

    def test_email(self):
        result = self._cohort_students_and_upload(
            'username,email,cohort\n'
            ',student_1@example.com,Cohort 1\n'
            ',student_2@example.com,Cohort 2'
        )
        self.assertDictContainsSubset({'total': 2, 'attempted': 2, 'succeeded': 2, 'failed': 0}, result)
        self.verify_rows_in_csv(
            [
                dict(zip(self.csv_header_row, ['Cohort 1', 'True', '1', ''])),
                dict(zip(self.csv_header_row, ['Cohort 2', 'True', '1', ''])),
            ],
            verify_order=False
        )

    def test_username_and_email(self):
        result = self._cohort_students_and_upload(
            u'username,email,cohort\n'
            u'student_1\xec,student_1@example.com,Cohort 1\n'
            u'student_2,student_2@example.com,Cohort 2'
        )
        self.assertDictContainsSubset({'total': 2, 'attempted': 2, 'succeeded': 2, 'failed': 0}, result)
        self.verify_rows_in_csv(
            [
                dict(zip(self.csv_header_row, ['Cohort 1', 'True', '1', ''])),
                dict(zip(self.csv_header_row, ['Cohort 2', 'True', '1', ''])),
            ],
            verify_order=False
        )

    def test_prefer_email(self):
        """
        Test that `cohort_students_and_upload` greedily prefers 'email' over
        'username' when identifying the user.  This means that if a correct
        email is present, an incorrect or non-matching username will simply be
        ignored.
        """
        result = self._cohort_students_and_upload(
            u'username,email,cohort\n'
            u'student_1\xec,student_1@example.com,Cohort 1\n'  # valid username and email
            u'Invalid,student_2@example.com,Cohort 2'      # invalid username, valid email
        )
        self.assertDictContainsSubset({'total': 2, 'attempted': 2, 'succeeded': 2, 'failed': 0}, result)
        self.verify_rows_in_csv(
            [
                dict(zip(self.csv_header_row, ['Cohort 1', 'True', '1', ''])),
                dict(zip(self.csv_header_row, ['Cohort 2', 'True', '1', ''])),
            ],
            verify_order=False
        )

    def test_non_existent_user(self):
        result = self._cohort_students_and_upload(
            'username,email,cohort\n'
            'Invalid,,Cohort 1\n'
            'student_2,also_fake@bad.com,Cohort 2'
        )
        self.assertDictContainsSubset({'total': 2, 'attempted': 2, 'succeeded': 0, 'failed': 2}, result)
        self.verify_rows_in_csv(
            [
                dict(zip(self.csv_header_row, ['Cohort 1', 'True', '0', 'Invalid'])),
                dict(zip(self.csv_header_row, ['Cohort 2', 'True', '0', 'also_fake@bad.com'])),
            ],
            verify_order=False
        )

    def test_non_existent_cohort(self):
        result = self._cohort_students_and_upload(
            'username,email,cohort\n'
            ',student_1@example.com,Does Not Exist\n'
            'student_2,,Cohort 2'
        )
        self.assertDictContainsSubset({'total': 2, 'attempted': 2, 'succeeded': 1, 'failed': 1}, result)
        self.verify_rows_in_csv(
            [
                dict(zip(self.csv_header_row, ['Does Not Exist', 'False', '0', ''])),
                dict(zip(self.csv_header_row, ['Cohort 2', 'True', '1', ''])),
            ],
            verify_order=False
        )

    def test_too_few_commas(self):
        """
        A CSV file may be malformed and lack traling commas at the end of a row.
        In this case, those cells take on the value None by the CSV parser.
        Make sure we handle None values appropriately.

        i.e.:
            header_1,header_2,header_3
            val_1,val_2,val_3  <- good row
            val_1,,  <- good row
            val_1    <- bad row; no trailing commas to indicate empty rows
        """
        result = self._cohort_students_and_upload(
            u'username,email,cohort\n'
            u'student_1\xec,\n'
            u'student_2'
        )
        self.assertDictContainsSubset({'total': 2, 'attempted': 2, 'succeeded': 0, 'failed': 2}, result)
        self.verify_rows_in_csv(
            [
                dict(zip(self.csv_header_row, ['', 'False', '0', ''])),
            ],
            verify_order=False
        )

    def test_only_header_row(self):
        result = self._cohort_students_and_upload(
            u'username,email,cohort'
        )
        self.assertDictContainsSubset({'total': 0, 'attempted': 0, 'succeeded': 0, 'failed': 0}, result)
        self.verify_rows_in_csv([])

    def test_carriage_return(self):
        """
        Test that we can handle carriage returns in our file.
        """
        result = self._cohort_students_and_upload(
            u'username,email,cohort\r'
            u'student_1\xec,,Cohort 1\r'
            u'student_2,,Cohort 2'
        )
        self.assertDictContainsSubset({'total': 2, 'attempted': 2, 'succeeded': 2, 'failed': 0}, result)
        self.verify_rows_in_csv(
            [
                dict(zip(self.csv_header_row, ['Cohort 1', 'True', '1', ''])),
                dict(zip(self.csv_header_row, ['Cohort 2', 'True', '1', ''])),
            ],
            verify_order=False
        )

    def test_carriage_return_line_feed(self):
        """
        Test that we can handle carriage returns and line feeds in our file.
        """
        result = self._cohort_students_and_upload(
            u'username,email,cohort\r\n'
            u'student_1\xec,,Cohort 1\r\n'
            u'student_2,,Cohort 2'
        )
        self.assertDictContainsSubset({'total': 2, 'attempted': 2, 'succeeded': 2, 'failed': 0}, result)
        self.verify_rows_in_csv(
            [
                dict(zip(self.csv_header_row, ['Cohort 1', 'True', '1', ''])),
                dict(zip(self.csv_header_row, ['Cohort 2', 'True', '1', ''])),
            ],
            verify_order=False
        )

    def test_move_users_to_new_cohort(self):
        self.cohort_1.users.add(self.student_1)
        self.cohort_2.users.add(self.student_2)

        result = self._cohort_students_and_upload(
            u'username,email,cohort\n'
            u'student_1\xec,,Cohort 2\n'
            u'student_2,,Cohort 1'
        )
        self.assertDictContainsSubset({'total': 2, 'attempted': 2, 'succeeded': 2, 'failed': 0}, result)
        self.verify_rows_in_csv(
            [
                dict(zip(self.csv_header_row, ['Cohort 1', 'True', '1', ''])),
                dict(zip(self.csv_header_row, ['Cohort 2', 'True', '1', ''])),
            ],
            verify_order=False
        )

    def test_move_users_to_same_cohort(self):
        self.cohort_1.users.add(self.student_1)
        self.cohort_2.users.add(self.student_2)

        result = self._cohort_students_and_upload(
            u'username,email,cohort\n'
            u'student_1\xec,,Cohort 1\n'
            u'student_2,,Cohort 2'
        )
        self.assertDictContainsSubset({'total': 2, 'attempted': 2, 'skipped': 2, 'failed': 0}, result)
        self.verify_rows_in_csv(
            [
                dict(zip(self.csv_header_row, ['Cohort 1', 'True', '0', ''])),
                dict(zip(self.csv_header_row, ['Cohort 2', 'True', '0', ''])),
            ],
            verify_order=False
        )
