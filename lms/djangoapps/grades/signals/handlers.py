"""
Grades related signals.
"""

from django.dispatch import receiver
from logging import getLogger

from student.models import user_by_anonymous_id
from submissions.models import score_set, score_reset

from .signals import SCORE_CHANGED
from ..tasks import recalculate_subsection_grade

log = getLogger(__name__)


@receiver(score_set)
def submissions_score_set_handler(sender, **kwargs):  # pylint: disable=unused-argument
    """
    Consume the score_set signal defined in the Submissions API, and convert it
    to a SCORE_CHANGED signal defined in this module. Converts the unicode keys
    for user, course and item into the standard representation for the
    SCORE_CHANGED signal.

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

    SCORE_CHANGED.send(
        sender=None,
        points_possible=points_possible,
        points_earned=points_earned,
        user_id=user.id,
        course_id=course_id,
        usage_id=usage_id
    )


@receiver(score_reset)
def submissions_score_reset_handler(sender, **kwargs):  # pylint: disable=unused-argument
    """
    Consume the score_reset signal defined in the Submissions API, and convert
    it to a SCORE_CHANGED signal indicating that the score has been set to 0/0.
    Converts the unicode keys for user, course and item into the standard
    representation for the SCORE_CHANGED signal.

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

    SCORE_CHANGED.send(
        sender=None,
        points_possible=0,
        points_earned=0,
        user_id=user.id,
        course_id=course_id,
        usage_id=usage_id
    )


@receiver(SCORE_CHANGED)
def enqueue_update(sender, **kwargs):  # pylint: disable=unused-argument
    """
    Handles the SCORE_CHANGED signal by enqueueing an update operation to occur asynchronously.
    """
    recalculate_subsection_grade.apply_async(args=(kwargs['user_id'], kwargs['course_id'], kwargs['usage_id']))
