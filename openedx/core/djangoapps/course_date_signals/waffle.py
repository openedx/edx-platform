"""
This module contains various configuration settings via
waffle switches for the course_date_signals app.
"""


from openedx.core.djangoapps.waffle_utils import CourseWaffleFlag

# .. toggle_name: studio.custom_relative_dates
# .. toggle_implementation: CourseWaffleFlag
# .. toggle_default: False
# .. toggle_description: Waffle flag to enable custom pacing input for Personalized Learner Schedule (PLS).
# ..    This flag guards an input in Studio for a self paced course, where the user can enter date offsets
# ..    for a subsection.
# .. toggle_use_cases: temporary
# .. toggle_creation_date: 2021-07-12
# .. toggle_target_removal_date: 2021-12-31
# .. toggle_warning: Flag course_experience.relative_dates should also be active for relative dates functionalities to work.
# .. toggle_tickets: https://openedx.atlassian.net/browse/AA-844
CUSTOM_RELATIVE_DATES = CourseWaffleFlag('studio.custom_relative_dates', __name__)
