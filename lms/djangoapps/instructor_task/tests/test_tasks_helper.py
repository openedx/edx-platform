# -*- coding: utf-8 -*-

"""
Unit tests for LMS instructor-initiated background tasks helper functions.

Tests that CSV grade report generation works with unicode emails.

"""
import ddt
from mock import Mock, patch
import tempfile
import unicodecsv

from xmodule.modulestore.tests.factories import CourseFactory
from student.tests.factories import UserFactory
from student.models import CourseEnrollment
from xmodule.partitions.partitions import Group, UserPartition

from openedx.core.djangoapps.course_groups.models import CourseUserGroupPartitionGroup
from openedx.core.djangoapps.course_groups.tests.helpers import CohortFactory
import openedx.core.djangoapps.user_api.course_tag.api as course_tag_api
from openedx.core.djangoapps.user_api.partition_schemes import RandomUserPartitionScheme
from instructor_task.models import ReportStore
from instructor_task.tasks_helper import cohort_students_and_upload, upload_grades_csv, upload_students_csv
from instructor_task.tests.test_base import InstructorTaskCourseTestCase, TestReportMixin


@ddt.ddt
class TestInstructorGradeReport(TestReportMixin, InstructorTaskCourseTestCase):
    """
    Tests that CSV grade report generation works.
    """
    def setUp(self):
        super(TestInstructorGradeReport, self).setUp()
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

    def _verify_cell_data_for_user(self, username, course_id, column_header, expected_cell_content):
        """
        Verify cell data in the grades CSV for a particular user.
        """
        with patch('instructor_task.tasks_helper._get_current_task'):
            result = upload_grades_csv(None, None, course_id, None, 'graded')
            self.assertDictContainsSubset({'attempted': 2, 'succeeded': 2, 'failed': 0}, result)
            report_store = ReportStore.from_config()
            report_csv_filename = report_store.links_for(course_id)[0][0]
            with open(report_store.path_to(course_id, report_csv_filename)) as csv_file:
                for row in unicodecsv.DictReader(csv_file):
                    if row.get('username') == username:
                        self.assertEqual(row[column_header], expected_cell_content)

    def test_cohort_data_in_grading(self):
        """
        Test that cohort data is included in grades csv if cohort configuration is enabled for course.
        """
        cohort_groups = ['cohort 1', 'cohort 2']
        course = CourseFactory.create(cohort_config={'cohorted': True, 'auto_cohort': True,
                                                     'auto_cohort_groups': cohort_groups})

        user_1 = 'user_1'
        user_2 = 'user_2'
        CourseEnrollment.enroll(UserFactory.create(username=user_1), course.id)
        CourseEnrollment.enroll(UserFactory.create(username=user_2), course.id)

        # In auto cohorting a group will be assigned to a user only when user visits a problem
        # In grading calculation we only add a group in csv if group is already assigned to
        # user rather than creating a group automatically at runtime
        self._verify_cell_data_for_user(user_1, course.id, 'Cohort Name', '')
        self._verify_cell_data_for_user(user_2, course.id, 'Cohort Name', '')

    def test_unicode_cohort_data_in_grading(self):
        """
        Test that cohorts can contain unicode characters.
        """
        course = CourseFactory.create(cohort_config={'cohorted': True})

        # Create users and manually assign cohorts
        user1 = UserFactory.create(username='user1')
        user2 = UserFactory.create(username='user2')
        CourseEnrollment.enroll(user1, course.id)
        CourseEnrollment.enroll(user2, course.id)
        professor_x = u'ÞrÖfessÖr X'
        magneto = u'MàgnëtÖ'
        cohort1 = CohortFactory(course_id=course.id, name=professor_x)
        cohort2 = CohortFactory(course_id=course.id, name=magneto)
        cohort1.users.add(user1)
        cohort2.users.add(user2)

        self._verify_cell_data_for_user(user1.username, course.id, 'Cohort Name', professor_x)
        self._verify_cell_data_for_user(user2.username, course.id, 'Cohort Name', magneto)

    def test_unicode_user_partitions(self):
        """
        Test that user partition groups can contain unicode characters.
        """
        user_groups = [u'ÞrÖfessÖr X', u'MàgnëtÖ']
        user_partition = UserPartition(
            0,
            'x_man',
            'X Man',
            [
                Group(0, user_groups[0]),
                Group(1, user_groups[1])
            ]
        )

        # Create course with group configurations
        self.initialize_course(
            course_factory_kwargs={
                'user_partitions': [user_partition]
            }
        )

        _groups = [group.name for group in self.course.user_partitions[0].groups]
        self.assertEqual(_groups, user_groups)

    def test_cohort_scheme_partition(self):
        """
        Test that cohort-schemed user partitions are ignored in the
        grades export.
        """
        # Set up a course with 'cohort' and 'random' user partitions.
        cohort_scheme_partition = UserPartition(
            0,
            'Cohort-schemed Group Configuration',
            'Group Configuration based on Cohorts',
            [Group(0, 'Group A'), Group(1, 'Group B')],
            scheme_id='cohort'
        )
        experiment_group_a = Group(2, u'Expériment Group A')
        experiment_group_b = Group(3, u'Expériment Group B')
        experiment_partition = UserPartition(
            1,
            u'Content Expériment Configuration',
            u'Group Configuration for Content Expériments',
            [experiment_group_a, experiment_group_b],
            scheme_id='random'
        )
        course = CourseFactory.create(
            cohort_config={'cohorted': True},
            user_partitions=[cohort_scheme_partition, experiment_partition]
        )

        # Create user_a and user_b which are enrolled in the course
        # and assigned to experiment_group_a and experiment_group_b,
        # respectively.
        user_a = UserFactory.create(username='user_a')
        user_b = UserFactory.create(username='user_b')
        CourseEnrollment.enroll(user_a, course.id)
        CourseEnrollment.enroll(user_b, course.id)
        course_tag_api.set_course_tag(
            user_a,
            course.id,
            RandomUserPartitionScheme.key_for_partition(experiment_partition),
            experiment_group_a.id
        )
        course_tag_api.set_course_tag(
            user_b,
            course.id,
            RandomUserPartitionScheme.key_for_partition(experiment_partition),
            experiment_group_b.id
        )

        # Assign user_a to a group in the 'cohort'-schemed user
        # partition (by way of a cohort) to verify that the user
        # partition group does not show up in the "Experiment Group"
        # cell.
        cohort_a = CohortFactory.create(course_id=course.id, name=u'Cohørt A', users=[user_a])
        CourseUserGroupPartitionGroup(
            course_user_group=cohort_a,
            partition_id=cohort_scheme_partition.id,
            group_id=cohort_scheme_partition.groups[0].id
        ).save()

        # Verify that we see user_a and user_b in their respective
        # content experiment groups, and that we do not see any
        # content groups.
        experiment_group_message = u'Experiment Group ({content_experiment})'
        self._verify_cell_data_for_user(
            user_a.username,
            course.id,
            experiment_group_message.format(
                content_experiment=experiment_partition.name
            ),
            experiment_group_a.name
        )
        self._verify_cell_data_for_user(
            user_b.username,
            course.id,
            experiment_group_message.format(
                content_experiment=experiment_partition.name
            ),
            experiment_group_b.name
        )

        # Make sure cohort info is correct.
        cohort_name_header = 'Cohort Name'
        self._verify_cell_data_for_user(
            user_a.username,
            course.id,
            cohort_name_header,
            cohort_a.name
        )
        self._verify_cell_data_for_user(
            user_b.username,
            course.id,
            cohort_name_header,
            ''
        )

    @patch('instructor_task.tasks_helper._get_current_task')
    @patch('instructor_task.tasks_helper.iterate_grades_for')
    def test_unicode_in_csv_header(self, mock_iterate_grades_for, _mock_current_task):
        """
        Tests that CSV grade report works if unicode in headers.
        """
        # mock a response from `iterate_grades_for`
        mock_iterate_grades_for.return_value = [
            (
                self.create_student('username', 'student@example.com'),
                {'section_breakdown': [{'label': u'\u8282\u540e\u9898 01'}], 'percent': 0},
                'Cannot grade student'
            )
        ]
        result = upload_grades_csv(None, None, self.course.id, None, 'graded')
        self.assertDictContainsSubset({'attempted': 1, 'succeeded': 1, 'failed': 0}, result)


@ddt.ddt
class TestStudentReport(TestReportMixin, InstructorTaskCourseTestCase):
    """
    Tests that CSV student profile report generation works.
    """
    def setUp(self):
        super(TestStudentReport, self).setUp()
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
        super(TestCohortStudents, self).setUp()

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
