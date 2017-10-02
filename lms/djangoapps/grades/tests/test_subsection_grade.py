from ..models import PersistentSubsectionGrade
from ..subsection_grade import SubsectionGrade
from .utils import mock_get_score
from .base import  GradeTestBase


class SubsectionGradeTest(GradeTestBase):
    def test_save_and_load(self):
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
