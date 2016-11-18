"""
This module contains tasks for asynchronous execution of grade updates.
"""

from celery import task
from django.conf import settings
from django.contrib.auth.models import User
from django.db.utils import DatabaseError
from logging import getLogger

from courseware.model_data import get_score
from lms.djangoapps.course_blocks.api import get_course_blocks
from opaque_keys.edx.keys import UsageKey
from opaque_keys.edx.locator import CourseLocator
from xmodule.modulestore.django import modulestore

from .config.models import PersistentGradesEnabledFlag
from .new.subsection_grade import SubsectionGradeFactory
from .signals.signals import SUBSECTION_SCORE_CHANGED
from .transformer import GradesTransformer

log = getLogger(__name__)


@task(default_retry_delay=30, routing_key=settings.RECALCULATE_GRADES_ROUTING_KEY)
def recalculate_subsection_grade(user_id, course_id, usage_id, only_if_higher, raw_earned, raw_possible, **kwargs):
    """
    Updates a saved subsection grade.

    Arguments:
        user_id (int): id of applicable User object
        course_id (string): identifying the course
        usage_id (string): identifying the course block
        only_if_higher (boolean): indicating whether grades should
            be updated only if the new raw_earned is higher than the
            previous value.
        raw_earned (float): the raw points the learner earned on the
            problem that triggered the update.
        raw_possible (float): the max raw points the leaner could have
            earned on the problem.
        score_deleted (boolean): indicating whether the grade change is
            a result of the problem's score being deleted.
    """
    course_key = CourseLocator.from_string(course_id)
    if not PersistentGradesEnabledFlag.feature_enabled(course_key):
        return

    score_deleted = kwargs['score_deleted']
    scored_block_usage_key = UsageKey.from_string(usage_id).replace(course_key=course_key)

    # Verify the database has been updated with the scores when the task was
    # created. This race condition occurs if the transaction in the task
    # creator's process hasn't committed before the task initiates in the worker
    # process.
    if not _has_database_updated_with_new_score(
            user_id, scored_block_usage_key, raw_earned, raw_possible, score_deleted,
    ):
        raise _retry_recalculate_subsection_grade(
            user_id, course_id, usage_id, only_if_higher, raw_earned, raw_possible, score_deleted,
        )

    _update_subsection_grades(
        course_key,
        scored_block_usage_key,
        only_if_higher,
        course_id,
        user_id,
        usage_id,
        raw_earned,
        raw_possible,
        score_deleted,
    )


def _has_database_updated_with_new_score(
        user_id, scored_block_usage_key, expected_raw_earned, expected_raw_possible, score_deleted,
):
    """
    Returns whether the database has been updated with the
    expected new score values for the given problem and user.
    """
    score = get_score(user_id, scored_block_usage_key)

    if score is None:
        # score should be None only if it was deleted.
        # Otherwise, it hasn't yet been saved.
        return score_deleted

    found_raw_earned, found_raw_possible = score  # pylint: disable=unpacking-non-sequence
    return (
        found_raw_earned == expected_raw_earned and
        found_raw_possible == expected_raw_possible
    )


def _update_subsection_grades(
        course_key,
        scored_block_usage_key,
        only_if_higher,
        course_id,
        user_id,
        usage_id,
        raw_earned,
        raw_possible,
        score_deleted,
):
    """
    A helper function to update subsection grades in the database
    for each subsection containing the given block, and to signal
    that those subsection grades were updated.
    """
    student = User.objects.get(id=user_id)
    course_structure = get_course_blocks(student, modulestore().make_course_usage_key(course_key))
    subsections_to_update = course_structure.get_transformer_block_field(
        scored_block_usage_key,
        GradesTransformer,
        'subsections',
        set(),
    )

    course = modulestore().get_course(course_key, depth=0)
    subsection_grade_factory = SubsectionGradeFactory(student, course, course_structure)

    try:
        for subsection_usage_key in subsections_to_update:
            subsection_grade = subsection_grade_factory.update(
                course_structure[subsection_usage_key],
                only_if_higher,
            )
            SUBSECTION_SCORE_CHANGED.send(
                sender=recalculate_subsection_grade,
                course=course,
                course_structure=course_structure,
                user=student,
                subsection_grade=subsection_grade,
            )

    except DatabaseError as exc:
        raise _retry_recalculate_subsection_grade(
            user_id, course_id, usage_id, only_if_higher, raw_earned, raw_possible, score_deleted, exc,
        )


def _retry_recalculate_subsection_grade(
        user_id, course_id, usage_id, only_if_higher, raw_earned, raw_possible, score_deleted, exc=None,
):
    """
    Calls retry for the recalculate_subsection_grade task with the
    given inputs.
    """
    recalculate_subsection_grade.retry(
        kwargs=dict(
            user_id=user_id,
            course_id=course_id,
            usage_id=usage_id,
            only_if_higher=only_if_higher,
            raw_earned=raw_earned,
            raw_possible=raw_possible,
            score_deleted=score_deleted,
        ),
        exc=exc,
    )
