"""
Tests for the SubsectionGradeFactory class.
"""


import ddt
from django.conf import settings
from mock import patch

from lms.djangoapps.courseware.tests.test_submitting_problems import ProblemSubmissionTestMixin
from lms.djangoapps.grades.config.tests.utils import persistent_grades_feature_flags
from common.djangoapps.student.tests.factories import UserFactory

from ..constants import GradeOverrideFeatureEnum
from ..models import PersistentSubsectionGrade, PersistentSubsectionGradeOverride
from ..subsection_grade_factory import ZeroSubsectionGrade
from .base import GradeTestBase
from .utils import mock_get_score


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
        self.assertEqual(
            (grade.graded_total.earned, grade.graded_total.possible),
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

    def test_update_if_higher_zero_denominator(self):
        """
        Test that we get an updated score of 0, and not a ZeroDivisionError,
        when dealing with an invalid score like 0/0.
        """
        # This will create a PersistentSubsectionGrade with a score of 0/0.
        with mock_get_score(0, 0):
            grade = self.subsection_grade_factory.update(self.sequence)
        self.assert_grade(grade, 0, 0)

        # Ensure that previously storing a possible score of 0
        # does not raise a ZeroDivisionError when updating the grade.
        with mock_get_score(2, 2):
            grade = self.subsection_grade_factory.update(self.sequence, only_if_higher=True)
        self.assert_grade(grade, 2, 2)

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

    @ddt.data(
        (0, None),
        (None, 3),
        (None, None),
        (0, 3),
    )
    @ddt.unpack
    def test_update_with_override(self, earned_graded_override, possible_graded_override):
        """
        Tests that when a PersistentSubsectionGradeOverride exists, the update()
        method returns a CreateSubsectionGrade with scores that account
        for the override.
        """
        # first, do an update to create a persistent grade
        with mock_get_score(2, 3):
            grade = self.subsection_grade_factory.update(self.sequence)
            self.assert_grade(grade, 2, 3)

        # there should only be one persistent grade
        persistent_grade = PersistentSubsectionGrade.objects.first()
        self.assertEqual(2, persistent_grade.earned_graded)
        self.assertEqual(3, persistent_grade.possible_graded)

        # Now create the override
        PersistentSubsectionGradeOverride.update_or_create_override(
            UserFactory(),
            persistent_grade,
            earned_graded_override=earned_graded_override,
            earned_all_override=earned_graded_override,
            possible_graded_override=possible_graded_override,
            feature=GradeOverrideFeatureEnum.gradebook,
        )

        # Now, even if the problem scores interface gives us a 2/3,
        # the subsection grade returned should be 0/3 due to the override.
        with mock_get_score(2, 3):
            grade = self.subsection_grade_factory.update(self.sequence)
            expected_earned = earned_graded_override
            if earned_graded_override is None:
                expected_earned = persistent_grade.earned_graded
            expected_possible = possible_graded_override
            if possible_graded_override is None:
                expected_possible = persistent_grade.possible_graded
            self.assert_grade(grade, expected_earned, expected_possible)
