"""
Utility functions around course dates.

get_expected_duration: return the expected duration of a course (absent any user information)
"""

from datetime import timedelta
from typing import Optional

from openedx.core.djangoapps.catalog.utils import get_course_run_details
from openedx.core.djangoapps.course_date_signals.waffle import CUSTOM_RELATIVE_DATES


MIN_DURATION = timedelta(weeks=4)
MAX_DURATION = timedelta(weeks=18)


def get_expected_duration(course_id):
    """
    Return a `datetime.timedelta` defining the expected length of the supplied course.
    """

    access_duration = MIN_DURATION

    # The user course expiration date is the content availability date
    # plus the weeks_to_complete field from course-discovery.
    discovery_course_details = get_course_run_details(course_id, ['weeks_to_complete'])
    expected_weeks = discovery_course_details.get('weeks_to_complete')
    if expected_weeks:
        access_duration = timedelta(weeks=expected_weeks)

    # Course access duration is bounded by the min and max duration.
    access_duration = max(MIN_DURATION, min(MAX_DURATION, access_duration))

    return access_duration


def get_expected_duration_based_on_relative_due_dates(course) -> timedelta:
    """
    Calculate duration based on custom relative due dates.
    Returns the longest relative due date if set else a minimum duration of 1 week.
    """
    duration_in_weeks = 1
    if CUSTOM_RELATIVE_DATES.is_enabled(course.id):
        for section in course.get_children():
            if section.visible_to_staff_only:
                continue
            for subsection in section.get_children():
                relative_weeks_due = subsection.fields['relative_weeks_due'].read_from(subsection)
                if relative_weeks_due and relative_weeks_due > duration_in_weeks:
                    duration_in_weeks = relative_weeks_due
    return timedelta(weeks=duration_in_weeks)


def spaced_out_sections(course, duration: Optional[timedelta] = None):
    """
    Generator that returns sections of the course block with a suggested time to complete for each

    Returns:
        index (int): index of section
        section (block): a section block of the course
        relative time (timedelta): the amount of weeks to complete the section, since start of course
    """
    if not duration:
        duration = get_expected_duration(course.id)
    sections = [
        section
        for section
        in course.get_children()
        if not section.visible_to_staff_only
    ]
    weeks_per_section = duration / (len(sections) or 1)  # if course has zero sections
    for idx, section in enumerate(sections):
        yield idx, section, weeks_per_section * (idx + 1)
