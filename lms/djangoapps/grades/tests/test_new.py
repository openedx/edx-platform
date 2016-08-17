"""
Test saved subsection grade functionality.
"""

import ddt
from django.conf import settings
from django.http import Http404
from django.test import TestCase
from mock import patch, MagicMock

from capa.tests.response_xml_factory import MultipleChoiceResponseXMLFactory
from courseware.tests.helpers import get_request_for_user
from lms.djangoapps.course_blocks.api import get_course_blocks
from student.models import CourseEnrollment
from student.tests.factories import UserFactory
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory

from ..new.course_grade import CourseGrade, CourseGradeFactory
from ..new.subsection_grade import SubsectionGrade, SubsectionGradeFactory


class GradeTestBase(SharedModuleStoreTestCase):
    """
    Base class for Course- and SubsectionGradeFactory tests.
    """
    @classmethod
    def setUpClass(cls):
        super(GradeTestBase, cls).setUpClass()
        cls.course = CourseFactory.create()
        cls.chapter = ItemFactory.create(
            parent=cls.course,
            category="chapter",
            display_name="Test Chapter"
        )
        cls.sequence = ItemFactory.create(
            parent=cls.chapter,
            category='sequential',
            display_name="Test Sequential 1",
            graded=True
        )
        cls.vertical = ItemFactory.create(
            parent=cls.sequence,
            category='vertical',
            display_name='Test Vertical 1'
        )
        problem_xml = MultipleChoiceResponseXMLFactory().build_xml(
            question_text='The correct answer is Choice 3',
            choices=[False, False, True, False],
            choice_names=['choice_0', 'choice_1', 'choice_2', 'choice_3']
        )
        cls.problem = ItemFactory.create(
            parent=cls.vertical,
            category="problem",
            display_name="Test Problem",
            data=problem_xml
        )

    def setUp(self):
        self.request = get_request_for_user(UserFactory())
        self.client.login(username=self.request.user.username, password="test")
        self.subsection_grade_factory = SubsectionGradeFactory(self.request.user)
        self.course_structure = get_course_blocks(self.request.user, self.course.location)
        self.course.enable_subsection_grades_saved = True
        CourseEnrollment.enroll(self.request.user, self.course.id)


@ddt.ddt
class TestCourseGradeFactory(GradeTestBase):
    """
    Test that CourseGrades are calculated properly
    """

    @classmethod
    def setUpClass(cls):
        super(TestCourseGradeFactory, cls).setUpClass()

    def setUp(self):
        """
        Set up test course
        """
        super(TestCourseGradeFactory, self).setUp()

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
        grade_factory = CourseGradeFactory(self.request.user)
        with patch('lms.djangoapps.grades.new.course_grade._pretend_to_save_course_grades') as mock_save_grades:
            with patch.dict(settings.FEATURES, {'ENABLE_SUBSECTION_GRADES_SAVED': feature_flag}):
                with patch.object(self.course, 'enable_subsection_grades_saved', new=course_setting):
                    grade_factory.create(self.course)
        self.assertEqual(mock_save_grades.called, feature_flag and course_setting)


@ddt.ddt
class SubsectionGradeFactoryTest(GradeTestBase):
    """
    Tests for SubsectionGradeFactory functionality.

    Ensures that SubsectionGrades are created and updated properly, that
    persistent grades are functioning as expected, and that the flag to
    enable saving subsection grades blocks/enables that feature as expected.
    """

    @classmethod
    def setUpClass(cls):
        super(SubsectionGradeFactoryTest, cls).setUpClass()

    def setUp(self):
        """
        Set up test course
        """
        super(SubsectionGradeFactoryTest, self).setUp()

    @patch.dict(settings.FEATURES, {'ENABLE_SUBSECTION_GRADES_SAVED': True})
    def test_create(self):
        """
        Tests to ensure that a persistent subsection grade is created, saved, then fetched on re-request.
        """
        with patch(
            'lms.djangoapps.grades.new.subsection_grade.SubsectionGradeFactory._update_saved_grade',
            wraps=self.subsection_grade_factory._update_saved_grade
        ) as mock_save_grades:
            with patch(
                'lms.djangoapps.grades.new.subsection_grade.SubsectionGradeFactory._get_saved_grade',
                wraps=self.subsection_grade_factory._get_saved_grade
            ) as mock_get_saved_grade:
                with self.assertNumQueries(15):
                    grade_a = self.subsection_grade_factory.create(self.sequence, self.course_structure, self.course)
                self.assertTrue(mock_get_saved_grade.called)
                self.assertTrue(mock_save_grades.called)

                mock_get_saved_grade.reset_mock()
                mock_save_grades.reset_mock()

                with self.assertNumQueries(3):
                    grade_b = self.subsection_grade_factory.create(self.sequence, self.course_structure, self.course)
                self.assertTrue(mock_get_saved_grade.called)
                self.assertFalse(mock_save_grades.called)

        self.assertEqual(grade_a.url_name, grade_b.url_name)
        self.assertEqual(grade_a.all_total, grade_b.all_total)

    @ddt.data(
        (True, True),
        (True, False),
        (False, True),
        (False, False),
    )
    @ddt.unpack
    def test_subsection_grade_feature_gating(self, feature_flag, course_setting):
        # Grades are only saved if the feature flag and the advanced setting are
        # both set to True.
        with patch(
            'lms.djangoapps.grades.models.PersistentSubsectionGrade.read_grade'
        ) as mock_read_saved_grade:
            with patch.dict(settings.FEATURES, {'ENABLE_SUBSECTION_GRADES_SAVED': feature_flag}):
                with patch.object(self.course, 'enable_subsection_grades_saved', new=course_setting):
                    self.subsection_grade_factory.create(self.sequence, self.course_structure, self.course)
        self.assertEqual(mock_read_saved_grade.called, feature_flag and course_setting)


class SubsectionGradeTest(GradeTestBase):
    """
    Tests SubsectionGrade functionality.
    """

    @classmethod
    def setUpClass(cls):
        super(SubsectionGradeTest, cls).setUpClass()

    def setUp(self):
        super(SubsectionGradeTest, self).setUp()
        self.grade = self.subsection_grade_factory.create(self.sequence, self.course_structure, self.course)

    def test_compute(self):
        """
        Assuming the underlying score reporting methods work, test that the score is calculated properly.
        """
        with patch('lms.djangoapps.grades.new.subsection_grade.get_score', return_value=(0,1)):
            # The final 2 parameters are only passed through to our mocked-out get_score method
            self.grade.compute(self.request.user, self.course_structure, None, None)
        self.assertEqual(self.grade.all_total.earned, 0)
        self.assertEqual(self.grade.all_total.possible, 1)

    def test_save(self):
        # save works
        pass

    def test_load_from_data(self):
        # load from data works
        pass
