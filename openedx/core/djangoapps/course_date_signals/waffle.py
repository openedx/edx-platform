"""
This module contains various configuration settings via waffle switches for
course date signals.
"""

from openedx.core.djangoapps.waffle_utils import CourseWaffleFlag

WAFFLE_FLAG_NAMESPACE = "course_date_signals"

# .. toggle_name: course_date_signals.relative_dates_disable_suggested_schedule
# .. toggle_implementation: CourseWaffleFlag
# .. toggle_default: False
# .. toggle_description: Waffle flag to disable suggested schedule for self paced courses.
#   When suggested schedule is enabled, graded content in self paced courses
#   will be assigned a suggested relative due date. Suggested relative due dates
#   are calculated by getting an average time needed per section, by getting an
#   estimated duration of a course and dividing it by a number of sections,
#   and then multiplying it by an index of a section that is currently being
#   assigned a due date. E.g. if a course is estimated to be 4 weeks, has 4
#   sections, and each one is marked as graded, the first section's relative due
#   date is going to be one week from the date of the enrollment, the second -
#   two weeks, etc.
#   The estimated course duration is fetched from the Course Discovery service,
#   and is clamped between 4 and 18 weeks. If Course Discovery is not available
#   or value is not set for a course that is being requested, the estimated time
#   would be set to 4 weeks.
# .. toggle_use_cases: open_edx
# .. toggle_creation_date: 2024-09-02
# .. toggle_target_removal_date: None
DISABLE_SPACED_OUT_SECTIONS = CourseWaffleFlag(
    f"{WAFFLE_FLAG_NAMESPACE}.relative_dates_disable_suggested_schedule", __name__
)
