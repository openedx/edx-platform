"""
Tests for the CourseGradeFactory class.
"""


import itertools

import ddt
from django.conf import settings
from mock import patch
from six import text_type
from edx_toggles.toggles.testutils import override_waffle_switch
from lms.djangoapps.courseware.access import has_access
from lms.djangoapps.grades.config.tests.utils import persistent_grades_feature_flags
from openedx.core.djangoapps.content.block_structure.factory import BlockStructureFactory
from common.djangoapps.student.tests.factories import UserFactory
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

from ..config.waffle import ASSUME_ZERO_GRADE_IF_ABSENT, waffle_switch
from ..course_grade import CourseGrade, ZeroCourseGrade
from ..course_grade_factory import CourseGradeFactory
from ..subsection_grade import ReadSubsectionGrade, ZeroSubsectionGrade
from .base import GradeTestBase
from .utils import mock_get_score


@ddt.ddt
class TestCourseGradeFactory(GradeTestBase):
    """
    Test that CourseGrades are calculated properly
    """
    def _assert_zero_grade(self, course_grade, expected_grade_class):
        """
        Asserts whether the given course_grade is as expected with
        zero values.
        """
        self.assertIsInstance(course_grade, expected_grade_class)
        self.assertIsNone(course_grade.letter_grade)
        self.assertEqual(course_grade.percent, 0.0)
        self.assertIsNotNone(course_grade.chapter_grades)

    def test_course_grade_no_access(self):
        """
        Test to ensure a grade can be calculated for a student in a course, even if they themselves do not have access.
        """
        invisible_course = CourseFactory.create(visible_to_staff_only=True)
        access = has_access(self.request.user, 'load', invisible_course)
        self.assertEqual(access.has_access, False)
        self.assertEqual(access.error_code, 'not_visible_to_user')

        # with self.assertNoExceptionRaised: <- this isn't a real method, it's an implicit assumption
        grade = CourseGradeFactory().read(self.request.user, invisible_course)
        self.assertEqual(grade.percent, 0)

    @patch.dict(settings.FEATURES, {'PERSISTENT_GRADES_ENABLED_FOR_ALL_TESTS': False})
    @ddt.data(
        (True, True),
        (True, False),
        (False, True),
        (False, False),
    )
    @ddt.unpack
    def test_course_grade_feature_gating(self, feature_flag, course_setting):
        # Grades are only saved if the feature flag and the advanced setting are
        # both set to True.
        grade_factory = CourseGradeFactory()
        with persistent_grades_feature_flags(
            global_flag=feature_flag,
            enabled_for_all_courses=False,
            course_id=self.course.id,
            enabled_for_course=course_setting
        ):
            with patch('lms.djangoapps.grades.models.PersistentCourseGrade.read') as mock_read_grade:
                grade_factory.read(self.request.user, self.course)
        self.assertEqual(mock_read_grade.called, feature_flag and course_setting)

    def test_read_and_update(self):
        grade_factory = CourseGradeFactory()

        def _assert_read(expected_pass, expected_percent):
            """
            Creates the grade, ensuring it is as expected.
            """
            course_grade = grade_factory.read(self.request.user, self.course)
            _assert_grade_values(course_grade, expected_pass, expected_percent)
            _assert_section_order(course_grade)

        def _assert_grade_values(course_grade, expected_pass, expected_percent):
            self.assertEqual(course_grade.letter_grade, u'Pass' if expected_pass else None)
            self.assertEqual(course_grade.percent, expected_percent)

        def _assert_section_order(course_grade):
            sections = course_grade.chapter_grades[self.chapter.location]['sections']
            self.assertEqual(
                [section.display_name for section in sections],
                [self.sequence.display_name, self.sequence2.display_name]
            )

        with self.assertNumQueries(3), mock_get_score(1, 2):
            _assert_read(expected_pass=False, expected_percent=0)  # start off with grade of 0

        num_queries = 44
        with self.assertNumQueries(num_queries), mock_get_score(1, 2):
            grade_factory.update(self.request.user, self.course, force_update_subsections=True)

        with self.assertNumQueries(3):
            _assert_read(expected_pass=True, expected_percent=0.5)  # updated to grade of .5

        num_queries = 6
        with self.assertNumQueries(num_queries), mock_get_score(1, 4):
            grade_factory.update(self.request.user, self.course, force_update_subsections=False)

        with self.assertNumQueries(3):
            _assert_read(expected_pass=True, expected_percent=0.5)  # NOT updated to grade of .25

        num_queries = 23
        with self.assertNumQueries(num_queries), mock_get_score(2, 2):
            grade_factory.update(self.request.user, self.course, force_update_subsections=True)

        with self.assertNumQueries(3):
            _assert_read(expected_pass=True, expected_percent=1.0)  # updated to grade of 1.0

        num_queries = 28
        with self.assertNumQueries(num_queries), mock_get_score(0, 0):  # the subsection now is worth zero
            grade_factory.update(self.request.user, self.course, force_update_subsections=True)

        with self.assertNumQueries(3):
            _assert_read(expected_pass=False, expected_percent=0.0)  # updated to grade of 0.0

    @patch.dict(settings.FEATURES, {'ASSUME_ZERO_GRADE_IF_ABSENT_FOR_ALL_TESTS': False})
    @ddt.data(*itertools.product((True, False), (True, False)))
    @ddt.unpack
    def test_read_zero(self, assume_zero_enabled, create_if_needed):
        with override_waffle_switch(waffle_switch(ASSUME_ZERO_GRADE_IF_ABSENT), active=assume_zero_enabled):
            grade_factory = CourseGradeFactory()
            course_grade = grade_factory.read(self.request.user, self.course, create_if_needed=create_if_needed)
            if create_if_needed or assume_zero_enabled:
                self._assert_zero_grade(course_grade, ZeroCourseGrade if assume_zero_enabled else CourseGrade)
            else:
                self.assertIsNone(course_grade)

    def test_read_optimization(self):
        grade_factory = CourseGradeFactory()
        with patch('lms.djangoapps.grades.course_data.get_course_blocks') as mocked_course_blocks:
            mocked_course_blocks.return_value = self.course_structure
            with mock_get_score(1, 2):
                grade_factory.update(self.request.user, self.course, force_update_subsections=True)
                self.assertEqual(mocked_course_blocks.call_count, 1)

        with patch('lms.djangoapps.grades.course_data.get_course_blocks') as mocked_course_blocks:
            with patch('lms.djangoapps.grades.subsection_grade.get_score') as mocked_get_score:
                course_grade = grade_factory.read(self.request.user, self.course)
                self.assertEqual(course_grade.percent, 0.5)  # make sure it's not a zero-valued course grade
                self.assertFalse(mocked_get_score.called)  # no calls to CSM/submissions tables
                self.assertFalse(mocked_course_blocks.called)  # no user-specific transformer calculation

    def test_subsection_grade(self):
        grade_factory = CourseGradeFactory()
        with mock_get_score(1, 2):
            grade_factory.update(self.request.user, self.course, force_update_subsections=True)
        course_grade = grade_factory.read(self.request.user, course_structure=self.course_structure)
        subsection_grade = course_grade.subsection_grade(self.sequence.location)
        self.assertEqual(subsection_grade.percent_graded, 0.5)

    def test_subsection_type_graders(self):
        graders = CourseGrade.get_subsection_type_graders(self.course)
        self.assertEqual(len(graders), 2)
        self.assertEqual(graders["Homework"].type, "Homework")
        self.assertEqual(graders["NoCredit"].min_count, 0)

    def test_create_zero_subs_grade_for_nonzero_course_grade(self):
        subsection = self.course_structure[self.sequence.location]
        with mock_get_score(1, 2):
            self.subsection_grade_factory.update(subsection)
        course_grade = CourseGradeFactory().update(self.request.user, self.course)
        subsection1_grade = course_grade.subsection_grades[self.sequence.location]
        subsection2_grade = course_grade.subsection_grades[self.sequence2.location]
        self.assertIsInstance(subsection1_grade, ReadSubsectionGrade)
        self.assertIsInstance(subsection2_grade, ZeroSubsectionGrade)

    @ddt.data(True, False)
    def test_iter_force_update(self, force_update):
        with patch('lms.djangoapps.grades.subsection_grade_factory.SubsectionGradeFactory.update') as mock_update:
            set(CourseGradeFactory().iter(
                users=[self.request.user], course=self.course, force_update=force_update,
            ))
        self.assertEqual(mock_update.called, force_update)

    def test_course_grade_summary(self):
        with mock_get_score(1, 2):
            self.subsection_grade_factory.update(self.course_structure[self.sequence.location])
        course_grade = CourseGradeFactory().update(self.request.user, self.course)

        actual_summary = course_grade.summary

        # We should have had a zero subsection grade for sequential 2, since we never
        # gave it a mock score above.
        expected_summary = {
            'grade': None,
            'grade_breakdown': {
                'Homework': {
                    'category': 'Homework',
                    'percent': 0.25,
                    'detail': 'Homework = 25.00% of a possible 100.00%',
                },
                'NoCredit': {
                    'category': 'NoCredit',
                    'percent': 0.0,
                    'detail': 'NoCredit = 0.00% of a possible 0.00%',
                }
            },
            'percent': 0.25,
            'section_breakdown': [
                {
                    'category': 'Homework',
                    'detail': u'Homework 1 - Test Sequential X - 50% (1/2)',
                    'label': u'HW 01',
                    'percent': 0.5
                },
                {
                    'category': 'Homework',
                    'detail': u'Homework 2 - Test Sequential A - 0% (0/1)',
                    'label': u'HW 02',
                    'percent': 0.0
                },
                {
                    'category': 'Homework',
                    'detail': u'Homework Average = 25%',
                    'label': u'HW Avg',
                    'percent': 0.25,
                    'prominent': True
                },
                {
                    'category': 'NoCredit',
                    'detail': u'NoCredit Average = 0%',
                    'label': u'NC Avg',
                    'percent': 0,
                    'prominent': True
                },
            ]
        }
        self.assertEqual(expected_summary, actual_summary)


class TestGradeIteration(SharedModuleStoreTestCase):
    """
    Test iteration through student course grades.
    """
    COURSE_NUM = "1000"
    COURSE_NAME = "grading_test_course"

    @classmethod
    def setUpClass(cls):
        super(TestGradeIteration, cls).setUpClass()
        cls.course = CourseFactory.create(
            display_name=cls.COURSE_NAME,
            number=cls.COURSE_NUM
        )

    def setUp(self):
        """
        Create a course and a handful of users to assign grades
        """
        super(TestGradeIteration, self).setUp()

        self.students = [
            UserFactory.create(username='student1'),
            UserFactory.create(username='student2'),
            UserFactory.create(username='student3'),
            UserFactory.create(username='student4'),
            UserFactory.create(username='student5'),
        ]

    def test_empty_student_list(self):
        """
        If we don't pass in any students, it should return a zero-length
        iterator, but it shouldn't error.
        """
        grade_results = list(CourseGradeFactory().iter([], self.course))
        self.assertEqual(grade_results, [])

    def test_all_empty_grades(self):
        """
        No students have grade entries.
        """
        with patch.object(
            BlockStructureFactory,
            'create_from_store',
            wraps=BlockStructureFactory.create_from_store
        ) as mock_create_from_store:
            all_course_grades, all_errors = self._course_grades_and_errors_for(self.course, self.students)
            self.assertEqual(mock_create_from_store.call_count, 1)

        self.assertEqual(len(all_errors), 0)
        for course_grade in all_course_grades.values():
            self.assertIsNone(course_grade.letter_grade)
            self.assertEqual(course_grade.percent, 0.0)

    @patch('lms.djangoapps.grades.course_grade_factory.CourseGradeFactory.read')
    def test_grading_exception(self, mock_course_grade):
        """Test that we correctly capture exception messages that bubble up from
        grading. Note that we only see errors at this level if the grading
        process for this student fails entirely due to an unexpected event --
        having errors in the problem sets will not trigger this.

        We patch the grade() method with our own, which will generate the errors
        for student3 and student4.
        """

        student1, student2, student3, student4, student5 = self.students
        mock_course_grade.side_effect = [
            Exception(u"Error for {}.".format(student.username))
            if student.username in ['student3', 'student4']
            else mock_course_grade.return_value
            for student in self.students
        ]
        with self.assertNumQueries(8):
            all_course_grades, all_errors = self._course_grades_and_errors_for(self.course, self.students)
        self.assertEqual(
            {student: text_type(all_errors[student]) for student in all_errors},
            {
                student3: "Error for student3.",
                student4: "Error for student4.",
            }
        )

        # But we should still have five gradesets
        self.assertEqual(len(all_course_grades), 5)

        # Even though two will simply be empty
        self.assertIsNone(all_course_grades[student3])
        self.assertIsNone(all_course_grades[student4])

        # The rest will have grade information in them
        self.assertIsNotNone(all_course_grades[student1])
        self.assertIsNotNone(all_course_grades[student2])
        self.assertIsNotNone(all_course_grades[student5])

    def _course_grades_and_errors_for(self, course, students):
        """
        Simple helper method to iterate through student grades and give us
        two dictionaries -- one that has all students and their respective
        course grades, and one that has only students that could not be graded
        and their respective error messages.
        """
        students_to_course_grades = {}
        students_to_errors = {}

        for student, course_grade, error in CourseGradeFactory().iter(students, course):
            students_to_course_grades[student] = course_grade
            if error:
                students_to_errors[student] = error

        return students_to_course_grades, students_to_errors
