"""
Tests of the SubsectionGrade classes.
"""


from ddt import data, ddt, unpack

from ..models import PersistentSubsectionGrade
from ..subsection_grade import CreateSubsectionGrade, ReadSubsectionGrade
from .base import GradeTestBase
from .utils import mock_get_score


@ddt
class SubsectionGradeTest(GradeTestBase):

    @data((50, 100, .50), (59.49, 100, .59), (59.51, 100, .60), (59.50, 100, .60), (60.5, 100, .60))
    @unpack
    def test_create_and_read(self, mock_earned, mock_possible, expected_result):
        with mock_get_score(mock_earned, mock_possible):
            # Create a grade that *isn't* saved to the database
            created_grade = CreateSubsectionGrade(
                self.sequence,
                self.course_structure,
                self.subsection_grade_factory._submissions_scores,
                self.subsection_grade_factory._csm_scores,
            )
            self.assertEqual(PersistentSubsectionGrade.objects.count(), 0)
            self.assertEqual(created_grade.percent_graded, expected_result)

            # save to db, and verify object is in database
            created_grade.update_or_create_model(self.request.user)
            self.assertEqual(PersistentSubsectionGrade.objects.count(), 1)

            # read from db, and ensure output matches input
            saved_model = PersistentSubsectionGrade.read_grade(
                user_id=self.request.user.id,
                usage_key=self.sequence.location,
            )
            read_grade = ReadSubsectionGrade(
                self.sequence,
                saved_model,
                self.subsection_grade_factory
            )

            self.assertEqual(created_grade.url_name, read_grade.url_name)
            read_grade.all_total.first_attempted = created_grade.all_total.first_attempted = None
            self.assertEqual(created_grade.all_total, read_grade.all_total)
            self.assertEqual(created_grade.percent_graded, expected_result)

    def test_zero(self):
        with mock_get_score(1, 0):
            grade = CreateSubsectionGrade(
                self.sequence,
                self.course_structure,
                self.subsection_grade_factory._submissions_scores,
                self.subsection_grade_factory._csm_scores,
            )
            self.assertEqual(grade.percent_graded, 0.0)
