"""
This module contains tasks for asynchronous execution of grade updates.
"""

from celery import task
from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db.utils import DatabaseError
from logging import getLogger

log = getLogger(__name__)

from celery_utils.logged_task import LoggedTask
from celery_utils.persist_on_failure import PersistOnFailureTask
from courseware.model_data import get_score
from lms.djangoapps.course_blocks.api import get_course_blocks
from lms.djangoapps.courseware import courses
from opaque_keys.edx.keys import CourseKey, UsageKey
from opaque_keys.edx.locator import CourseLocator
from openedx.core.djangoapps.monitoring_utils import (
    set_custom_metrics_for_course_key, set_custom_metric
)
from student.models import CourseEnrollment
from submissions import api as sub_api
from track.event_transaction_utils import (
    set_event_transaction_type,
    set_event_transaction_id,
)
from util.date_utils import from_timestamp
from xmodule.modulestore.django import modulestore

from .constants import ScoreDatabaseTableEnum
from .new.subsection_grade_factory import SubsectionGradeFactory
from .new.course_grade_factory import CourseGradeFactory
from .signals.signals import SUBSECTION_SCORE_CHANGED
from .transformer import GradesTransformer


class DatabaseNotReadyError(IOError):
    """
    Subclass of IOError to indicate the database has not yet committed
    the data we're trying to find.
    """
    pass


KNOWN_RETRY_ERRORS = (  # Errors we expect occasionally, should be resolved on retry
    DatabaseError,
    ValidationError,
    DatabaseNotReadyError
)
RECALCULATE_GRADE_DELAY = 2  # in seconds, to prevent excessive _has_db_updated failures. See TNL-6424.


class _BaseTask(PersistOnFailureTask, LoggedTask):  # pylint: disable=abstract-method
    """
    Include persistence features, as well as logging of task invocation.
    """
    abstract = True


@task(base=_BaseTask)
def compute_grades_for_course(course_key, offset, batch_size):
    """
    Compute grades for a set of students in the specified course.

    The set of students will be determined by the order of enrollment date, and
    limited to at most <batch_size> students, starting from the specified
    offset.
    """

    course = courses.get_course_by_id(CourseKey.from_string(course_key))
    enrollments = CourseEnrollment.objects.filter(course_id=course.id).order_by('created')
    student_iter = (enrollment.user for enrollment in enrollments[offset:offset + batch_size])
    list(CourseGradeFactory().iter(course, students=student_iter, force_update=True))


@task(bind=True, base=_BaseTask, default_retry_delay=30, routing_key=settings.RECALCULATE_GRADES_ROUTING_KEY)
def recalculate_subsection_grade_v3(self, **kwargs):
    """
    Latest version of the recalculate_subsection_grade task.  See docstring
    for _recalculate_subsection_grade for further description.
    """
    _recalculate_subsection_grade(self, **kwargs)


def _recalculate_subsection_grade(self, **kwargs):
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
        scored_block_usage_key = UsageKey.from_string(kwargs['usage_id']).replace(course_key=course_key)

        set_custom_metrics_for_course_key(course_key)
        set_custom_metric('usage_id', unicode(scored_block_usage_key))

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
        has_database_updated = _has_db_updated_with_new_score(self, scored_block_usage_key, **kwargs)

        if not has_database_updated:
            raise DatabaseNotReadyError

        _update_subsection_grades(
            course_key,
            scored_block_usage_key,
            kwargs['only_if_higher'],
            kwargs['user_id'],
        )
    except Exception as exc:   # pylint: disable=broad-except
        if not isinstance(exc, KNOWN_RETRY_ERRORS):
            log.info("tnl-6244 grades unexpected failure: {}. task id: {}. kwargs={}".format(
                repr(exc),
                self.request.id,
                kwargs,
            ))
        raise self.retry(kwargs=kwargs, exc=exc)


def _has_db_updated_with_new_score(self, scored_block_usage_key, **kwargs):
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
        db_is_updated = kwargs['score_deleted']
    else:
        db_is_updated = found_modified_time >= from_timestamp(kwargs['expected_modified_time'])

    if not db_is_updated:
        log.info(
            u"Grades: tasks._has_database_updated_with_new_score is False. Task ID: {}. Kwargs: {}. Found "
            u"modified time: {}".format(
                self.request.id,
                kwargs,
                found_modified_time,
            )
        )

    return db_is_updated


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
