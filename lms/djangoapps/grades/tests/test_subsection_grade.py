from ..models import PersistentSubsectionGrade
from ..subsection_grade import SubsectionGrade
from .utils import mock_get_score
from .base import GradeTestBase


class SubsectionGradeTest(GradeTestBase):
    def test_create_and_read(self):
        with mock_get_score(1, 2):
            # Create a grade that *isn't* saved to the database
            created_grade = SubsectionGrade.create(
                self.sequence,
                self.course_structure,
                self.subsection_grade_factory._submissions_scores,
                self.subsection_grade_factory._csm_scores,
            )
            self.assertEqual(PersistentSubsectionGrade.objects.count(), 0)

            # save to db, and verify object is in database
            created_grade.update_or_create_model(self.request.user)
            self.assertEqual(PersistentSubsectionGrade.objects.count(), 1)

            # read from db, and ensure output matches input
            saved_model = PersistentSubsectionGrade.read_grade(
                user_id=self.request.user.id,
                usage_key=self.sequence.location,
            )
            read_grade = SubsectionGrade.read(
                self.sequence,
                saved_model,
                self.course_structure,
                self.subsection_grade_factory._submissions_scores,
                self.subsection_grade_factory._csm_scores,
            )

            self.assertEqual(created_grade.url_name, read_grade.url_name)
            read_grade.all_total.first_attempted = created_grade.all_total.first_attempted = None
            self.assertEqual(created_grade.all_total, read_grade.all_total)
