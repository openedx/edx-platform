"""
SubsectionGrade Class
"""
from collections import OrderedDict
from lazy import lazy

from courseware.model_data import ScoresClient
from lms.djangoapps.grades.scores import get_score, possibly_scored
from student.models import anonymous_id_for_user
from submissions import api as submissions_api
from xmodule import block_metadata_utils, graders
from xmodule.graders import Score

from ..models import PersistentSubsectionGradeModel


# TODO
# Note: If the problem weight changes after the grade is saved,
# it may be confusing to the student since the scores won't add
# up.  So consider saving the problem-weight along with the
# visible_block_ids.  It would still be shared across multiple
# users who saw the subsection with the same course-version.


class SubsectionGrade(object):
    """
    Class for Subsection Grades.
    """
    def __init__(self, subsection):
        self.location = subsection.location
        self.display_name = block_metadata_utils.display_name_with_default_escaped(subsection)
        self.url_name = block_metadata_utils.url_name_for_block(subsection)

        self.format = getattr(subsection, 'format', '')
        self.due = getattr(subsection, 'due', None)
        self.graded = getattr(subsection, 'graded', False)

        self.graded_total = None  # aggregated grade for all graded problems
        self.all_total = None  # aggregated grade for all problems, regardless of whether they are graded
        self.locations_to_scores = OrderedDict()  # dict of problem locations to their Score objects

    @lazy
    def scores(self):
        """
        List of all problem scores in the subsection.
        """
        return list(self.locations_to_scores.itervalues())

    def compute(self, student, course_structure, scores_client, submissions_scores):
        """
        Compute the grade of this subsection for the given student and course.
        """
        for descendant_key in course_structure.post_order_traversal(
                filter_func=possibly_scored,
                start_node=self.location,
        ):
            self._compute_block_score(student, descendant_key, course_structure, scores_client, submissions_scores)

        self.all_total, self.graded_total = graders.aggregate_scores(self.scores, self.display_name)

    def save(self, student, subsection, course):
        """
        Persist the SubsectionGrade.
        """
        # shouldn't need to pass course_id to the model API since it's retrievable from the block_key
        PersistentSubsectionGradeModel.save_grade(
            user=student,
            subtree_edited_data=subsection.subtree_edited_date,
            block_key=self.location,
            course_version=course.course_version,
            visible_block_keys=self.locations_to_scores.keys(),
            earned_all=self.all_total.total_correct,
            possible_all=self.all_total.total_possible,
            earned_graded=self.graded_total.total_correct,
            possible_graded=self.graded_total.total_possible,
        )

    def load_from_data(self, model, course_structure, scores_client, submissions_scores):
        """
        Load the subsection grade from the persisted model.
        """
        for block_key in model.visible_block_keys:
            self._compute_block_score(model.user, block_key, course_structure, scores_client, submissions_scores)

        self.graded_total = Score(
            model.graded_total.total_correct,
            model.graded_total.total_possible,
            True,
            self.display_name,
            self.location,
        )
        self.all_total = Score(
            model.all_total.total_correct,
            model.all_total.total_possible,
            False,
            self.display_name,
            self.location,
        )

    def _compute_block_score(self, student, block_key, course_structure, scores_client, submissions_scores):
        """
        Compute score for the given block.
        """
        block = course_structure[block_key]

        if getattr(block, 'has_score', False):
            (earned, possible) = get_score(
                student,
                block,
                scores_client,
                submissions_scores,
            )
            if earned is not None or possible is not None:
                # cannot grade a problem with a denominator of 0
                block_graded = block.graded if possible > 0 else False

                self.locations_to_scores[block.location] = Score(
                    earned,
                    possible,
                    block_graded,
                    block_metadata_utils.display_name_with_default_escaped(block),
                    block.location,
                )


class SubsectionGradeFactory(object):
    """
    Factory for Subsection Grades.
    """
    def __init__(self, student):
        self.student = student

        self._scores_client = None
        self._submissions_scores = None

    def create(self, subsection, course_structure, course):
        """
        Returns the SubsectionGrade object for the student and subsection.
        """
        self._prefetch_scores(course_structure, course)
        return (
            self._get_saved_grade(subsection, course_structure, course) or
            self._compute_and_update_grade(subsection, course_structure, course)
        )

    def _compute_and_update_grade(self, subsection, course_structure, course):
        """
        Freshly computes and updates the grade for the student and subsection.
        """
        subsection_grade = SubsectionGrade(subsection)
        subsection_grade.compute(self.student, course_structure, self._scores_client, self._submissions_scores)
        self._update_saved_grade(subsection_grade, subsection, course)
        return subsection_grade

    def _get_saved_grade(self, subsection, course_structure, course):  # pylint: disable=unused-argument
        """
        Returns the saved grade for the student and subsection.
        """
        if course.enable_subsection_grades_saved:
            # TODO Retrieve the saved grade for the subsection, if it exists.
            pass
            model = PersistentSubsectionGradeModel.get_grade(
                user=self.student,
                block_key=subsection.location,
            )
            subsection_grade = SubsectionGrade(subsection)
            subsection_grade.load_from_data(model, course_structure, self._scores_client, self._submissions_scores)
            return subsection_grade

    def _update_saved_grade(self, subsection_grade, subsection, course):  # pylint: disable=unused-argument
        """
        Updates the saved grade for the student and subsection.
        """
        if course.enable_subsection_grades_saved:
            # TODO Update the saved grade for the subsection.
            pass
            subsection_grade.save(self.student, subsection, course)

    def _prefetch_scores(self, course_structure, course):
        """
        Returns the prefetched scores for the given student and course.
        """
        if not self._scores_client:
            scorable_locations = [block_key for block_key in course_structure if possibly_scored(block_key)]
            self._scores_client = ScoresClient.create_for_locations(
                course.id, self.student.id, scorable_locations
            )
            self._submissions_scores = submissions_api.get_scores(
                unicode(course.id), anonymous_id_for_user(self.student, course.id)
            )
