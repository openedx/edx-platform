"""
This module contains tasks for asynchronous execution of grade updates.
"""

from celery import task
from django.conf import settings
from django.contrib.auth.models import User
from django.db.utils import IntegrityError
from logging import getLogger

from courseware.model_data import get_score
from lms.djangoapps.course_blocks.api import get_course_blocks
from opaque_keys.edx.keys import UsageKey
from opaque_keys.edx.locator import CourseLocator
from openedx.core.djangoapps.content.block_structure.api import get_course_in_cache
from xmodule.modulestore.django import modulestore

from .config.models import PersistentGradesEnabledFlag
from .new.course_grade import CourseGradeFactory
from .new.subsection_grade import SubsectionGradeFactory
from .signals.signals import SUBSECTION_SCORE_CHANGED
from .transformer import GradesTransformer

log = getLogger(__name__)


@task(default_retry_delay=30, routing_key=settings.RECALCULATE_GRADES_ROUTING_KEY)
def recalculate_subsection_grade(user_id, course_id, usage_id, only_if_higher, raw_earned, raw_possible):
    """
    Updates a saved subsection grade.
    This method expects the following parameters:
        - user_id: serialized id of applicable User object
        - course_id: Unicode string identifying the course
        - usage_id: Unicode string identifying the course block
        - only_if_higher: boolean indicating whether grades should
        be updated only if the new raw_earned is higher than the previous
        value.
        - raw_earned: the raw points the learner earned on the problem that
        triggered the update
        - raw_possible: the max raw points the leaner could have earned
        on the problem
    """
    if not PersistentGradesEnabledFlag.feature_enabled(course_id):
        return

    course_key = CourseLocator.from_string(course_id)
    scored_block_usage_key = UsageKey.from_string(usage_id).replace(course_key=course_key)
    score = get_score(user_id, scored_block_usage_key)

    # If the score is None, it has not been saved at all yet
    # and we need to retry until it has been saved.
    if score is None:
        _retry_recalculate_subsection_grade(user_id, course_id, usage_id, only_if_higher, raw_earned, raw_possible)
    else:
        module_raw_earned, module_raw_possible = score  # pylint: disable=unpacking-non-sequence

    # Validate that the retrieved scores match the scores when the task was created.
    # This race condition occurs if the transaction in the task creator's process hasn't
    # committed before the task initiates in the worker process.
    grades_match = module_raw_earned == raw_earned and module_raw_possible == raw_possible

    # We have to account for the situation where a student's state
    # has been deleted- in this case, get_score returns (None, None), but
    # the score change signal will contain 0 for raw_earned.
    state_deleted = module_raw_earned is None and module_raw_possible is None and raw_earned == 0

    if not (state_deleted or grades_match):
        _retry_recalculate_subsection_grade(user_id, course_id, usage_id, only_if_higher, raw_earned, raw_possible)

    _update_subsection_grades(
        course_key,
        scored_block_usage_key,
        only_if_higher,
        course_id,
        user_id,
        usage_id,
        raw_earned,
        raw_possible,
    )


@task(default_retry_delay=30, routing_key=settings.RECALCULATE_GRADES_ROUTING_KEY)
def recalculate_course_grade(user_id, course_id):
    """
    Updates a saved course grade.
    This method expects the following parameters:
       - user_id: serialized id of applicable User object
       - course_id: Unicode string representing the course
    """
    if not PersistentGradesEnabledFlag.feature_enabled(course_id):
        return
    student = User.objects.get(id=user_id)
    course_key = CourseLocator.from_string(course_id)
    course = modulestore().get_course(course_key, depth=0)

    try:
        CourseGradeFactory(student).update(course)
    except IntegrityError as exc:
        raise recalculate_course_grade.retry(args=[user_id, course_id], exc=exc)


def _retry_recalculate_subsection_grade(user_id, course_id, usage_id, only_if_higher, grade, max_grade, exc=None):
    """
    Calls retry for the recalculate_subsection_grade task with the
    given inputs.
    """
    raise recalculate_subsection_grade.retry(
        args=[
            user_id,
            course_id,
            usage_id,
            only_if_higher,
            grade,
            max_grade,
        ],
        exc=exc
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
):
    """
    A helper function to update subsection grades in the database
    for each subsection containing the given block, and to signal
    that those subsection grades were updated.
    """
    collected_block_structure = get_course_in_cache(course_key)
    course = modulestore().get_course(course_key, depth=0)
    student = User.objects.get(id=user_id)
    subsection_grade_factory = SubsectionGradeFactory(student, course, collected_block_structure)
    subsections_to_update = collected_block_structure.get_transformer_block_field(
        scored_block_usage_key,
        GradesTransformer,
        'subsections',
        set()
    )

    try:
        for subsection_usage_key in subsections_to_update:
            transformed_subsection_structure = get_course_blocks(
                student,
                subsection_usage_key,
                collected_block_structure=collected_block_structure,
            )
            subsection_grade = subsection_grade_factory.update(
                transformed_subsection_structure[subsection_usage_key],
                transformed_subsection_structure,
                only_if_higher,
            )
            SUBSECTION_SCORE_CHANGED.send(
                sender=recalculate_subsection_grade,
                course=course,
                user=student,
                subsection_grade=subsection_grade,
            )

    except IntegrityError as exc:
        _retry_recalculate_subsection_grade(user_id, course_id, usage_id, only_if_higher, raw_earned, raw_possible, exc)
