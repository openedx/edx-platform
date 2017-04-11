"""
SubsectionGrade Class
"""
from collections import OrderedDict
from lazy import lazy
from logging import getLogger
from lms.djangoapps.grades.scores import get_score, possibly_scored
from lms.djangoapps.grades.models import BlockRecord, PersistentSubsectionGrade
from xmodule import block_metadata_utils, graders
from xmodule.graders import AggregatedScore

from ..config.waffle import waffle, WRITE_ONLY_IF_ENGAGED


log = getLogger(__name__)


class SubsectionGradeBase(object):
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

        self.course_version = getattr(subsection, 'course_version', None)
        self.subtree_edited_timestamp = getattr(subsection, 'subtree_edited_on', None)

        self.graded_total = None  # aggregated grade for all graded problems
        self.all_total = None  # aggregated grade for all problems, regardless of whether they are graded

    @property
    def scores(self):
        """
        List of all problem scores in the subsection.
        """
        return self.locations_to_scores.values()

    @property
    def attempted(self):
        """
        Returns whether any problem in this subsection
        was attempted by the student.
        """

        assert self.all_total is not None, (
            "SubsectionGrade not fully populated yet.  Call init_from_structure or init_from_model "
            "before use."
        )
        return self.all_total.attempted


class ZeroSubsectionGrade(SubsectionGradeBase):
    """
    Class for Subsection Grades with Zero values.
    """
    def __init__(self, subsection, course_data):
        super(ZeroSubsectionGrade, self).__init__(subsection)
        self.graded_total = AggregatedScore(tw_earned=0, tw_possible=None, graded=False, attempted=False)
        self.all_total = AggregatedScore(tw_earned=0, tw_possible=None, graded=self.graded, attempted=False)
        self.course_data = course_data

    @lazy
    def locations_to_scores(self):
        """
        Overrides the locations_to_scores member variable in order
        to return empty scores for all scorable problems in the
        course.
        """
        locations = OrderedDict()  # dict of problem locations to ProblemScore
        for block_key in self.course_data.structure.post_order_traversal(
                filter_func=possibly_scored,
                start_node=self.location,
        ):
            block = self.course_data.structure[block_key]
            if getattr(block, 'has_score', False):
                locations[block_key] = get_score(
                    submissions_scores={}, csm_scores={}, persisted_block=None, block=block,
                )
        return locations


class SubsectionGrade(SubsectionGradeBase):
    """
    Class for Subsection Grades.
    """
    def __init__(self, subsection):
        super(SubsectionGrade, self).__init__(subsection)
        self.locations_to_scores = OrderedDict()  # dict of problem locations to ProblemScore

    def init_from_structure(self, student, course_structure, submissions_scores, csm_scores):
        """
        Compute the grade of this subsection for the given student and course.
        """
        for descendant_key in course_structure.post_order_traversal(
                filter_func=possibly_scored,
                start_node=self.location,
        ):
            self._compute_block_score(descendant_key, course_structure, submissions_scores, csm_scores)

        self.all_total, self.graded_total = graders.aggregate_scores(self.scores)
        self._log_event(log.debug, u"init_from_structure", student)
        return self

    def init_from_model(self, student, model, course_structure, submissions_scores, csm_scores):
        """
        Load the subsection grade from the persisted model.
        """
        for block in model.visible_blocks.blocks:
            self._compute_block_score(block.locator, course_structure, submissions_scores, csm_scores, block)

        self.graded_total = AggregatedScore(
            tw_earned=model.earned_graded,
            tw_possible=model.possible_graded,
            graded=True,
            attempted=model.first_attempted is not None,
        )
        self.all_total = AggregatedScore(
            tw_earned=model.earned_all,
            tw_possible=model.possible_all,
            graded=False,
            attempted=model.first_attempted is not None,
        )
        self._log_event(log.debug, u"init_from_model", student)
        return self

    @classmethod
    def bulk_create_models(cls, student, subsection_grades, course_key):
        """
        Saves the subsection grade in a persisted model.
        """
        subsection_grades = filter(lambda subs_grade: subs_grade._should_persist_per_attempted, subsection_grades)
        return PersistentSubsectionGrade.bulk_create_grades(
            [subsection_grade._persisted_model_params(student) for subsection_grade in subsection_grades],  # pylint: disable=protected-access
            course_key,
        )

    def create_model(self, student):
        """
        Saves the subsection grade in a persisted model.
        """
        if self._should_persist_per_attempted:
            self._log_event(log.debug, u"create_model", student)
            return PersistentSubsectionGrade.create_grade(**self._persisted_model_params(student))

    def update_or_create_model(self, student):
        """
        Saves or updates the subsection grade in a persisted model.
        """
        if self._should_persist_per_attempted:
            self._log_event(log.debug, u"update_or_create_model", student)
            return PersistentSubsectionGrade.update_or_create_grade(**self._persisted_model_params(student))

    @property
    def _should_persist_per_attempted(self):
        """
        Returns whether the SubsectionGrade's model should be
        persisted based on settings and attempted status.
        """
        return not waffle().is_enabled(WRITE_ONLY_IF_ENGAGED) or self.attempted

    def _compute_block_score(
            self,
            block_key,
            course_structure,
            submissions_scores,
            csm_scores,
            persisted_block=None,
    ):
        """
        Compute score for the given block. If persisted_values
        is provided, it is used for possible and weight.
        """
        try:
            block = course_structure[block_key]
        except KeyError:
            # It's possible that the user's access to that
            # block has changed since the subsection grade
            # was last persisted.
            pass
        else:
            if getattr(block, 'has_score', False):
                problem_score = get_score(
                    submissions_scores,
                    csm_scores,
                    persisted_block,
                    block,
                )
                if problem_score:
                    self.locations_to_scores[block_key] = problem_score

    def _persisted_model_params(self, student):
        """
        Returns the parameters for creating/updating the
        persisted model for this subsection grade.
        """
        return dict(
            user_id=student.id,
            usage_key=self.location,
            course_version=self.course_version,
            subtree_edited_timestamp=self.subtree_edited_timestamp,
            earned_all=self.all_total.earned,
            possible_all=self.all_total.possible,
            earned_graded=self.graded_total.earned,
            possible_graded=self.graded_total.possible,
            visible_blocks=self._get_visible_blocks,
            attempted=self.attempted
        )

    @property
    def _get_visible_blocks(self):
        """
        Returns the list of visible blocks.
        """
        return [
            BlockRecord(location, score.weight, score.raw_possible, score.graded)
            for location, score in
            self.locations_to_scores.iteritems()
        ]

    def _log_event(self, log_func, log_statement, student):
        """
        Logs the given statement, for this instance.
        """
        log_func(
            u"Grades: SG.{}, subsection: {}, course: {}, "
            u"version: {}, edit: {}, user: {},"
            u"total: {}/{}, graded: {}/{}".format(
                log_statement,
                self.location,
                self.location.course_key,
                self.course_version,
                self.subtree_edited_timestamp,
                student.id,
                self.all_total.earned,
                self.all_total.possible,
                self.graded_total.earned,
                self.graded_total.possible,
            )
        )
