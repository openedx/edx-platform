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
from submissions import api as sub_api
from student.models import anonymous_id_for_user
from track.event_transaction_utils import (
    set_event_transaction_type,
    set_event_transaction_id,
    get_event_transaction_type,
    get_event_transaction_id
)
from util.date_utils import from_timestamp
from xmodule.modulestore.django import modulestore

from .config.models import PersistentGradesEnabledFlag
from .new.subsection_grade import SubsectionGradeFactory
from .signals.signals import SUBSECTION_SCORE_CHANGED
from .transformer import GradesTransformer

log = getLogger(__name__)


@task(default_retry_delay=30, routing_key=settings.RECALCULATE_GRADES_ROUTING_KEY)
def recalculate_subsection_grade(
        # pylint: disable=unused-argument
        user_id, course_id, usage_id, only_if_higher, weighted_earned, weighted_possible, **kwargs
):
    """
    Shim to allow us to modify this task's signature without blowing up production on deployment.
    """
    recalculate_subsection_grade_v2.apply(
        kwargs=dict(
            user_id=user_id,
            course_id=course_id,
            usage_id=usage_id,
            only_if_higher=only_if_higher,
            expected_modified_time=kwargs.get('expected_modified_time', 0),  # Use the unix epoch as a default
            score_deleted=kwargs['score_deleted'],
        )
    )


@task(default_retry_delay=30, routing_key=settings.RECALCULATE_GRADES_ROUTING_KEY)
def recalculate_subsection_grade_v2(**kwargs):
    """
    Updates a saved subsection grade.

    Arguments:
        user_id (int): id of applicable User object
        course_id (string): identifying the course
        usage_id (string): identifying the course block
        only_if_higher (boolean): indicating whether grades should
            be updated only if the new raw_earned is higher than the
            previous value.
        expected_modified_time (serialized timestamp): indicates when the task
            was queued so that we can verify the underlying data update.
        score_deleted (boolean): indicating whether the grade change is
            a result of the problem's score being deleted.
        event_transaction_id(string): uuid identifying the current
            event transaction.
        event_transaction_type(string): human-readable type of the
            event at the root of the current event transaction.
    """
    course_key = CourseLocator.from_string(kwargs['course_id'])
    if not PersistentGradesEnabledFlag.feature_enabled(course_key):
        return

    score_deleted = kwargs['score_deleted']
    scored_block_usage_key = UsageKey.from_string(kwargs['usage_id']).replace(course_key=course_key)
    expected_modified_time = from_timestamp(kwargs['expected_modified_time'])

    # The request cache is not maintained on celery workers,
    # where this code runs. So we take the values from the
    # main request cache and store them in the local request
    # cache. This correlates model-level grading events with
    # higher-level ones.
    set_event_transaction_id(kwargs.pop('event_transaction_id', None))
    set_event_transaction_type(kwargs.pop('event_transaction_type', None))

    # Verify the database has been updated with the scores when the task was
    # created. This race condition occurs if the transaction in the task
    # creator's process hasn't committed before the task initiates in the worker
    # process.
    if not _has_database_updated_with_new_score(
            kwargs['user_id'], scored_block_usage_key, expected_modified_time, score_deleted,
    ):
        raise _retry_recalculate_subsection_grade(**kwargs)

    _update_subsection_grades(
        course_key,
        scored_block_usage_key,
        kwargs['only_if_higher'],
        kwargs['course_id'],
        kwargs['user_id'],
        kwargs['usage_id'],
        kwargs['expected_modified_time'],
        score_deleted,
    )


def _has_database_updated_with_new_score(
        user_id, scored_block_usage_key, expected_modified_time, score_deleted,
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
    elif score.module_type == 'openassessment':
        anon_id = anonymous_id_for_user(User.objects.get(id=user_id), scored_block_usage_key.course_key)
        course_id = unicode(scored_block_usage_key.course_key)
        item_id = unicode(scored_block_usage_key)

        api_score = sub_api.get_score(
            {
                "student_id": anon_id,
                "course_id": course_id,
                "item_id": item_id,
                "item_type": "openassessment"
            }
        )
        reported_modified_time = api_score.created_at
    else:
        reported_modified_time = score.modified

    return reported_modified_time >= expected_modified_time


def _update_subsection_grades(
        course_key,
        scored_block_usage_key,
        only_if_higher,
        course_id,
        user_id,
        usage_id,
        expected_modified_time,
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
            if subsection_usage_key in course_structure:
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
            user_id,
            course_id,
            usage_id,
            only_if_higher,
            expected_modified_time,
            score_deleted,
            exc,
        )


def _retry_recalculate_subsection_grade(
        user_id,
        course_id,
        usage_id,
        only_if_higher,
        expected_modified_time,
        score_deleted,
        exc=None,
):
    """
    Calls retry for the recalculate_subsection_grade task with the
    given inputs.
    """
    recalculate_subsection_grade_v2.retry(
        kwargs=dict(
            user_id=user_id,
            course_id=course_id,
            usage_id=usage_id,
            only_if_higher=only_if_higher,
            expected_modified_time=expected_modified_time,
            score_deleted=score_deleted,
            event_transaction_id=unicode(get_event_transaction_id()),
            event_transaction_type=unicode(get_event_transaction_type()),
        ),
        exc=exc,
    )
