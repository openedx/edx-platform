"""
Grades related signals.
"""

from django.dispatch import receiver
from logging import getLogger

from courseware.model_data import get_score, set_score
from openedx.core.lib.grade_utils import is_score_higher
from student.models import user_by_anonymous_id
from submissions.models import score_set, score_reset

from .signals import PROBLEM_SCORE_CHANGED, SUBSECTION_SCORE_CHANGED, SCORE_PUBLISHED
from ..new.course_grade import CourseGradeFactory
from ..tasks import recalculate_subsection_grade


log = getLogger(__name__)


@receiver(score_set)
def submissions_score_set_handler(sender, **kwargs):  # pylint: disable=unused-argument
    """
    Consume the score_set signal defined in the Submissions API, and convert it
    to a PROBLEM_SCORE_CHANGED signal defined in this module. Converts the unicode keys
    for user, course and item into the standard representation for the
    PROBLEM_SCORE_CHANGED signal.

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

    PROBLEM_SCORE_CHANGED.send(
        sender=None,
        points_earned=points_earned,
        points_possible=points_possible,
        user_id=user.id,
        course_id=course_id,
        usage_id=usage_id
    )


@receiver(score_reset)
def submissions_score_reset_handler(sender, **kwargs):  # pylint: disable=unused-argument
    """
    Consume the score_reset signal defined in the Submissions API, and convert
    it to a PROBLEM_SCORE_CHANGED signal indicating that the score has been set to 0/0.
    Converts the unicode keys for user, course and item into the standard
    representation for the PROBLEM_SCORE_CHANGED signal.

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

    PROBLEM_SCORE_CHANGED.send(
        sender=None,
        points_earned=0,
        points_possible=0,
        user_id=user.id,
        course_id=course_id,
        usage_id=usage_id
    )


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
            prev_raw_earned, prev_raw_possible = previous_score  # pylint: disable=unpacking-non-sequence

            if not is_score_higher(prev_raw_earned, prev_raw_possible, raw_earned, raw_possible):
                update_score = False
                log.warning(
                    u"Grades: Rescore is not higher than previous: "
                    u"user: {}, block: {}, previous: {}/{}, new: {}/{} ".format(
                        user, block.location, prev_raw_earned, prev_raw_possible, raw_earned, raw_possible,
                    )
                )

    if update_score:
        set_score(user.id, block.location, raw_earned, raw_possible)
        PROBLEM_SCORE_CHANGED.send(
            sender=None,
            points_earned=raw_earned,
            points_possible=raw_possible,
            user_id=user.id,
            course_id=unicode(block.location.course_key),
            usage_id=unicode(block.location),
            only_if_higher=only_if_higher,
        )
    return update_score


@receiver(PROBLEM_SCORE_CHANGED)
def enqueue_subsection_update(sender, **kwargs):  # pylint: disable=unused-argument
    """
    Handles the PROBLEM_SCORE_CHANGED signal by enqueueing a subsection update operation to occur asynchronously.
    """
    result = recalculate_subsection_grade.apply_async(
        kwargs=dict(
            user_id=kwargs['user_id'],
            course_id=kwargs['course_id'],
            usage_id=kwargs['usage_id'],
            only_if_higher=kwargs.get('only_if_higher'),
            raw_earned=kwargs.get('points_earned'),
            raw_possible=kwargs.get('points_possible'),
            score_deleted=kwargs.get('score_deleted', False),
        )
    )
    log.info(
        u'Grades: Request async calculation of subsection grades with args: {}. Task [{}]'.format(
            ', '.join('{}:{}'.format(arg, kwargs[arg]) for arg in sorted(kwargs)),
            getattr(result, 'id', 'N/A'),
        )
    )


@receiver(SUBSECTION_SCORE_CHANGED)
def recalculate_course_grade(sender, course, course_structure, user, **kwargs):  # pylint: disable=unused-argument
    """
    Updates a saved course grade.
    """
    CourseGradeFactory(user).update(course, course_structure)
