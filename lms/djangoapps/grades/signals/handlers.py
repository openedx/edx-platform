"""
Grades related signals.
"""
from contextlib import contextmanager
from logging import getLogger

from courseware.model_data import get_score, set_score
from django.dispatch import receiver
from openedx.core.djangoapps.course_groups.signals.signals import COHORT_MEMBERSHIP_UPDATED
from openedx.core.lib.grade_utils import is_score_higher_or_equal
from student.models import user_by_anonymous_id
from student.signals import ENROLLMENT_TRACK_UPDATED
from submissions.models import score_reset, score_set
from track.event_transaction_utils import get_event_transaction_id, get_event_transaction_type
from util.date_utils import to_timestamp
from xblock.scorable import ScorableXBlockMixin, Score

from .signals import (
    PROBLEM_RAW_SCORE_CHANGED,
    PROBLEM_WEIGHTED_SCORE_CHANGED,
    SCORE_PUBLISHED,
    SUBSECTION_SCORE_CHANGED,
    SUBSECTION_OVERRIDE_CHANGED,
)
from ..constants import ScoreDatabaseTableEnum
from ..course_grade_factory import CourseGradeFactory
from .. import events
from ..scores import weighted_score
from ..tasks import RECALCULATE_GRADE_DELAY_SECONDS, recalculate_subsection_grade_v3

log = getLogger(__name__)


@receiver(score_set)
def submissions_score_set_handler(sender, **kwargs):  # pylint: disable=unused-argument
    """
    Consume the score_set signal defined in the Submissions API, and convert it
    to a PROBLEM_WEIGHTED_SCORE_CHANGED signal defined in this module. Converts the
    unicode keys for user, course and item into the standard representation for the
    PROBLEM_WEIGHTED_SCORE_CHANGED signal.

    This method expects that the kwargs dictionary will contain the following
    entries (See the definition of score_set):
      - 'points_possible': integer,
      - 'points_earned': integer,
      - 'anonymous_user_id': unicode,
      - 'course_id': unicode,
      - 'item_id': unicode
    """
    points_possible = kwargs['points_possible']
    points_earned = kwargs['points_earned']
    course_id = kwargs['course_id']
    usage_id = kwargs['item_id']
    user = user_by_anonymous_id(kwargs['anonymous_user_id'])
    if user is None:
        return
    if points_possible == 0:
        # This scenario is known to not succeed, see TNL-6559 for details.
        return

    PROBLEM_WEIGHTED_SCORE_CHANGED.send(
        sender=None,
        weighted_earned=points_earned,
        weighted_possible=points_possible,
        user_id=user.id,
        anonymous_user_id=kwargs['anonymous_user_id'],
        course_id=course_id,
        usage_id=usage_id,
        modified=kwargs['created_at'],
        score_db_table=ScoreDatabaseTableEnum.submissions,
    )


@receiver(score_reset)
def submissions_score_reset_handler(sender, **kwargs):  # pylint: disable=unused-argument
    """
    Consume the score_reset signal defined in the Submissions API, and convert
    it to a PROBLEM_WEIGHTED_SCORE_CHANGED signal indicating that the score
    has been set to 0/0. Converts the unicode keys for user, course and item
    into the standard representation for the PROBLEM_WEIGHTED_SCORE_CHANGED signal.

    This method expects that the kwargs dictionary will contain the following
    entries (See the definition of score_reset):
      - 'anonymous_user_id': unicode,
      - 'course_id': unicode,
      - 'item_id': unicode
    """
    course_id = kwargs['course_id']
    usage_id = kwargs['item_id']
    user = user_by_anonymous_id(kwargs['anonymous_user_id'])
    if user is None:
        return

    PROBLEM_WEIGHTED_SCORE_CHANGED.send(
        sender=None,
        weighted_earned=0,
        weighted_possible=0,
        user_id=user.id,
        anonymous_user_id=kwargs['anonymous_user_id'],
        course_id=course_id,
        usage_id=usage_id,
        modified=kwargs['created_at'],
        score_deleted=True,
        score_db_table=ScoreDatabaseTableEnum.submissions,
    )


@contextmanager
def disconnect_submissions_signal_receiver(signal):
    """
    Context manager to be used for temporarily disconnecting edx-submission's set or reset signal.
    """
    if signal == score_set:
        handler = submissions_score_set_handler
    else:
        if signal != score_reset:
            raise ValueError("This context manager only handles score_set and score_reset signals.")
        handler = submissions_score_reset_handler

    signal.disconnect(handler)
    try:
        yield
    finally:
        signal.connect(handler)


@receiver(SCORE_PUBLISHED)
def score_published_handler(sender, block, user, raw_earned, raw_possible, only_if_higher, **kwargs):  # pylint: disable=unused-argument
    """
    Handles whenever a block's score is published.
    Returns whether the score was actually updated.
    """
    update_score = True
    if only_if_higher:
        previous_score = get_score(user.id, block.location)

        if previous_score is not None:
            prev_raw_earned, prev_raw_possible = (previous_score.grade, previous_score.max_grade)

            if not is_score_higher_or_equal(prev_raw_earned, prev_raw_possible, raw_earned, raw_possible):
                update_score = False
                log.warning(
                    u"Grades: Rescore is not higher than previous: "
                    u"user: {}, block: {}, previous: {}/{}, new: {}/{} ".format(
                        user, block.location, prev_raw_earned, prev_raw_possible, raw_earned, raw_possible,
                    )
                )

    if update_score:
        # Set the problem score in CSM.

        # adding temporary log for understanding EDUCATOR-1931
        if user.is_anonymous():
            log.info("Problem [%s] was accessed by anonymous user", block.location)

        score_modified_time = set_score(user.id, block.location, raw_earned, raw_possible)

        # Set the problem score on the xblock.
        if isinstance(block, ScorableXBlockMixin):
            block.set_score(Score(raw_earned=raw_earned, raw_possible=raw_possible))

        # Fire a signal (consumed by enqueue_subsection_update, below)
        PROBLEM_RAW_SCORE_CHANGED.send(
            sender=None,
            raw_earned=raw_earned,
            raw_possible=raw_possible,
            weight=getattr(block, 'weight', None),
            user_id=user.id,
            course_id=unicode(block.location.course_key),
            usage_id=unicode(block.location),
            only_if_higher=only_if_higher,
            modified=score_modified_time,
            score_db_table=ScoreDatabaseTableEnum.courseware_student_module,
            score_deleted=kwargs.get('score_deleted', False),
        )
    return update_score


@receiver(PROBLEM_RAW_SCORE_CHANGED)
def problem_raw_score_changed_handler(sender, **kwargs):  # pylint: disable=unused-argument
    """
    Handles the raw score changed signal, converting the score to a
    weighted score and firing the PROBLEM_WEIGHTED_SCORE_CHANGED signal.
    """
    if kwargs['raw_possible'] is not None:
        weighted_earned, weighted_possible = weighted_score(
            kwargs['raw_earned'],
            kwargs['raw_possible'],
            kwargs['weight'],
        )
    else:  # TODO: remove as part of TNL-5982
        weighted_earned, weighted_possible = kwargs['raw_earned'], kwargs['raw_possible']

    PROBLEM_WEIGHTED_SCORE_CHANGED.send(
        sender=None,
        weighted_earned=weighted_earned,
        weighted_possible=weighted_possible,
        user_id=kwargs['user_id'],
        course_id=kwargs['course_id'],
        usage_id=kwargs['usage_id'],
        only_if_higher=kwargs['only_if_higher'],
        score_deleted=kwargs.get('score_deleted', False),
        modified=kwargs['modified'],
        score_db_table=kwargs['score_db_table'],
    )


@receiver(PROBLEM_WEIGHTED_SCORE_CHANGED)
@receiver(SUBSECTION_OVERRIDE_CHANGED)
def enqueue_subsection_update(sender, **kwargs):  # pylint: disable=unused-argument
    """
    Handles the PROBLEM_WEIGHTED_SCORE_CHANGED or SUBSECTION_OVERRIDE_CHANGED signals by
    enqueueing a subsection update operation to occur asynchronously.
    """
    events.grade_updated(**kwargs)
    recalculate_subsection_grade_v3.apply_async(
        kwargs=dict(
            user_id=kwargs['user_id'],
            anonymous_user_id=kwargs.get('anonymous_user_id'),
            course_id=kwargs['course_id'],
            usage_id=kwargs['usage_id'],
            only_if_higher=kwargs.get('only_if_higher'),
            expected_modified_time=to_timestamp(kwargs['modified']),
            score_deleted=kwargs.get('score_deleted', False),
            event_transaction_id=unicode(get_event_transaction_id()),
            event_transaction_type=unicode(get_event_transaction_type()),
            score_db_table=kwargs['score_db_table'],
        ),
        countdown=RECALCULATE_GRADE_DELAY_SECONDS,
    )


@receiver(SUBSECTION_SCORE_CHANGED)
def recalculate_course_grade_only(sender, course, course_structure, user, **kwargs):  # pylint: disable=unused-argument
    """
    Updates a saved course grade, but does not update the subsection
    grades the user has in this course.
    """
    CourseGradeFactory().update(user, course=course, course_structure=course_structure)


@receiver(ENROLLMENT_TRACK_UPDATED)
@receiver(COHORT_MEMBERSHIP_UPDATED)
def recalculate_course_and_subsection_grades(sender, user, course_key, **kwargs):
    """
    Updates a saved course grade, forcing the subsection grades
    from which it is calculated to update along the way.
    """
    previous_course_grade = CourseGradeFactory().read(user, course_key=course_key)
    if previous_course_grade and previous_course_grade.attempted:
        CourseGradeFactory().update(user=user, course_key=course_key, force_update_subsections=True)
