"""
SubsectionGrade Class
"""
from collections import OrderedDict
from lazy import lazy
from logging import getLogger
from courseware.model_data import ScoresClient
from lms.djangoapps.grades.scores import get_score, possibly_scored
from lms.djangoapps.grades.models import BlockRecord, PersistentSubsectionGrade
from lms.djangoapps.grades.config.models import PersistentGradesEnabledFlag
from student.models import anonymous_id_for_user, User
from submissions import api as submissions_api
from xmodule import block_metadata_utils, graders
from xmodule.graders import Score


log = getLogger(__name__)


class SubsectionGrade(object):
    """
    Class for Subsection Grades.
    """
    def __init__(self, subsection, course):
        self.location = subsection.location
        self.display_name = block_metadata_utils.display_name_with_default_escaped(subsection)
        self.url_name = block_metadata_utils.url_name_for_block(subsection)

        self.format = getattr(subsection, 'format', '')
        self.due = getattr(subsection, 'due', None)
        self.graded = getattr(subsection, 'graded', False)

        self.course_version = getattr(course, 'course_version', None)
        self.subtree_edited_timestamp = subsection.subtree_edited_on

        self.graded_total = None  # aggregated grade for all graded problems
        self.all_total = None  # aggregated grade for all problems, regardless of whether they are graded
        self.locations_to_weighted_scores = OrderedDict()  # dict of problem locations to (Score, weight) tuples

        self._scores = None

    @property
    def scores(self):
        """
        List of all problem scores in the subsection.
        """
        if self._scores is None:
            self._scores = [score for score, _ in self.locations_to_weighted_scores.itervalues()]
        return self._scores

    def init_from_structure(self, student, course_structure, scores_client, submissions_scores):
        """
        Compute the grade of this subsection for the given student and course.
        """
        assert self._scores is None
        for descendant_key in course_structure.post_order_traversal(
                filter_func=possibly_scored,
                start_node=self.location,
        ):
            self._compute_block_score(
                student, descendant_key, course_structure, scores_client, submissions_scores, persisted_values={},
            )
        self.all_total, self.graded_total = graders.aggregate_scores(self.scores, self.display_name, self.location)
        self._log_event(log.warning, u"init_from_structure", student)

    def init_from_model(self, student, model, course_structure, scores_client, submissions_scores):
        """
        Load the subsection grade from the persisted model.
        """
        assert self._scores is None
        for block in model.visible_blocks.blocks:
            persisted_values = {'weight': block.weight, 'possible': block.max_score}
            self._compute_block_score(
                student,
                block.locator,
                course_structure,
                scores_client,
                submissions_scores,
                persisted_values
            )

        self.graded_total = Score(
            earned=model.earned_graded,
            possible=model.possible_graded,
            graded=True,
            section=self.display_name,
            module_id=self.location,
        )
        self.all_total = Score(
            earned=model.earned_all,
            possible=model.possible_all,
            graded=False,
            section=self.display_name,
            module_id=self.location,
        )
        self._log_event(log.warning, u"init_from_model", student)

    @classmethod
    def bulk_create_models(cls, student, subsection_grades, course_key):
        """
        Saves the subsection grade in a persisted model.
        """
        return PersistentSubsectionGrade.bulk_create_grades(
            [subsection_grade._persisted_model_params(student) for subsection_grade in subsection_grades],  # pylint: disable=protected-access
            course_key,
        )

    def create_model(self, student):
        """
        Saves the subsection grade in a persisted model.
        """
        self._log_event(log.info, u"create_model", student)
        return PersistentSubsectionGrade.create_grade(**self._persisted_model_params(student))

    def update_or_create_model(self, student):
        """
        Saves or updates the subsection grade in a persisted model.
        """
        self._log_event(log.info, u"update_or_create_model", student)
        return PersistentSubsectionGrade.update_or_create_grade(**self._persisted_model_params(student))

    def _compute_block_score(
            self,
            student,
            block_key,
            course_structure,
            scores_client,
            submissions_scores,
            persisted_values,
    ):
        """
        Compute score for the given block. If persisted_values
        is provided, it is used for possible and weight.
        """
        block = course_structure[block_key]

        if getattr(block, 'has_score', False):

            possible = persisted_values.get('possible', None)
            weight = persisted_values.get('weight', getattr(block, 'weight', None))

            (earned, possible) = get_score(
                student,
                block,
                scores_client,
                submissions_scores,
                weight,
                possible,
            )

            if earned is not None or possible is not None:
                # There's a chance that the value of graded is not the same
                # value when the problem was scored. Since we get the value
                # from the block_structure.
                #
                # Cannot grade a problem with a denominator of 0.
                # TODO: None > 0 is not python 3 compatible.
                block_graded = block.graded if possible > 0 else False

                self.locations_to_weighted_scores[block.location] = (
                    Score(
                        earned,
                        possible,
                        block_graded,
                        block_metadata_utils.display_name_with_default_escaped(block),
                        block.location,
                    ),
                    weight,
                )

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
        )

    @property
    def _get_visible_blocks(self):
        """
        Returns the list of visible blocks.
        """
        return [
            BlockRecord(location, weight, score.possible)
            for location, (score, weight) in
            self.locations_to_weighted_scores.iteritems()
        ]

    def _log_event(self, log_func, log_statement, student):
        """
        Logs the given statement, for this instance.
        """
        log_func(
            u"Persistent Grades: SG.{}, subsection: {}, course: {}, "
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


class SubsectionGradeFactory(object):
    """
    Factory for Subsection Grades.
    """
    def __init__(self, student, course, course_structure):
        self.student = student
        self.course = course
        self.course_structure = course_structure

        self._cached_subsection_grades = None
        self._unsaved_subsection_grades = []

    def create(self, subsection, block_structure=None, read_only=False):
        """
        Returns the SubsectionGrade object for the student and subsection.

        If block_structure is provided, uses it for finding and computing
        the grade instead of the course_structure passed in earlier.

        If read_only is True, doesn't save any updates to the grades.
        """
        self._log_event(
            log.warning, u"create, read_only: {0}, subsection: {1}".format(read_only, subsection.location)
        )

        block_structure = self._get_block_structure(block_structure)
        subsection_grade = self._get_saved_grade(subsection, block_structure)
        if not subsection_grade:
            subsection_grade = SubsectionGrade(subsection, self.course)
            subsection_grade.init_from_structure(
                self.student, block_structure, self._scores_client, self._submissions_scores
            )
            if PersistentGradesEnabledFlag.feature_enabled(self.course.id):
                if read_only:
                    self._unsaved_subsection_grades.append(subsection_grade)
                else:
                    grade_model = subsection_grade.create_model(self.student)
                    self._update_saved_subsection_grade(subsection.location, grade_model)
        return subsection_grade

    def bulk_create_unsaved(self):
        """
        Bulk creates all the unsaved subsection_grades to this point.
        """
        self._log_event(log.warning, u"bulk_create_unsaved")

        SubsectionGrade.bulk_create_models(self.student, self._unsaved_subsection_grades, self.course.id)
        self._unsaved_subsection_grades = []

    def update(self, subsection, block_structure=None):
        """
        Updates the SubsectionGrade object for the student and subsection.
        """
        # Save ourselves the extra queries if the course does not persist
        # subsection grades.
        if not PersistentGradesEnabledFlag.feature_enabled(self.course.id):
            return

        self._log_event(log.warning, u"update, subsection: {}".format(subsection.location))

        block_structure = self._get_block_structure(block_structure)
        subsection_grade = SubsectionGrade(subsection, self.course)
        subsection_grade.init_from_structure(
            self.student, block_structure, self._scores_client, self._submissions_scores
        )

        grade_model = subsection_grade.update_or_create_model(self.student)
        self._update_saved_subsection_grade(subsection.location, grade_model)
        return subsection_grade

    @lazy
    def _scores_client(self):
        """
        Lazily queries and returns all the scores stored in the user
        state (in CSM) for the course, while caching the result.
        """
        scorable_locations = [block_key for block_key in self.course_structure if possibly_scored(block_key)]
        return ScoresClient.create_for_locations(self.course.id, self.student.id, scorable_locations)

    @lazy
    def _submissions_scores(self):
        """
        Lazily queries and returns the scores stored by the
        Submissions API for the course, while caching the result.
        """
        anonymous_user_id = anonymous_id_for_user(self.student, self.course.id)
        return submissions_api.get_scores(unicode(self.course.id), anonymous_user_id)

    def _get_saved_grade(self, subsection, block_structure):  # pylint: disable=unused-argument
        """
        Returns the saved grade for the student and subsection.
        """
        if not PersistentGradesEnabledFlag.feature_enabled(self.course.id):
            return

        saved_subsection_grade = self._get_saved_subsection_grade(subsection.location)
        if saved_subsection_grade:
            subsection_grade = SubsectionGrade(subsection, self.course)
            subsection_grade.init_from_model(
                self.student, saved_subsection_grade, block_structure, self._scores_client, self._submissions_scores
            )
            return subsection_grade

    def _get_saved_subsection_grade(self, subsection_usage_key):
        """
        Returns the saved value of the subsection grade for
        the given subsection usage key, caching the value.
        Returns None if not found.
        """
        if self._cached_subsection_grades is None:
            self._cached_subsection_grades = {
                record.full_usage_key: record
                for record in PersistentSubsectionGrade.bulk_read_grades(self.student.id, self.course.id)
            }
        return self._cached_subsection_grades.get(subsection_usage_key)

    def _update_saved_subsection_grade(self, subsection_usage_key, subsection_model):
        """
        Updates (or adds) the subsection grade for the given
        subsection usage key in the local cache, iff the cache
        is populated.
        """
        if self._cached_subsection_grades is not None:
            self._cached_subsection_grades[subsection_usage_key] = subsection_model

    def _get_block_structure(self, block_structure):
        """
        If block_structure is None, returns self.course_structure.
        Otherwise, returns block_structure after verifying that the
        given block_structure is a sub-structure of self.course_structure.
        """
        if block_structure:
            if block_structure.root_block_usage_key not in self.course_structure:
                raise ValueError
            return block_structure
        else:
            return self.course_structure

    def _log_event(self, log_func, log_statement):
        """
        Logs the given statement, for this instance.
        """
        log_func(u"Persistent Grades: SGF.{}, course: {}, version: {}, edit: {}, user: {}".format(
            log_statement,
            self.course.id,
            getattr(self.course, 'course_version', None),
            self.course.subtree_edited_on,
            self.student.id,
        ))
