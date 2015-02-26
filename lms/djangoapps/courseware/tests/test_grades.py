"""
Test grade calculation.
"""
from django.http import Http404
from django.test.utils import override_settings
from django.core.cache import cache
from django.test.client import RequestFactory
from mock import patch
from opaque_keys.edx.locations import SlashSeparatedCourseKey, Location
import uuid

from courseware.grades import grade, iterate_grades_for, MaxScoresCache, descriptor_filter
from courseware.model_data import FieldDataCache
from courseware.tests.factories import StudentModuleFactory
from xmodule.modulestore.tests.django_utils import TEST_DATA_MOCK_MODULESTORE
from student.tests.factories import UserFactory
from student.models import CourseEnrollment
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase


def _grade_with_errors(student, request, course, keep_raw_scores=False):
    """This fake grade method will throw exceptions for student3 and
    student4, but allow any other students to go through normal grading.

    It's meant to simulate when something goes really wrong while trying to
    grade a particular student, so we can test that we won't kill the entire
    course grading run.
    """
    if student.username in ['student3', 'student4']:
        raise Exception("I don't like {}".format(student.username))

    return grade(student, request, course, keep_raw_scores=keep_raw_scores)


class TestGradeIteration(ModuleStoreTestCase):
    """
    Test iteration through student gradesets.
    """
    COURSE_NUM = "1000"
    COURSE_NAME = "grading_test_course"

    def setUp(self):
        """
        Create a course and a handful of users to assign grades
        """
        super(TestGradeIteration, self).setUp()

        self.course = CourseFactory.create(
            display_name=self.COURSE_NAME,
            number=self.COURSE_NUM
        )
        self.students = [
            UserFactory.create(username='student1'),
            UserFactory.create(username='student2'),
            UserFactory.create(username='student3'),
            UserFactory.create(username='student4'),
            UserFactory.create(username='student5'),
        ]

    def test_empty_student_list(self):
        """If we don't pass in any students, it should return a zero-length
        iterator, but it shouldn't error."""
        gradeset_results = list(iterate_grades_for(self.course.id, []))
        self.assertEqual(gradeset_results, [])

    def test_nonexistent_course(self):
        """If the course we want to get grades for does not exist, a `Http404`
        should be raised. This is a horrible crossing of abstraction boundaries
        and should be fixed, but for now we're just testing the behavior. :-("""
        with self.assertRaises(Http404):
            gradeset_results = iterate_grades_for(SlashSeparatedCourseKey("I", "dont", "exist"), [])
            gradeset_results.next()

    def test_all_empty_grades(self):
        """No students have grade entries"""
        all_gradesets, all_errors = self._gradesets_and_errors_for(self.course.id, self.students)
        self.assertEqual(len(all_errors), 0)
        for gradeset in all_gradesets.values():
            self.assertIsNone(gradeset['grade'])
            self.assertEqual(gradeset['percent'], 0.0)

    @patch('courseware.grades.grade', _grade_with_errors)
    def test_grading_exception(self):
        """Test that we correctly capture exception messages that bubble up from
        grading. Note that we only see errors at this level if the grading
        process for this student fails entirely due to an unexpected event --
        having errors in the problem sets will not trigger this.

        We patch the grade() method with our own, which will generate the errors
        for student3 and student4.
        """
        all_gradesets, all_errors = self._gradesets_and_errors_for(self.course.id, self.students)
        student1, student2, student3, student4, student5 = self.students
        self.assertEqual(
            all_errors,
            {
                student3: "I don't like student3",
                student4: "I don't like student4"
            }
        )

        # But we should still have five gradesets
        self.assertEqual(len(all_gradesets), 5)

        # Even though two will simply be empty
        self.assertFalse(all_gradesets[student3])
        self.assertFalse(all_gradesets[student4])

        # The rest will have grade information in them
        self.assertTrue(all_gradesets[student1])
        self.assertTrue(all_gradesets[student2])
        self.assertTrue(all_gradesets[student5])

    ################################# Helpers #################################
    def _gradesets_and_errors_for(self, course_id, students):
        """Simple helper method to iterate through student grades and give us
        two dictionaries -- one that has all students and their respective
        gradesets, and one that has only students that could not be graded and
        their respective error messages."""
        students_to_gradesets = {}
        students_to_errors = {}

        for student, gradeset, err_msg in iterate_grades_for(course_id, students):
            students_to_gradesets[student] = gradeset
            if err_msg:
                students_to_errors[student] = err_msg

        return students_to_gradesets, students_to_errors


class TestMaxScoresCache(ModuleStoreTestCase):
    """docstring for TestMaxScoresCache"""
    def setUp(self):
        super(TestMaxScoresCache, self).setUp()
        self.student = UserFactory.create()
        self.course = CourseFactory.create()
        self.problems = []
        for _ in xrange(3):
            self.problems.append(
                ItemFactory.create(category='problem', parent=self.course)
            )

        CourseEnrollment.enroll(self.student, self.course.id)
        self.request = RequestFactory().get('/')
        self.locations = [problem.location for problem in self.problems]

    @override_settings(KEY_PREFIX=str(uuid.uuid4()))  # hack to ensure unique cache per test
    def test_max_scores_cache(self):

        max_scores_cache = MaxScoresCache(self.locations)

        self.assertEqual(max_scores_cache.locations, self.locations)
        self.assertEqual(len(max_scores_cache._max_scores_cache), 0)

        self.assertEqual(len(max_scores_cache._max_scores_updates), 0)
        # add score to cache
        max_scores_cache.set(self.locations[0], 1)
        self.assertEqual(len(max_scores_cache._max_scores_updates), 1)
        # push to remote cache
        max_scores_cache.push_to_remote()
        # fetch from remote cache
        max_scores_cache.fetch_from_remote()
        # see cache is populated
        self.assertEqual(len(max_scores_cache._max_scores_cache), 1)


class TestDescriptorFilter(ModuleStoreTestCase):

    def setUp(self):
        super(TestDescriptorFilter, self).setUp()
        self.student = UserFactory.create()
        self.course = CourseFactory.create()
        chapter = ItemFactory.create(category='chapter', parent=self.course)
        sequential = ItemFactory.create(category='sequential', parent=chapter)
        vertical = ItemFactory.create(category='vertical', parent=sequential)
        ItemFactory.create(category='video', parent=vertical)
        ItemFactory.create(category='html', parent=vertical)
        ItemFactory.create(category='discussion', parent=vertical)
        ItemFactory.create(category='problem', parent=vertical)

        CourseEnrollment.enroll(self.student, self.course.id)

    def test_field_data_cache_no_filter(self):
        field_data_cache_no_filter = FieldDataCache.cache_for_descriptor_descendents(
            self.course.id, self.student, self.course, depth=None
        )
        categories = set(descriptor.category for descriptor in field_data_cache_no_filter.descriptors)
        self.assertIn('video', categories)
        self.assertIn('html', categories)
        self.assertIn('discussion', categories)
        self.assertIn('problem', categories)

    def test_field_data_cache_filter(self):
        field_data_cache_filter = FieldDataCache.cache_for_descriptor_descendents(
            self.course.id, self.student, self.course, depth=None, descriptor_filter=descriptor_filter
        )
        categories = set(descriptor.category for descriptor in field_data_cache_filter.descriptors)
        self.assertNotIn('video', categories)
        self.assertNotIn('html', categories)
        self.assertNotIn('discussion', categories)
        self.assertIn('problem', categories)
