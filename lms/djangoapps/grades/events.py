"""
Emits course grade events.
"""
from crum import get_current_user
from eventtracking import tracker

from common.djangoapps.track import contexts
from common.djangoapps.track.event_transaction_utils import (
    create_new_event_transaction_id,
    get_event_transaction_id,
    get_event_transaction_type,
    set_event_transaction_type
)

COURSE_GRADE_CALCULATED = 'edx.grades.course.grade_calculated'
GRADES_OVERRIDE_EVENT_TYPE = 'edx.grades.problem.score_overridden'
GRADES_RESCORE_EVENT_TYPE = 'edx.grades.problem.rescored'
PROBLEM_SUBMITTED_EVENT_TYPE = 'edx.grades.problem.submitted'
STATE_DELETED_EVENT_TYPE = 'edx.grades.problem.state_deleted'
SUBSECTION_OVERRIDE_EVENT_TYPE = 'edx.grades.subsection.score_overridden'
SUBSECTION_GRADE_CALCULATED = 'edx.grades.subsection.grade_calculated'


def grade_updated(**kwargs):
    """
    Emits the appropriate grade-related event after checking for which
    event-transaction is active.

    Emits a problem.submitted event only if there is no current event
    transaction type, i.e. we have not reached this point in the code via
    an outer event type (such as problem.rescored or score_overridden).
    """
    root_type = get_event_transaction_type()

    if not root_type:
        root_id = get_event_transaction_id()
        if not root_id:
            root_id = create_new_event_transaction_id()
        set_event_transaction_type(PROBLEM_SUBMITTED_EVENT_TYPE)
        tracker.emit(
            str(PROBLEM_SUBMITTED_EVENT_TYPE),
            {
                'user_id': str(kwargs['user_id']),
                'course_id': str(kwargs['course_id']),
                'problem_id': str(kwargs['usage_id']),
                'event_transaction_id': str(root_id),
                'event_transaction_type': str(PROBLEM_SUBMITTED_EVENT_TYPE),
                'weighted_earned': kwargs.get('weighted_earned'),
                'weighted_possible': kwargs.get('weighted_possible'),
            }
        )

    elif root_type in [GRADES_RESCORE_EVENT_TYPE, GRADES_OVERRIDE_EVENT_TYPE]:
        current_user = get_current_user()
        instructor_id = getattr(current_user, 'id', None)
        tracker.emit(
            str(root_type),
            {
                'course_id': str(kwargs['course_id']),
                'user_id': str(kwargs['user_id']),
                'problem_id': str(kwargs['usage_id']),
                'new_weighted_earned': kwargs.get('weighted_earned'),
                'new_weighted_possible': kwargs.get('weighted_possible'),
                'only_if_higher': kwargs.get('only_if_higher'),
                'instructor_id': str(instructor_id),
                'event_transaction_id': str(get_event_transaction_id()),
                'event_transaction_type': str(root_type),
            }
        )

    elif root_type in [SUBSECTION_OVERRIDE_EVENT_TYPE]:
        tracker.emit(
            str(root_type),
            {
                'course_id': str(kwargs['course_id']),
                'user_id': str(kwargs['user_id']),
                'problem_id': str(kwargs['usage_id']),
                'only_if_higher': kwargs.get('only_if_higher'),
                'override_deleted': kwargs.get('score_deleted', False),
                'event_transaction_id': str(get_event_transaction_id()),
                'event_transaction_type': str(root_type),
            }
        )


def subsection_grade_calculated(subsection_grade):
    """
    Emits an edx.grades.subsection.grade_calculated event
    with data from the passed subsection_grade.
    """
    event_name = SUBSECTION_GRADE_CALCULATED
    context = contexts.course_context_from_course_id(subsection_grade.course_id)
    # TODO (AN-6134): remove this context manager
    with tracker.get_tracker().context(event_name, context):
        tracker.emit(
            event_name,
            {
                'user_id': str(subsection_grade.user_id),
                'course_id': str(subsection_grade.course_id),
                'block_id': str(subsection_grade.usage_key),
                'course_version': str(subsection_grade.course_version),
                'weighted_total_earned': subsection_grade.earned_all,
                'weighted_total_possible': subsection_grade.possible_all,
                'weighted_graded_earned': subsection_grade.earned_graded,
                'weighted_graded_possible': subsection_grade.possible_graded,
                'first_attempted': str(subsection_grade.first_attempted),
                'subtree_edited_timestamp': str(subsection_grade.subtree_edited_timestamp),
                'event_transaction_id': str(get_event_transaction_id()),
                'event_transaction_type': str(get_event_transaction_type()),
                'visible_blocks_hash': str(subsection_grade.visible_blocks_id),
            }
        )


def course_grade_calculated(course_grade):
    """
    Emits an edx.grades.course.grade_calculated event
    with data from the passed course_grade.
    """
    event_name = COURSE_GRADE_CALCULATED
    context = contexts.course_context_from_course_id(course_grade.course_id)
    # TODO (AN-6134): remove this context manager
    with tracker.get_tracker().context(event_name, context):
        tracker.emit(
            event_name,
            {
                'user_id': str(course_grade.user_id),
                'course_id': str(course_grade.course_id),
                'course_version': str(course_grade.course_version),
                'percent_grade': course_grade.percent_grade,
                'letter_grade': str(course_grade.letter_grade),
                'course_edited_timestamp': str(course_grade.course_edited_timestamp),
                'event_transaction_id': str(get_event_transaction_id()),
                'event_transaction_type': str(get_event_transaction_type()),
                'grading_policy_hash': str(course_grade.grading_policy_hash),
            }
        )
