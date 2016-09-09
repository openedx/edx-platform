"""
Grades related signals.
"""
from logging import getLogger

from django.dispatch import receiver

from opaque_keys.edx.locator import CourseLocator
from opaque_keys.edx.keys import UsageKey
from openedx.core.djangoapps.content.block_structure.api import get_course_in_cache
from student.models import user_by_anonymous_id
from submissions.models import score_set, score_reset

from .signals import SCORE_CHANGED
from ..config.models import PersistentGradesEnabledFlag
from ..transformer import GradesTransformer
from ..new.subsection_grade import SubsectionGradeFactory

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

    # If any of the kwargs were missing, at least one of the following values
    # will be None.
    SCORE_CHANGED.send(
        sender=None,
        points_possible=points_possible,
        points_earned=points_earned,
        user=user,
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

    # If any of the kwargs were missing, at least one of the following values
    # will be None.
    SCORE_CHANGED.send(
        sender=None,
        points_possible=0,
        points_earned=0,
        user=user,
        course_id=course_id,
        usage_id=usage_id
    )


@receiver(SCORE_CHANGED)
def recalculate_subsection_grade_handler(sender, **kwargs):  # pylint: disable=unused-argument
    """
    Consume the SCORE_CHANGED signal and trigger an update.
    This method expects that the kwargs dictionary will contain the following
    entries (See the definition of SCORE_CHANGED):
       - points_possible: Maximum score available for the exercise
       - points_earned: Score obtained by the user
       - user: User object
       - course_id: Unicode string representing the course
       - usage_id: Unicode string indicating the courseware instance
    """
    try:
        course_id = kwargs['course_id']
        usage_id = kwargs['usage_id']
        student = kwargs['user']
    except KeyError:
        log.exception(
            u"Failed to process SCORE_CHANGED signal, some arguments were missing."
            "user: %s, course_id: %s, usage_id: %s.",
            kwargs.get('user', None),
            kwargs.get('course_id', None),
            kwargs.get('usage_id', None),
        )
        return

    course_key = CourseLocator.from_string(course_id)
    if not PersistentGradesEnabledFlag.feature_enabled(course_key):
        return

    usage_key = UsageKey.from_string(usage_id).replace(course_key=course_key)
    block_structure = get_course_in_cache(course_key)

    subsections_to_update = block_structure.get_transformer_block_field(
        usage_key,
        GradesTransformer,
        'subsections',
        set()
    )

    for subsection in subsections_to_update:
        SubsectionGradeFactory(student).update(subsection, course_key)
