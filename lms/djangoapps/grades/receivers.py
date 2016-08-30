"""
Grades related signals.
"""
from django.conf import settings
from logging import getLogger
from opaque_keys.edx.locator import CourseLocator
from opaque_keys.edx.keys import UsageKey

from .signals import SCORE_CHANGED
from .transformer import GradesTransformer
from .new.subsection_grade import SubsectionGradeFactory
from openedx.core.djangoapps.content.block_structure.api import get_block_structure_manager
from student.models import user_by_anonymous_id

log = getLogger(__name__)


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
    points_possible = kwargs.get('points_possible', None)
    points_earned = kwargs.get('points_earned', None)
    course_id = kwargs.get('course_id', None)
    usage_id = kwargs.get('item_id', None)
    user = None
    if 'anonymous_user_id' in kwargs:
        user = user_by_anonymous_id(kwargs.get('anonymous_user_id'))

    # If any of the kwargs were missing, at least one of the following values
    # will be None.
    if all((user, points_possible, points_earned, course_id, usage_id)):
        SCORE_CHANGED.send(
            sender=None,
            points_possible=points_possible,
            points_earned=points_earned,
            user=user,
            course_id=course_id,
            usage_id=usage_id
        )
    else:
        log.exception(
            u"Failed to process score_set signal from Submissions API. "
            "points_possible: %s, points_earned: %s, user: %s, course_id: %s, "
            "usage_id: %s", points_possible, points_earned, user, course_id, usage_id
        )


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
    course_id = kwargs.get('course_id', None)
    usage_id = kwargs.get('item_id', None)
    user = None
    if 'anonymous_user_id' in kwargs:
        user = user_by_anonymous_id(kwargs.get('anonymous_user_id'))

    # If any of the kwargs were missing, at least one of the following values
    # will be None.
    if all((user, course_id, usage_id)):
        SCORE_CHANGED.send(
            sender=None,
            points_possible=0,
            points_earned=0,
            user=user,
            course_id=course_id,
            usage_id=usage_id
        )
    else:
        log.exception(
            u"Failed to process score_reset signal from Submissions API. "
            "user: %s, course_id: %s, usage_id: %s", user, course_id, usage_id
        )


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
    if not settings.FEATURES.get('ENABLE_SUBSECTION_GRADES_SAVED', False):
        return

    try:
        course_id = kwargs['course_id']
        usage_id = kwargs['usage_id']
        student = kwargs['user']
    except KeyError as ex:
        log.exception(
            u"Failed to process SCORE_CHANGED signal, some arguments were missing."
            "user: %s, course_id: %s, usage_id: %s.",
            kwargs.get('user', None),
            kwargs.get('course_id', None),
            kwargs.get('usage_id', None),
            ex.message
        )
        return

    course_key = CourseLocator.from_string(course_id)
    usage_key = UsageKey.from_string(usage_id).replace(course_key=course_key)
    manager = get_block_structure_manager(course_key)
    block_structure = manager.get_collected()

    subsections_to_update = block_structure.get_transformer_block_field(
        usage_key,
        GradesTransformer,
        'containing_subsections',
        set()
    )

    for subsection in subsections_to_update:
        SubsectionGradeFactory(student).update(usage_key, course_key)
