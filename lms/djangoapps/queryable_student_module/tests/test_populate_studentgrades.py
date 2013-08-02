import json
from datetime import datetime
from pytz import UTC
from mock import Mock, patch

from django.test import TestCase
from django.test.utils import override_settings
from django.core.management import call_command

from courseware import grades
from courseware.tests.factories import StudentModuleFactory
from courseware.tests.modulestore_config import TEST_DATA_MONGO_MODULESTORE
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from student.tests.factories import UserFactory as StudentUserFactory
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory

from queryable_student_module.models import Log, CourseGrade, AssignmentTypeGrade, AssignmentGrade
from queryable_student_module.management.commands import populate_studentgrades


class TestPopulateStudentGradesUpdateCourseGrade(TestCase):
    """
    Tests the helper fuction update_course_grade in the populate_studentgrades custom command
    """

    def setUp(self):
        self.course_grade = CourseGrade(percent=0.9, grade='A')
        self.gradeset = {'percent': 0.9, 'grade': 'A'}

    def test_no_update(self):
        """
        Values are the same, so no update
        """
        self.assertFalse(populate_studentgrades.update_course_grade(self.course_grade, self.gradeset))

    def test_percents_not_equal(self):
        """
        Update because the percents don't equal
        """
        self.course_grade.percent = 1.0

        self.assertTrue(populate_studentgrades.update_course_grade(self.course_grade, self.gradeset))

    def test_different_grade(self):
        """
        Update because the grade is different
        """
        self.course_grade.grade = 'Foo'

        self.assertTrue(populate_studentgrades.update_course_grade(self.course_grade, self.gradeset))

    def test_grade_as_null(self):
        """
        Percent is the same and grade are both null, so no update
        """
        self.course_grade.grade = None
        self.gradeset['grade'] = None

        self.assertFalse(populate_studentgrades.update_course_grade(self.course_grade, self.gradeset))


class TestPopulateStudentGradesGetAssignmentIndex(TestCase):
    """
    Tests the helper fuction get_assignment_index in the populate_studentgrades custom command
    """

    def test_simple(self):
        """
        Simple test if returns correct index.
        """

        self.assertEquals(populate_studentgrades.get_assignment_index("HW 3"), 2)
        self.assertEquals(populate_studentgrades.get_assignment_index("HW 02"), 1)
        self.assertEquals(populate_studentgrades.get_assignment_index("HW 11"), 10)
        self.assertEquals(populate_studentgrades.get_assignment_index("HW 001"), 0)

    def test_no_index(self):
        """
        Test if returns -1 for badly formed input
        """

        self.assertEquals(populate_studentgrades.get_assignment_index("HW Avg"), -1)
        self.assertEquals(populate_studentgrades.get_assignment_index("HW"), -1)
        self.assertEquals(populate_studentgrades.get_assignment_index("HW "), -1)


class TestPopulateStudentGradesGetStudentProblems(TestCase):
    """
    Tests the helper fuction get_student_problems in the populate_studentgrades custom command
    """

    def setUp(self):
        self.student_module = StudentModuleFactory(
            module_type='problem',
            module_state_key='one',
            grade=1,
            max_grade=1,
        )

    def test_single_problem(self):
        """
        Test returns a single problem
        """

        problem_set = populate_studentgrades.get_student_problems(
            self.student_module.course_id,
            self.student_module.student,
        )

        self.assertEquals(len(problem_set), 1)
        self.assertEquals(problem_set[0], self.student_module.module_state_key)

    def test_problem_with_no_submission(self):
        """
        Test to make sure only returns the problems with a submission.
        """

        student_module_no_submission = StudentModuleFactory(
            course_id=self.student_module.course_id,
            student=self.student_module.student,
            module_type='problem',
            module_state_key='no_submission',
            grade=None,
            max_grade=None,
        )

        problem_set = populate_studentgrades.get_student_problems(
            self.student_module.course_id,
            self.student_module.student,
        )

        self.assertEquals(len(problem_set), 1)
        self.assertEquals(problem_set[0], self.student_module.module_state_key)


class TestPopulateStudentGradesAssignmentExistsAndHasProblems(TestCase):
    """
    Tests the helper fuction assignment_exists_and_has_prob in the populate_studentgrades custom command
    """

    def setUp(self):
        self.category = 'HW'
        self.assignment_problems_map = {
            self.category: [
                ['cat_1_problem_id_1'],
            ]
        }

    def test_simple(self):
        """
        Test where assignment does exist and has problems
        """

        self.assertTrue(populate_studentgrades.assignment_exists_and_has_prob(
                        self.assignment_problems_map,
                        self.category,
                        len(self.assignment_problems_map[self.category]) - 1, )
                        )

    def test_assignment_exist_no_problems(self):
        """
        Test where assignment exists but has no problems
        """

        self.assignment_problems_map['Final'] = [[]]

        self.assertFalse(populate_studentgrades.assignment_exists_and_has_prob(
                         self.assignment_problems_map, 'Final', 0)
                         )

    def test_negative_index(self):
        """
        Test handles negative indexes well by returning False
        """

        self.assertFalse(populate_studentgrades.assignment_exists_and_has_prob({}, "", -1))
        self.assertFalse(populate_studentgrades.assignment_exists_and_has_prob({}, "", -5))

    def test_non_existing_category(self):
        """
        Test handled a category that doesn't actually exist by returning False
        """

        self.assertFalse(populate_studentgrades.assignment_exists_and_has_prob({}, "Foo", 0))
        self.assertFalse(populate_studentgrades.assignment_exists_and_has_prob(self.assignment_problems_map, "Foo", 0))

    def test_index_too_high(self):
        """
        Test that if the index is higher than the actual number of assignments
        """

        self.assertFalse(populate_studentgrades.assignment_exists_and_has_prob(
                         self.assignment_problems_map, self.category, len(self.assignment_problems_map[self.category])))


class TestPopulateStudentGradesStudentDidProblems(TestCase):
    """
    Tests the helper fuction student_did_problems in the populate_studentgrades custom command
    """

    def setUp(self):
        self.student_problems = ['cat_1_problem_1']

    def test_student_did_do_problems(self):
        """
        Test where student did do some of the problems
        """

        self.assertTrue(populate_studentgrades.student_did_problems(self.student_problems, self.student_problems))

        problem_set = list(self.student_problems)
        problem_set.append('cat_2_problem_1')
        self.assertTrue(populate_studentgrades.student_did_problems(self.student_problems, problem_set))

    def test_student_did_not_do_problems(self):
        """
        Test where student didn't do any problems in the list
        """

        self.assertFalse(populate_studentgrades.student_did_problems(self.student_problems, []))
        self.assertFalse(populate_studentgrades.student_did_problems([], self.student_problems))

        problem_set = ['cat_1_problem_2']
        self.assertFalse(populate_studentgrades.student_did_problems(self.student_problems, problem_set))


class TestPopulateStudentGradesStoreCourseGradeIfNeed(TestCase):
    """
    Tests the helper fuction store_course_grade_if_need in the populate_studentgrades custom command
    """

    def setUp(self):
        self.student = StudentUserFactory()
        self.course_id = 'test/test/test'
        self.gradeset = {
            'percent': 1.0,
            'grade': 'A',
        }
        self.course_grade = CourseGrade(
            user_id=self.student.id,
            course_id=self.course_id,
            percent=self.gradeset['percent'],
            grade=self.gradeset['grade'],
        )
        self.course_grade.save()

    def test_new_course_grade_store(self):
        """
        Test stores because it's a new CourseGrade
        """

        self.assertEqual(len(CourseGrade.objects.filter(course_id__exact=self.course_id)), 1)
        student = StudentUserFactory()
        return_value = populate_studentgrades.store_course_grade_if_need(
            student, self.course_id, self.gradeset
        )

        self.assertTrue(return_value)
        self.assertEqual(len(CourseGrade.objects.filter(course_id__exact=self.course_id)), 2)

    @patch('queryable_student_module.management.commands.populate_studentgrades.update_course_grade')
    def test_update_store(self, mock_update_course_grade):
        """
        Test stores because update_course_grade returns True
        """
        mock_update_course_grade.return_value = True

        updated_time = self.course_grade.updated

        return_value = populate_studentgrades.store_course_grade_if_need(
            self.student, self.course_id, self.gradeset
        )

        self.assertTrue(return_value)

        course_grades = CourseGrade.objects.filter(
            course_id__exact=self.course_id,
            user_id=self.student.id,
        )
        self.assertEqual(len(course_grades), 1)
        self.assertNotEqual(updated_time, course_grades[0].updated)

    @patch('queryable_student_module.management.commands.populate_studentgrades.update_course_grade')
    def test_no_update_no_store(self, mock_update_course_grade):
        """
        Test doesn't touch the row because it is not newly created and update_course_grade returns False
        """
        mock_update_course_grade.return_value = False

        updated_time = self.course_grade.updated

        return_value = populate_studentgrades.store_course_grade_if_need(
            self.student, self.course_id, self.gradeset
        )

        self.assertFalse(return_value)

        course_grades = CourseGrade.objects.filter(
            course_id__exact=self.course_id,
            user_id=self.student.id,
        )
        self.assertEqual(len(course_grades), 1)
        self.assertEqual(updated_time, course_grades[0].updated)


class TestPopulateStudentGradesStoreAssignmentTypeGradeIfNeed(TestCase):
    """
    Tests the helper fuction store_assignment_type_grade in the populate_studentgrades custom command
    """

    def setUp(self):
        self.student = StudentUserFactory()
        self.course_id = 'test/test/test'
        self.category = 'Homework'
        self.percent = 1.0
        self.assignment_type_grade = AssignmentTypeGrade(
            user_id=self.student.id,
            username=self.student.username,
            name=self.student.profile.name,
            course_id=self.course_id,
            category=self.category,
            percent=self.percent,
        )
        self.assignment_type_grade.save()

    def test_new_assignment_type_grade_store(self):
        """
        Test the function both stores the new assignment type grade and returns True meaning that it had
        """

        self.assertEqual(len(AssignmentTypeGrade.objects.filter(course_id__exact=self.course_id)), 1)
        return_value = populate_studentgrades.store_assignment_type_grade(
            self.student, self.course_id, 'Foo 01', 1.0
        )

        self.assertTrue(return_value)
        self.assertEqual(len(AssignmentTypeGrade.objects.filter(course_id__exact=self.course_id)), 2)

    def test_difference_percent_store(self):
        """
        Test updates the percent value when it is different
        """

        new_percent = self.percent - 0.1
        return_value = populate_studentgrades.store_assignment_type_grade(
            self.student, self.course_id, self.category, new_percent
        )

        self.assertTrue(return_value)

        assignment_type_grades = AssignmentTypeGrade.objects.filter(
            course_id__exact=self.course_id,
            user_id=self.student.id,
            category=self.category,
        )
        self.assertEqual(len(assignment_type_grades), 1)
        self.assertEqual(assignment_type_grades[0].percent, new_percent)

    def test_same_percent_no_store(self):
        """
        Test does not touch row if the row exists and the precent is not different
        """
        updated_time = self.assignment_type_grade.updated

        return_value = populate_studentgrades.store_assignment_type_grade(
            self.student, self.course_id, self.category, self.percent
        )

        self.assertFalse(return_value)

        assignment_type_grades = AssignmentTypeGrade.objects.filter(
            course_id__exact=self.course_id,
            user_id=self.student.id,
            category=self.category,
        )
        self.assertEqual(len(assignment_type_grades), 1)
        self.assertEqual(assignment_type_grades[0].percent, self.percent)
        self.assertEqual(assignment_type_grades[0].updated, updated_time)


class TestPopulateStudentGradesStoreAssignmentGradeIfNeed(TestCase):
    """
    Tests the helper fuction store_assignment_grade_if_need in the populate_studentgrades custom command
    """

    def setUp(self):
        self.student = StudentUserFactory()
        self.course_id = 'test/test/test'
        self.label = 'HW 01'
        self.percent = 1.0
        self.assignment_grade = AssignmentGrade(
            user_id=self.student.id,
            username=self.student.username,
            name=self.student.profile.name,
            course_id=self.course_id,
            label=self.label,
            percent=self.percent,
        )
        self.assignment_grade.save()

    def test_new_assignment_grade_store(self):
        """
        Test the function both stores the new assignment grade and returns True meaning that it had
        """

        self.assertEqual(len(AssignmentGrade.objects.filter(course_id__exact=self.course_id)), 1)
        return_value = populate_studentgrades.store_assignment_grade_if_need(
            self.student, self.course_id, 'Foo 01', 1.0
        )

        self.assertTrue(return_value)
        self.assertEqual(len(AssignmentGrade.objects.filter(course_id__exact=self.course_id)), 2)

    def test_difference_percent_store(self):
        """
        Test updates the percent value when it is different
        """

        new_percent = self.percent - 0.1
        return_value = populate_studentgrades.store_assignment_grade_if_need(
            self.student, self.course_id, self.label, new_percent
        )

        self.assertTrue(return_value)

        assignment_grades = AssignmentGrade.objects.filter(
            course_id__exact=self.course_id,
            user_id=self.student.id,
            label=self.label,
        )
        self.assertEqual(len(assignment_grades), 1)
        self.assertEqual(assignment_grades[0].percent, new_percent)

    def test_same_percent_no_store(self):
        """
        Test does not touch row if the row exists and the precent is not different
        """
        updated_time = self.assignment_grade.updated

        return_value = populate_studentgrades.store_assignment_grade_if_need(
            self.student, self.course_id, self.label, self.percent
        )

        self.assertFalse(return_value)

        assignment_grades = AssignmentGrade.objects.filter(
            course_id__exact=self.course_id,
            user_id=self.student.id,
            label=self.label,
        )
        self.assertEqual(len(assignment_grades), 1)
        self.assertEqual(assignment_grades[0].percent, self.percent)
        self.assertEqual(assignment_grades[0].updated, updated_time)


@override_settings(MODULESTORE=TEST_DATA_MONGO_MODULESTORE)
class TestPopulateStudentGradesCommand(ModuleStoreTestCase):

    def create_studentmodule(self):
        """
        Creates a StudentModule. This can't be in setUp because some functions can't have one in the database.
        """
        sm = StudentModuleFactory(
            course_id=self.course.id,
            module_type='problem',
            grade=1,
            max_grade=1,
            state=json.dumps({'attempts': 1}),
        )

    def create_log_entry(self):
        """
        Adds a queryable log entry to the database
        """
        log = Log(script_id=self.script_id, course_id=self.course.id, created=datetime.now(UTC))
        log.save()

    def setUp(self):
        self.command = 'populate_studentgrades'
        self.script_id = 'studentgrades'
        self.course = CourseFactory.create()
        self.category = 'Homework'
        self.gradeset = {
            'percent': 1.0,
            'grade': 'A',
            'section_breakdown': [
                {'category': self.category, 'label': 'HW Avg', 'percent': 1.0, 'prominent': True},
                {'category': self.category, 'label': 'HW 01', 'percent': 1.0},
            ],
        }
        # Make sure these are correct with the above gradeset
        self.assignment_type_index = 0
        self.assignment_index = 1

    def test_missing_input(self):
        """
        Fails safely when not given enough input
        """
        try:
            call_command(self.command)
            self.assertTrue(True)
        except:
            self.assertTrue(False)

    def test_just_logs_if_empty_course(self):
        """
        If the course has nothing in it, just logs the run in the log table.
        """

        call_command(self.command, self.course.id)

        self.assertEqual(len(Log.objects.filter(script_id__exact=self.script_id, course_id__exact=self.course.id)), 1)
        self.assertEqual(len(CourseGrade.objects.filter(course_id__exact=self.course.id)), 0)
        self.assertEqual(len(AssignmentTypeGrade.objects.filter(course_id__exact=self.course.id)), 0)
        self.assertEqual(len(AssignmentGrade.objects.filter(course_id__exact=self.course.id)), 0)

    @patch('courseware.grades.grade')
    def test_force_update(self, mock_grade):
        """
        Even if there is a log entry for incremental update, force a full update

        This may be done because something happened in the last update.
        """
        mock_grade.return_value = self.gradeset

        # Create a StudentModule that is before the log entry
        sm = StudentModuleFactory(
            course_id=self.course.id,
            module_type='problem',
            grade=1,
            max_grade=1,
            state=json.dumps({'attempts': 1}),
        )

        self.create_log_entry()

        call_command(self.command, self.course.id, force=True)

        self.assertEqual(len(Log.objects.filter(script_id__exact=self.script_id, course_id__exact=self.course.id)), 2)
        self.assertEqual(len(CourseGrade.objects.filter(user_id=sm.student.id, course_id__exact=self.course.id)), 1)
        self.assertEqual(len(AssignmentTypeGrade.objects.filter(
                             user_id=sm.student.id, course_id__exact=self.course.id, category=self.category)), 1)
        self.assertEqual(len(AssignmentGrade.objects.filter(
                             user_id=sm.student.id,
                             course_id__exact=self.course.id,
                             label=self.gradeset['section_breakdown'][self.assignment_index]['label'], )), 1)

    @patch('courseware.grades.grade')
    def test_incremental_update_if_log_exists(self, mock_grade):
        """
        Make sure it uses the log entry if it exists and we aren't forcing a full update
        """
        mock_grade.return_value = self.gradeset

        # Create a StudentModule that is before the log entry
        sm = StudentModuleFactory(
            course_id=self.course.id,
            module_type='problem',
            grade=1,
            max_grade=1,
            state=json.dumps({'attempts': 1}),
        )
        sm.student.last_name = "Student1"
        sm.student.save()

        self.create_log_entry()

        # Create a StudentModule that is after the log entry, different name
        sm = StudentModuleFactory(
            course_id=self.course.id,
            module_type='problem',
            grade=1,
            max_grade=1,
            state=json.dumps({'attempts': 1}),
        )
        sm.student.last_name = "Student2"
        sm.student.save()

        call_command(self.command, self.course.id)

        self.assertEqual(mock_grade.call_count, 1)

    @patch('queryable_student_module.management.commands.populate_studentgrades.store_course_grade_if_need')
    @patch('courseware.grades.grade')
    def test_store_course_grade(self, mock_grade, mock_method):
        """
        Calls store_course_grade_if_need for all students
        """
        mock_grade.return_value = self.gradeset

        self.create_studentmodule()

        call_command(self.command, self.course.id)

        self.assertEqual(mock_method.call_count, 1)

    @patch('queryable_student_module.management.commands.populate_studentgrades.store_assignment_type_grade')
    @patch('courseware.grades.grade')
    def test_store_assignment_type_grade(self, mock_grade, mock_method):
        """
        Calls store_assignment_type_grade when such a section exists
        """
        mock_grade.return_value = self.gradeset

        self.create_studentmodule()

        call_command(self.command, self.course.id)

        self.assertEqual(mock_method.call_count, 1)

    @patch('queryable_student_module.management.commands.populate_studentgrades.store_assignment_grade_if_need')
    @patch('courseware.grades.grade')
    def test_store_assignment_grade_percent_not_zero(self, mock_grade, mock_method):
        """
        Calls store_assignment_grade_if_need when the percent for that assignment is not zero
        """
        mock_grade.return_value = self.gradeset

        self.create_studentmodule()

        call_command(self.command, self.course.id)

        self.assertEqual(mock_method.call_count, 1)

    @patch('queryable_student_module.management.commands.populate_studentgrades.get_assignment_index')
    @patch('queryable_student_module.management.commands.populate_studentgrades.store_assignment_grade_if_need')
    @patch('courseware.grades.grade')
    def test_assignment_grade_percent_zero_bad_index(self, mock_grade, mock_method, mock_assign_index):
        """
        Does not call store_assignment_grade_if_need when the percent is zero because get_assignment_index returns a
        negative number.
        """
        self.gradeset['section_breakdown'][self.assignment_index]['percent'] = 0.0
        mock_grade.return_value = self.gradeset

        mock_assign_index.return_value = -1

        self.create_studentmodule()

        call_command(self.command, self.course.id)

        self.assertEqual(mock_grade.call_count, 1)
        self.assertEqual(mock_method.call_count, 0)

    @patch('queryable_student_module.management.commands.populate_studentgrades.get_student_problems')
    @patch('queryable_student_module.management.commands.populate_studentgrades.assignment_exists_and_has_prob')
    @patch('queryable_student_module.util.get_assignment_to_problem_map')
    @patch('queryable_student_module.management.commands.populate_studentgrades.store_assignment_grade_if_need')
    @patch('courseware.grades.grade')
    def test_assignment_grade_percent_zero_no_student_problems(self, mock_grade, mock_method, mock_assign_problem_map,
                                                               mock_assign_exists, mock_student_problems):
        """
        Does not call store_assignment_grade_if_need when the percent is zero because the student did not submit
        answers to any problems in that assignment.
        """
        self.gradeset['section_breakdown'][self.assignment_index]['percent'] = 0.0
        mock_grade.return_value = self.gradeset

        mock_assign_problem_map.return_value = {
            self.gradeset['section_breakdown'][self.assignment_index]['category']: [[]]
        }

        mock_assign_exists.return_value = True

        mock_student_problems.return_value = []

        self.create_studentmodule()

        call_command(self.command, self.course.id)

        self.assertEqual(mock_method.call_count, 0)

    @patch('queryable_student_module.management.commands.populate_studentgrades.get_student_problems')
    @patch('queryable_student_module.management.commands.populate_studentgrades.assignment_exists_and_has_prob')
    @patch('queryable_student_module.util.get_assignment_to_problem_map')
    @patch('queryable_student_module.management.commands.populate_studentgrades.store_assignment_grade_if_need')
    @patch('courseware.grades.grade')
    def test_assignment_grade_percent_zero_has_student_problems(self, mock_grade, mock_method, mock_assign_problem_map,
                                                                mock_assign_exists, mock_student_problems):
        """
        Calls store_assignment_grade_if_need when the percent is zero because the student did submit answers to
        problems in that assignment.
        """
        self.gradeset['section_breakdown'][self.assignment_index]['percent'] = 0.0
        mock_grade.return_value = self.gradeset

        mock_assign_problem_map.return_value = {
            self.gradeset['section_breakdown'][self.assignment_index]['category']: [['problem_1']]
        }

        mock_assign_exists.return_value = True

        mock_student_problems.return_value = ['problem_1']

        self.create_studentmodule()

        call_command(self.command, self.course.id)

        self.assertEqual(mock_method.call_count, 1)
