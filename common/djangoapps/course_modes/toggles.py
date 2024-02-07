"""
Toggles for the Course Modes app
"""

from edx_toggles.toggles import WaffleFlag


# .. toggle_name: course_modes.extend_certificate_relevant_modes_with_honor
# .. toggle_implementation: WaffleFlag
# .. toggle_default: False
# .. toggle_description: Determines whether the HONOR certificates should be sent to the Credentials
#  service to update user credentials.
# .. toggle_use_cases: vip
# .. toggle_creation_date: 2022-06-21
# .. toggle_target_removal_date: None
# .. toggle_warnings: None
# .. toggle_tickets: RGOeX-1413
EXTEND_CERTIFICATE_RELEVANT_MODES_WITH_HONOR_FLAG = WaffleFlag(
    'course_modes.extend_certificate_relevant_modes_with_honor', __name__,
)
