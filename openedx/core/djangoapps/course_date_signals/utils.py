"""
Utility functions around course dates.

get_expected_duration: return the expected duration of a course (absent any user information)
"""

from datetime import timedelta

from course_modes.models import CourseMode
from openedx.core.djangoapps.catalog.utils import get_course_run_details


MIN_DURATION = timedelta(weeks=4)
MAX_DURATION = timedelta(weeks=18)


def get_expected_duration(course):
    """
    Return a `datetime.timedelta` defining the expected length of the supplied course.
    """

    access_duration = MIN_DURATION

    verified_mode = CourseMode.verified_mode_for_course(course=course, include_expired=True)

    if not verified_mode:
        return None

    # The user course expiration date is the content availability date
    # plus the weeks_to_complete field from course-discovery.
    discovery_course_details = get_course_run_details(course.id, ['weeks_to_complete'])
    expected_weeks = discovery_course_details.get('weeks_to_complete')
    if expected_weeks:
        access_duration = timedelta(weeks=expected_weeks)

    # Course access duration is bounded by the min and max duration.
    access_duration = max(MIN_DURATION, min(MAX_DURATION, access_duration))

    return access_duration
