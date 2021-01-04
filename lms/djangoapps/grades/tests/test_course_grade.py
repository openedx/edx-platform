import ddt
import six
from crum import set_current_request
from django.conf import settings
from mock import patch

from edx_toggles.toggles.testutils import override_waffle_switch
from openedx.core.djangolib.testing.utils import get_mock_request
from common.djangoapps.student.models import CourseEnrollment
from common.djangoapps.student.tests.factories import UserFactory
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory

from ..config.waffle import ASSUME_ZERO_GRADE_IF_ABSENT, waffle_switch
from ..course_data import CourseData
from ..course_grade import ZeroCourseGrade
from ..course_grade_factory import CourseGradeFactory
from .base import GradeTestBase
from .utils import answer_problem


@patch.dict(settings.FEATURES, {'ASSUME_ZERO_GRADE_IF_ABSENT_FOR_ALL_TESTS': False})
@ddt.ddt
class ZeroGradeTest(GradeTestBase):
    """
    Tests ZeroCourseGrade (and, implicitly, ZeroSubsectionGrade)
    functionality.
    """

    @ddt.data(True, False)
    def test_zero(self, assume_zero_enabled):
        """
        Creates a ZeroCourseGrade and ensures it's empty.
        """
        with override_waffle_switch(waffle_switch(ASSUME_ZERO_GRADE_IF_ABSENT), active=assume_zero_enabled):
            course_data = CourseData(self.request.user, structure=self.course_structure)
            chapter_grades = ZeroCourseGrade(self.request.user, course_data).chapter_grades
            for chapter in chapter_grades:
                for section in chapter_grades[chapter]['sections']:
                    for score in six.itervalues(section.problem_scores):
                        self.assertEqual(score.earned, 0)
                        self.assertEqual(score.first_attempted, None)
                    self.assertEqual(section.all_total.earned, 0)

    @ddt.data(True, False)
    def test_zero_null_scores(self, assume_zero_enabled):
        """
        Creates a zero course grade and ensures that null scores aren't included in the section problem scores.
        """
        with override_waffle_switch(waffle_switch(ASSUME_ZERO_GRADE_IF_ABSENT), active=assume_zero_enabled):
            with patch('lms.djangoapps.grades.subsection_grade.get_score', return_value=None):
                course_data = CourseData(self.request.user, structure=self.course_structure)
                chapter_grades = ZeroCourseGrade(self.request.user, course_data).chapter_grades
                for chapter in chapter_grades:
                    self.assertNotEqual({}, chapter_grades[chapter]['sections'])
                    for section in chapter_grades[chapter]['sections']:
                        self.assertEqual({}, section.problem_scores)


class TestScoreForModule(SharedModuleStoreTestCase):
    """
    Test the method that calculates the score for a given block based on the
    cumulative scores of its children. This test class uses a hard-coded block
    hierarchy with scores as follows:
                                                a
                                       +--------+--------+
                                       b                 c
                        +--------------+-----------+     |
                        d              e           f     g
                     +-----+     +-----+-----+     |     |
                     h     i     j     k     l     m     n
                   (2/5) (3/5) (0/1)   -   (1/3)   -   (3/10)

    """

    @classmethod
    def setUpClass(cls):
        super(TestScoreForModule, cls).setUpClass()
        cls.course = CourseFactory.create()
        with cls.store.bulk_operations(cls.course.id):
            cls.a = ItemFactory.create(parent=cls.course, category="chapter", display_name="a")
            cls.b = ItemFactory.create(parent=cls.a, category="sequential", display_name="b")
            cls.c = ItemFactory.create(parent=cls.a, category="sequential", display_name="c")
            cls.d = ItemFactory.create(parent=cls.b, category="vertical", display_name="d")
            cls.e = ItemFactory.create(parent=cls.b, category="vertical", display_name="e")
            cls.f = ItemFactory.create(parent=cls.b, category="vertical", display_name="f")
            cls.g = ItemFactory.create(parent=cls.c, category="vertical", display_name="g")
            cls.h = ItemFactory.create(parent=cls.d, category="problem", display_name="h")
            cls.i = ItemFactory.create(parent=cls.d, category="problem", display_name="i")
            cls.j = ItemFactory.create(parent=cls.e, category="problem", display_name="j")
            cls.k = ItemFactory.create(parent=cls.e, category="html", display_name="k")
            cls.l = ItemFactory.create(parent=cls.e, category="problem", display_name="l")
            cls.m = ItemFactory.create(parent=cls.f, category="html", display_name="m")
            cls.n = ItemFactory.create(parent=cls.g, category="problem", display_name="n")

        cls.request = get_mock_request(UserFactory())
        CourseEnrollment.enroll(cls.request.user, cls.course.id)

        answer_problem(cls.course, cls.request, cls.h, score=2, max_value=5)
        answer_problem(cls.course, cls.request, cls.i, score=3, max_value=5)
        answer_problem(cls.course, cls.request, cls.j, score=0, max_value=1)
        answer_problem(cls.course, cls.request, cls.l, score=1, max_value=3)
        answer_problem(cls.course, cls.request, cls.n, score=3, max_value=10)

        cls.course_grade = CourseGradeFactory().read(cls.request.user, cls.course)

    @classmethod
    def tearDownClass(cls):
        super(TestScoreForModule, cls).tearDownClass()
        set_current_request(None)

    def test_score_chapter(self):
        earned, possible = self.course_grade.score_for_module(self.a.location)
        self.assertEqual(earned, 9)
        self.assertEqual(possible, 24)

    def test_score_section_many_leaves(self):
        earned, possible = self.course_grade.score_for_module(self.b.location)
        self.assertEqual(earned, 6)
        self.assertEqual(possible, 14)

    def test_score_section_one_leaf(self):
        earned, possible = self.course_grade.score_for_module(self.c.location)
        self.assertEqual(earned, 3)
        self.assertEqual(possible, 10)

    def test_score_vertical_two_leaves(self):
        earned, possible = self.course_grade.score_for_module(self.d.location)
        self.assertEqual(earned, 5)
        self.assertEqual(possible, 10)

    def test_score_vertical_two_leaves_one_unscored(self):
        earned, possible = self.course_grade.score_for_module(self.e.location)
        self.assertEqual(earned, 1)
        self.assertEqual(possible, 4)

    def test_score_vertical_no_score(self):
        earned, possible = self.course_grade.score_for_module(self.f.location)
        self.assertEqual(earned, 0)
        self.assertEqual(possible, 0)

    def test_score_vertical_one_leaf(self):
        earned, possible = self.course_grade.score_for_module(self.g.location)
        self.assertEqual(earned, 3)
        self.assertEqual(possible, 10)

    def test_score_leaf(self):
        earned, possible = self.course_grade.score_for_module(self.h.location)
        self.assertEqual(earned, 2)
        self.assertEqual(possible, 5)

    def test_score_leaf_no_score(self):
        earned, possible = self.course_grade.score_for_module(self.m.location)
        self.assertEqual(earned, 0)
        self.assertEqual(possible, 0)
