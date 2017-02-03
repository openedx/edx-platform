"""
Tests for reset_grades management command.
"""
from datetime import datetime, timedelta
import ddt
from django.core.management.base import CommandError
from django.test import TestCase
from freezegun import freeze_time
from mock import patch, MagicMock

from lms.djangoapps.grades.management.commands import reset_grades
from lms.djangoapps.grades.models import PersistentSubsectionGrade, PersistentCourseGrade
from opaque_keys.edx.locator import CourseLocator, BlockUsageLocator


@ddt.ddt
class TestResetGrades(TestCase):
    """
    Tests generate course blocks management command.
    """
    num_users = 3
    num_courses = 5
    num_subsections = 7

    def setUp(self):
        super(TestResetGrades, self).setUp()
        self.command = reset_grades.Command()

        self.user_ids = [user_id for user_id in range(self.num_users)]

        self.course_keys = []
        for course_index in range(self.num_courses):
            self.course_keys.append(
                CourseLocator(
                    org='some_org',
                    course='some_course',
                    run=unicode(course_index),
                )
            )

        self.subsection_keys_by_course = {}
        for course_key in self.course_keys:
            subsection_keys_in_course = []
            for subsection_index in range(self.num_subsections):
                subsection_keys_in_course.append(
                    BlockUsageLocator(
                        course_key=course_key,
                        block_type='sequential',
                        block_id=unicode(subsection_index),
                    )
                )
            self.subsection_keys_by_course[course_key] = subsection_keys_in_course

    def _update_or_create_grades(self, courses_keys=None):
        """
        Creates grades for all courses and subsections.
        """
        if courses_keys is None:
            courses_keys = self.course_keys

        course_grade_params = {
            "course_version": "JoeMcEwing",
            "course_edited_timestamp": datetime(
                year=2016,
                month=8,
                day=1,
                hour=18,
                minute=53,
                second=24,
                microsecond=354741,
            ),
            "percent_grade": 77.7,
            "letter_grade": "Great job",
            "passed": True,
        }
        subsection_grade_params = {
            "course_version": "deadbeef",
            "subtree_edited_timestamp": "2016-08-01 18:53:24.354741",
            "earned_all": 6.0,
            "possible_all": 12.0,
            "earned_graded": 6.0,
            "possible_graded": 8.0,
            "visible_blocks": MagicMock(),
            "attempted": True,
        }

        for course_key in courses_keys:
            for user_id in self.user_ids:
                course_grade_params['user_id'] = user_id
                course_grade_params['course_id'] = course_key
                PersistentCourseGrade.update_or_create_course_grade(**course_grade_params)
                for subsection_key in self.subsection_keys_by_course[course_key]:
                    subsection_grade_params['user_id'] = user_id
                    subsection_grade_params['usage_key'] = subsection_key
                    PersistentSubsectionGrade.update_or_create_grade(**subsection_grade_params)

    def _assert_grades_exist_for_courses(self, course_keys):
        """
        Assert grades for given courses exist.
        """
        for course_key in course_keys:
            self.assertIsNotNone(PersistentCourseGrade.read_course_grade(self.user_ids[0], course_key))
            for subsection_key in self.subsection_keys_by_course[course_key]:
                self.assertIsNotNone(PersistentSubsectionGrade.read_grade(self.user_ids[0], subsection_key))

    def _assert_grades_absent_for_courses(self, course_keys):
        """
        Assert grades for given courses do not exist.
        """
        for course_key in course_keys:
            with self.assertRaises(PersistentCourseGrade.DoesNotExist):
                PersistentCourseGrade.read_course_grade(self.user_ids[0], course_key)

            for subsection_key in self.subsection_keys_by_course[course_key]:
                with self.assertRaises(PersistentSubsectionGrade.DoesNotExist):
                    PersistentSubsectionGrade.read_grade(self.user_ids[0], subsection_key)

    def _assert_stat_logged(self, mock_log, num_rows, grade_model_class, message_substring, log_offset):
        self.assertIn('reset_grade: ' + message_substring, mock_log.info.call_args_list[log_offset][0][0])
        self.assertEqual(grade_model_class.__name__, mock_log.info.call_args_list[log_offset][0][1])
        self.assertEqual(num_rows, mock_log.info.call_args_list[log_offset][0][2])

    def _assert_course_delete_stat_logged(self, mock_log, num_rows):
        self._assert_stat_logged(mock_log, num_rows, PersistentCourseGrade, 'Deleted', log_offset=4)

    def _assert_subsection_delete_stat_logged(self, mock_log, num_rows):
        self._assert_stat_logged(mock_log, num_rows, PersistentSubsectionGrade, 'Deleted', log_offset=2)

    def _assert_course_query_stat_logged(self, mock_log, num_rows, num_courses=None):
        if num_courses is None:
            num_courses = self.num_courses
        log_offset = num_courses + 1 + num_courses + 1
        self._assert_stat_logged(mock_log, num_rows, PersistentCourseGrade, 'Would delete', log_offset)

    def _assert_subsection_query_stat_logged(self, mock_log, num_rows, num_courses=None):
        if num_courses is None:
            num_courses = self.num_courses
        log_offset = num_courses + 1
        self._assert_stat_logged(mock_log, num_rows, PersistentSubsectionGrade, 'Would delete', log_offset)

    def _date_from_now(self, days=None):
        return datetime.now() + timedelta(days=days)

    def _date_str_from_now(self, days=None):
        future_date = self._date_from_now(days=days)
        return future_date.strftime(reset_grades.DATE_FORMAT)

    @patch('lms.djangoapps.grades.management.commands.reset_grades.log')
    def test_reset_all_courses(self, mock_log):
        self._update_or_create_grades()
        self._assert_grades_exist_for_courses(self.course_keys)

        with self.assertNumQueries(4):
            self.command.handle(delete=True, all_courses=True)

        self._assert_grades_absent_for_courses(self.course_keys)
        self._assert_subsection_delete_stat_logged(
            mock_log,
            num_rows=self.num_users * self.num_courses * self.num_subsections,
        )
        self._assert_course_delete_stat_logged(
            mock_log,
            num_rows=self.num_users * self.num_courses,
        )

    @patch('lms.djangoapps.grades.management.commands.reset_grades.log')
    @ddt.data(1, 2, 3)
    def test_reset_some_courses(self, num_courses_to_reset, mock_log):
        self._update_or_create_grades()
        self._assert_grades_exist_for_courses(self.course_keys)

        with self.assertNumQueries(4):
            self.command.handle(
                delete=True,
                courses=[unicode(course_key) for course_key in self.course_keys[:num_courses_to_reset]]
            )

        self._assert_grades_absent_for_courses(self.course_keys[:num_courses_to_reset])
        self._assert_grades_exist_for_courses(self.course_keys[num_courses_to_reset:])
        self._assert_subsection_delete_stat_logged(
            mock_log,
            num_rows=self.num_users * num_courses_to_reset * self.num_subsections,
        )
        self._assert_course_delete_stat_logged(
            mock_log,
            num_rows=self.num_users * num_courses_to_reset,
        )

    def test_reset_by_modified_start_date(self):
        self._update_or_create_grades()
        self._assert_grades_exist_for_courses(self.course_keys)

        num_courses_with_updated_grades = 2
        with freeze_time(self._date_from_now(days=4)):
            self._update_or_create_grades(self.course_keys[:num_courses_with_updated_grades])

        with self.assertNumQueries(4):
            self.command.handle(delete=True, modified_start=self._date_str_from_now(days=2), all_courses=True)

        self._assert_grades_absent_for_courses(self.course_keys[:num_courses_with_updated_grades])
        self._assert_grades_exist_for_courses(self.course_keys[num_courses_with_updated_grades:])

    def test_reset_by_modified_start_end_date(self):
        self._update_or_create_grades()
        self._assert_grades_exist_for_courses(self.course_keys)

        with freeze_time(self._date_from_now(days=3)):
            self._update_or_create_grades(self.course_keys[:2])
        with freeze_time(self._date_from_now(days=5)):
            self._update_or_create_grades(self.course_keys[2:4])

        with self.assertNumQueries(4):
            self.command.handle(
                delete=True,
                modified_start=self._date_str_from_now(days=2),
                modified_end=self._date_str_from_now(days=4),
                all_courses=True,
            )

        # Only grades for courses modified within the 2->4 days
        # should be deleted.
        self._assert_grades_absent_for_courses(self.course_keys[:2])
        self._assert_grades_exist_for_courses(self.course_keys[2:])

    @patch('lms.djangoapps.grades.management.commands.reset_grades.log')
    def test_dry_run_all_courses(self, mock_log):
        self._update_or_create_grades()
        self._assert_grades_exist_for_courses(self.course_keys)

        with self.assertNumQueries(2):
            self.command.handle(dry_run=True, all_courses=True)

        self._assert_grades_exist_for_courses(self.course_keys)
        self._assert_subsection_query_stat_logged(
            mock_log,
            num_rows=self.num_users * self.num_courses * self.num_subsections,
        )
        self._assert_course_query_stat_logged(
            mock_log,
            num_rows=self.num_users * self.num_courses,
        )

    @patch('lms.djangoapps.grades.management.commands.reset_grades.log')
    @ddt.data(1, 2, 3)
    def test_dry_run_some_courses(self, num_courses_to_query, mock_log):
        self._update_or_create_grades()
        self._assert_grades_exist_for_courses(self.course_keys)

        with self.assertNumQueries(2):
            self.command.handle(
                dry_run=True,
                courses=[unicode(course_key) for course_key in self.course_keys[:num_courses_to_query]]
            )

        self._assert_grades_exist_for_courses(self.course_keys)
        self._assert_subsection_query_stat_logged(
            mock_log,
            num_rows=self.num_users * num_courses_to_query * self.num_subsections,
            num_courses=num_courses_to_query,
        )
        self._assert_course_query_stat_logged(
            mock_log,
            num_rows=self.num_users * num_courses_to_query,
            num_courses=num_courses_to_query,
        )

    @patch('lms.djangoapps.grades.management.commands.reset_grades.log')
    def test_reset_no_existing_grades(self, mock_log):
        self._assert_grades_absent_for_courses(self.course_keys)

        with self.assertNumQueries(4):
            self.command.handle(delete=True, all_courses=True)

        self._assert_grades_absent_for_courses(self.course_keys)
        self._assert_subsection_delete_stat_logged(mock_log, num_rows=0)
        self._assert_course_delete_stat_logged(mock_log, num_rows=0)

    def test_invalid_key(self):
        with self.assertRaisesRegexp(CommandError, 'Invalid key specified.*invalid/key'):
            self.command.handle(dry_run=True, courses=['invalid/key'])

    def test_no_run_mode(self):
        with self.assertRaisesMessage(CommandError, 'Either --delete or --dry_run must be specified.'):
            self.command.handle(all_courses=True)

    def test_both_run_modes(self):
        with self.assertRaisesMessage(CommandError, 'Both --delete and --dry_run cannot be specified.'):
            self.command.handle(all_courses=True, dry_run=True, delete=True)

    def test_no_course_mode(self):
        with self.assertRaisesMessage(CommandError, 'Either --courses or --all_courses must be specified.'):
            self.command.handle(dry_run=True)

    def test_both_course_modes(self):
        with self.assertRaisesMessage(CommandError, 'Both --courses and --all_courses cannot be specified.'):
            self.command.handle(dry_run=True, all_courses=True, courses=['some/course/key'])
