"""
SubsectionGrade Class
"""
from collections import OrderedDict
from contextlib import contextmanager
from django.db import transaction
from django.db.utils import DatabaseError
from lazy import lazy
from logging import getLogger
from courseware.model_data import ScoresClient
from lms.djangoapps.grades.scores import get_score, possibly_scored
from lms.djangoapps.grades.models import BlockRecord, PersistentSubsectionGrade
from lms.djangoapps.grades.config.models import PersistentGradesEnabledFlag
from openedx.core.lib.grade_utils import is_score_higher
from student.models import anonymous_id_for_user, User
from submissions import api as submissions_api
from traceback import format_exc
from xmodule import block_metadata_utils, graders
from xmodule.graders import AggregatedScore


log = getLogger(__name__)


@contextmanager
def persistence_safe_fallback():
    """
    A context manager intended to be used to wrap robust grades database-specific code that can be ignored on failure.
    """
    try:
        with transaction.atomic():
            yield
    except DatabaseError:
        # Error deliberately logged, then swallowed. It's assumed that the wrapped code is not guaranteed to succeed.
        # TODO: enqueue a celery task to finish the task asynchronously, see TNL-5471
        log.warning("Persistent Grades: database_error.safe_fallback.\n{}".format(format_exc()))


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
        self.locations_to_scores = OrderedDict()  # dict of problem locations to ProblemScore

    @property
    def scores(self):
        """
        List of all problem scores in the subsection.
        """
        return self.locations_to_scores.values()

    def init_from_structure(self, student, course_structure, submissions_scores, csm_scores):
        """
        Compute the grade of this subsection for the given student and course.
        """
        for descendant_key in course_structure.post_order_traversal(
                filter_func=possibly_scored,
                start_node=self.location,
        ):
            self._compute_block_score(descendant_key, course_structure, submissions_scores, csm_scores)

        self.all_total, self.graded_total = graders.aggregate_scores(self.scores, self.display_name, self.location)
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
            display_name=self.display_name,
            module_id=self.location,
        )
        self.all_total = AggregatedScore(
            tw_earned=model.earned_all,
            tw_possible=model.possible_all,
            graded=False,
            display_name=self.display_name,
            module_id=self.location,
        )
        self._log_event(log.debug, u"init_from_model", student)
        return self

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
        self._log_event(log.debug, u"create_model", student)
        return PersistentSubsectionGrade.create_grade(**self._persisted_model_params(student))

    def update_or_create_model(self, student):
        """
        Saves or updates the subsection grade in a persisted model.
        """
        self._log_event(log.debug, u"update_or_create_model", student)
        return PersistentSubsectionGrade.update_or_create_grade(**self._persisted_model_params(student))

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
        block = course_structure[block_key]

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
            log.debug, u"create, read_only: {0}, subsection: {1}".format(read_only, subsection.location)
        )

        block_structure = self._get_block_structure(block_structure)
        subsection_grade = self._get_bulk_cached_grade(subsection, block_structure)
        if not subsection_grade:
            subsection_grade = SubsectionGrade(subsection, self.course).init_from_structure(
                self.student, block_structure, self._submissions_scores, self._csm_scores,
            )
            if PersistentGradesEnabledFlag.feature_enabled(self.course.id):
                if read_only:
                    self._unsaved_subsection_grades.append(subsection_grade)
                else:
                    with persistence_safe_fallback():
                        grade_model = subsection_grade.create_model(self.student)
                        self._update_saved_subsection_grade(subsection.location, grade_model)
        return subsection_grade

    def bulk_create_unsaved(self):
        """
        Bulk creates all the unsaved subsection_grades to this point.
        """
        self._log_event(log.debug, u"bulk_create_unsaved")

        with persistence_safe_fallback():
            SubsectionGrade.bulk_create_models(self.student, self._unsaved_subsection_grades, self.course.id)
            self._unsaved_subsection_grades = []

    def update(self, subsection, block_structure=None, only_if_higher=None):
        """
        Updates the SubsectionGrade object for the student and subsection.
        """
        self._log_event(log.warning, u"update, subsection: {}".format(subsection.location))

        block_structure = self._get_block_structure(block_structure)
        calculated_grade = SubsectionGrade(subsection, self.course).init_from_structure(
            self.student, block_structure, self._submissions_scores, self._csm_scores,
        )

        if only_if_higher:
            try:
                grade_model = PersistentSubsectionGrade.read_grade(self.student.id, subsection.location)
            except PersistentSubsectionGrade.DoesNotExist:
                pass
            else:
                orig_subsection_grade = SubsectionGrade(subsection, self.course).init_from_model(
                    self.student, grade_model, block_structure, self._submissions_scores, self._csm_scores,
                )
                if not is_score_higher(
                        orig_subsection_grade.graded_total.earned,
                        orig_subsection_grade.graded_total.possible,
                        calculated_grade.graded_total.earned,
                        calculated_grade.graded_total.possible,
                ):
                    return orig_subsection_grade

        if PersistentGradesEnabledFlag.feature_enabled(self.course.id):
            grade_model = calculated_grade.update_or_create_model(self.student)
            self._update_saved_subsection_grade(subsection.location, grade_model)

        return calculated_grade

    @lazy
    def _csm_scores(self):
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

    def _get_bulk_cached_grade(self, subsection, block_structure):  # pylint: disable=unused-argument
        """
        Returns the student's SubsectionGrade for the subsection,
        while caching the results of a bulk retrieval for the
        course, for future access of other subsections.
        Returns None if not found.
        """
        if not PersistentGradesEnabledFlag.feature_enabled(self.course.id):
            return

        saved_subsection_grades = self._get_bulk_cached_subsection_grades()
        subsection_grade = saved_subsection_grades.get(subsection.location)
        if subsection_grade:
            return SubsectionGrade(subsection, self.course).init_from_model(
                self.student, subsection_grade, block_structure, self._submissions_scores, self._csm_scores,
            )

    def _get_bulk_cached_subsection_grades(self):
        """
        Returns and caches (for future access) the results of
        a bulk retrieval of all subsection grades in the course.
        """
        if self._cached_subsection_grades is None:
            self._cached_subsection_grades = {
                record.full_usage_key: record
                for record in PersistentSubsectionGrade.bulk_read_grades(self.student.id, self.course.id)
            }
        return self._cached_subsection_grades

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
