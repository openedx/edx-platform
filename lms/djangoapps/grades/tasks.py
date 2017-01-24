"""
This module contains tasks for asynchronous execution of grade updates.
"""

from celery import task
from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db.utils import DatabaseError
from logging import getLogger

from courseware.model_data import get_score
from lms.djangoapps.course_blocks.api import get_course_blocks
from openedx.core.djangoapps.celery_utils.task import PersistOnFailureTask
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
from .constants import ScoreDatabaseTableEnum
from .new.subsection_grade import SubsectionGradeFactory
from .signals.signals import SUBSECTION_SCORE_CHANGED
from .transformer import GradesTransformer

log = getLogger(__name__)

KNOWN_RETRY_ERRORS = (DatabaseError, ValidationError)  # Errors we expect occasionally, should be resolved on retry


# TODO (TNL-6373) DELETE ME once v3 is successfully deployed to Prod.
@task(base=PersistOnFailureTask, default_retry_delay=30, routing_key=settings.RECALCULATE_GRADES_ROUTING_KEY)
def recalculate_subsection_grade_v2(**kwargs):
    """
    Shim to support tasks enqueued by older workers during initial deployment.
    """
    _recalculate_subsection_grade(recalculate_subsection_grade_v2, **kwargs)


@task(base=PersistOnFailureTask, default_retry_delay=30, routing_key=settings.RECALCULATE_GRADES_ROUTING_KEY)
def recalculate_subsection_grade_v3(**kwargs):
    """
    Latest version of the recalculate_subsection_grade task.  See docstring
    for _recalculate_subsection_grade for further description.
    """
    _recalculate_subsection_grade(recalculate_subsection_grade_v3, **kwargs)


def _recalculate_subsection_grade(task_func, **kwargs):
    """
    Updates a saved subsection grade.

    Keyword Arguments:
        user_id (int): id of applicable User object
        anonymous_user_id (int, OPTIONAL): Anonymous ID of the User
        course_id (string): identifying the course
        usage_id (string): identifying the course block
        only_if_higher (boolean): indicating whether grades should
            be updated only if the new raw_earned is higher than the
            previous value.
        expected_modified_time (serialized timestamp): indicates when the task
            was queued so that we can verify the underlying data update.
        score_deleted (boolean): indicating whether the grade change is
            a result of the problem's score being deleted.
        event_transaction_id (string): uuid identifying the current
            event transaction.
        event_transaction_type (string): human-readable type of the
            event at the root of the current event transaction.
        score_db_table (ScoreDatabaseTableEnum): database table that houses
            the changed score. Used in conjunction with expected_modified_time.
    """
    try:
        course_key = CourseLocator.from_string(kwargs['course_id'])
        if not PersistentGradesEnabledFlag.feature_enabled(course_key):
            return

        scored_block_usage_key = UsageKey.from_string(kwargs['usage_id']).replace(course_key=course_key)

        # The request cache is not maintained on celery workers,
        # where this code runs. So we take the values from the
        # main request cache and store them in the local request
        # cache. This correlates model-level grading events with
        # higher-level ones.
        set_event_transaction_id(kwargs.get('event_transaction_id'))
        set_event_transaction_type(kwargs.get('event_transaction_type'))

        # Verify the database has been updated with the scores when the task was
        # created. This race condition occurs if the transaction in the task
        # creator's process hasn't committed before the task initiates in the worker
        # process.
        if task_func == recalculate_subsection_grade_v2:
            has_database_updated = _has_db_updated_with_new_score_bwc_v2(
                kwargs['user_id'],
                scored_block_usage_key,
                from_timestamp(kwargs['expected_modified_time']),
                kwargs['score_deleted'],
            )
        else:
            has_database_updated = _has_db_updated_with_new_score(scored_block_usage_key, **kwargs)

        if not has_database_updated:
            raise _retry_recalculate_subsection_grade(task_func, **kwargs)

        _update_subsection_grades(
            course_key,
            scored_block_usage_key,
            kwargs['only_if_higher'],
            kwargs['user_id'],
        )

    except Exception as exc:   # pylint: disable=broad-except
        if not isinstance(exc, KNOWN_RETRY_ERRORS):
            log.info("tnl-6244 grades unexpected failure: {}. kwargs={}".format(
                repr(exc),
                kwargs
            ))
        raise _retry_recalculate_subsection_grade(task_func, exc=exc, **kwargs)


def _has_db_updated_with_new_score(scored_block_usage_key, **kwargs):
    """
    Returns whether the database has been updated with the
    expected new score values for the given problem and user.
    """
    if kwargs['score_db_table'] == ScoreDatabaseTableEnum.courseware_student_module:
        score = get_score(kwargs['user_id'], scored_block_usage_key)
        found_modified_time = score.modified if score is not None else None

    else:
        assert kwargs['score_db_table'] == ScoreDatabaseTableEnum.submissions
        score = sub_api.get_score(
            {
                "student_id": kwargs['anonymous_user_id'],
                "course_id": unicode(scored_block_usage_key.course_key),
                "item_id": unicode(scored_block_usage_key),
                "item_type": scored_block_usage_key.block_type,
            }
        )
        found_modified_time = score['created_at'] if score is not None else None

    if score is None:
        # score should be None only if it was deleted.
        # Otherwise, it hasn't yet been saved.
        return kwargs['score_deleted']

    return found_modified_time >= from_timestamp(kwargs['expected_modified_time'])


# TODO (TNL-6373) DELETE ME once v3 is successfully deployed to Prod.
def _has_db_updated_with_new_score_bwc_v2(
        user_id, scored_block_usage_key, expected_modified_time, score_deleted,
):
    """
    DEPRECATED version for backward compatibility with v2 tasks.

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
        if api_score is None:
            # Same case as the initial 'if' above, for submissions-specific scores
            return score_deleted
        reported_modified_time = api_score['created_at']
    else:
        reported_modified_time = score.modified

    return reported_modified_time >= expected_modified_time


def _update_subsection_grades(
        course_key,
        scored_block_usage_key,
        only_if_higher,
        user_id,
):
    """
    A helper function to update subsection grades in the database
    for each subsection containing the given block, and to signal
    that those subsection grades were updated.
    """
    student = User.objects.get(id=user_id)
    store = modulestore()
    with store.bulk_operations(course_key):
        course_structure = get_course_blocks(student, store.make_course_usage_key(course_key))
        subsections_to_update = course_structure.get_transformer_block_field(
            scored_block_usage_key,
            GradesTransformer,
            'subsections',
            set(),
        )

        course = store.get_course(course_key, depth=0)
        subsection_grade_factory = SubsectionGradeFactory(student, course, course_structure)

        for subsection_usage_key in subsections_to_update:
            if subsection_usage_key in course_structure:
                subsection_grade = subsection_grade_factory.update(
                    course_structure[subsection_usage_key],
                    only_if_higher,
                )
                SUBSECTION_SCORE_CHANGED.send(
                    sender=None,
                    course=course,
                    course_structure=course_structure,
                    user=student,
                    subsection_grade=subsection_grade,
                )


def _retry_recalculate_subsection_grade(task_func, exc=None, **kwargs):
    """
    Calls retry for the recalculate_subsection_grade task with the
    given inputs.
    """
    task_func.retry(kwargs=kwargs, exc=exc)
