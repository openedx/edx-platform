"""
Test saved subsection grade functionality.
"""
# pylint: disable=protected-access

import datetime

import ddt
from django.conf import settings
import itertools

from mock import patch
import pytz

from capa.tests.response_xml_factory import MultipleChoiceResponseXMLFactory
from courseware.access import has_access
from courseware.tests.test_submitting_problems import ProblemSubmissionTestMixin
from lms.djangoapps.course_blocks.api import get_course_blocks
from lms.djangoapps.grades.config.tests.utils import persistent_grades_feature_flags
from openedx.core.djangolib.testing.utils import get_mock_request
from student.models import CourseEnrollment
from student.tests.factories import UserFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase, SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from xmodule.modulestore.tests.utils import TEST_DATA_DIR
from xmodule.modulestore.xml_importer import import_course_from_xml

from ..config.waffle import waffle, ASSUME_ZERO_GRADE_IF_ABSENT, WRITE_ONLY_IF_ENGAGED
from ..models import PersistentSubsectionGrade
from ..new.course_data import CourseData
from ..new.course_grade_factory import CourseGradeFactory
from ..new.course_grade import ZeroCourseGrade, CourseGrade
from ..new.subsection_grade_factory import SubsectionGradeFactory
from ..new.subsection_grade import ZeroSubsectionGrade, SubsectionGrade
from .utils import mock_get_score, mock_get_submissions_score


class GradeTestBase(SharedModuleStoreTestCase):
    """
    Base class for Course- and SubsectionGradeFactory tests.
    """
    @classmethod
    def setUpClass(cls):
        super(GradeTestBase, cls).setUpClass()
        cls.course = CourseFactory.create()
        with cls.store.bulk_operations(cls.course.id):
            cls.chapter = ItemFactory.create(
                parent=cls.course,
                category="chapter",
                display_name="Test Chapter"
            )
            cls.sequence = ItemFactory.create(
                parent=cls.chapter,
                category='sequential',
                display_name="Test Sequential 1",
                graded=True,
                format="Homework"
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
            cls.sequence2 = ItemFactory.create(
                parent=cls.chapter,
                category='sequential',
                display_name="Test Sequential 2",
                graded=True,
                format="Homework"
            )
            cls.problem2 = ItemFactory.create(
                parent=cls.sequence2,
                category="problem",
                display_name="Test Problem",
                data=problem_xml
            )

    def setUp(self):
        super(GradeTestBase, self).setUp()
        self.request = get_mock_request(UserFactory())
        self.client.login(username=self.request.user.username, password="test")
        self._update_grading_policy()
        self.course_structure = get_course_blocks(self.request.user, self.course.location)
        self.subsection_grade_factory = SubsectionGradeFactory(self.request.user, self.course, self.course_structure)
        CourseEnrollment.enroll(self.request.user, self.course.id)

    def _update_grading_policy(self, passing=0.5):
        """
        Updates the course's grading policy.
        """
        self.grading_policy = {
            "GRADER": [
                {
                    "type": "Homework",
                    "min_count": 1,
                    "drop_count": 0,
                    "short_label": "HW",
                    "weight": 1.0,
                },
            ],
            "GRADE_CUTOFFS": {
                "Pass": passing,
            },
        }
        self.course.set_grading_policy(self.grading_policy)
        self.store.update_item(self.course, 0)


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
        Test to ensure a grade can ba calculated for a student in a course, even if they themselves do not have access.
        """
        invisible_course = CourseFactory.create(visible_to_staff_only=True)
        access = has_access(self.request.user, 'load', invisible_course)
        self.assertEqual(access.has_access, False)
        self.assertEqual(access.error_code, 'not_visible_to_user')

        # with self.assertNoExceptionRaised: <- this isn't a real method, it's an implicit assumption
        grade = CourseGradeFactory().create(self.request.user, invisible_course)
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
            with patch('lms.djangoapps.grades.models.PersistentCourseGrade.read_course_grade') as mock_read_grade:
                grade_factory.create(self.request.user, self.course)
        self.assertEqual(mock_read_grade.called, feature_flag and course_setting)

    def test_create(self):
        grade_factory = CourseGradeFactory()

        def _assert_create(expected_pass):
            """
            Creates the grade, ensuring it is as expected.
            """
            course_grade = grade_factory.create(self.request.user, self.course)
            self.assertEqual(course_grade.letter_grade, u'Pass' if expected_pass else None)
            self.assertEqual(course_grade.percent, 0.5)

        with self.assertNumQueries(12), mock_get_score(1, 2):
            _assert_create(expected_pass=True)

        with self.assertNumQueries(14), mock_get_score(1, 2):
            grade_factory.update(self.request.user, self.course)

        with self.assertNumQueries(1):
            _assert_create(expected_pass=True)

        self._update_grading_policy(passing=0.9)

        with self.assertNumQueries(8):
            _assert_create(expected_pass=False)

    @ddt.data(True, False)
    def test_create_zero(self, assume_zero_enabled):
        with waffle().override(ASSUME_ZERO_GRADE_IF_ABSENT, active=assume_zero_enabled):
            grade_factory = CourseGradeFactory()
            course_grade = grade_factory.create(self.request.user, self.course)
            self._assert_zero_grade(course_grade, ZeroCourseGrade if assume_zero_enabled else CourseGrade)

    def test_create_zero_subs_grade_for_nonzero_course_grade(self):
        with waffle().override(ASSUME_ZERO_GRADE_IF_ABSENT), waffle().override(WRITE_ONLY_IF_ENGAGED):
            subsection = self.course_structure[self.sequence.location]
            with mock_get_score(1, 2):
                self.subsection_grade_factory.update(subsection)
            course_grade = CourseGradeFactory().update(self.request.user, self.course)
            subsection1_grade = course_grade.subsection_grades[self.sequence.location]
            subsection2_grade = course_grade.subsection_grades[self.sequence2.location]
            self.assertIsInstance(subsection1_grade, SubsectionGrade)
            self.assertIsInstance(subsection2_grade, ZeroSubsectionGrade)

    def test_read(self):
        grade_factory = CourseGradeFactory()
        with mock_get_score(1, 2):
            grade_factory.update(self.request.user, self.course)

        def _assert_read():
            """
            Reads the grade, ensuring it is as expected and requires just one query
            """
            with self.assertNumQueries(1):
                course_grade = grade_factory.read(self.request.user, self.course)
            self.assertEqual(course_grade.letter_grade, u'Pass')
            self.assertEqual(course_grade.percent, 0.5)

        _assert_read()
        self._update_grading_policy(passing=0.9)
        _assert_read()

    @ddt.data(True, False)
    def test_read_zero(self, assume_zero_enabled):
        with waffle().override(ASSUME_ZERO_GRADE_IF_ABSENT, active=assume_zero_enabled):
            grade_factory = CourseGradeFactory()
            course_grade = grade_factory.read(self.request.user, course_key=self.course.id)
            if assume_zero_enabled:
                self._assert_zero_grade(course_grade, ZeroCourseGrade)
            else:
                self.assertIsNone(course_grade)


@ddt.ddt
class TestSubsectionGradeFactory(ProblemSubmissionTestMixin, GradeTestBase):
    """
    Tests for SubsectionGradeFactory functionality.

    Ensures that SubsectionGrades are created and updated properly, that
    persistent grades are functioning as expected, and that the flag to
    enable saving subsection grades blocks/enables that feature as expected.
    """

    def assert_grade(self, grade, expected_earned, expected_possible):
        """
        Asserts that the given grade object has the expected score.
        """
        self.assertEqual(
            (grade.all_total.earned, grade.all_total.possible),
            (expected_earned, expected_possible),
        )

    def test_create(self):
        """
        Assuming the underlying score reporting methods work,
        test that the score is calculated properly.
        """
        with mock_get_score(1, 2):
            grade = self.subsection_grade_factory.create(self.sequence)
        self.assert_grade(grade, 1, 2)

    def test_create_internals(self):
        """
        Tests to ensure that a persistent subsection grade is
        created, saved, then fetched on re-request.
        """
        with patch(
            'lms.djangoapps.grades.new.subsection_grade.PersistentSubsectionGrade.create_grade',
            wraps=PersistentSubsectionGrade.create_grade
        ) as mock_create_grade:
            with patch(
                'lms.djangoapps.grades.new.subsection_grade_factory.SubsectionGradeFactory._get_bulk_cached_grade',
                wraps=self.subsection_grade_factory._get_bulk_cached_grade
            ) as mock_get_bulk_cached_grade:
                with self.assertNumQueries(14):
                    grade_a = self.subsection_grade_factory.create(self.sequence)
                self.assertTrue(mock_get_bulk_cached_grade.called)
                self.assertTrue(mock_create_grade.called)

                mock_get_bulk_cached_grade.reset_mock()
                mock_create_grade.reset_mock()

                with self.assertNumQueries(0):
                    grade_b = self.subsection_grade_factory.create(self.sequence)
                self.assertTrue(mock_get_bulk_cached_grade.called)
                self.assertFalse(mock_create_grade.called)

        self.assertEqual(grade_a.url_name, grade_b.url_name)
        grade_b.all_total.attempted = False  # TODO TNL-5930
        self.assertEqual(grade_a.all_total, grade_b.all_total)

    def test_update(self):
        """
        Assuming the underlying score reporting methods work,
        test that the score is calculated properly.
        """
        with mock_get_score(1, 2):
            grade = self.subsection_grade_factory.update(self.sequence)
        self.assert_grade(grade, 1, 2)

    def test_update_if_higher(self):
        def verify_update_if_higher(mock_score, expected_grade):
            """
            Updates the subsection grade and verifies the
            resulting grade is as expected.
            """
            with mock_get_score(*mock_score):
                grade = self.subsection_grade_factory.update(self.sequence, only_if_higher=True)
                self.assert_grade(grade, *expected_grade)

        verify_update_if_higher((1, 2), (1, 2))  # previous value was non-existent
        verify_update_if_higher((2, 4), (2, 4))  # previous value was equivalent
        verify_update_if_higher((1, 4), (2, 4))  # previous value was greater
        verify_update_if_higher((3, 4), (3, 4))  # previous value was less

    @patch.dict(settings.FEATURES, {'PERSISTENT_GRADES_ENABLED_FOR_ALL_TESTS': False})
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
            'lms.djangoapps.grades.models.PersistentSubsectionGrade.bulk_read_grades'
        ) as mock_read_saved_grade:
            with persistent_grades_feature_flags(
                global_flag=feature_flag,
                enabled_for_all_courses=False,
                course_id=self.course.id,
                enabled_for_course=course_setting
            ):
                self.subsection_grade_factory.create(self.sequence)
        self.assertEqual(mock_read_saved_grade.called, feature_flag and course_setting)


class ZeroGradeTest(GradeTestBase):
    """
    Tests ZeroCourseGrade (and, implicitly, ZeroSubsectionGrade)
    functionality.
    """
    def test_zero(self):
        """
        Creates a ZeroCourseGrade and ensures it's empty.
        """
        course_data = CourseData(self.request.user, structure=self.course_structure)
        chapter_grades = ZeroCourseGrade(self.request.user, course_data).chapter_grades
        for chapter in chapter_grades:
            for section in chapter_grades[chapter]['sections']:
                for score in section.locations_to_scores.itervalues():
                    self.assertEqual(score.earned, 0)
                    self.assertEqual(score.attempted, False)
                self.assertEqual(section.all_total.earned, 0)


class SubsectionGradeTest(GradeTestBase):
    """
    Tests SubsectionGrade functionality.
    """

    def test_save_and_load(self):
        """
        Test that grades are persisted to the database properly,
        and that loading saved grades returns the same data.
        """
        # Create a grade that *isn't* saved to the database
        input_grade = SubsectionGrade(self.sequence)
        input_grade.init_from_structure(
            self.request.user,
            self.course_structure,
            self.subsection_grade_factory._submissions_scores,
            self.subsection_grade_factory._csm_scores,
        )
        self.assertEqual(PersistentSubsectionGrade.objects.count(), 0)

        # save to db, and verify object is in database
        input_grade.create_model(self.request.user)
        self.assertEqual(PersistentSubsectionGrade.objects.count(), 1)

        # load from db, and ensure output matches input
        loaded_grade = SubsectionGrade(self.sequence)
        saved_model = PersistentSubsectionGrade.read_grade(
            user_id=self.request.user.id,
            usage_key=self.sequence.location,
        )
        loaded_grade.init_from_model(
            self.request.user,
            saved_model,
            self.course_structure,
            self.subsection_grade_factory._submissions_scores,
            self.subsection_grade_factory._csm_scores,
        )

        self.assertEqual(input_grade.url_name, loaded_grade.url_name)
        loaded_grade.all_total.attempted = False  # TODO TNL-5930
        self.assertEqual(input_grade.all_total, loaded_grade.all_total)


@ddt.ddt
class TestMultipleProblemTypesSubsectionScores(SharedModuleStoreTestCase):
    """
    Test grading of different problem types.
    """

    SCORED_BLOCK_COUNT = 7
    ACTUAL_TOTAL_POSSIBLE = 17.0

    @classmethod
    def setUpClass(cls):
        super(TestMultipleProblemTypesSubsectionScores, cls).setUpClass()
        cls.load_scoreable_course()
        chapter1 = cls.course.get_children()[0]
        cls.seq1 = chapter1.get_children()[0]

    def setUp(self):
        super(TestMultipleProblemTypesSubsectionScores, self).setUp()
        password = u'test'
        self.student = UserFactory.create(is_staff=False, username=u'test_student', password=password)
        self.client.login(username=self.student.username, password=password)
        self.request = get_mock_request(self.student)
        self.course_structure = get_course_blocks(self.student, self.course.location)

    @classmethod
    def load_scoreable_course(cls):
        """
        This test course lives at `common/test/data/scoreable`.

        For details on the contents and structure of the file, see
        `common/test/data/scoreable/README`.
        """

        course_items = import_course_from_xml(
            cls.store,
            'test_user',
            TEST_DATA_DIR,
            source_dirs=['scoreable'],
            static_content_store=None,
            target_id=cls.store.make_course_key('edX', 'scoreable', '3000'),
            raise_on_failure=True,
            create_if_not_present=True,
        )

        cls.course = course_items[0]

    def test_score_submission_for_all_problems(self):
        subsection_factory = SubsectionGradeFactory(
            self.student,
            course_structure=self.course_structure,
            course=self.course,
        )
        score = subsection_factory.create(self.seq1)

        self.assertEqual(score.all_total.earned, 0.0)
        self.assertEqual(score.all_total.possible, self.ACTUAL_TOTAL_POSSIBLE)

        # Choose arbitrary, non-default values for earned and possible.
        earned_per_block = 3.0
        possible_per_block = 7.0
        with mock_get_submissions_score(earned_per_block, possible_per_block) as mock_score:
            # Configure one block to return no possible score, the rest to return 3.0 earned / 7.0 possible
            block_count = self.SCORED_BLOCK_COUNT - 1
            mock_score.side_effect = itertools.chain(
                [(earned_per_block, None, earned_per_block, None, True)],
                itertools.repeat(mock_score.return_value)
            )
            score = subsection_factory.update(self.seq1)
        self.assertEqual(score.all_total.earned, earned_per_block * block_count)
        self.assertEqual(score.all_total.possible, possible_per_block * block_count)


@ddt.ddt
class TestVariedMetadata(ProblemSubmissionTestMixin, ModuleStoreTestCase):
    """
    Test that changing the metadata on a block has the desired effect on the
    persisted score.
    """
    default_problem_metadata = {
        u'graded': True,
        u'weight': 2.5,
        u'due': datetime.datetime(2099, 3, 15, 12, 30, 0, tzinfo=pytz.utc),
    }

    def setUp(self):
        super(TestVariedMetadata, self).setUp()
        self.course = CourseFactory.create()
        with self.store.bulk_operations(self.course.id):
            self.chapter = ItemFactory.create(
                parent=self.course,
                category="chapter",
                display_name="Test Chapter"
            )
            self.sequence = ItemFactory.create(
                parent=self.chapter,
                category='sequential',
                display_name="Test Sequential 1",
                graded=True
            )
            self.vertical = ItemFactory.create(
                parent=self.sequence,
                category='vertical',
                display_name='Test Vertical 1'
            )
        self.problem_xml = u'''
            <problem url_name="capa-optionresponse">
              <optionresponse>
                <optioninput options="('Correct', 'Incorrect')" correct="Correct"></optioninput>
                <optioninput options="('Correct', 'Incorrect')" correct="Correct"></optioninput>
              </optionresponse>
            </problem>
        '''
        self.request = get_mock_request(UserFactory())
        self.client.login(username=self.request.user.username, password="test")
        CourseEnrollment.enroll(self.request.user, self.course.id)

    def _get_altered_metadata(self, alterations):
        """
        Returns a copy of the default_problem_metadata dict updated with the
        specified alterations.
        """
        metadata = self.default_problem_metadata.copy()
        metadata.update(alterations)
        return metadata

    def _add_problem_with_alterations(self, alterations):
        """
        Add a problem to the course with the specified metadata alterations.
        """

        metadata = self._get_altered_metadata(alterations)
        ItemFactory.create(
            parent=self.vertical,
            category="problem",
            display_name="problem",
            data=self.problem_xml,
            metadata=metadata,
        )

    def _get_score(self):
        """
        Return the score of the test problem when one correct problem (out of
        two) is submitted.
        """

        self.submit_question_answer(u'problem', {u'2_1': u'Correct'})
        course_structure = get_course_blocks(self.request.user, self.course.location)
        subsection_factory = SubsectionGradeFactory(
            self.request.user,
            course_structure=course_structure,
            course=self.course,
        )
        return subsection_factory.create(self.sequence)

    @ddt.data(
        ({}, 1.25, 2.5),
        ({u'weight': 27}, 13.5, 27),
        ({u'weight': 1.0}, 0.5, 1.0),
        ({u'weight': 0.0}, 0.0, 0.0),
        ({u'weight': None}, 1.0, 2.0),
    )
    @ddt.unpack
    def test_weight_metadata_alterations(self, alterations, expected_earned, expected_possible):
        self._add_problem_with_alterations(alterations)
        score = self._get_score()
        self.assertEqual(score.all_total.earned, expected_earned)
        self.assertEqual(score.all_total.possible, expected_possible)

    @ddt.data(
        ({u'graded': True}, 1.25, 2.5),
        ({u'graded': False}, 0.0, 0.0),
    )
    @ddt.unpack
    def test_graded_metadata_alterations(self, alterations, expected_earned, expected_possible):
        self._add_problem_with_alterations(alterations)
        score = self._get_score()
        self.assertEqual(score.graded_total.earned, expected_earned)
        self.assertEqual(score.graded_total.possible, expected_possible)


class TestCourseGradeLogging(ProblemSubmissionTestMixin, SharedModuleStoreTestCase):
    """
    Tests logging in the course grades module.
    Uses a larger course structure than other
    unit tests.
    """
    def setUp(self):
        super(TestCourseGradeLogging, self).setUp()
        self.course = CourseFactory.create()
        with self.store.bulk_operations(self.course.id):
            self.chapter = ItemFactory.create(
                parent=self.course,
                category="chapter",
                display_name="Test Chapter"
            )
            self.sequence = ItemFactory.create(
                parent=self.chapter,
                category='sequential',
                display_name="Test Sequential 1",
                graded=True
            )
            self.sequence_2 = ItemFactory.create(
                parent=self.chapter,
                category='sequential',
                display_name="Test Sequential 2",
                graded=True
            )
            self.sequence_3 = ItemFactory.create(
                parent=self.chapter,
                category='sequential',
                display_name="Test Sequential 3",
                graded=False
            )
            self.vertical = ItemFactory.create(
                parent=self.sequence,
                category='vertical',
                display_name='Test Vertical 1'
            )
            self.vertical_2 = ItemFactory.create(
                parent=self.sequence_2,
                category='vertical',
                display_name='Test Vertical 2'
            )
            self.vertical_3 = ItemFactory.create(
                parent=self.sequence_3,
                category='vertical',
                display_name='Test Vertical 3'
            )
            problem_xml = MultipleChoiceResponseXMLFactory().build_xml(
                question_text='The correct answer is Choice 2',
                choices=[False, False, True, False],
                choice_names=['choice_0', 'choice_1', 'choice_2', 'choice_3']
            )
            self.problem = ItemFactory.create(
                parent=self.vertical,
                category="problem",
                display_name="test_problem_1",
                data=problem_xml
            )
            self.problem_2 = ItemFactory.create(
                parent=self.vertical_2,
                category="problem",
                display_name="test_problem_2",
                data=problem_xml
            )
            self.problem_3 = ItemFactory.create(
                parent=self.vertical_3,
                category="problem",
                display_name="test_problem_3",
                data=problem_xml
            )
        self.request = get_mock_request(UserFactory())
        self.client.login(username=self.request.user.username, password="test")
        self.course_structure = get_course_blocks(self.request.user, self.course.location)
        self.subsection_grade_factory = SubsectionGradeFactory(self.request.user, self.course, self.course_structure)
        CourseEnrollment.enroll(self.request.user, self.course.id)

    def _create_course_grade_and_check_logging(
            self,
            factory_method,
            log_mock,
            log_statement,
    ):
        """
        Creates a course grade and asserts that the associated logging
        matches the expected totals passed in to the function.
        """
        factory_method(self.request.user, self.course)
        self.assertIn(log_statement, log_mock.info.call_args[0][0])
        self.assertIn(unicode(self.course.id), log_mock.info.call_args[0][1])
        self.assertEquals(self.request.user.id, log_mock.info.call_args[0][2])

    def test_course_grade_logging(self):
        grade_factory = CourseGradeFactory()
        with persistent_grades_feature_flags(
            global_flag=True,
            enabled_for_all_courses=False,
            course_id=self.course.id,
            enabled_for_course=True
        ):
            with patch('lms.djangoapps.grades.new.course_grade_factory.log') as log_mock:
                # returns Zero when no grade, with ASSUME_ZERO_GRADE_IF_ABSENT
                with waffle().override(ASSUME_ZERO_GRADE_IF_ABSENT, active=True):
                    self._create_course_grade_and_check_logging(grade_factory.create, log_mock, u'CreateZero')

                # read, but not persisted
                self._create_course_grade_and_check_logging(grade_factory.create, log_mock, u'Update')

                # update and persist
                self._create_course_grade_and_check_logging(grade_factory.update, log_mock, u'Update')

                # read from persistence, using create
                self._create_course_grade_and_check_logging(grade_factory.create, log_mock, u'Read')

                # read from persistence, using read
                self._create_course_grade_and_check_logging(grade_factory.read, log_mock, u'Read')
