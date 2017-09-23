"""
Test saved subsection grade functionality.
"""
# pylint: disable=protected-access

import datetime
import itertools

import ddt
import pytz
from capa.tests.response_xml_factory import MultipleChoiceResponseXMLFactory
from courseware.access import has_access
from courseware.tests.test_submitting_problems import ProblemSubmissionTestMixin
from django.conf import settings
from lms.djangoapps.course_blocks.api import get_course_blocks
from lms.djangoapps.grades.config.tests.utils import persistent_grades_feature_flags
from mock import patch
from openedx.core.djangolib.testing.utils import get_mock_request
from student.models import CourseEnrollment
from student.tests.factories import UserFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase, SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from xmodule.modulestore.tests.utils import TEST_DATA_DIR
from xmodule.modulestore.xml_importer import import_course_from_xml

from ..config.waffle import ASSUME_ZERO_GRADE_IF_ABSENT, waffle
from ..course_data import CourseData
from ..course_grade import CourseGrade, ZeroCourseGrade
from ..course_grade_factory import CourseGradeFactory
from ..models import PersistentSubsectionGrade
from ..subsection_grade import SubsectionGrade, ZeroSubsectionGrade
from ..subsection_grade_factory import SubsectionGradeFactory
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
            # AED 2017-06-19: make cls.sequence belong to multiple parents,
            # so we can test that DAGs with this shape are handled correctly.
            cls.chapter_2 = ItemFactory.create(
                parent=cls.course,
                category='chapter',
                display_name='Test Chapter 2'
            )
            cls.chapter_2.children.append(cls.sequence.location)
            cls.store.update_item(cls.chapter_2, UserFactory().id)

    def setUp(self):
        super(GradeTestBase, self).setUp()
        self.request = get_mock_request(UserFactory())
        self.client.login(username=self.request.user.username, password="test")
        self._set_grading_policy()
        self.course_structure = get_course_blocks(self.request.user, self.course.location)
        self.subsection_grade_factory = SubsectionGradeFactory(self.request.user, self.course, self.course_structure)
        CourseEnrollment.enroll(self.request.user, self.course.id)

    def _set_grading_policy(self, passing=0.5):
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

    def test_read(self):
        grade_factory = CourseGradeFactory()

        def _assert_read(expected_pass, expected_percent):
            """
            Creates the grade, ensuring it is as expected.
            """
            course_grade = grade_factory.read(self.request.user, self.course)
            self.assertEqual(course_grade.letter_grade, u'Pass' if expected_pass else None)
            self.assertEqual(course_grade.percent, expected_percent)

        with self.assertNumQueries(1), mock_get_score(1, 2):
            _assert_read(expected_pass=False, expected_percent=0)

        with self.assertNumQueries(37), mock_get_score(1, 2):
            grade_factory.update(self.request.user, self.course, force_update_subsections=True)

        with self.assertNumQueries(1):
            _assert_read(expected_pass=True, expected_percent=0.5)

    @patch.dict(settings.FEATURES, {'ASSUME_ZERO_GRADE_IF_ABSENT_FOR_ALL_TESTS': False})
    @ddt.data(*itertools.product((True, False), (True, False)))
    @ddt.unpack
    def test_read_zero(self, assume_zero_enabled, create_if_needed):
        with waffle().override(ASSUME_ZERO_GRADE_IF_ABSENT, active=assume_zero_enabled):
            grade_factory = CourseGradeFactory()
            course_grade = grade_factory.read(self.request.user, self.course, create_if_needed=create_if_needed)
            if create_if_needed or assume_zero_enabled:
                self._assert_zero_grade(course_grade, ZeroCourseGrade if assume_zero_enabled else CourseGrade)
            else:
                self.assertIsNone(course_grade)

    def test_create_zero_subs_grade_for_nonzero_course_grade(self):
        subsection = self.course_structure[self.sequence.location]
        with mock_get_score(1, 2):
            self.subsection_grade_factory.update(subsection)
        course_grade = CourseGradeFactory().update(self.request.user, self.course)
        subsection1_grade = course_grade.subsection_grades[self.sequence.location]
        subsection2_grade = course_grade.subsection_grades[self.sequence2.location]
        self.assertIsInstance(subsection1_grade, SubsectionGrade)
        self.assertIsInstance(subsection2_grade, ZeroSubsectionGrade)

    @ddt.data(True, False)
    def test_iter_force_update(self, force_update):
        with patch('lms.djangoapps.grades.subsection_grade_factory.SubsectionGradeFactory.update') as mock_update:
            set(CourseGradeFactory().iter(
                users=[self.request.user], course=self.course, force_update=force_update
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
                }
            },
            'percent': 0.25,
            'section_breakdown': [
                {
                    'category': 'Homework',
                    'detail': u'Homework 1 - Test Sequential 1 - 50% (1/2)',
                    'label': u'HW 01',
                    'percent': 0.5
                },
                {
                    'category': 'Homework',
                    'detail': u'Homework 2 - Test Sequential 2 - 0% (0/1)',
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
            ]
        }
        self.assertEqual(expected_summary, actual_summary)


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

    def test_create_zero(self):
        """
        Test that a zero grade is returned.
        """
        grade = self.subsection_grade_factory.create(self.sequence)
        self.assertIsInstance(grade, ZeroSubsectionGrade)
        self.assert_grade(grade, 0.0, 1.0)

    def test_update(self):
        """
        Assuming the underlying score reporting methods work,
        test that the score is calculated properly.
        """
        with mock_get_score(1, 2):
            grade = self.subsection_grade_factory.update(self.sequence)
        self.assert_grade(grade, 1, 2)

    def test_write_only_if_engaged(self):
        """
        Test that scores are not persisted when a learner has
        never attempted a problem, but are persisted if the
        learner's state has been deleted.
        """
        with mock_get_score(0, 0, None):
            self.subsection_grade_factory.update(self.sequence)
        # ensure no grades have been persisted
        self.assertEqual(0, len(PersistentSubsectionGrade.objects.all()))

        with mock_get_score(0, 0, None):
            self.subsection_grade_factory.update(self.sequence, score_deleted=True)
        # ensure a grade has been persisted
        self.assertEqual(1, len(PersistentSubsectionGrade.objects.all()))

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
        with waffle().override(ASSUME_ZERO_GRADE_IF_ABSENT, active=assume_zero_enabled):
            course_data = CourseData(self.request.user, structure=self.course_structure)
            chapter_grades = ZeroCourseGrade(self.request.user, course_data).chapter_grades
            for chapter in chapter_grades:
                for section in chapter_grades[chapter]['sections']:
                    for score in section.problem_scores.itervalues():
                        self.assertEqual(score.earned, 0)
                        self.assertEqual(score.first_attempted, None)
                    self.assertEqual(section.all_total.earned, 0)

    @ddt.data(True, False)
    def test_zero_null_scores(self, assume_zero_enabled):
        """
        Creates a zero course grade and ensures that null scores aren't included in the section problem scores.
        """
        with waffle().override(ASSUME_ZERO_GRADE_IF_ABSENT, active=assume_zero_enabled):
            with patch('lms.djangoapps.grades.subsection_grade.get_score', return_value=None):
                course_data = CourseData(self.request.user, structure=self.course_structure)
                chapter_grades = ZeroCourseGrade(self.request.user, course_data).chapter_grades
                for chapter in chapter_grades:
                    self.assertNotEqual({}, chapter_grades[chapter]['sections'])
                    for section in chapter_grades[chapter]['sections']:
                        self.assertEqual({}, section.problem_scores)


class SubsectionGradeTest(GradeTestBase):
    """
    Tests SubsectionGrade functionality.
    """

    def test_save_and_load(self):
        """
        Test that grades are persisted to the database properly,
        and that loading saved grades returns the same data.
        """
        with mock_get_score(1, 2):
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
            loaded_grade.all_total.first_attempted = input_grade.all_total.first_attempted = None
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
                [(earned_per_block, None, earned_per_block, None, datetime.datetime(2000, 1, 1))],
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
