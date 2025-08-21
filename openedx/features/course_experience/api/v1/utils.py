
"""
Course Experience API utilities.
"""
from eventtracking import tracker

from lms.djangoapps.courseware.access import has_access
from lms.djangoapps.courseware.masquerade import is_masquerading, setup_masquerade
from lms.djangoapps.course_api.api import course_detail
from openedx.core.djangoapps.schedules.utils import reset_self_paced_schedule
from openedx.features.course_experience.utils import dates_banner_should_display


def reset_deadlines_for_course(request, course_key, research_event_data={}):  # lint-amnesty, pylint: disable=dangerous-default-value
    """
    Set the start_date of a schedule to today, which in turn will adjust due dates for
    sequentials belonging to a self paced course

    Args:
        request (Request): The request object
        course_key (str): The course key
        research_event_data (dict): Any data that should be included in the research tracking event
            Example: sending the location of where the reset deadlines banner (i.e. outline-tab)
    """

    course_masquerade, user = setup_masquerade(
        request,
        course_key,
        has_access(request.user, 'staff', course_key)
    )

    # We ignore the missed_deadlines because this util is used in endpoint from the Learning MFE for
    # learners who have remaining attempts on a problem and reset their due dates in order to
    # submit additional attempts. This can apply for 'completed' (submitted) content that would
    # not be marked as past_due
    _missed_deadlines, missed_gated_content = dates_banner_should_display(course_key, user)
    if not missed_gated_content:
        reset_self_paced_schedule(user, course_key)

        course_overview = course_detail(request, user.username, course_key)
        # For context here, research_event_data should already contain `location` indicating
        # the page/location dates were reset from and could also contain `block_id` if reset
        # within courseware.
        research_event_data.update({
            'courserun_key': str(course_key),
            'is_masquerading': is_masquerading(user, course_key, course_masquerade),
            'is_staff': has_access(user, 'staff', course_key).has_access,
            'org_key': course_overview.display_org_with_default,
            'user_id': user.id,
        })
        tracker.emit('edx.ui.lms.reset_deadlines.clicked', research_event_data)
